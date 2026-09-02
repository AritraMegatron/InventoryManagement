from copy import deepcopy

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.demand_inventory_service import build_plan_summary, default_demand_selection
from app.services.network_service import build_command_center_snapshot
from app.services.workflow_persistence_service import (
    approve_replenishment_plan,
    clear_demand_action_workflow,
    ensure_command_center_decisions,
    ensure_demand_inventory_workspace,
    save_command_center_decision,
    save_generated_replenishment_plan,
    save_inventory_rows,
)
from app.state.demo_state import build_brand_state


def _workspace(brand_id: str):
    brand_state = build_brand_state(brand_id)
    region, outlet_id = default_demand_selection(brand_state)
    workspace = ensure_demand_inventory_workspace(
        brand_state,
        default_region=region,
        default_outlet_id=outlet_id,
    )
    return brand_state, workspace, outlet_id


def test_command_center_decision_survives_snapshot_rebuild():
    brand = build_brand_state(CANADA_BRAND_ID)
    snapshot = build_command_center_snapshot(brand['network']['outlets'], brand['profile'])
    decisions = ensure_command_center_decisions(brand, snapshot['actions'])
    assert decisions['statuses']['inventory_risk'] == 'Awaiting decision'

    save_command_center_decision(
        brand,
        action_id='inventory_risk',
        status='Approved · Transfer task created',
        action_items=snapshot['actions'],
    )

    rebuilt = build_command_center_snapshot(brand['network']['outlets'], brand['profile'])
    decisions = ensure_command_center_decisions(brand, rebuilt['actions'])
    assert decisions['statuses']['inventory_risk'].startswith('Approved')


def test_demand_workspace_persists_selection_and_rows():
    brand, workspace, _ = _workspace(CANADA_BRAND_ID)
    workspace['region'] = 'British Columbia'
    workspace['forecast_horizon'] = 14
    rows = [{'id': 1, 'product': 'Maple Cream Cold Brew', 'action_type': 'Order'}]
    save_inventory_rows(brand, rows)

    again = ensure_demand_inventory_workspace(
        brand,
        default_region='Ontario',
        default_outlet_id='ignored',
    )
    assert again['region'] == 'British Columbia'
    assert again['forecast_horizon'] == 14
    assert again['inventory_rows'] == rows


def test_generated_and_approved_plan_is_durable_and_artifact_backed():
    brand, workspace, outlet_id = _workspace(CANADA_BRAND_ID)
    inventory_rows = [
        {
            'product': 'Maple Cream Cold Brew',
            'action_type': 'Order',
            'action_quantity': 25,
        },
        {
            'product': 'Salted Maple Latte',
            'action_type': '',
            'action_quantity': 0,
        },
    ]
    save_inventory_rows(brand, inventory_rows)
    plan_rows = build_plan_summary(brand, outlet_id, inventory_rows)
    save_generated_replenishment_plan(
        brand,
        outlet_id=outlet_id,
        plan_rows=plan_rows,
    )

    assert workspace['plan_generated'] is True
    assert brand['artifacts']['purchase_plans']
    assert brand['decisions']['demand_inventory']['replenishment_plan']['status'] == 'Ready for approval'

    approved = approve_replenishment_plan(brand)
    assert any(row['status'] == 'Approved' for row in approved)
    assert workspace['plan_approved'] is True
    assert brand['decisions']['demand_inventory']['replenishment_plan']['status'] == 'Approved'


def test_planning_invalidation_clears_only_demand_action_artifacts():
    brand, workspace, _ = _workspace(INDIA_BRAND_ID)
    workspace['forecast_run_number'] = 4
    workspace['planning_run_number'] = 2
    workspace['inventory_built'] = True
    workspace['inventory_rows'] = [{'id': 1}]
    workspace['plan_rows'] = [{'id': 'purchase_order'}]
    brand['artifacts']['purchase_plans'] = [{'id': 'purchase_order'}]
    brand['artifacts']['product_pilots'] = [{'concept_id': 'keep_me'}]

    clear_demand_action_workflow(brand)

    assert workspace['forecast_run_number'] == 4
    assert workspace['planning_run_number'] == 2
    assert workspace['inventory_rows'] == []
    assert workspace['plan_rows'] == []
    assert brand['artifacts']['purchase_plans'] == []
    assert brand['artifacts']['product_pilots'] == [{'concept_id': 'keep_me'}]


def test_brand_workflows_are_isolated():
    india, india_workspace, _ = _workspace(INDIA_BRAND_ID)
    canada, canada_workspace, _ = _workspace(CANADA_BRAND_ID)
    india_workspace['plan_approved'] = True
    canada_workspace['plan_approved'] = False
    assert india['workflows']['demand_inventory']['plan_approved'] is True
    assert canada['workflows']['demand_inventory']['plan_approved'] is False
