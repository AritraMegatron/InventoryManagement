from __future__ import annotations

from copy import deepcopy

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.demand_inventory_service import (
    advance_forecast_run,
    advance_planning_run,
    build_dashboard_snapshot,
    build_inventory_planning_data,
    build_plan_summary,
    default_demand_selection,
    ensure_usable_stock,
    format_demand_money,
    get_demand_regions,
    outlets_for_region,
)
from app.state.demo_state import build_brand_state


def test_canada_demand_context_is_tenant_specific() -> None:
    state = build_brand_state(CANADA_BRAND_ID)
    region, outlet_id = default_demand_selection(state)

    assert region == 'Ontario'
    assert outlet_id.startswith('ca-')
    assert 'Ontario' in get_demand_regions(state)
    assert 'Quebec' in get_demand_regions(state)
    assert len(outlets_for_region(state, 'Ontario')) >= 4

    snapshot = build_dashboard_snapshot(state, outlet_id, horizon=7, run_number=0)
    product_names = {row['product'] for row in snapshot['inventory_rows']}

    assert snapshot['outlet'].city in {'Toronto', 'Mississauga', 'Ottawa', 'Hamilton'}
    assert 'Maple Cream Cold Brew' in product_names
    assert any(signal['label'] == 'NHL home-game night' for signal in snapshot['signals']) or len(snapshot['signals']) == 3
    assert format_demand_money(snapshot['kpis']['expected_revenue'], state['profile']).startswith('C$')


def test_india_demand_context_still_uses_existing_demo() -> None:
    state = build_brand_state(INDIA_BRAND_ID)
    region, outlet_id = default_demand_selection(state)
    snapshot = build_dashboard_snapshot(state, outlet_id, horizon=7, run_number=0)

    assert region == 'Delhi NCR'
    assert outlet_id == 'dlf_noida'
    assert snapshot['outlet'].name == 'DLF Mall of India'
    assert snapshot['inventory_rows'][0]['product'] == 'Classic Cold Coffee'
    assert format_demand_money(snapshot['kpis']['expected_revenue'], state['profile']).startswith('₹')


def test_forecast_and_planning_counters_are_independent() -> None:
    state = build_brand_state(CANADA_BRAND_ID)
    workflow = state['workflows']['demand_inventory']

    assert workflow == {'forecast_run_number': 0, 'planning_run_number': 0}

    assert advance_forecast_run(state) == 1
    assert workflow['forecast_run_number'] == 1
    assert workflow['planning_run_number'] == 0

    assert advance_forecast_run(state) == 2
    assert workflow['forecast_run_number'] == 2
    assert workflow['planning_run_number'] == 0

    assert advance_planning_run(state) == 1
    assert workflow['forecast_run_number'] == 2
    assert workflow['planning_run_number'] == 1


def test_planning_rows_expose_usable_stock() -> None:
    for brand_id in (INDIA_BRAND_ID, CANADA_BRAND_ID):
        state = build_brand_state(brand_id)
        _, outlet_id = default_demand_selection(state)
        planning = ensure_usable_stock(
            build_inventory_planning_data(state, outlet_id, horizon=7, run_number=0)
        )

        for row in planning['inventory_rows']:
            assert row['usable_stock'] == max(0, row['on_hand'] - row['safety_stock'])


def test_canada_plan_documents_use_cad_and_canadian_demo_metadata() -> None:
    state = build_brand_state(CANADA_BRAND_ID)
    _, outlet_id = default_demand_selection(state)
    planning = ensure_usable_stock(
        build_inventory_planning_data(state, outlet_id, horizon=7, run_number=0)
    )
    rows = deepcopy(planning['inventory_rows'])

    rows[0]['action_type'] = 'Order'
    rows[0]['action_quantity'] = 12

    transfer_source = next(iter(rows[1]['transfer_options']))
    transfer_capacity = rows[1]['transfer_options'][transfer_source]
    rows[1]['action_type'] = 'Transfer'
    rows[1]['action_quantity'] = min(5, max(1, transfer_capacity))
    rows[1]['transfer_source'] = transfer_source

    plans = build_plan_summary(state, outlet_id, rows)
    purchase, transfer = plans

    assert purchase['company_name'] == 'Maple & Mason Café Canada'
    assert purchase['document_number'].startswith('PO-CA-')
    assert purchase['cost'].startswith('C$')
    assert purchase['status'] == 'Ready for approval'
    assert transfer['document_number'].startswith('STN-CA-')
    assert transfer['cost'].startswith('C$')
    assert transfer['status'] == 'Ready for approval'
