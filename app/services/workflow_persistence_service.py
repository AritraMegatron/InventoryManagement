from __future__ import annotations

from copy import deepcopy
from typing import Any


COMMAND_DECISION_VERSION = 1
DEMAND_WORKSPACE_VERSION = 4


def ensure_command_center_decisions(
    brand_state: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return durable per-brand Command Center decision state.

    Action ids are intentionally stable across synthetic network refreshes.  The
    presentation text may change as the network changes, but an executive
    decision remains attached to the business action id rather than to a page
    instance.
    """

    root = brand_state.setdefault('decisions', {}).setdefault('command_center', {})
    statuses = root.setdefault('statuses', {})

    if root.get('state_version') != COMMAND_DECISION_VERSION:
        preserved = {
            str(key): str(value)
            for key, value in statuses.items()
            if isinstance(key, str) and isinstance(value, str)
        }
        root.clear()
        root.update(
            {
                'state_version': COMMAND_DECISION_VERSION,
                'statuses': preserved,
            }
        )
        statuses = root['statuses']

    current_ids = {str(item['id']) for item in action_items}
    for action_id in current_ids:
        statuses.setdefault(action_id, 'Awaiting decision')

    # Remove obsolete synthetic actions while retaining the stable current set.
    for action_id in list(statuses):
        if action_id not in current_ids:
            statuses.pop(action_id, None)

    return root


def save_command_center_decision(
    brand_state: dict[str, Any],
    *,
    action_id: str,
    status: str,
    action_items: list[dict[str, Any]],
) -> None:
    decisions = ensure_command_center_decisions(brand_state, action_items)
    decisions['statuses'][str(action_id)] = str(status)


def ensure_demand_inventory_workspace(
    brand_state: dict[str, Any],
    *,
    default_region: str,
    default_outlet_id: str,
) -> dict[str, Any]:
    """Lazily add durable UI/workflow state to Demand & Inventory.

    Existing Step-4 browser sessions already contain the two independent run
    counters.  This function upgrades them in place without resetting either
    counter or forcing the presenter to clear NiceGUI user storage.
    """

    workflow = brand_state.setdefault('workflows', {}).setdefault('demand_inventory', {})
    workflow.setdefault('forecast_run_number', 0)
    workflow.setdefault('planning_run_number', 0)

    if workflow.get('workspace_version') != DEMAND_WORKSPACE_VERSION:
        preserved_forecast_run = int(workflow.get('forecast_run_number', 0) or 0)
        preserved_planning_run = int(workflow.get('planning_run_number', 0) or 0)
        brand_state.setdefault('artifacts', {})['purchase_plans'] = []
        brand_state.setdefault('artifacts', {})['transfer_plans'] = []
        brand_state.setdefault('decisions', {})['demand_inventory'] = {}
        workflow.update(
            {
                'workspace_version': DEMAND_WORKSPACE_VERSION,
                'forecast_loaded': False,
                'forecast_run_number': preserved_forecast_run,
                'planning_run_number': preserved_planning_run,
                'region': default_region,
                'outlet_id': default_outlet_id,
                'forecast_horizon': 7,
                'planning_horizon': 7,
                'inventory_built': False,
                'inventory_rows': [],
                'plan_generated': False,
                'plan_approved': False,
                'plan_rows': [],
            }
        )

    workflow.setdefault('region', default_region)
    workflow.setdefault('outlet_id', default_outlet_id)
    workflow.setdefault('forecast_horizon', 7)
    workflow.setdefault('planning_horizon', 7)
    workflow.setdefault('inventory_built', False)
    workflow.setdefault('inventory_rows', [])
    workflow.setdefault('plan_generated', False)
    workflow.setdefault('plan_approved', False)
    workflow.setdefault('plan_rows', [])
    return workflow


def clear_demand_action_workflow(brand_state: dict[str, Any]) -> None:
    """Invalidate generated inventory actions/plans but keep forecast settings."""

    workflow = brand_state['workflows']['demand_inventory']
    workflow['inventory_built'] = False
    workflow['inventory_rows'] = []
    workflow['plan_generated'] = False
    workflow['plan_approved'] = False
    workflow['plan_rows'] = []

    brand_state.setdefault('artifacts', {})['purchase_plans'] = []
    brand_state.setdefault('artifacts', {})['transfer_plans'] = []
    brand_state.setdefault('decisions', {})['demand_inventory'] = {}


def save_inventory_rows(
    brand_state: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    workflow = brand_state['workflows']['demand_inventory']
    workflow['inventory_built'] = True
    workflow['inventory_rows'] = deepcopy(rows)


def clear_generated_replenishment_plan(brand_state: dict[str, Any]) -> None:
    """Invalidate only generated documents while preserving edited inventory rows."""

    workflow = brand_state['workflows']['demand_inventory']
    workflow['plan_generated'] = False
    workflow['plan_approved'] = False
    workflow['plan_rows'] = []
    brand_state.setdefault('artifacts', {})['purchase_plans'] = []
    brand_state.setdefault('artifacts', {})['transfer_plans'] = []
    brand_state.setdefault('decisions', {})['demand_inventory'] = {}


def save_generated_replenishment_plan(
    brand_state: dict[str, Any],
    *,
    outlet_id: str,
    plan_rows: list[dict[str, Any]],
) -> None:
    workflow = brand_state['workflows']['demand_inventory']
    copied_rows = deepcopy(plan_rows)
    ready_rows = [row for row in copied_rows if row.get('status') == 'Ready for approval']

    workflow['plan_rows'] = copied_rows
    workflow['plan_generated'] = bool(ready_rows)
    workflow['plan_approved'] = False

    artifacts = brand_state.setdefault('artifacts', {})
    artifacts['purchase_plans'] = [
        deepcopy(row) for row in copied_rows if row.get('plan_type') == 'purchase'
    ]
    artifacts['transfer_plans'] = [
        deepcopy(row) for row in copied_rows if row.get('plan_type') == 'transfer'
    ]

    total_cost = sum(float(row.get('total_cost_value', 0.0)) for row in ready_rows)
    brand_state.setdefault('decisions', {})['demand_inventory'] = {
        'replenishment_plan': {
            'outlet_id': outlet_id,
            'status': 'Ready for approval' if ready_rows else 'No actions selected',
            'plan_count': len(ready_rows),
            'total_cost_value': round(total_cost, 2),
        }
    }


def approve_replenishment_plan(brand_state: dict[str, Any]) -> list[dict[str, Any]]:
    workflow = brand_state['workflows']['demand_inventory']
    rows = deepcopy(workflow.get('plan_rows', []))

    for row in rows:
        if row.get('status') == 'Ready for approval':
            row['status'] = 'Approved'
            row['fulfillment_status'] = ('Ordered · Awaiting receipt'
                if row.get('plan_type') == 'purchase' else 'Awaiting dispatch')

    workflow['plan_rows'] = deepcopy(rows)
    workflow['plan_generated'] = bool(rows)
    workflow['plan_approved'] = any(row.get('status') == 'Approved' for row in rows)

    artifacts = brand_state.setdefault('artifacts', {})
    artifacts['purchase_plans'] = [
        deepcopy(row) for row in rows if row.get('plan_type') == 'purchase'
    ]
    artifacts['transfer_plans'] = [
        deepcopy(row) for row in rows if row.get('plan_type') == 'transfer'
    ]

    decision = brand_state.setdefault('decisions', {}).setdefault(
        'demand_inventory', {}
    ).setdefault('replenishment_plan', {})
    decision['status'] = 'Approved'
    decision['plan_count'] = sum(1 for row in rows if row.get('status') == 'Approved')
    return rows
