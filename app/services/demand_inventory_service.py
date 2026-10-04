from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from copy import deepcopy
import math
import random
from typing import Any

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.mock_data import (
    OUTLETS as INDIA_OUTLETS,
    REGIONS as INDIA_REGIONS,
    build_dashboard_snapshot as build_india_dashboard_snapshot,
    build_inventory_planning_data as build_india_inventory_planning_data,
    build_plan_summary as build_india_plan_summary,
    format_inr,
)
from app.services.currency_service import format_money
from app.data.ingredient_bom import BOM_BY_BRAND
from app.services.ingredient_planning_service import (
    ensure_ingredient_stock, build_ingredient_rows, build_ingredient_purchase_lines,
)


@dataclass(frozen=True)
class DemandOutlet:
    outlet_id: str
    name: str
    city: str
    region: str
    outlet_format: str
    daily_baseline: int
    delivery_share: int
    cluster: str
    average_ticket: float


CANADA_PRODUCTS: list[dict[str, Any]] = [
    {
        'product': 'Maple Cream Cold Brew',
        'price': 6.95,
        'share': 0.19,
        'ingredient': 'Cold brew concentrate',
    },
    {
        'product': 'Salted Maple Latte',
        'price': 7.25,
        'share': 0.18,
        'ingredient': 'Maple syrup',
    },
    {
        'product': 'Blueberry Oat Latte',
        'price': 7.45,
        'share': 0.16,
        'ingredient': 'Blueberry compote',
    },
    {
        'product': 'Vanilla Bean Frappe',
        'price': 7.75,
        'share': 0.15,
        'ingredient': 'Vanilla base',
    },
    {
        'product': 'Montreal Mocha',
        'price': 7.85,
        'share': 0.13,
        'ingredient': 'Chocolate sauce',
    },
    {
        'product': 'Strawberry Yogurt Smoothie',
        'price': 8.25,
        'share': 0.11,
        'ingredient': 'Strawberry puree',
    },
    {
        'product': 'Butter Tart Sundae',
        'price': 8.95,
        'share': 0.08,
        'ingredient': 'Butter tart crumble',
    },
]


CANADA_DEMAND_SIGNALS: list[dict[str, Any]] = [
    {'icon': 'sports_hockey', 'label': 'NHL home-game night', 'impact_pct': 14.8, 'metric': 'evening traffic'},
    {'icon': 'wb_sunny', 'label': 'Warm afternoon', 'impact_pct': 9.2, 'metric': 'cold beverage demand'},
    {'icon': 'festival', 'label': 'Long-weekend event', 'impact_pct': 12.4, 'metric': 'all-day footfall'},
    {'icon': 'celebration', 'label': 'Downtown festival', 'impact_pct': 11.7, 'metric': 'walk-in demand'},
    {'icon': 'school', 'label': 'University term activity', 'impact_pct': 7.6, 'metric': 'afternoon demand'},
    {'icon': 'music_note', 'label': 'Arena concert nearby', 'impact_pct': 13.1, 'metric': 'post-event demand'},
    {'icon': 'delivery_dining', 'label': 'Delivery-app promotion', 'impact_pct': 10.9, 'metric': 'delivery orders'},
    {'icon': 'flight', 'label': 'Tourism weekend uplift', 'impact_pct': 7.4, 'metric': 'all-day demand'},
    {'icon': 'ac_unit', 'label': 'Winter storm warning', 'impact_pct': -10.6, 'metric': 'walk-in traffic'},
    {'icon': 'directions_subway', 'label': 'Transit service disruption', 'impact_pct': -6.5, 'metric': 'commuter traffic'},
    {'icon': 'thermostat', 'label': 'Heat warning', 'impact_pct': 13.7, 'metric': 'cold beverage demand'},
    {'icon': 'local_offer', 'label': 'Shopping-centre promotion', 'impact_pct': 8.8, 'metric': 'mall footfall'},
]


CANADA_VENDOR_DIRECTORY = {
    'Northern Dairy Supply': {
        'phone': '+1 416-555-0101',
        'address': 'Demo distribution hub · Toronto, ON, Canada',
    },
    'Ontario Roasting Co.': {
        'phone': '+1 416-555-0102',
        'address': 'Demo roasting hub · Mississauga, ON, Canada',
    },
    'Maple Grove Ingredients': {
        'phone': '+1 514-555-0103',
        'address': 'Demo ingredient hub · Montreal, QC, Canada',
    },
    'Pacific Produce Supply': {
        'phone': '+1 604-555-0104',
        'address': 'Demo produce hub · Vancouver, BC, Canada',
    },
    'Prairie Packaging': {
        'phone': '+1 403-555-0105',
        'address': 'Demo packaging hub · Calgary, AB, Canada',
    },
}


