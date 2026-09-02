from __future__ import annotations

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.ai_live_state_service import build_live_state_payload
from app.services.auth_service import authenticate_demo_account, get_auth_session
from app.services.network_service import build_priority_actions
from app.services.product_innovation_service import (
    refresh_market_scan,
    save_pilot_plan,
)
from app.services.reset_service import reset_demo_workspace
from app.services.workflow_persistence_service import (
    ensure_command_center_decisions,
    ensure_demand_inventory_workspace,
    save_command_center_decision,
    save_generated_replenishment_plan,
    save_inventory_rows,
)
from app.state.demo_state import get_brand_state, select_brand


def _canada_mutated_storage() -> tuple[dict, dict]:
    user_storage: dict = {}
    tab_storage: dict = {}
    assert authenticate_demo_account(user_storage, 'maplemason', 'vespercanada')
    brand_state = get_brand_state(user_storage, CANADA_BRAND_ID)

    actions = build_priority_actions(
        brand_state['network']['outlets'],
        brand_state['profile'],
    )
    ensure_command_center_decisions(brand_state, actions)
    save_command_center_decision(
        brand_state,
        action_id=actions[0]['id'],
        status=actions[0]['approved_status'],
        action_items=actions,
    )

    workflow = ensure_demand_inventory_workspace(
        brand_state,
        default_region='Ontario',
        default_outlet_id='ca-toronto-1',
    )
    workflow['planning_horizon'] = 14
    save_inventory_rows(
        brand_state,
        [
            {
                'product': 'Maple Cream Cold Brew',
                'status': 'Stockout risk',
                'action_type': 'Transfer',
                'action_quantity': 18,
                'transfer_source': 'Queen Street West',
            }
        ],
    )
    save_generated_replenishment_plan(
        brand_state,
        outlet_id='ca-toronto-1',
        plan_rows=[
            {
                'id': 'store_transfer',
                'plan': 'Store transfer',
                'scope': '18 units · 1 product',
                'cost': 'C$43.10',
                'total_cost_value': 43.10,
                'status': 'Ready for approval',
                'plan_type': 'transfer',
                'expected_completion': '02 Sep · 10:30',
                'details': [
                    {
                        'product': 'Maple Cream Cold Brew',
                        'source': 'Queen Street West',
                        'destination': 'Yorkville',
                        'quantity': 18,
                        'eta': '02 Sep · 10:30',
                        'cost': 'C$43.10',
                    }
                ],
            }
        ],
    )

    refresh_market_scan(brand_state)
    save_pilot_plan(
        brand_state,
        concept_id='maple_protein_cold_brew',
        markets=['Toronto', 'Vancouver'],
        outlet_count=5,
        duration_weeks=4,
        test_price=7.45,
    )

    tab_storage[f'vesper_outlet_intelligence_v2:{CANADA_BRAND_ID}'] = {
        'candidates': {
            'custom': {
                'name': 'King Street West Test Site',
                'city': 'Toronto',
                'state': 'Ontario',
                'address': 'King Street West, Toronto, ON',
                'status': 'Review',
                'score': 91,
                'sales': 166000,
                'rent': 14750,
                'margin': 22.1,
                'break_even': 15,
                'cannibalization': 'Low',
                'analysis_status': 'Analyzed',
            }
        },
        'decisions': {'custom': 'Shortlisted'},
    }
    user_storage['vesper_ai_chat'] = {'history': [{'role': 'user', 'content': 'old'}]}
    return user_storage, tab_storage


def test_live_state_reflects_current_canada_workflows() -> None:
    user_storage, tab_storage = _canada_mutated_storage()
    brand_state = get_brand_state(user_storage, CANADA_BRAND_ID)
    payload = build_live_state_payload(
        brand_state,
        user_query='What is happening in Toronto and what did I plan?',
        page_name='Command Center',
        outlet_candidate_state=tab_storage[
            f'vesper_outlet_intelligence_v2:{CANADA_BRAND_ID}'
        ],
    )

    assert payload['company_summary']['brand'] == 'Maple & Mason Café — Canada'
    assert payload['company_summary']['currency'] == 'CAD'
    assert payload['demand_inventory']['planning_horizon_days'] == 14
    assert payload['demand_inventory']['plan_generated'] is True
    assert payload['replenishment_artifacts']['transfer_plans'][0]['items'][0][
        'product'
    ] == 'Maple Cream Cold Brew'
    assert payload['location_candidates'][0]['name'] == 'King Street West Test Site'
    assert payload['location_candidates'][0]['management_decision'] == 'Shortlisted'
    assert payload['product_innovation']['market_scan_run_number'] == 1
    assert any(
        row['pilot'] and row['pilot']['outlet_count'] == 5
        for row in payload['product_innovation']['opportunities']
    )
    assert any(
        status != 'Awaiting decision'
        for status in payload['decisions']['command_center']['statuses'].values()
    )


def test_query_aware_outlet_context_matches_named_city() -> None:
    storage: dict = {}
    state = select_brand(storage, CANADA_BRAND_ID)
    payload = build_live_state_payload(
        state,
        user_query='How are the Vancouver outlets performing?',
        page_name='Network Intelligence',
    )
    rows = payload['relevant_existing_outlets']
    assert rows
    assert all(row['city'] == 'Vancouver' for row in rows)


def test_reset_restores_only_current_brand_and_preserves_authentication() -> None:
    user_storage, tab_storage = _canada_mutated_storage()

    india_state = select_brand(user_storage, INDIA_BRAND_ID)
    india_state['workflows']['network_intelligence']['analysis_run_number'] = 7
    select_brand(user_storage, CANADA_BRAND_ID)

    fresh = reset_demo_workspace(
        user_storage,
        tab_storage,
        CANADA_BRAND_ID,
    )

    assert get_auth_session(user_storage)['brand_id'] == CANADA_BRAND_ID
    assert fresh['workflows']['demand_inventory']['forecast_run_number'] == 0
    assert fresh['workflows']['demand_inventory']['planning_run_number'] == 0
    assert fresh['decisions']['command_center'] == {}
    assert fresh['artifacts']['purchase_plans'] == []
    assert fresh['artifacts']['transfer_plans'] == []
    assert fresh['artifacts']['product_pilots'] == []
    assert 'vesper_ai_chat' not in user_storage
    assert f'vesper_outlet_intelligence_v2:{CANADA_BRAND_ID}' not in tab_storage

    # The other brand is deliberately untouched.
    assert get_brand_state(user_storage, INDIA_BRAND_ID)['workflows'][
        'network_intelligence'
    ]['analysis_run_number'] == 7
