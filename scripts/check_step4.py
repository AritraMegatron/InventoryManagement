from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.demand_inventory_service import (
    advance_forecast_run,
    advance_planning_run,
    build_dashboard_snapshot,
    build_inventory_planning_data,
    default_demand_selection,
    ensure_usable_stock,
    format_demand_money,
    get_demand_regions,
)
from app.state.demo_state import build_brand_state


def show_brand(brand_id: str) -> None:
    state = build_brand_state(brand_id)
    profile = state['profile']
    region, outlet_id = default_demand_selection(state)
    snapshot = build_dashboard_snapshot(state, outlet_id, horizon=7, run_number=0)
    planning = ensure_usable_stock(
        build_inventory_planning_data(state, outlet_id, horizon=7, run_number=0)
    )

    print(profile['display_name'])
    print(f"  Default region: {region}")
    print(f"  Regions: {', '.join(get_demand_regions(state)[1:])}")
    print(f"  Outlet: {snapshot['outlet'].name} · {snapshot['outlet'].city}")
    print(f"  Forecast demand: {snapshot['kpis']['predicted_units']:,} units")
    print(f"  Expected revenue: {format_demand_money(snapshot['kpis']['expected_revenue'], profile)}")
    print(f"  Inventory risks: {planning['at_risk_count']}")
    print(f"  Avoidable waste: {format_demand_money(planning['avoidable_waste'], profile)}")
    print(f"  Products: {', '.join(row['product'] for row in planning['inventory_rows'][:3])} ...")
    print()


def main() -> None:
    canada = build_brand_state(CANADA_BRAND_ID)
    workflow = canada['workflows']['demand_inventory']

    advance_forecast_run(canada)
    assert workflow['forecast_run_number'] == 1
    assert workflow['planning_run_number'] == 0

    advance_planning_run(canada)
    assert workflow['forecast_run_number'] == 1
    assert workflow['planning_run_number'] == 1

    show_brand(INDIA_BRAND_ID)
    show_brand(CANADA_BRAND_ID)
    print('Forecast/planning counters: INDEPENDENT')
    print('STEP 4 CHECK: PASS')


if __name__ == '__main__':
    main()
