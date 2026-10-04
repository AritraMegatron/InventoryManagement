"""One stable, date-anchored daily item dataset per brand/outlet demo session."""
from datetime import date, timedelta
from hashlib import sha256
import random
from app.services.demand_signal_service import build_signal_scenario, signal_multiplier
from app.data.brand_catalog import CANADA_BRAND_ID


def ensure_sales_inputs(brand_state, products):
    """Freeze seed assumptions before network rows become derived outputs.

    Revenue / weighted menu price gives item units. Revenue / ticket gives
    transactions. Keeping these inputs separate prevents compounding on refresh.
    """
    input_key = 'canada_sales_inputs_v1' if brand_state['brand_id'] == CANADA_BRAND_ID else 'india_sales_inputs_v1'
    if input_key not in brand_state:
        weighted_price = sum(p['price'] * p['share'] for p in products)
        inputs = {}
        for row in brand_state['network']['outlets']:
            inputs[row['store_id']] = {
                'daily_item_baseline': max(1, round(row['monthly_revenue'] / weighted_price / 30)),
                'items_per_order': max(1.0, row['average_ticket'] / weighted_price),
                'average_ticket': row['average_ticket'],
            }
        brand_state[input_key] = inputs
        # One-time per-brand upgrade to the shared item-level dataset.
        previous_as_of = brand_state.get('demand_dataset_v1', {}).get('as_of', date.today().isoformat())
        brand_state['demand_dataset_v1'] = {'as_of': previous_as_of, 'outlets': {}}
        brand_state.pop('ingredient_inventory', None)
        workflow = brand_state.setdefault('workflows', {}).setdefault('demand_inventory', {})
        if brand_state['brand_id'] != CANADA_BRAND_ID:
            aliases = {'dlf_noida': 'noida-1', 'connaught_place': 'new-delhi-1',
                       'cyber_hub': 'gurugram-1', 'elante_chandigarh': 'chandigarh-1',
                       'phoenix_pune': 'pune-1'}
            selected = aliases.get(workflow.get('outlet_id'), workflow.get('outlet_id'))
            row = next((r for r in brand_state['network']['outlets'] if r['store_id'] == selected), None)
            row = row or next(r for r in brand_state['network']['outlets'] if r['store_id'] == 'noida-1')
            workflow.update(outlet_id=row['store_id'], region=row['region'])
        workflow.update(forecast_loaded=False, inventory_built=False, inventory_rows=[],
                        plan_generated=False, plan_approved=False, plan_rows=[])
        for key in ('purchase_plans', 'transfer_plans'):
            brand_state.setdefault('artifacts', {})[key] = []
        brand_state.setdefault('decisions', {})['demand_inventory'] = {}
    return brand_state[input_key]


def get_demand_dataset(brand_state, outlet, products):
    root = brand_state.setdefault('demand_dataset_v1', {
        'as_of': date.today().isoformat(), 'outlets': {},
    })
    if root.get('signal_dataset_version') != 1:
        root['outlets'] = {}
        root['signal_dataset_version'] = 1
    outlet_id = outlet.outlet_id
    if outlet_id not in root['outlets']:
        anchor = date.fromisoformat(root['as_of'])
        signals = build_signal_scenario(brand_state, outlet, products, anchor)
        records = []
        for product in products:
            daily = {}
            history_start = -29
            for offset in range(history_start, 31):
                day = anchor + timedelta(days=offset)
                key = f"{brand_state['brand_id']}:{outlet_id}:{product['product']}:{day}"
                rng = random.Random(int(sha256(key.encode()).hexdigest()[:12], 16))
                weekend = 1.16 if day.weekday() >= 5 else 1.0
                event = signal_multiplier(signals, product['product'], day) if offset > 0 else 1.0
                # Days 15-30 extend the same forecast with wider synthetic variation.
                noise = rng.uniform(.91, 1.09) if offset <= 0 or offset > 14 else rng.uniform(.96, 1.05)
                trend = 1 + max(0, offset) * .004
                daily[str(offset)] = max(1, round(outlet.daily_baseline * product['share'] * weekend * event * trend * noise))
            records.append({'product': product['product'], 'price': product['price'], 'daily': daily})
        root['outlets'][outlet_id] = {'as_of': root['as_of'], 'items': records, 'signals': signals}
        if 'daily_orders' not in root['outlets'][outlet_id]:
            input_key = 'canada_sales_inputs_v1' if brand_state['brand_id'] == CANADA_BRAND_ID else 'india_sales_inputs_v1'
            basket = brand_state[input_key][outlet_id]['items_per_order']
            root['outlets'][outlet_id]['daily_orders'] = {
                str(i): max(1, round(sum(r['daily'][str(i)] for r in records) / basket))
                for i in range(-29, 31)
            }
    return root['outlets'][outlet_id]


def period_item_totals(dataset, horizon):
    return {r['product']: sum(r['daily'][str(i)] for i in range(1, horizon + 1))
            for r in dataset['items']}


def daily_totals(dataset, offsets):
    return [sum(r['daily'][str(i)] for r in dataset['items']) for i in offsets]
