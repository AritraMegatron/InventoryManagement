from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID
from app.services.ai_live_state_service import build_live_state_payload
from app.services.auth_service import authenticate_demo_account
from app.services.product_innovation_service import save_pilot_plan
from app.services.reset_service import reset_demo_workspace
from app.services.workflow_persistence_service import (
    ensure_demand_inventory_workspace,
    save_generated_replenishment_plan,
)
from app.state.demo_state import get_brand_state


def main() -> None:
    user_storage: dict = {}
    tab_storage: dict = {}
    assert authenticate_demo_account(user_storage, 'maplemason', 'vespercanada')
    state = get_brand_state(user_storage, CANADA_BRAND_ID)

    workflow = ensure_demand_inventory_workspace(
        state,
        default_region='Ontario',
        default_outlet_id='ca-toronto-1',
    )
    workflow['planning_horizon'] = 14
    save_generated_replenishment_plan(
        state,
        outlet_id='ca-toronto-1',
        plan_rows=[
            {
                'plan': 'Store transfer',
                'scope': '18 units · Maple Cream Cold Brew',
                'cost': 'C$43.10',
                'total_cost_value': 43.10,
                'status': 'Ready for approval',
                'plan_type': 'transfer',
                'expected_completion': 'Tomorrow · 10:30',
                'details': [
                    {
                        'product': 'Maple Cream Cold Brew',
                        'source': 'Queen Street West',
                        'destination': 'Yorkville',
                        'quantity': 18,
                        'eta': 'Tomorrow · 10:30',
                        'cost': 'C$43.10',
                    }
                ],
            }
        ],
    )
    save_pilot_plan(
        state,
        concept_id='maple_protein_cold_brew',
        markets=['Toronto', 'Vancouver'],
        outlet_count=5,
        duration_weeks=4,
        test_price=7.45,
    )

    payload = build_live_state_payload(
        state,
        user_query='What is my current plan and what needs attention?',
        page_name='Demand & Inventory',
    )
    print(payload['company_summary']['brand'])
    print('Currency:', payload['company_summary']['currency'])
    print('Planning horizon:', payload['demand_inventory']['planning_horizon_days'])
    print('Generated plan:', payload['demand_inventory']['plan_generated'])
    print('Product pilot count:', payload['artifact_counts']['product_pilots'])
    print('AI LIVE STATE: PASS')

    reset_demo_workspace(user_storage, tab_storage, CANADA_BRAND_ID)
    reset_state = get_brand_state(user_storage, CANADA_BRAND_ID)
    assert reset_state['decisions']['command_center'] == {}
    assert reset_state['artifacts']['product_pilots'] == []
    assert reset_state['workflows']['demand_inventory']['planning_run_number'] == 0
    print('RESET: PASS')
    print('STEP 8 CHECK: PASS')


if __name__ == '__main__':
    main()
