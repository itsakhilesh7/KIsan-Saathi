"""Prefetches and caches Agmarknet mandi daily prices for the pilot district and state fallbacks.

Pilot targets:
- State: Telangana, District: Warangal
- Commodities: Paddy (Common & Fine), Cotton, Green Chilli, Dry Chillies, Tomato
- Plus Telangana state-level fallbacks for Cotton and Dry Chillies.

Reports record counts, prices, and whether older arrival dates are returned by the live API.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from backend.app.core.config import get_settings
from backend.app.core.http_client import get_http_client
from backend.app.integrations.data_gov.mandi import fetch_mandi_prices
from backend.app.integrations.data_gov.mandi_cache import get_mandi_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("prefetch_mandi")


async def run_prefetch() -> dict[str, Any]:
    settings = get_settings()
    cache = get_mandi_cache()
    client = get_http_client()

    targets = [
        {"state": "Telangana", "district": "Warangal", "commodity": "Paddy(Common)"},
        {"state": "Telangana", "district": "Warangal", "commodity": "Cotton"},
        {"state": "Telangana", "district": "Warangal", "commodity": "Green Chilli"},
        {"state": "Telangana", "district": "Warangal", "commodity": "Dry Chillies"},
        {"state": "Telangana", "district": "Warangal", "commodity": "Tomato"},
        {"state": "Telangana", "district": None, "commodity": "Cotton"},
        {"state": "Telangana", "district": None, "commodity": "Dry Chillies"},
    ]

    total_cached = 0
    results_summary = []
    now = datetime.now(timezone.utc)

    print("=" * 80)
    print("STARTING MANDI CACHE PREFETCH FOR PILOT (WARANGAL, TELANGANA)")
    print("=" * 80)

    for t in targets:
        st = t["state"]
        dist = t["district"]
        comm = t["commodity"]
        loc_label = f"{dist}, {st}" if dist else f"{st} (State Level)"

        print(f"\nFetching: {comm} in {loc_label}...")
        try:
            evidence = await fetch_mandi_prices(
                commodity=comm,
                state=st,
                district=dist,
                settings=settings,
                client=client,
                use_cache=True,
            )
            count = len(evidence)
            total_cached += count

            dates_seen = []
            for ev in evidence:
                d = ev.data
                arr_date = d.get("arrival_date")
                mkt = d.get("market")
                modal = d.get("modal_price")
                dates_seen.append(arr_date)
                print(f"  -> Market: {mkt} | Variety: {d.get('variety')} | Price: Rs {modal} | Date: {arr_date}")

            unique_dates = sorted(set(d for d in dates_seen if d), reverse=True)
            results_summary.append({
                "commodity": comm,
                "location": loc_label,
                "records_count": count,
                "arrival_dates": unique_dates,
            })
        except Exception as e:
            print(f"  ERROR fetching {comm}: {e}")
            results_summary.append({
                "commodity": comm,
                "location": loc_label,
                "records_count": 0,
                "error": str(e),
                "arrival_dates": [],
            })

    print("\n" + "=" * 80)
    print("PREFETCH SUMMARY & ARRIVAL DATES REPORT")
    print("=" * 80)
    print(f"Total evidence records cached: {total_cached}")
    print(f"Cache location: {cache.db_path}\n")

    print("| Target Commodity | Target Location | Records Found | Arrival Dates Reported | Older Dates Detected? |")
    print("|---|---|---|---|---|")

    today_str = now.strftime("%Y-%m-%d")
    for r in results_summary:
        dates = r.get("arrival_dates", [])
        dates_str = ", ".join(dates) if dates else "None"
        older = any(d < today_str for d in dates) if dates else "N/A"
        print(f"| {r['commodity']} | {r['location']} | {r['records_count']} | {dates_str} | {older} |")

    return {
        "total_cached": total_cached,
        "results": results_summary,
    }


if __name__ == "__main__":
    asyncio.run(run_prefetch())
