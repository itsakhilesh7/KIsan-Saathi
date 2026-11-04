"""One-time live verification script for data.gov.in Agmarknet mandi API.

Fetches live records for Telangana, analyzes real field formats, extracts unique
commodities/districts, and saves a sanitized fixture to backend/tests/fixtures/.
CRITICAL: Never logs or prints DATA_GOV_API_KEY.
"""

import asyncio
import json
from pathlib import Path

import httpx

from backend.app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    api_key = settings.DATA_GOV_API_KEY.strip().strip("<>").strip()

    if not api_key:
        print("[!] DATA_GOV_API_KEY is not set in backend/.env!")
        return

    print(f"[*] API key present, length: {len(api_key)}, prefix: {api_key[:6]}")
    url = f"{settings.DATA_GOV_BASE_URL}/{settings.MANDI_RESOURCE_ID}"
    params = {
        "api-key": api_key,
        "format": "json",
        "offset": "0",
        "limit": "50",
        "filters[state]": "Telangana",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    print("[*] Querying live data.gov.in Mandi API for Telangana (limit=10, timeout=60s)...")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers=headers)

    print(f"[*] Response Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"[!] Error response: {resp.text[:300]}")
        return

    data = resp.json()
    status = data.get("status")
    total = data.get("total")
    count = data.get("count")
    records = data.get("records", [])

    print(f"[*] Status: {status}, Total Available: {total}, Returned Count: {count}")
    print(f"[*] Updated Date: {data.get('updated_date')}")

    if not records:
        print("[!] No records returned for Telangana with filter. Let's inspect raw keys:")
        print(list(data.keys()))
        return

    first = records[0]
    print("\n[*] Sample Record Keys and Types:")
    for k, v in first.items():
        print(f"    - {k}: {repr(v)} ({type(v).__name__})")

    commodities = sorted({r.get("commodity") for r in records if r.get("commodity")})
    districts = sorted({r.get("district") for r in records if r.get("district")})
    markets = sorted({r.get("market") for r in records if r.get("market")})

    print(f"\n[*] Unique Commodities ({len(commodities)}): {commodities}")
    print(f"[*] Unique Districts ({len(districts)}): {districts}")
    print(f"[*] Unique Markets ({len(markets)}): {markets[:10]}...")

    # Save sanitized fixture for unit tests
    fixtures_dir = Path("backend/tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixtures_dir / "mandi_telangana_sample.json"

    sanitized_data = {
        "status": status,
        "total": str(total),
        "count": str(count),
        "limit": "50",
        "offset": "0",
        "updated_date": data.get("updated_date", "2026-11-04"),
        "records": records,
    }

    fixture_path.write_text(json.dumps(sanitized_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Sanitized fixture saved to {fixture_path}")


if __name__ == "__main__":
    asyncio.run(main())
