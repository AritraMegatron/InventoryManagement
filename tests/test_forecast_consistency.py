import unittest
from copy import deepcopy
from app.state.demo_state import build_brand_state
from app.services.demand_inventory_service import (
    build_dashboard_snapshot, build_inventory_planning_data, get_demand_outlets,
)


class ForecastConsistencyTests(unittest.TestCase):
    def test_both_brands_all_outlets(self):
        for brand in ('northstar_india', 'maple_mason_canada'):
            state = build_brand_state(brand)
            for outlet in get_demand_outlets(state):
                with self.subTest(brand=brand, outlet=outlet):
                    snapshots = {}
                    plans = {}
                    for h in (7, 14, 30):
                        snapshots[h] = build_dashboard_snapshot(state, outlet, h)
                    for h in (7, 14):
                        plans[h] = build_inventory_planning_data(state, outlet, h)
                        self.assertEqual(snapshots[h]['kpis']['predicted_units'], sum(r['forecast'] for r in plans[h]['inventory_rows']))
                        self.assertEqual(snapshots[h]['kpis']['predicted_units'], sum(snapshots[h]['forecast'][7:]))
                        prices = {r['product']:r['price'] for r in state['demand_dataset_v1']['outlets'][outlet]['items']}
                        self.assertEqual(snapshots[h]['kpis']['expected_revenue'], round(sum(r['forecast']*prices[r['product']] for r in plans[h]['inventory_rows']), 2))
                    self.assertEqual(snapshots[7]['forecast'][7:], snapshots[14]['forecast'][7:14])
                    self.assertEqual(snapshots[14]['forecast'][7:], snapshots[30]['forecast'][7:21])
                    self.assertEqual(snapshots[7]['actual'][:7], snapshots[30]['actual'][:7])
                    self.assertEqual([r['on_hand'] for r in plans[7]['inventory_rows']], [r['on_hand'] for r in plans[14]['inventory_rows']])
                    self.assertEqual(snapshots[7], build_dashboard_snapshot(state, outlet, 7, 99))
                    self.assertEqual(plans[7], build_inventory_planning_data(state, outlet, 7, 99))

    def test_outlet_round_trip(self):
        for brand in ('northstar_india', 'maple_mason_canada'):
            state = build_brand_state(brand)
            a,b = list(get_demand_outlets(state))[:2]
            before = deepcopy(build_dashboard_snapshot(state,a,7))
            build_dashboard_snapshot(state,b,14,1)
            self.assertEqual(before, build_dashboard_snapshot(state,a,7,2))


if __name__ == '__main__':
    unittest.main()