CANADA_PRODUCT_RECIPES = BOM_BY_BRAND[CANADA_BRAND_ID]


CANADA_TRANSFER_RESOURCES = [
    {'driver': 'Alex Morgan', 'phone': '+1 416-555-0111', 'vehicle': 'Demo Van CA-01'},
    {'driver': 'Jordan Lee', 'phone': '+1 647-555-0112', 'vehicle': 'Demo Van CA-02'},
    {'driver': 'Taylor Singh', 'phone': '+1 604-555-0113', 'vehicle': 'Demo Van CA-03'},
]


CANADA_PROCUREMENT_MANAGERS = [
    {'name': 'Maya Thompson', 'title': 'National Supply Planning Manager', 'phone': '+1 416-555-0121'},
    {'name': 'Noah Tremblay', 'title': 'Procurement & Logistics Manager', 'phone': '+1 514-555-0122'},
]



def demand_inventory_workflow_state(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical per-brand Demand & Inventory workflow state."""

    return brand_state['workflows']['demand_inventory']


def advance_forecast_run(brand_state: dict[str, Any]) -> int:
    """Advance only the demand-forecast scenario counter."""

    workflow = demand_inventory_workflow_state(brand_state)
    workflow['forecast_run_number'] = int(workflow.get('forecast_run_number', 0)) + 1
    return int(workflow['forecast_run_number'])


def advance_planning_run(brand_state: dict[str, Any]) -> int:
    """Advance only the inventory-planning scenario counter."""

    workflow = demand_inventory_workflow_state(brand_state)
    workflow['planning_run_number'] = int(workflow.get('planning_run_number', 0)) + 1
    return int(workflow['planning_run_number'])

def _stable_seed(text: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(text))


def format_demand_money(value: float, profile: dict[str, Any]) -> str:
    """Use India grouping for the existing demo and standard CAD formatting in Canada."""

    if profile['currency_code'] == 'INR':
        return format_inr(value)
    return format_money(value, profile, compact=False)


def _canada_outlets(brand_state: dict[str, Any]) -> dict[str, DemandOutlet]:
    result: dict[str, DemandOutlet] = {}
    for row in brand_state['network']['outlets']:
        daily_orders = max(90, int(round(float(row['monthly_orders']) / 30)))
        result[str(row['store_id'])] = DemandOutlet(
            outlet_id=str(row['store_id']),
            name=str(row['outlet']),
            city=str(row['city']),
            region=str(row['region']),
            outlet_format=str(row['format']),
            daily_baseline=daily_orders,
            delivery_share=int(row['delivery_share_pct']),
            cluster=str(row['city']),
            average_ticket=float(row['average_ticket']),
        )
    return result


def get_demand_outlets(brand_state: dict[str, Any]) -> dict[str, Any]:
    brand_id = brand_state['brand_id']
    if brand_id == INDIA_BRAND_ID:
        return INDIA_OUTLETS
    if brand_id == CANADA_BRAND_ID:
        return _canada_outlets(brand_state)
    raise KeyError(f'Unsupported demo brand: {brand_id}')


def get_demand_regions(brand_state: dict[str, Any]) -> list[str]:
    if brand_state['brand_id'] == INDIA_BRAND_ID:
        return list(INDIA_REGIONS)
    outlets = get_demand_outlets(brand_state)
    return ['All regions', *sorted({outlet.region for outlet in outlets.values()})]


def outlets_for_region(brand_state: dict[str, Any], region: str) -> dict[str, str]:
    return {
        outlet_id: f'{outlet.name} · {outlet.city}'
        for outlet_id, outlet in get_demand_outlets(brand_state).items()
        if region == 'All regions' or outlet.region == region
    }


def default_demand_selection(brand_state: dict[str, Any]) -> tuple[str, str]:
    if brand_state['brand_id'] == INDIA_BRAND_ID:
        return 'Delhi NCR', 'dlf_noida'

    regions = get_demand_regions(brand_state)
    default_region = 'Ontario' if 'Ontario' in regions else regions[1]
    options = outlets_for_region(brand_state, default_region)
    return default_region, next(iter(options))


def get_demand_outlet(brand_state: dict[str, Any], outlet_id: str) -> Any:
    return get_demand_outlets(brand_state)[outlet_id]


def _demand_multiplier(day_index: int, future: bool) -> float:
    weekday = (date.today() + timedelta(days=day_index)).weekday()
    weekend = 1.16 if weekday >= 5 else 1.0
    event = 1.09 if future and day_index in {2, 3} else 1.0
    return weekend * event


def _select_canada_signals(
    rng: random.Random,
    excluded_labels: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded_labels = excluded_labels or set()
    available = [s for s in CANADA_DEMAND_SIGNALS if s['label'] not in excluded_labels]
    if len(available) < 3:
        available = CANADA_DEMAND_SIGNALS
    selected = rng.sample(available, 3)
    result: list[dict[str, Any]] = []
    for signal in selected:
        impact = float(signal['impact_pct'])
        result.append({
            **signal,
            'detail': f"{'+' if impact >= 0 else ''}{impact:.1f}% {signal['metric']}",
        })
    return result


def build_dashboard_snapshot(
    brand_state: dict[str, Any],
    outlet_id: str,
    horizon: int = 7,
    run_number: int = 0,
    excluded_signal_labels: set[str] | None = None,
) -> dict[str, Any]:
    """Build one tenant-aware demand snapshot."""

    if brand_state['brand_id'] == INDIA_BRAND_ID:
        return build_india_dashboard_snapshot(
            outlet_id=outlet_id,
            horizon=horizon,
            run_number=run_number,
            excluded_signal_labels=excluded_signal_labels,
        )

    profile = brand_state['profile']
    outlet = get_demand_outlet(brand_state, outlet_id)
    rng = random.Random(_stable_seed(f'canada:{outlet_id}:{horizon}:{run_number}'))

    history_days = 7
    categories: list[str] = []
    actual: list[int | None] = []
    forecast: list[int | None] = []
    lower: list[int | None] = []
    upper: list[int | None] = []
    history_values: list[int] = []
    start = date.today() - timedelta(days=history_days - 1)

    for index in range(history_days):
        current = start + timedelta(days=index)
        categories.append(current.strftime('%d %b'))
        base = outlet.daily_baseline * _demand_multiplier(index - history_days + 1, False)
        value = int(base * rng.uniform(0.92, 1.08))
        history_values.append(value)
        actual.append(value)
        forecast.append(None)
        lower.append(None)
        upper.append(None)

    forecast[-1] = history_values[-1]
    lower[-1] = history_values[-1]
    upper[-1] = history_values[-1]

    future_values: list[int] = []
    for index in range(1, horizon + 1):
        current = date.today() + timedelta(days=index)
        categories.append(current.strftime('%d %b'))
        base = outlet.daily_baseline * _demand_multiplier(index, True)
        trend = 1 + index * 0.004
        value = int(base * trend * rng.uniform(0.96, 1.05))
        uncertainty = 0.07 + index * 0.004
        future_values.append(value)
        actual.append(None)
        forecast.append(value)
        lower.append(int(value * (1 - uncertainty)))
        upper.append(int(value * (1 + uncertainty)))

    predicted_units = sum(future_values)
    expected_revenue = predicted_units * outlet.average_ticket
    confidence = round(92.2 - max(0, horizon - 7) * 0.20 + rng.uniform(-0.5, 0.5), 1)

    tomorrow_total = future_values[0]
    inventory_rows: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    at_risk_count = 0
    projected_waste_value = 0.0

    for index, product in enumerate(CANADA_PRODUCTS):
        product_forecast = max(12, int(tomorrow_total * product['share'] * rng.uniform(0.92, 1.08)))
        safety_stock = max(5, int(product_forecast * rng.uniform(0.14, 0.22)))

        if index == (run_number + len(outlet_id)) % len(CANADA_PRODUCTS):
            on_hand = int(product_forecast * rng.uniform(0.48, 0.70))
        elif index == (run_number + len(outlet_id) + 3) % len(CANADA_PRODUCTS):
            on_hand = int(product_forecast * rng.uniform(1.55, 1.85))
        else:
            on_hand = int(product_forecast * rng.uniform(0.94, 1.40))

        available_after_safety = on_hand - safety_stock
        gap = available_after_safety - product_forecast
        coverage = round(on_hand / max(product_forecast, 1), 1)

        if gap < -5:
            status = 'Stockout risk'
            severity = 'High'
            recommended_qty = abs(gap) + safety_stock
            action = f'Transfer {recommended_qty} units'
            at_risk_count += 1
            impact_value = recommended_qty * product['price'] * 0.62
            risks.append({
                'product': product['product'],
                'severity': severity,
                'detail': f'Projected shortage of {recommended_qty} units before tomorrow evening peak.',
                'impact': format_demand_money(impact_value, profile),
                'recommended_qty': recommended_qty,
            })
        elif coverage > 1.6:
            status = 'Overstock'
            severity = 'Medium'
            excess = max(1, on_hand - product_forecast - safety_stock)
            action = f'Redeploy {excess} units'
            impact_value = excess * product['price'] * 0.32
            projected_waste_value += impact_value
            risks.append({
                'product': product['product'],
                'severity': severity,
                'detail': f'{excess} units are above target coverage and may become waste.',
                'impact': format_demand_money(impact_value, profile),
                'recommended_qty': excess,
            })
        elif gap < 3:
            status = 'Watch'
            severity = 'Medium'
            top_up = safety_stock + 4
            action = f'Top up {top_up} units'
            at_risk_count += 1
            impact_value = top_up * product['price'] * 0.30
            risks.append({
                'product': product['product'],
                'severity': severity,
                'detail': 'Inventory is adequate only if demand stays near the lower forecast bound.',
                'impact': format_demand_money(impact_value, profile),
                'recommended_qty': top_up,
            })
        else:
            status = 'Healthy'
            action = 'No action'

        inventory_rows.append({
            'id': index + 1,
            'product': product['product'],
            'forecast': product_forecast,
            'on_hand': on_hand,
            'safety_stock': safety_stock,
            'coverage': f'{coverage:.1f} days',
            'status': status,
            'action': action,
        })

    risks.sort(key=lambda item: {'High': 0, 'Medium': 1, 'Low': 2}[item['severity']])
    primary_risk = risks[0] if risks else {
        'product': 'No critical risk',
        'severity': 'Low',
        'detail': 'All products are projected to remain within target coverage.',
        'impact': format_demand_money(0, profile),
        'recommended_qty': 0,
    }

    service_level = round(97.3 - at_risk_count * 0.85 + rng.uniform(-0.25, 0.25), 1)
    prevented_sales_loss = max(
        350.0,
        sum(item['recommended_qty'] for item in risks if item['severity'] == 'High') * outlet.average_ticket,
    )
    avoidable_waste = max(projected_waste_value, 180.0 + rng.uniform(0, 260))

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
        'signals': _select_canada_signals(rng, excluded_signal_labels),
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
            'impact': format_demand_money(prevented_sales_loss, profile),
            'waste': format_demand_money(avoidable_waste, profile),
            'priority': primary_risk['severity'],
        },
    }


def _canada_source_candidates(brand_state: dict[str, Any], outlet_id: str) -> list[str]:
    outlets = get_demand_outlets(brand_state)
    target = outlets[outlet_id]
    same_region = [
        outlet.name for key, outlet in outlets.items()
        if key != outlet_id and outlet.region == target.region
    ]
    if len(same_region) >= 2:
        return same_region[:2]
    fallback = [outlet.name for key, outlet in outlets.items() if key != outlet_id]
    return (same_region + fallback)[:2]


def _build_item_planning_data(
    brand_state: dict[str, Any],
    outlet_id: str,
    horizon: int,
    run_number: int = 0,
) -> dict[str, Any]:
    """Build a planning snapshot using a planning-specific run counter."""

    if brand_state['brand_id'] == INDIA_BRAND_ID:
        return build_india_inventory_planning_data(
            outlet_id=outlet_id,
            horizon=horizon,
            run_number=run_number,
        )

    profile = brand_state['profile']
    outlet = get_demand_outlet(brand_state, outlet_id)
    horizon = 7 if int(horizon) <= 7 else 14
    rng = random.Random(_stable_seed(f'canada-plan:{outlet_id}:{horizon}:{run_number}'))

    total_demand = sum(
        int(
            outlet.daily_baseline
            * _demand_multiplier(day_index, True)
            * (1 + day_index * 0.004)
            * rng.uniform(0.97, 1.04)
        )
        for day_index in range(1, horizon + 1)
    )

    shortage_index = (run_number + len(outlet_id) + horizon) % len(CANADA_PRODUCTS)
    watch_index = (shortage_index + 2) % len(CANADA_PRODUCTS)
    overstock_index = (shortage_index + 4) % len(CANADA_PRODUCTS)
    source_candidates = _canada_source_candidates(brand_state, outlet_id)

    inventory_rows: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    projected_waste_value = 0.0
    at_risk_count = 0

    for index, product in enumerate(CANADA_PRODUCTS):
        forecast = max(20, int(total_demand * product['share'] * rng.uniform(0.96, 1.04)))
        average_daily = forecast / horizon
        safety_stock = max(6, int(average_daily * rng.uniform(1.4, 1.9)))
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
                        _stable_seed(f'{outlet_id}:{source}:{index}:{horizon}:{run_number}')
                    ).uniform(0.7, 2.2)
                ),
            )
            for source in source_candidates
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
                'Transfer' if max(transfer_options.values(), default=0) >= recommended_qty else 'Order'
            )
            action = f'{recommended_mode} {recommended_qty} units'
            detail = f'Projected shortage of {recommended_qty} units across the next {horizon} days.'
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
            detail = f'{excess} units are above the {horizon}-day target coverage.'
            impact = excess * product['price'] * 0.20
            projected_waste_value += impact
        else:
            severity = 'Low'
            detail = ''
            impact = 0.0
            recommended_qty = 0

        if severity != 'Low':
            risks.append({
                'product': product['product'],
                'severity': severity,
                'detail': detail,
                'impact': format_demand_money(impact, profile),
                'recommended_qty': recommended_qty,
            })

        inventory_rows.append({
            'id': index + 1,
            'product': product['product'],
            'forecast': forecast,
            'on_hand': on_hand,
            'usable_stock': max(0, on_hand - safety_stock),
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
        })

    if len(risks) < 4:
        healthy_rows = [row for row in inventory_rows if row['status'] == 'Healthy']
        healthy_rows.sort(key=lambda row: row['on_hand'] - row['forecast'] - row['safety_stock'])
        for row in healthy_rows:
            buffer_units = max(0, row['on_hand'] - row['forecast'] - row['safety_stock'])
            risks.append({
                'product': row['product'],
                'severity': 'Low',
                'detail': (
                    f"Healthy for the next {horizon} days; {buffer_units} units remain "
                    'above target coverage. No action required.'
                ),
                'impact': format_demand_money(0, profile),
                'recommended_qty': 0,
            })
            if len(risks) >= 4:
                break

    risks.sort(key=lambda item: {'High': 0, 'Medium': 1, 'Low': 2}[item['severity']])
    primary_risk = risks[0] if risks else {
        'product': 'No critical risk',
        'severity': 'Low',
        'detail': f'All products are projected to remain within target coverage for the next {horizon} days.',
        'impact': format_demand_money(0, profile),
        'recommended_qty': 0,
    }

    prevented_sales_loss = max(
        350.0,
        sum(risk['recommended_qty'] for risk in risks if risk['severity'] == 'High') * outlet.average_ticket,
    )
    avoidable_waste = max(projected_waste_value, 180.0 + rng.uniform(0, 260))
    service_level = round(97.3 - at_risk_count * 0.9 + rng.uniform(-0.25, 0.25), 1)

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
            'headline': f'Protect the next {horizon}-day demand window at {outlet.name}',
            'body': primary_risk['detail'],
            'impact': format_demand_money(prevented_sales_loss, profile),
            'waste': format_demand_money(avoidable_waste, profile),
            'priority': primary_risk['severity'],
        },
    }


def ensure_usable_stock(planning_data: dict[str, Any]) -> dict[str, Any]:
    """Add a consistent usable-stock field to legacy India planning rows."""

    for row in planning_data.get('inventory_rows', []):
        row['usable_stock'] = max(0, int(row['on_hand']) - int(row['safety_stock']))
    return planning_data


def _source_summary(sources: list[str]) -> str:
    unique = list(dict.fromkeys(source for source in sources if source))
    if not unique:
        return '—'
    if len(unique) == 1:
        return unique[0]
    return f'{unique[0]} + {len(unique) - 1}'


def _purchase_scope(details: list[dict[str, Any]]) -> str:
    if not details:
        return 'No purchase items'
    vendors = len({detail['vendor'] for detail in details})
    return f"{len(details)} {'ingredient' if len(details) == 1 else 'ingredients'} · {vendors} {'vendor' if vendors == 1 else 'vendors'}"


def _transfer_scope(details: list[dict[str, Any]]) -> str:
    if not details:
        return 'No transfer items'
    total_units = sum(int(detail['quantity']) for detail in details)
    products = len({detail['product'] for detail in details})
    return f"{total_units} units · {products} {'product' if products == 1 else 'products'}"


def _canada_document_metadata(
    brand_state: dict[str, Any],
    outlet_id: str,
    plan_type: str,
) -> dict[str, str]:
    outlet = get_demand_outlet(brand_state, outlet_id)
    manager = CANADA_PROCUREMENT_MANAGERS[
        _stable_seed(f'{outlet_id}:{plan_type}') % len(CANADA_PROCUREMENT_MANAGERS)
    ]
    prefix = 'PO-CA' if plan_type == 'purchase' else 'STN-CA'
    suffix = _stable_seed(f'{outlet_id}:{plan_type}:{date.today()}') % 9000 + 1000
    return {
        'company_name': 'Maple & Mason Café Canada',
        'company_phone': '+1 416-555-0100',
        'company_address': 'Demo operations office · Toronto, ON, Canada',
        'outlet_name': outlet.name,
        'outlet_address': f'Demo outlet · {outlet.city}, {outlet.region}, Canada',
        'outlet_phone': '+1 416-555-0190',
        'document_number': f'{prefix}-{date.today():%Y%m%d}-{suffix}',
        'document_date': date.today().strftime('%d %b %Y'),
        'manager_name': manager['name'],
        'manager_title': manager['title'],
        'manager_phone': manager['phone'],
    }


def _build_legacy_plan_summary(
    brand_state: dict[str, Any],
    outlet_id: str,
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build tenant-specific procurement and transfer documents."""

    if brand_state['brand_id'] == INDIA_BRAND_ID:
        return build_india_plan_summary(outlet_id=outlet_id, inventory_rows=inventory_rows)

    profile = brand_state['profile']
    outlet = get_demand_outlet(brand_state, outlet_id)
    purchase_items: dict[tuple[str, str, str, float], dict[str, Any]] = {}

    for row in inventory_rows:
        if row.get('action_type') != 'Order':
            continue
        product_quantity = int(row.get('action_quantity', 0))
        if product_quantity <= 0:
            continue
        for ingredient, per_unit, unit, vendor, unit_cost in CANADA_PRODUCT_RECIPES[row['product']]:
            key = (vendor, ingredient, unit, unit_cost)
            item = purchase_items.setdefault(key, {
                'vendor': vendor,
                'item': ingredient,
                'quantity': 0.0,
                'unit': unit,
                'cost_value': 0.0,
            })
            quantity = product_quantity * per_unit
            item['quantity'] += quantity
            item['cost_value'] += quantity * unit_cost

    purchase_details = [
        {
            'id': index,
            'vendor': item['vendor'],
            'vendor_phone': CANADA_VENDOR_DIRECTORY[item['vendor']]['phone'],
            'vendor_address': CANADA_VENDOR_DIRECTORY[item['vendor']]['address'],
            'item': item['item'],
            'quantity': round(item['quantity'], 2),
            'unit': item['unit'],
            'cost': format_demand_money(item['cost_value'], profile),
            'cost_value': item['cost_value'],
        }
        for index, item in enumerate(
            sorted(purchase_items.values(), key=lambda value: (value['vendor'], value['item'])),
            start=1,
        )
    ]

    transfer_details: list[dict[str, Any]] = []
    selected_transfers = [
        row for row in inventory_rows
        if row.get('action_type') == 'Transfer' and int(row.get('action_quantity', 0)) > 0
    ]
    for index, row in enumerate(selected_transfers):
        resource = CANADA_TRANSFER_RESOURCES[index % len(CANADA_TRANSFER_RESOURCES)]
        quantity = int(row['action_quantity'])
        cost_value = 35.0 + quantity * 0.45
        eta_date = date.today() + timedelta(days=1 + index % 2)
        transfer_details.append({
            'id': index + 1,
            'product': row['product'],
            'source': row.get('transfer_source', 'Nearby outlet'),
            'destination': outlet.name,
            'quantity': quantity,
            'driver': resource['driver'],
            'driver_phone': resource['phone'],
            'vehicle': resource['vehicle'],
            'eta': f"{eta_date.strftime('%d %b')} · {'10:30' if index % 2 == 0 else '15:00'}",
            'cost': format_demand_money(cost_value, profile),
            'cost_value': cost_value,
        })

    purchase_cost = sum(item['cost_value'] for item in purchase_details)
    transfer_cost = sum(item['cost_value'] for item in transfer_details)
    purchase_metadata = _canada_document_metadata(brand_state, outlet_id, 'purchase')
    transfer_metadata = _canada_document_metadata(brand_state, outlet_id, 'transfer')

    return [
        {
            'id': 'purchase_order',
            'plan': 'Purchase order',
            'scope': _purchase_scope(purchase_details),
            'source_summary': _source_summary([detail['vendor'] for detail in purchase_details]),
            'expected_completion': (
                (date.today() + timedelta(days=2)).strftime('%d %b') + ' · 10:00'
                if purchase_details else '—'
            ),
            'cost': format_demand_money(purchase_cost, profile),
            'status': 'Ready for approval' if purchase_details else 'No actions selected',
            'plan_type': 'purchase',
            'details': purchase_details,
            'total_cost_value': purchase_cost,
            **purchase_metadata,
        },
        {
            'id': 'store_transfer',
            'plan': 'Store transfer',
            'scope': _transfer_scope(transfer_details),
            'source_summary': _source_summary([detail['source'] for detail in transfer_details]),
            'expected_completion': (
                (date.today() + timedelta(days=2)).strftime('%d %b') + ' · 15:00'
                if len(transfer_details) > 1
                else transfer_details[0]['eta'] if transfer_details
                else '—'
            ),
            'cost': format_demand_money(transfer_cost, profile),
            'status': 'Ready for approval' if transfer_details else 'No actions selected',
            'plan_type': 'transfer',
            'details': transfer_details,
            'total_cost_value': transfer_cost,
            **transfer_metadata,
        },
    ]


def build_inventory_planning_data(
    brand_state: dict[str, Any], outlet_id: str, horizon: int, run_number: int = 0,
) -> dict[str, Any]:
    planning = _build_item_planning_data(brand_state, outlet_id, horizon, run_number)
    baseline = _build_item_planning_data(brand_state, outlet_id, 7, 0)
    ensure_ingredient_stock(brand_state, outlet_id, baseline['inventory_rows'])
    planning['ingredient_rows'] = build_ingredient_rows(
        brand_state, outlet_id, planning['inventory_rows'],
    )
    return planning


def build_plan_summary(
    brand_state: dict[str, Any], outlet_id: str,
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # Reuse existing country-specific document headers and transfer logistics.
    # Purchase lines are exclusively sourced from the same net BOM calculation
    # used by the ingredient chart, never from gross legacy recipe quantities.
    transfer_rows = deepcopy(inventory_rows)
    for row in transfer_rows:
        if row.get('action_type') == 'Order':
            row['action_type'] = ''
    plans = _build_legacy_plan_summary(brand_state, outlet_id, transfer_rows)
    baseline = _build_item_planning_data(brand_state, outlet_id, 7, 0)
    ensure_ingredient_stock(brand_state, outlet_id, baseline['inventory_rows'])
    ingredients = build_ingredient_rows(brand_state, outlet_id, inventory_rows)
    details = build_ingredient_purchase_lines(brand_state, ingredients)
    profile = brand_state['profile']
    for line in details:
        line['cost'] = format_demand_money(line['cost_value'], profile)
    purchase = next(plan for plan in plans if plan['plan_type'] == 'purchase')
    cost = round(sum(line['cost_value'] for line in details), 2)
    purchase.update({
        'details': details, 'scope': _purchase_scope(details),
        'source_summary': _source_summary([line['vendor'] for line in details]),
        'total_cost_value': cost, 'cost': format_demand_money(cost, profile),
        'status': 'Ready for approval' if details else 'No procurement needed',
        'expected_completion': (date.today() + timedelta(days=2)).strftime('%d %b')
            + ' · 10:00' if details else '—',
        'calculation_basis': 'BOM for remaining production minus ingredient on hand; no ingredient safety stock',
        'ingredient_snapshot': ingredients,
    })
    return plans
