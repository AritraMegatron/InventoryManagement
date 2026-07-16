from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
import random
from typing import Any


@dataclass(frozen=True)
class Outlet:
    outlet_id: str
    name: str
    city: str
    region: str
    outlet_format: str
    daily_baseline: int
    delivery_share: int
    cluster: str


OUTLETS: dict[str, Outlet] = {
    'dlf_noida': Outlet(
        'dlf_noida',
        'DLF Mall of India',
        'Noida',
        'Delhi NCR',
        'Mall kiosk',
        820,
        31,
        'Noida Central',
    ),
    'connaught_place': Outlet(
        'connaught_place',
        'Connaught Place',
        'New Delhi',
        'Delhi NCR',
        'High-street café',
        960,
        26,
        'Central Delhi',
    ),
    'cyber_hub': Outlet(
        'cyber_hub',
        'Cyber Hub',
        'Gurugram',
        'Delhi NCR',
        'Premium café',
        910,
        34,
        'Gurugram Central',
    ),
    'select_citywalk': Outlet(
        'select_citywalk',
        'Select Citywalk',
        'New Delhi',
        'Delhi NCR',
        'Mall kiosk',
        760,
        28,
        'South Delhi',
    ),
    'ambience_gurugram': Outlet(
        'ambience_gurugram',
        'Ambience Mall',
        'Gurugram',
        'Delhi NCR',
        'Mall kiosk',
        700,
        33,
        'Gurugram Central',
    ),
    'elante_chandigarh': Outlet(
        'elante_chandigarh',
        'Elante Mall',
        'Chandigarh',
        'North',
        'Mall kiosk',
        620,
        24,
        'Chandigarh',
    ),
    'phoenix_pune': Outlet(
        'phoenix_pune',
        'Phoenix Marketcity',
        'Pune',
        'West',
        'Mall kiosk',
        680,
        30,
        'Pune East',
    ),
}

REGIONS = ['All regions', 'Delhi NCR', 'North', 'West']

PRODUCTS = [
    {
        'product': 'Classic Cold Coffee',
        'price': 235,
        'share': 0.19,
        'unit': 'cups',
        'shelf': 2,
        'ingredient': 'Coffee premix',
    },
    {
        'product': 'Belgian Chocolate Shake',
        'price': 285,
        'share': 0.18,
        'unit': 'cups',
        'shelf': 3,
        'ingredient': 'Chocolate base',
    },
    {
        'product': 'Oreo Crumble Shake',
        'price': 295,
        'share': 0.17,
        'unit': 'cups',
        'shelf': 3,
        'ingredient': 'Oreo crumble',
    },
    {
        'product': 'Classic Vanilla Shake',
        'price': 245,
        'share': 0.14,
        'unit': 'cups',
        'shelf': 3,
        'ingredient': 'Vanilla base',
    },
    {
        'product': 'Mango Alphonso Shake',
        'price': 275,
        'share': 0.13,
        'unit': 'cups',
        'shelf': 2,
        'ingredient': 'Mango pulp',
    },
    {
        'product': 'Strawberry Fields Shake',
        'price': 275,
        'share': 0.11,
        'unit': 'cups',
        'shelf': 2,
        'ingredient': 'Strawberry base',
    },
    {
        'product': 'Salted Caramel Sundae',
        'price': 315,
        'share': 0.08,
        'unit': 'servings',
        'shelf': 2,
        'ingredient': 'Caramel sauce',
    },
]

SOURCE_OUTLETS = {
    'dlf_noida': ['Select Citywalk', 'Connaught Place'],
    'connaught_place': ['Select Citywalk', 'DLF Mall of India'],
    'cyber_hub': ['Ambience Mall', 'Select Citywalk'],
    'select_citywalk': ['Connaught Place', 'DLF Mall of India'],
    'ambience_gurugram': ['Cyber Hub', 'Select Citywalk'],
    'elante_chandigarh': ['Sector 17 Chandigarh', 'Mohali Walk'],
    'phoenix_pune': ['Koregaon Park', 'Amanora Mall'],
}

