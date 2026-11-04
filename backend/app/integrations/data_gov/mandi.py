"""Agmarknet Mandi daily prices connector for data.gov.in.

Fetches daily mandi commodity prices, validates against Evidence schema,
handles pagination and retries, and strictly suppresses credentials in URLs and logs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from ...core.config import Settings, get_settings
from ...core.http_client import get_http_client
from ...schemas.evidence import Evidence, SourceType
from .commodity_resolver import resolve_commodity

log = logging.getLogger("integrations.data_gov.mandi")


class MandiAPIError(Exception):
    """Raised when an operation on the data.gov.in Mandi API fails."""


def _parse_arrival_date(raw_date: str | None) -> str | None:
    """Parses date string from Agmarknet ('DD/MM/YYYY' or ISO) into ISO 'YYYY-MM-DD'."""
    if not raw_date or not isinstance(raw_date, str):
        return None

    cleaned = raw_date.strip()
    # Try parsing DD/MM/YYYY
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return cleaned


def _parse_price(val: Any) -> float | None:
    """Safely casts price fields to float, returning None if unparseable or missing."""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def sanitize_source_url(base_url: str, resource_id: str, filters: dict[str, str]) -> str:
    """Constructs a clean, auditable source URL without api-key."""
    query_parts = ["format=json"]
    for k, v in sorted(filters.items()):
        query_parts.append(f"filters[{k}]={v}")
    return f"{base_url.rstrip('/')}/{resource_id}?{'&'.join(query_parts)}"


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any],
    max_retries: int = 3,
    timeout: float = 60.0,
) -> httpx.Response:
    """Executes GET request with exponential backoff on 429 and 5xx."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    last_err: Exception | None = None

    for attempt in range(max_retries):
        try:
            r = await client.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                log.warning("data.gov.in returned %d (attempt %d/%d)", r.status_code, attempt + 1, max_retries)
                last_err = MandiAPIError(f"HTTP {r.status_code} from data.gov.in")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue

            r.raise_for_status()
            return r
        except httpx.TransportError as e:
            log.warning("data.gov.in transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            last_err = MandiAPIError(f"Transport error connecting to data.gov.in: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))
        except httpx.HTTPStatusError as e:
            log.error("data.gov.in HTTP status error: %d", e.response.status_code)
            raise MandiAPIError(f"data.gov.in error HTTP {e.response.status_code}") from e

    raise last_err or MandiAPIError("data.gov.in request failed after max retries.")


async def fetch_mandi_prices(
    commodity: str | None = None,
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[Evidence]:
    """Queries Agmarknet daily mandi prices from data.gov.in and normalizes to Evidence objects."""
    cfg = settings or get_settings()
    c = client or get_http_client()

    api_key = cfg.DATA_GOV_API_KEY.strip().strip("<>").strip()
    if not api_key:
        raise MandiAPIError("DATA_GOV_API_KEY is not configured in backend/.env.")

    # Resolve commodity alias if given (e.g. 'పత్తి' -> 'Cotton')
    canonical_commodity = resolve_commodity(commodity) if commodity else None
    search_commodity = canonical_commodity or commodity

    # Build query filters
    filters: dict[str, str] = {}
    if state:
        filters["state"] = state
    if district:
        filters["district"] = district
    if market:
        filters["market"] = market
    if search_commodity:
        filters["commodity"] = search_commodity

    params: dict[str, Any] = {
        "api-key": api_key,
        "format": "json",
        "offset": str(offset),
        "limit": str(limit),
    }
    for k, v in filters.items():
        params[f"filters[{k}]"] = v

    url = f"{cfg.DATA_GOV_BASE_URL.rstrip('/')}/{cfg.MANDI_RESOURCE_ID}"
    clean_source_url = sanitize_source_url(cfg.DATA_GOV_BASE_URL, cfg.MANDI_RESOURCE_ID, filters)

    log.info("Querying mandi prices with filters: %s", filters)

    try:
        resp = await _get_with_retry(c, url, params=params, timeout=60.0)
        body = resp.json()
    except Exception as e:
        log.exception("Failed to query data.gov.in mandi dataset")
        raise MandiAPIError(f"Query to data.gov.in failed: {e}") from e

    raw_records = body.get("records", [])
    if not raw_records:
        log.info("Zero mandi records returned for filters: %s", filters)
        return []

    evidence_list: list[Evidence] = []
    for r in raw_records:
        rec_state = r.get("state") or state or "Unknown"
        rec_district = r.get("district") or district or "Unknown"
        rec_market = r.get("market") or market or "Unknown"
        rec_commodity = r.get("commodity") or search_commodity or "Unknown"
        rec_variety = r.get("variety")
        rec_grade = r.get("grade")

        raw_arrival = r.get("arrival_date")
        arrival_iso = _parse_arrival_date(raw_arrival)

        min_p = _parse_price(r.get("min_price"))
        max_p = _parse_price(r.get("max_price"))
        modal_p = _parse_price(r.get("modal_price"))

        # Build clean ID
        slug_parts = [rec_state, rec_district, rec_market, rec_commodity, arrival_iso or "na"]
        slug = "_".join(str(p).replace(" ", "-").replace("/", "-") for p in slug_parts).lower()
        evidence_id = f"mandi_{slug}"

        ev = Evidence(
            evidence_id=evidence_id,
            source_type=SourceType.MANDI_RECORD,
            source_name="Agmarknet Mandi Daily Prices",
            source_url=clean_source_url,
            publisher="Directorate of Marketing & Inspection (DMI), via data.gov.in",
            observation_or_publication_date=arrival_iso,
            location=f"{rec_market}, {rec_district}, {rec_state}",
            data={
                "state": rec_state,
                "district": rec_district,
                "market": rec_market,
                "commodity": rec_commodity,
                "variety": rec_variety,
                "grade": rec_grade,
                "arrival_date": arrival_iso,
                "raw_arrival_date": raw_arrival,
                "min_price": min_p,
                "max_price": max_p,
                "modal_price": modal_p,
                "unit": "price as reported",
            },
            limitations=[
                "Daily reported price from Agmarknet, not a live real-time continuous quote.",
                "Dataset provides no explicit unit field; prices reported as modal values.",
            ],
        )
        evidence_list.append(ev)

    return evidence_list
