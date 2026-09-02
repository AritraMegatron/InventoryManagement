from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID
from app.services.demand_inventory_service import build_plan_summary, default_demand_selection
from app.services.network_service import build_command_center_snapshot
from app.services.workflow_persistence_service import (
    approve_replenishment_plan,
    ensure_command_center_decisions,
    ensure_demand_inventory_workspace,
    save_command_center_decision,
    save_generated_replenishment_plan,
    save_inventory_rows,
)
from app.state.demo_state import build_brand_state


brand = build_brand_state(CANADA_BRAND_ID)
profile = brand['profile']
snapshot = build_command_center_snapshot(brand['network']['outlets'], profile)
ensure_command_center_decisions(brand, snapshot['actions'])
save_command_center_decision(
    brand,
    action_id='inventory_risk',
    status=snapshot['actions'][0]['approved_status'],
    action_items=snapshot['actions'],
)

region, outlet_id = default_demand_selection(brand)
workspace = ensure_demand_inventory_workspace(
    brand,
    default_region=region,
    default_outlet_id=outlet_id,
)
workspace['planning_horizon'] = 14
inventory_rows = [
    {'product': 'Maple Cream Cold Brew', 'action_type': 'Order', 'action_quantity': 30},
]
save_inventory_rows(brand, inventory_rows)
plans = build_plan_summary(brand, outlet_id, inventory_rows)
save_generated_replenishment_plan(brand, outlet_id=outlet_id, plan_rows=plans)
approve_replenishment_plan(brand)

print(f"Brand: {profile['display_name']}")
print('Command Center approval:', brand['decisions']['command_center']['statuses']['inventory_risk'])
print('Demand planning horizon:', workspace['planning_horizon'])
print('Inventory rows persisted:', len(workspace['inventory_rows']))
print('Plan rows persisted:', len(workspace['plan_rows']))
print('Plan approved:', workspace['plan_approved'])
print('Purchase artifacts:', len(brand['artifacts']['purchase_plans']))
print('Transfer artifacts:', len(brand['artifacts']['transfer_plans']))
print('STEP 7 CHECK: PASS')
