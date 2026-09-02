from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.currency_service import format_money
from app.state.demo_state import build_brand_state, get_brand_state, select_brand


def summarize(brand_id: str) -> None:
    state = build_brand_state(brand_id)
    profile = state['profile']
    outlets = state['network']['outlets']
    total_revenue = sum(row['monthly_revenue'] for row in outlets)
    total_profit = sum(row['operating_profit'] for row in outlets)
    underperforming = sum(row['status'] == 'Underperforming' for row in outlets)

    print(f"{profile['display_name']}")
    print(f"  Country: {profile['country']}")
    print(f"  Currency: {profile['currency_code']} ({profile['currency_symbol']})")
    print(f"  Outlets: {len(outlets)}")
    print(f"  Monthly revenue: {format_money(total_revenue, profile)}")
    print(f"  Operating profit: {format_money(total_profit, profile)}")
    print(f"  Underperforming outlets: {underperforming}")
    print()


def main() -> None:
    summarize(INDIA_BRAND_ID)
    summarize(CANADA_BRAND_ID)

    storage: dict = {}
    india = get_brand_state(storage, INDIA_BRAND_ID)
    india['decisions']['command_center']['local_test'] = 'india'

    canada = select_brand(storage, CANADA_BRAND_ID)
    canada['decisions']['command_center']['local_test'] = 'canada'

    assert get_brand_state(storage, INDIA_BRAND_ID)['decisions']['command_center']['local_test'] == 'india'
    assert get_brand_state(storage, CANADA_BRAND_ID)['decisions']['command_center']['local_test'] == 'canada'
    assert india['workflows']['demand_inventory']['forecast_run_number'] == 0
    assert india['workflows']['demand_inventory']['planning_run_number'] == 0

    print('STEP 1 CHECK: PASS')


if __name__ == '__main__':
    main()
