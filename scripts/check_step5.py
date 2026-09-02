from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID, get_brand_profile
from app.data.outlet_candidates import clone_default_candidates
from app.services.currency_service import format_money
from app.services.location_service import create_location_service


def main() -> None:
    india = clone_default_candidates(INDIA_BRAND_ID)
    canada = clone_default_candidates(CANADA_BRAND_ID)
    ca_profile = get_brand_profile(CANADA_BRAND_ID)

    print(f'India candidates: {len(india)}')
    print('  ' + ', '.join(item['name'] for item in india.values()))
    print(f'Canada candidates: {len(canada)}')
    for item in canada.values():
        print(
            f"  {item['name']} · {item['city']}, {item['state']} · "
            f"rent {format_money(float(item['rent']), ca_profile)} · "
            f"sales {format_money(float(item['sales']), ca_profile)}"
        )

    service = create_location_service(ca_profile)
    results = asyncio.run(service.suggest('Toronto', limit=3))
    assert results and results[0].city == 'Toronto'
    print(f'Canada address fallback: PASS — {results[0].formatted_address}')

    assert all(float(item['lng']) < 0 for item in canada.values())
    assert all(41 <= float(item['lat']) <= 84 for item in canada.values())
    print('Canada map coordinates: PASS')
    print('STEP 5 CHECK: PASS')


if __name__ == '__main__':
    main()