DEMAND_SIGNAL_LIBRARY = [
    {
        'icon': 'sports_cricket',
        'label': 'Cricket tournament final',
        'impact_pct': 18.6,
        'metric': 'evening demand',
    },
    {
        'icon': 'wb_sunny',
        'label': 'Hot afternoon',
        'impact_pct': 8.4,
        'metric': 'beverage demand',
    },
    {
        'icon': 'festival',
        'label': 'Regional holiday',
        'impact_pct': 13.2,
        'metric': 'all-day footfall',
    },
    {
        'icon': 'local_offer',
        'label': 'Weekend mall promotion',
        'impact_pct': 11.5,
        'metric': 'walk-in demand',
    },
    {
        'icon': 'school',
        'label': 'School vacation',
        'impact_pct': 7.8,
        'metric': 'afternoon traffic',
    },
    {
        'icon': 'groups',
        'label': 'College festival',
        'impact_pct': 16.4,
        'metric': 'late-afternoon demand',
    },
    {
        'icon': 'music_note',
        'label': 'Live concert nearby',
        'impact_pct': 12.1,
        'metric': 'post-event demand',
    },
    {
        'icon': 'movie',
        'label': 'Blockbuster movie release',
        'impact_pct': 9.6,
        'metric': 'evening mall traffic',
    },
    {
        'icon': 'delivery_dining',
        'label': 'Food-delivery promotion',
        'impact_pct': 14.7,
        'metric': 'delivery orders',
    },
    {
        'icon': 'payments',
        'label': 'Salary weekend',
        'impact_pct': 10.3,
        'metric': 'premium product demand',
    },
    {
        'icon': 'flight',
        'label': 'Tourist season uplift',
        'impact_pct': 6.9,
        'metric': 'all-day demand',
    },
    {
        'icon': 'corporate_fare',
        'label': 'Corporate park event',
        'impact_pct': 8.8,
        'metric': 'weekday demand',
    },
    {
        'icon': 'thunderstorm',
        'label': 'Heavy evening rain',
        'impact_pct': -7.2,
        'metric': 'walk-in demand',
    },
    {
        'icon': 'directions_subway',
        'label': 'Metro service disruption',
        'impact_pct': -5.8,
        'metric': 'commuter footfall',
    },
    {
        'icon': 'device_thermostat',
        'label': 'Heatwave warning',
        'impact_pct': 12.6,
        'metric': 'cold beverage demand',
    },
    {
        'icon': 'traffic',
        'label': 'Local road closure',
        'impact_pct': -6.4,
        'metric': 'delivery throughput',
    },
    {
        'icon': 'celebration',
        'label': 'Wedding season',
        'impact_pct': 5.7,
        'metric': 'bulk-order demand',
    },
    {
        'icon': 'campaign',
        'label': 'Competitor discount campaign',
        'impact_pct': -4.9,
        'metric': 'local demand',
    },
    {
        'icon': 'temple_hindu',
        'label': 'Religious festival',
        'impact_pct': 15.8,
        'metric': 'family demand',
    },
    {
        'icon': 'luggage',
        'label': 'Long-weekend travel exodus',
        'impact_pct': -8.1,
        'metric': 'neighborhood demand',
    },
]

