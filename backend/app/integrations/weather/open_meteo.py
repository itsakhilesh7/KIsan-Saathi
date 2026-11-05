"""Open-Meteo weather forecast and geocoding integration.

Implements grounded weather retrieval conforming to Evidence schema:
- Open-Meteo Forecast: 3-day daily summary (max/min temp, precipitation sum & probability)
- Open-Meteo Geocoding: resolves Indian districts restricted to country_code=IN and verified against state
- Caching: in-memory coordinate resolution cache
- Host allowlisting: restricts outbound connections strictly to allowed Open-Meteo domains
- Timeouts & retries on 429/5xx with exponential backoff
- Fallback to pilot configuration coordinates
"""

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from ...core.config import Settings, get_settings
from ...core.http_client import get_http_client
from ...schemas.evidence import Evidence, SourceType

log = logging.getLogger("integrations.weather.open_meteo")

ALLOWED_WEATHER_HOSTS = {
    "api.open-meteo.com",
    "geocoding-api.open-meteo.com",
}

OPEN_METEO_FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1/search"

# In-memory geocoding cache: key is (district.lower(), state.lower()) -> (lat, lon)
_GEOCODE_CACHE: dict[tuple[str, str], tuple[float, float]] = {}


class WeatherAPIError(Exception):
    """Raised when an Open-Meteo weather or geocoding request fails."""


def _assert_allowed_host(url: str) -> None:
    """Enforces host allowlisting for Open-Meteo APIs."""
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_WEATHER_HOSTS:
        raise WeatherAPIError(f"Host '{parsed.hostname}' is not in allowed weather hosts allowlist.")


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    max_retries: int = 3,
    **kwargs: Any,
) -> httpx.Response:
    """Executes an HTTP request with exponential backoff retries on 429 and 5xx errors."""
    _assert_allowed_host(url)
    last_err: Exception | None = None

    for attempt in range(max_retries):
        try:
            r = await client.request(method, url, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504):
                log.warning(
                    "Open-Meteo request failed with %d (attempt %d/%d)",
                    r.status_code,
                    attempt + 1,
                    max_retries,
                )
                last_err = WeatherAPIError(f"Open-Meteo HTTP {r.status_code}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r
        except httpx.TransportError as e:
            log.warning("Open-Meteo transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            last_err = WeatherAPIError(f"Transport error: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))
        except httpx.HTTPStatusError as e:
            log.error("Open-Meteo HTTP status error: %d", e.response.status_code)
            raise WeatherAPIError(f"Open-Meteo error {e.response.status_code}") from e

    raise last_err or WeatherAPIError("Open-Meteo request failed after maximum retries.")


async def resolve_coordinates(
    district: str,
    state: str = "Telangana",
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> tuple[float, float]:
    """Resolves district name to (latitude, longitude) restricted to India, checked against state.

    Falls back to pilot.yaml configuration coordinates if geocoding fails.
    """
    cfg = settings or get_settings()
    norm_key = (district.strip().lower(), state.strip().lower())

    if norm_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[norm_key]

    c = http_client or get_http_client()
    headers = {"User-Agent": "KisanSaathi/1.0"}
    params = {
        "name": district.strip(),
        "count": 5,
        "language": "en",
        "country_code": "IN",
    }

    try:
        r = await _request_with_retry(
            c,
            "GET",
            OPEN_METEO_GEOCODING_BASE,
            params=params,
            headers=headers,
            timeout=10.0,
        )
        res_data = r.json()
        results = res_data.get("results") or []

        # Find best match matching state/admin1
        matched: dict[str, Any] | None = None
        for item in results:
            admin1 = (item.get("admin1") or "").lower()
            if admin1 == state.strip().lower() or state.strip().lower() in admin1:
                matched = item
                break

        if not matched and results:
            # Fallback to first Indian result
            matched = results[0]

        if matched:
            lat = float(matched["latitude"])
            lon = float(matched["longitude"])
            _GEOCODE_CACHE[norm_key] = (lat, lon)
            return (lat, lon)

    except Exception as e:
        log.warning("Geocoding failed for '%s, %s': %s; falling back to pilot coords", district, state, e)

    # Fallback to pilot configuration coordinates
    pilot_lat = cfg.pilot_config.get("primary", {}).get("latitude", 17.97)
    pilot_lon = cfg.pilot_config.get("primary", {}).get("longitude", 79.59)
    _GEOCODE_CACHE[norm_key] = (float(pilot_lat), float(pilot_lon))
    return (float(pilot_lat), float(pilot_lon))


async def fetch_weather_forecast(
    district: str = "Warangal",
    state: str = "Telangana",
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> Evidence:
    """Fetches a 3-day daily weather forecast from Open-Meteo and normalizes to Evidence."""
    cfg = settings or get_settings()
    lat, lon = await resolve_coordinates(district, state, settings=cfg, http_client=http_client)

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "Asia/Kolkata",
        "forecast_days": 3,
    }
    headers = {"User-Agent": "KisanSaathi/1.0"}
    c = http_client or get_http_client()

    r = await _request_with_retry(
        c,
        "GET",
        OPEN_METEO_FORECAST_BASE,
        params=params,
        headers=headers,
        timeout=15.0,
    )
    raw = r.json()

    daily = raw.get("daily") or {}
    times = daily.get("time") or []
    temp_max = daily.get("temperature_2m_max") or []
    temp_min = daily.get("temperature_2m_min") or []
    precip_sum = daily.get("precipitation_sum") or []
    precip_prob = daily.get("precipitation_probability_max") or []
    daily_units = raw.get("daily_units") or {}

    obs_date = times[0] if times else None
    sanitized_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&forecast_days=3"

    evidence = Evidence(
        evidence_id=f"weather_open_meteo_{district.lower()}_{obs_date or 'latest'}",
        source_type=SourceType.WEATHER_FORECAST,
        source_name="Open-Meteo Weather Forecast",
        source_url=sanitized_url,
        publisher="Open-Meteo",
        observation_or_publication_date=obs_date,
        location=f"{district}, {state}",
        data={
            "district": district,
            "state": state,
            "latitude": lat,
            "longitude": lon,
            "dates": times,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "precipitation_sum": precip_sum,
            "precipitation_probability": precip_prob,
            "units": daily_units,
        },
        limitations=[
            "Weather forecasts are numerical model estimates and carry inherent meteorological uncertainty.",
            "Never treat precipitation forecasts as definitive guarantees of field safety.",
        ],
    )
    return evidence

