from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID, get_brand_profile
from app.data.network_demo_data import build_network_rows
from app.services.currency_service import format_money
from app.services.network_service import (
    build_command_center_snapshot,
    build_region_centers,
    build_table_columns,
)


def print_brand(brand_id: str) -> None:
    profile = get_brand_profile(brand_id)
    outlets = build_network_rows(brand_id)
    snapshot = build_command_center_snapshot(outlets, profile)
    summary = snapshot['summary']
    regions = list(build_region_centers(outlets, profile))
    money_columns = [
        column['label']
        for column in build_table_columns(profile)
        if column['name'] in {
            'revenue_unit',
            'profit_unit',
            'forecast_unit',
            'revenue_per_employee_unit',
        }
    ]

    print(profile['display_name'])
    print(f"  Outlets: {summary['outlet_count']}")
    print(f"  Revenue: {format_money(summary['monthly_revenue'], profile)}")
    print(f"  Forecast: {format_money(summary['next_month_revenue'], profile)}")
    print(f"  Profit: {format_money(summary['operating_profit'], profile)}")
    print(f"  Underperforming: {summary['underperforming_count']}")
    print(f"  Revenue at risk: {format_money(snapshot['revenue_at_risk'], profile)}")
    print(f"  Regions: {', '.join(regions[1:])}")
    print(f"  Money columns: {', '.join(money_columns)}")
    for action in snapshot['actions']:
        print(f"  Action: {action['title']} — {action['impact']}")
    print()


def main() -> None:
    india = build_command_center_snapshot(
        build_network_rows(INDIA_BRAND_ID),
        get_brand_profile(INDIA_BRAND_ID),
    )
    canada = build_command_center_snapshot(
        build_network_rows(CANADA_BRAND_ID),
        get_brand_profile(CANADA_BRAND_ID),
    )

    assert india['summary']['outlet_count'] == 63
    assert canada['summary']['outlet_count'] == 24
    assert india['summary']['underperforming_count'] == 19
    assert canada['summary']['underperforming_count'] == 7

    print_brand(INDIA_BRAND_ID)
    print_brand(CANADA_BRAND_ID)
    print('STEP 3 CHECK: PASS')


if __name__ == '__main__':
    main()
