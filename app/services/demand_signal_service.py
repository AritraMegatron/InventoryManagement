"""Select a coherent fictional scenario; apply it to eligible item/date pairs."""
from datetime import date, timedelta
from hashlib import sha256
from app.data.demand_signal_catalog import SIGNALS


CATALOG_VERSION = 1


def _rank(text):
    return int(sha256(text.encode()).hexdigest()[:16], 16)


def product_group(name):
    if 'Sundae' in name:
        return 'dessert'
    if 'Latte' in name or name == 'Montreal Mocha':
        return 'hot'
    return 'cold'


def eligible_dates(signal, country, outlet, anchor, days=7):
    if signal['country'] != country:
        return []
    if signal['cities'] and outlet.city not in signal['cities']:
        return []
    if signal['formats'] and outlet.outlet_format not in signal['formats']:
        return []
    return [anchor+timedelta(days=i) for i in range(1,days+1)
            if (anchor+timedelta(days=i)).month in signal['months']
            and (not signal['weekdays'] or (anchor+timedelta(days=i)).weekday() in signal['weekdays'])]


def build_signal_scenario(brand_state, outlet, products, anchor):
    country = brand_state['profile']['country_code']
    groups = {product_group(p['product']) for p in products}
    seed = f"{brand_state['brand_id']}:{outlet.outlet_id}:{anchor}:{CATALOG_VERSION}"
    selected = []
    for group in ('weather','event','commercial'):
        candidates = []
        for signal in SIGNALS:
            dates = eligible_dates(signal,country,outlet,anchor)
            if signal['group'] == group and dates and (signal['target']=='all' or signal['target'] in groups):
                candidates.append((signal,dates))
        if not candidates:
            continue
        signal,dates = min(candidates, key=lambda pair:_rank(seed+pair[0]['id']))
        if group != 'weather':
            dates = [dates[_rank(seed+signal['id']+'date') % len(dates)]]
        scope = {'all':'all menu items','hot':'hot drinks','cold':'cold drinks','dessert':'desserts'}[signal['target']]
        date_text = ', '.join(d.strftime('%d %b') for d in dates)
        selected.append({**signal,'dates':[d.isoformat() for d in dates],
            'source_mode':'simulated','city':outlet.city,
            'detail':f"{signal['impact_pct']:+}% {scope} on affected dates · {outlet.city} · {date_text}"})
    return selected


def signal_multiplier(signals, product_name, day):
    factor = 1.0
    for signal in signals:
        if day.isoformat() in signal['dates'] and signal['target'] in ('all',product_group(product_name)):
            factor *= 1 + signal['impact_pct']/100
    return factor
