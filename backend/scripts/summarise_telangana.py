"""Summarises Telangana mandi data from live data.gov.in Agmarknet API."""

import asyncio
import logging
from collections import defaultdict

from backend.app.core.config import get_settings
from backend.app.integrations.data_gov.mandi import fetch_mandi_prices

logging.basicConfig(level=logging.WARNING)


async def main():
    settings = get_settings()
    if not settings.DATA_GOV_API_KEY:
        print("ERROR: DATA_GOV_API_KEY is missing from backend/.env")
        return

    print("Fetching live Agmarknet records for Telangana...")
    evidence_list = await fetch_mandi_prices(state="Telangana", limit=1000, settings=settings)
    print(f"Total records fetched for Telangana: {len(evidence_list)}")

    districts = defaultdict(int)
    commodities = defaultdict(int)
    markets = defaultdict(int)
    warangal_by_comm = defaultdict(list)
    chilli_records = []

    for ev in evidence_list:
        d = ev.data
        dist = d.get("district") or "Unknown"
        comm = d.get("commodity") or "Unknown"
        mkt = d.get("market") or "Unknown"

        districts[dist] += 1
        commodities[comm] += 1
        markets[mkt] += 1

        if "chilli" in comm.lower() or "mirchi" in comm.lower():
            chilli_records.append(d)

        if "warangal" in dist.lower():
            warangal_by_comm[comm].append(d)

    print("\n=================== TELANGANA DISTRICTS ===================")
    for dist, count in sorted(districts.items(), key=lambda x: -x[1]):
        print(f"  {dist:<25}: {count} records")

    print("\n=================== TELANGANA TOP COMMODITIES ===================")
    for comm, count in sorted(commodities.items(), key=lambda x: -x[1])[:25]:
        print(f"  {comm:<25}: {count} records")

    print("\n=================== CHILLI COMMODITIES IN DATASET ===================")
    chilli_comms = set(r.get("commodity") for r in chilli_records)
    for c in sorted(chilli_comms):
        samples = [r for r in chilli_records if r.get("commodity") == c][:2]
        print(f"  Commodity: '{c}' ({len([r for r in chilli_records if r.get('commodity') == c])} records)")
        for s in samples:
            print(f"    Sample: District={s.get('district')}, Market={s.get('market')}, Variety={s.get('variety')}, Modal={s.get('modal_price')}")

    print("\n=================== WARANGAL DISTRICT BREAKDOWN ===================")
    print(f"Total commodities reporting in Warangal: {len(warangal_by_comm)}")
    for comm, rows in sorted(warangal_by_comm.items(), key=lambda x: -len(x[1])):
        mkt_list = sorted(set(r.get("market") for r in rows))
        print(f"\n  Commodity: {comm} ({len(rows)} records across {len(mkt_list)} markets: {', '.join(mkt_list)})")
        for r in rows[:5]:
            print(f"    Market: {r.get('market'):<20} | Variety: {r.get('variety'):<15} | Modal: {r.get('modal_price')} | Date: {r.get('arrival_date')}")


if __name__ == "__main__":
    asyncio.run(main())