def _select_demand_signals(
    rng: random.Random,
    excluded_labels: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Select three signals while avoiding the previous selection."""

    excluded_labels = excluded_labels or set()

    available_signals = [
        signal
        for signal in DEMAND_SIGNAL_LIBRARY
        if signal['label'] not in excluded_labels
    ]

    # Safety fallback in case the library is shortened later.
    if len(available_signals) < 3:
        available_signals = DEMAND_SIGNAL_LIBRARY

    selected_signals = rng.sample(
        available_signals,
        k=3,
    )

    formatted_signals: list[dict[str, Any]] = []

    for signal in selected_signals:
        impact = signal['impact_pct']
        sign = '+' if impact >= 0 else ''

        formatted_signals.append(
            {
                **signal,
                'detail': (
                    f"{sign}{impact:.1f}% "
                    f"{signal['metric']}"
                ),
            }
        )

    return formatted_signals

def outlets_for_region(region: str) -> dict[str, str]:
    return {
        outlet_id: f'{outlet.name} · {outlet.city}'
        for outlet_id, outlet in OUTLETS.items()
        if region == 'All regions' or outlet.region == region
    }


def format_inr(value: float) -> str:
    value = int(round(value))
    sign = '-' if value < 0 else ''
    digits = str(abs(value))
    if len(digits) <= 3:
        return f'{sign}₹{digits}'
    last_three = digits[-3:]
    remaining = digits[:-3]
    groups = []
    while remaining:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    grouped = ','.join(reversed(groups)) + ',' + last_three
    return f'{sign}₹{grouped}'


def _seed(outlet_id: str, horizon: int, run_number: int) -> int:
    return sum(ord(char) for char in outlet_id) * 37 + horizon * 11 + run_number * 101


def _demand_multiplier(day_index: int, future: bool) -> float:
    weekday = (date.today() + timedelta(days=day_index)).weekday()
    weekend = 1.18 if weekday >= 5 else 1.0
    event = 1.11 if future and day_index in {2, 3} else 1.0
    return weekend * event


def build_dashboard_snapshot(
    outlet_id: str,
    horizon: int = 7,
    run_number: int = 0,
    excluded_signal_labels: set[str] | None = None,
) -> dict[str, Any]:


    outlet = OUTLETS[outlet_id]
    rng = random.Random(_seed(outlet_id, horizon, run_number))

    history_days = 7
    categories: list[str] = []
    actual: list[int | None] = []
    forecast: list[int | None] = []
    lower: list[int | None] = []
    upper: list[int | None] = []

    start = date.today() - timedelta(days=history_days - 1)
    history_values: list[int] = []

    for index in range(history_days):
        current = start + timedelta(days=index)
        categories.append(current.strftime('%d %b'))
        base = outlet.daily_baseline * _demand_multiplier(index - history_days + 1, False)
        value = int(base * rng.uniform(0.91, 1.09))
        history_values.append(value)
        actual.append(value)
        forecast.append(None)
        lower.append(None)
        upper.append(None)

    forecast[history_days - 1] = history_values[-1]
    lower[history_days - 1] = history_values[-1]
    upper[history_days - 1] = history_values[-1]

    future_values: list[int] = []
    for index in range(1, horizon + 1):
        current = date.today() + timedelta(days=index)
        categories.append(current.strftime('%d %b'))
        base = outlet.daily_baseline * _demand_multiplier(index, True)
        trend = 1 + (index * 0.006)
        value = int(base * trend * rng.uniform(0.96, 1.05))
        uncertainty = 0.075 + index * 0.004
        future_values.append(value)
        actual.append(None)
        forecast.append(value)
        lower.append(int(value * (1 - uncertainty)))
        upper.append(int(value * (1 + uncertainty)))

    predicted_units = sum(future_values)
    average_ticket = 271 + rng.randint(-7, 11)
    expected_revenue = predicted_units * average_ticket
    confidence = round(91.8 - max(0, horizon - 7) * 0.22 + rng.uniform(-0.6, 0.6), 1)

    inventory_rows: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    projected_waste_value = 0
    at_risk_count = 0

    tomorrow_total = future_values[0]
    for index, product in enumerate(PRODUCTS):
        product_forecast = max(20, int(tomorrow_total * product['share'] * rng.uniform(0.92, 1.09)))
        safety_stock = max(8, int(product_forecast * rng.uniform(0.14, 0.22)))

        # Force a convincing mix of shortages, healthy stock, and overstock.
        if index == (run_number + len(outlet_id)) % len(PRODUCTS):
            on_hand = int(product_forecast * rng.uniform(0.48, 0.69))
        elif index == (run_number + len(outlet_id) + 3) % len(PRODUCTS):
            on_hand = int(product_forecast * rng.uniform(1.55, 1.88))
        else:
            on_hand = int(product_forecast * rng.uniform(0.92, 1.42))

        available_after_safety = on_hand - safety_stock
        gap = available_after_safety - product_forecast
        coverage = round(on_hand / max(product_forecast, 1), 1)

        if gap < -10:
            status = 'Stockout risk'
            severity = 'High'
            recommended_qty = abs(gap) + safety_stock
            action = f'Transfer {recommended_qty} units'
            at_risk_count += 1
            risk_cost = recommended_qty * product['price'] * 0.62
            risks.append(
                {
                    'product': product['product'],
                    'severity': severity,
                    'detail': f'Projected shortage of {recommended_qty} units before tomorrow evening peak.',
                    'impact': format_inr(risk_cost),
                    'recommended_qty': recommended_qty,
                },
            )
        elif coverage > 1.6:
            status = 'Overstock'
            severity = 'Medium'
            excess = max(1, on_hand - product_forecast - safety_stock)
            action = f'Redeploy {excess} units'
            waste_value = excess * product['price'] * 0.32
            projected_waste_value += waste_value
            risks.append(
                {
                    'product': product['product'],
                    'severity': severity,
                    'detail': f'{excess} units are above target coverage and may become waste.',
                    'impact': format_inr(waste_value),
                    'recommended_qty': excess,
                },
            )
        elif gap < 5:
            status = 'Watch'
            severity = 'Medium'
            top_up = safety_stock + 8
            action = f'Top up {top_up} units'
            at_risk_count += 1
            risks.append(
                {
                    'product': product['product'],
                    'severity': severity,
                    'detail': 'Inventory is adequate only if demand stays near the lower forecast bound.',
                    'impact': format_inr(top_up * product['price'] * 0.30),
                    'recommended_qty': top_up,
                },
            )
        else:
            status = 'Healthy'
            severity = 'Low'
            action = 'No action'

        inventory_rows.append(
            {
                'id': index + 1,
                'product': product['product'],
                'forecast': product_forecast,
                'on_hand': on_hand,
                'safety_stock': safety_stock,
                'coverage': f'{coverage:.1f} days',
                'status': status,
                'action': action,
            },
        )

    risks.sort(key=lambda item: {'High': 0, 'Medium': 1, 'Low': 2}[item['severity']])
    primary_risk = risks[0] if risks else {
        'product': 'No critical risk',
        'severity': 'Low',
        'detail': 'All products are projected to remain within target coverage.',
        'impact': '₹0',
        'recommended_qty': 0,
    }

    service_level = round(97.1 - at_risk_count * 0.85 + rng.uniform(-0.25, 0.25), 1)
    prevented_sales_loss = max(
        12000,
        sum(item['recommended_qty'] for item in risks if item['severity'] == 'High') * average_ticket,
    )
    avoidable_waste = max(projected_waste_value, 6800 + rng.randint(0, 9200))

    signals = _select_demand_signals(
        rng,
        excluded_labels=excluded_signal_labels,
    )

    return {
        'outlet': outlet,
        'horizon': horizon,
        'categories': categories,
        'actual': actual,
        'forecast': forecast,
        'lower': lower,
        'upper': upper,
        'inventory_rows': inventory_rows,
        'risks': risks[:4],
        'primary_risk': primary_risk,
        'signals': signals,
        'kpis': {
            'predicted_units': predicted_units,
            'expected_revenue': expected_revenue,
            'service_level': service_level,
            'at_risk_count': at_risk_count,
            'avoidable_waste': avoidable_waste,
            'confidence': confidence,
        },
        'recommendation': {
            'headline': f"Protect tomorrow's evening peak at {outlet.name}",
            'body': primary_risk['detail'],
            'impact': format_inr(prevented_sales_loss),
            'waste': format_inr(avoidable_waste),
            'priority': primary_risk['severity'],
        },
    }


def build_replenishment_plan(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    outlet: Outlet = snapshot['outlet']
    source_candidates = SOURCE_OUTLETS[outlet.outlet_id]
    plan: list[dict[str, Any]] = []

    for index, risk in enumerate(snapshot['risks']):
        if risk['severity'] == 'High':
            method = 'Inter-store transfer'
            source = source_candidates[index % len(source_candidates)]
            eta = f'{55 + index * 15} min'
        elif 'waste' in risk['detail']:
            method = 'Reverse transfer'
            source = source_candidates[(index + 1) % len(source_candidates)]
            eta = f'{75 + index * 10} min'
        else:
            method = 'Supplier top-up'
            source = 'Regional distributor'
            eta = 'Tomorrow 08:30'

        plan.append(
            {
                'id': index + 1,
                'product': risk['product'],
                'method': method,
                'from': source,
                'quantity': risk['recommended_qty'],
                'eta': eta,
                'impact': risk['impact'],
                'status': 'Recommended',
            },
        )

    if not plan:
        plan.append(
            {
                'id': 1,
                'product': 'All products',
                'method': 'No action',
                'from': '—',
                'quantity': 0,
                'eta': '—',
                'impact': '₹0',
                'status': 'Healthy',
            },
        )
    return plan
