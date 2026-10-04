"""One stable, date-anchored daily item dataset per brand/outlet demo session."""
from datetime import date, timedelta
from hashlib import sha256
import random
from app.services.demand_signal_service import build_signal_scenario, signal_multiplier


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
            for offset in range(-6, 31):
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
    return root['outlets'][outlet_id]


def period_item_totals(dataset, horizon):
    return {r['product']: sum(r['daily'][str(i)] for i in range(1, horizon + 1))
            for r in dataset['items']}


def daily_totals(dataset, offsets):
    return [sum(r['daily'][str(i)] for r in dataset['items']) for i in offsets]
