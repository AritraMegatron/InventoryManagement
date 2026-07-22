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

# ---------------------------------------------------------------------------
# Inventory planning and action-plan mock data
# ---------------------------------------------------------------------------

# Each tuple is:
# ingredient, quantity needed for one product unit, unit, vendor, cost per unit
PRODUCT_RECIPES: dict[str, list[tuple[str, float, str, str, float]]] = {
    'Classic Cold Coffee': [
        ('Coffee premix', 0.025, 'kg', 'Delhi Beverage Supplies', 420.0),
        ('Milk', 0.250, 'L', 'DairyBest Foods', 62.0),
        ('Sugar syrup', 0.030, 'L', 'Delhi Beverage Supplies', 110.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Belgian Chocolate Shake': [
        ('Chocolate base', 0.080, 'kg', 'NCR Dessert Ingredients', 360.0),
        ('Milk', 0.220, 'L', 'DairyBest Foods', 62.0),
        ('Ice cream base', 0.120, 'kg', 'DairyBest Foods', 280.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Oreo Crumble Shake': [
        ('Oreo crumble', 0.055, 'kg', 'Crumble Foods', 310.0),
        ('Vanilla base', 0.090, 'kg', 'NCR Dessert Ingredients', 250.0),
        ('Milk', 0.220, 'L', 'DairyBest Foods', 62.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Classic Vanilla Shake': [
        ('Vanilla base', 0.110, 'kg', 'NCR Dessert Ingredients', 250.0),
        ('Milk', 0.230, 'L', 'DairyBest Foods', 62.0),
        ('Ice cream base', 0.080, 'kg', 'DairyBest Foods', 280.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Mango Alphonso Shake': [
        ('Mango pulp', 0.120, 'kg', 'FreshFruit Processing', 285.0),
        ('Milk', 0.210, 'L', 'DairyBest Foods', 62.0),
        ('Ice cream base', 0.090, 'kg', 'DairyBest Foods', 280.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Strawberry Fields Shake': [
        ('Strawberry base', 0.105, 'kg', 'FreshFruit Processing', 265.0),
        ('Milk', 0.220, 'L', 'DairyBest Foods', 62.0),
        ('Ice cream base', 0.085, 'kg', 'DairyBest Foods', 280.0),
        ('Cup and lid', 1.0, 'piece', 'PackRight India', 6.0),
    ],
    'Salted Caramel Sundae': [
        ('Caramel sauce', 0.055, 'kg', 'NCR Dessert Ingredients', 330.0),
        ('Ice cream base', 0.160, 'kg', 'DairyBest Foods', 280.0),
        ('Sundae cup and spoon', 1.0, 'set', 'PackRight India', 7.5),
    ],
}

VENDOR_DIRECTORY = {
    'Delhi Beverage Supplies': {
        'phone': '+91 98710 44218',
        'address': 'Okhla Industrial Area, New Delhi',
    },
    'DairyBest Foods': {
        'phone': '+91 98104 77631',
        'address': 'Sector 80, Noida, Uttar Pradesh',
    },
    'NCR Dessert Ingredients': {
        'phone': '+91 99582 11847',
        'address': 'Sahibabad Industrial Area, Ghaziabad',
    },
    'PackRight India': {
        'phone': '+91 98991 60352',
        'address': 'Naraina Industrial Area, New Delhi',
    },
    'Crumble Foods': {
        'phone': '+91 97171 28540',
        'address': 'Lawrence Road Industrial Area, New Delhi',
    },
    'FreshFruit Processing': {
        'phone': '+91 98211 70438',
        'address': 'Azadpur Produce District, New Delhi',
    },
}

TRANSFER_RESOURCES = [
    {
        'driver': 'Rajesh Kumar',
        'phone': '+91 98102 34812',
        'vehicle': 'Tata Ace · DL 01 AB 4821',
    },
    {
        'driver': 'Imran Khan',
        'phone': '+91 98992 51764',
        'vehicle': 'Mahindra Bolero Pickup · HR 26 DK 1194',
    },
    {
        'driver': 'Sandeep Yadav',
        'phone': '+91 99531 62087',
        'vehicle': 'Tata Intra · UP 16 CT 7308',
    },
]

DOCUMENT_COMPANIES = [
    {
        'name': 'Northstar Desserts & Beverages Pvt. Ltd.',
        'phone': '+91 120 451 8820',
        'address': 'Sector 18, Noida, Uttar Pradesh 201301',
    },
    {
        'name': 'The Shake Atelier Foods Pvt. Ltd.',
        'phone': '+91 124 498 1170',
        'address': 'DLF Phase 3, Gurugram, Haryana 122002',
    },
    {
        'name': 'Melt & Sip Hospitality Pvt. Ltd.',
        'phone': '+91 11 4158 9032',
        'address': 'Saket District Centre, New Delhi 110017',
    },
]

OUTLET_DOCUMENT_CONTACTS = {
    'dlf_noida': {
        'address': 'DLF Mall of India, Sector 18, Noida, Uttar Pradesh 201301',
        'phone': '+91 120 620 1840',
    },
    'connaught_place': {
        'address': 'Inner Circle, Connaught Place, New Delhi 110001',
        'phone': '+91 11 4365 2190',
    },
    'cyber_hub': {
        'address': 'DLF Cyber Hub, Gurugram, Haryana 122002',
        'phone': '+91 124 612 7740',
    },
    'select_citywalk': {
        'address': 'Select Citywalk, Saket, New Delhi 110017',
        'phone': '+91 11 4612 3380',
    },
    'ambience_gurugram': {
        'address': 'Ambience Mall, NH-8, Gurugram, Haryana 122002',
        'phone': '+91 124 466 9280',
    },
    'elante_chandigarh': {
        'address': 'Elante Mall, Industrial Area Phase I, Chandigarh 160002',
        'phone': '+91 172 503 1180',
    },
    'phoenix_pune': {
        'address': 'Phoenix Marketcity, Viman Nagar, Pune 411014',
        'phone': '+91 20 6689 2240',
    },
}

PROCUREMENT_MANAGERS = [
    {
        'name': 'Meera Kapoor',
        'title': 'Regional Procurement Manager',
        'phone': '+91 98188 40216',
    },
    {
        'name': 'Arjun Malhotra',
        'title': 'Procurement & Logistics Manager',
        'phone': '+91 98731 55904',
    },
    {
        'name': 'Nidhi Verma',
        'title': 'Supply Planning Manager',
        'phone': '+91 99580 73142',
    },
]


def _build_document_metadata(
    outlet_id: str,
    plan_type: str,
) -> dict[str, str]:
    outlet = OUTLETS[outlet_id]
    company_index = sum(ord(char) for char in outlet_id) % len(
        DOCUMENT_COMPANIES
    )
    manager_index = (
        sum(ord(char) for char in f'{outlet_id}:{plan_type}')
        % len(PROCUREMENT_MANAGERS)
    )
    company = DOCUMENT_COMPANIES[company_index]
    manager = PROCUREMENT_MANAGERS[manager_index]
    outlet_contact = OUTLET_DOCUMENT_CONTACTS[outlet_id]
    prefix = 'PO' if plan_type == 'purchase' else 'STN'
    suffix = (
        sum(ord(char) for char in f'{outlet_id}:{plan_type}:{date.today()}')
        % 9000
        + 1000
    )

    return {
        'company_name': company['name'],
        'company_phone': company['phone'],
        'company_address': company['address'],
        'outlet_name': outlet.name,
        'outlet_address': outlet_contact['address'],
        'outlet_phone': outlet_contact['phone'],
        'document_number': (
            f"{prefix}-{date.today():%Y%m%d}-{suffix}"
        ),
        'document_date': date.today().strftime('%d %b %Y'),
        'manager_name': manager['name'],
        'manager_title': manager['title'],
        'manager_phone': manager['phone'],
    }


def build_inventory_planning_data(
    outlet_id: str,
    horizon: int,
    run_number: int = 0,
) -> dict[str, Any]:
    """Return a consistent 7-day or 14-day inventory-planning snapshot."""

    horizon = 7 if int(horizon) <= 7 else 14
    outlet = OUTLETS[outlet_id]
    rng = random.Random(_seed(outlet_id, horizon, run_number) + 1709)

    total_demand = sum(
        int(
            outlet.daily_baseline
            * _demand_multiplier(day_index, True)
            * (1 + day_index * 0.006)
            * rng.uniform(0.97, 1.04)
        )
        for day_index in range(1, horizon + 1)
    )

    shortage_index = (run_number + len(outlet_id) + horizon) % len(PRODUCTS)
    watch_index = (shortage_index + 2) % len(PRODUCTS)
    overstock_index = (shortage_index + 4) % len(PRODUCTS)

    inventory_rows: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    projected_waste_value = 0.0
    at_risk_count = 0
    source_candidates = SOURCE_OUTLETS[outlet_id]

    for index, product in enumerate(PRODUCTS):
        forecast = max(
            30,
            int(total_demand * product['share'] * rng.uniform(0.96, 1.04)),
        )
        average_daily = forecast / horizon
        safety_stock = max(10, int(average_daily * rng.uniform(1.5, 2.0)))
        required_stock = forecast + safety_stock

        if index == shortage_index:
            stock_ratio = rng.uniform(0.64, 0.76)
        elif index == watch_index:
            stock_ratio = rng.uniform(0.88, 0.97)
        elif index == overstock_index:
            stock_ratio = rng.uniform(1.28, 1.42)
        else:
            stock_ratio = rng.uniform(1.01, 1.17)

        on_hand = int(required_stock * stock_ratio)
        gap = max(0, required_stock - on_hand)
        coverage_days = on_hand / max(average_daily, 1)

        transfer_options = {
            source: max(
                0,
                int(
                    average_daily
                    * random.Random(
                        _seed(
                            f'{outlet_id}:{source}:{index}',
                            horizon,
                            run_number,
                        )
                        + source_index * 31
                    ).uniform(0.7, 2.2)
                ),
            )
            for source_index, source in enumerate(source_candidates)
        }

        recommended_qty = int(math.ceil(gap))
        recommended_mode = 'Order'
        status = 'Healthy'
        action = 'No action'

        if gap > average_daily * 0.75:
            status = 'Stockout risk'
            severity = 'High'
            at_risk_count += 1
            recommended_mode = (
                'Transfer'
                if max(transfer_options.values(), default=0) >= recommended_qty
                else 'Order'
            )
            action = f'{recommended_mode} {recommended_qty} units'
            detail = (
                f'Projected shortage of {recommended_qty} units '
                f'across the next {horizon} days.'
            )
            impact = recommended_qty * product['price'] * 0.62
        elif gap > 0:
            status = 'Watch'
            severity = 'Medium'
            at_risk_count += 1
            action = f'Order {recommended_qty} units'
            detail = (
                f'Coverage is below the next {horizon}-day target; '
                f'{recommended_qty} additional units are recommended.'
            )
            impact = recommended_qty * product['price'] * 0.30
        elif on_hand > required_stock * 1.22:
            status = 'Overstock'
            severity = 'Medium'
            recommended_qty = 0
            excess = max(1, on_hand - required_stock)
            action = 'No action'
            detail = (
                f'{excess} units are above the '
                f'{horizon}-day target coverage.'
            )
            impact = excess * product['price'] * 0.20
            projected_waste_value += impact
        else:
            severity = 'Low'
            detail = ''
            impact = 0.0
            recommended_qty = 0

        if severity != 'Low':
            risks.append(
                {
                    'product': product['product'],
                    'severity': severity,
                    'detail': detail,
                    'impact': format_inr(impact),
                    'recommended_qty': recommended_qty,
                }
            )

        inventory_rows.append(
            {
                'id': index + 1,
                'product': product['product'],
                'forecast': forecast,
                'on_hand': on_hand,
                'safety_stock': safety_stock,
                'coverage': f'{coverage_days:.1f} days',
                'status': status,
                'action': action,
                'recommended_qty': recommended_qty,
                'recommended_mode': recommended_mode,
                'transfer_options': transfer_options,
                'action_type': '',
                'action_quantity': 0,
                'transfer_source': '',
                'action_taken': '',
            }
        )

    if len(risks) < 4:
        healthy_rows = [
            row
            for row in inventory_rows
            if row['status'] == 'Healthy'
        ]

        healthy_rows.sort(
            key=lambda row: (
                row['on_hand']
                - row['forecast']
                - row['safety_stock']
            )
        )

        for row in healthy_rows:
            target_buffer = max(
                0,
                row['on_hand']
                - row['forecast']
                - row['safety_stock'],
            )

            risks.append(
                {
                    'product': row['product'],
                    'severity': 'Low',
                    'detail': (
                        f"Healthy for the next {horizon} days; "
                        f"{target_buffer} units remain above target "
                        f"coverage. No action required."
                    ),
                    'impact': '₹0',
                    'recommended_qty': 0,
                }
            )

            if len(risks) >= 4:
                break

    risks.sort(
        key=lambda item: {'High': 0, 'Medium': 1, 'Low': 2}[item['severity']]
    )
    primary_risk = risks[0] if risks else {
        'product': 'No critical risk',
        'severity': 'Low',
        'detail': (
            f'All products are projected to remain within target '
            f'coverage for the next {horizon} days.'
        ),
        'impact': '₹0',
        'recommended_qty': 0,
    }

    prevented_sales_loss = max(
        12000,
        sum(
            risk['recommended_qty']
            for risk in risks
            if risk['severity'] == 'High'
        )
        * 271,
    )
    avoidable_waste = max(
        projected_waste_value,
        6800 + rng.randint(0, 9200),
    )
    service_level = round(
        97.2 - at_risk_count * 0.9 + rng.uniform(-0.25, 0.25),
        1,
    )

    return {
        'outlet': outlet,
        'horizon': horizon,
        'total_demand': total_demand,
        'inventory_rows': inventory_rows,
        'risks': risks[:4],
        'primary_risk': primary_risk,
        'at_risk_count': at_risk_count,
        'service_level': service_level,
        'avoidable_waste': avoidable_waste,
        'recommendation': {
            'headline': (
                f'Protect the next {horizon}-day demand window '
                f'at {outlet.name}'
            ),
            'body': primary_risk['detail'],
            'impact': format_inr(prevented_sales_loss),
            'waste': format_inr(avoidable_waste),
            'priority': primary_risk['severity'],
        },
    }


def _source_summary(
    sources: list[str],
) -> str:
    unique_sources = list(
        dict.fromkeys(
            source
            for source in sources
            if source
        )
    )

    if not unique_sources:
        return '—'

    if len(unique_sources) == 1:
        return unique_sources[0]

    return (
        f'{unique_sources[0]} '
        f'+ {len(unique_sources) - 1}'
    )


def _purchase_scope(
    purchase_details: list[dict[str, Any]],
) -> str:
    if not purchase_details:
        return 'No purchase items'

    ingredient_count = len(purchase_details)
    vendor_count = len(
        {
            detail['vendor']
            for detail in purchase_details
        }
    )

    ingredient_word = (
        'ingredient'
        if ingredient_count == 1
        else 'ingredients'
    )

    vendor_word = (
        'vendor'
        if vendor_count == 1
        else 'vendors'
    )

    return (
        f'{ingredient_count} {ingredient_word} · '
        f'{vendor_count} {vendor_word}'
    )


def _transfer_scope(
    transfer_details: list[dict[str, Any]],
) -> str:
    if not transfer_details:
        return 'No transfer items'

    total_units = sum(
        int(detail['quantity'])
        for detail in transfer_details
    )

    product_count = len(
        {
            detail['product']
            for detail in transfer_details
        }
    )

    product_word = (
        'product'
        if product_count == 1
        else 'products'
    )

    return (
        f'{total_units} units · '
        f'{product_count} {product_word}'
    )


def _transfer_completion(
    transfer_details: list[dict[str, Any]],
) -> str:
    if not transfer_details:
        return '—'

    if len(transfer_details) == 1:
        return transfer_details[0]['eta']

    return (
        (
            date.today()
            + timedelta(days=2)
        ).strftime('%d %b')
        + ' · 15:00'
    )


def build_plan_summary(
    outlet_id: str,
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return one purchase-order row and one store-transfer row."""

    outlet = OUTLETS[outlet_id]
    purchase_items: dict[tuple[str, str, str, float], dict[str, Any]] = {}

    for row in inventory_rows:
        if row.get('action_type') != 'Order':
            continue

        product_quantity = int(row.get('action_quantity', 0))

        if product_quantity <= 0:
            continue

        for ingredient, per_unit, unit, vendor, unit_cost in PRODUCT_RECIPES[
            row['product']
        ]:
            key = (vendor, ingredient, unit, unit_cost)
            item = purchase_items.setdefault(
                key,
                {
                    'vendor': vendor,
                    'item': ingredient,
                    'quantity': 0.0,
                    'unit': unit,
                    'cost_value': 0.0,
                },
            )
            quantity = product_quantity * per_unit
            item['quantity'] += quantity
            item['cost_value'] += quantity * unit_cost

    purchase_details = [
        {
            'id': index,
            'vendor': item['vendor'],
            'vendor_phone': VENDOR_DIRECTORY[item['vendor']]['phone'],
            'vendor_address': VENDOR_DIRECTORY[item['vendor']]['address'],
            'item': item['item'],
            'quantity': round(item['quantity'], 2),
            'unit': item['unit'],
            'cost': format_inr(item['cost_value']),
            'cost_value': item['cost_value'],
        }
        for index, item in enumerate(
            sorted(
                purchase_items.values(),
                key=lambda value: (value['vendor'], value['item']),
            ),
            start=1,
        )
    ]

    transfer_details: list[dict[str, Any]] = []

    for index, row in enumerate(
        (
            row
            for row in inventory_rows
            if (
                row.get('action_type') == 'Transfer'
                and int(row.get('action_quantity', 0)) > 0
            )
        )
    ):
        transfer_resource = TRANSFER_RESOURCES[
            index % len(TRANSFER_RESOURCES)
        ]
        quantity = int(row['action_quantity'])
        cost_value = 650 + quantity * 3.5
        eta_date = date.today() + timedelta(days=1 + index % 2)

        transfer_details.append(
            {
                'id': index + 1,
                'product': row['product'],
                'source': row.get('transfer_source', 'Nearby outlet'),
                'destination': outlet.name,
                'quantity': quantity,
                'driver': transfer_resource['driver'],
                'driver_phone': transfer_resource['phone'],
                'vehicle': transfer_resource['vehicle'],
                'eta': (
                    f"{eta_date.strftime('%d %b')} · "
                    f"{'10:30' if index % 2 == 0 else '15:00'}"
                ),
                'cost': format_inr(cost_value),
                'cost_value': cost_value,
            }
        )

    purchase_cost = sum(item['cost_value'] for item in purchase_details)
    transfer_cost = sum(item['cost_value'] for item in transfer_details)
    purchase_metadata = _build_document_metadata(
        outlet_id,
        'purchase',
    )
    transfer_metadata = _build_document_metadata(
        outlet_id,
        'transfer',
    )

    return [
        {
            'id': 'purchase_order',
            'plan': 'Purchase order',
            'scope': _purchase_scope(
                purchase_details
            ),
            'source_summary': _source_summary(
                [
                    detail['vendor']
                    for detail in purchase_details
                ]
            ),
            'expected_completion': (
                (
                    date.today()
                    + timedelta(days=2)
                ).strftime('%d %b')
                + ' · 10:00'
                if purchase_details
                else '—'
            ),
            'cost': format_inr(purchase_cost),
            'status': (
                'Ready for approval'
                if purchase_details
                else 'No actions selected'
            ),
            'plan_type': 'purchase',
            'details': purchase_details,
            'total_cost_value': purchase_cost,
            **purchase_metadata,
        },
        {
            'id': 'store_transfer',
            'plan': 'Store transfer',
            'scope': _transfer_scope(
                transfer_details
            ),
            'source_summary': _source_summary(
                [
                    detail['source']
                    for detail in transfer_details
                ]
            ),
            'expected_completion': _transfer_completion(
                transfer_details
            ),
            'cost': format_inr(transfer_cost),
            'status': (
                'Ready for approval'
                if transfer_details
                else 'No actions selected'
            ),
            'plan_type': 'transfer',
            'details': transfer_details,
            'total_cost_value': transfer_cost,
            **transfer_metadata,
        },
    ]

