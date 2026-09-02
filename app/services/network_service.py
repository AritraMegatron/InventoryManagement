from __future__ import annotations

from copy import deepcopy
import random
from typing import Any, Iterable

from app.services.currency_service import format_money



def _stable_seed(text: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(text))


def refresh_network_forecast(
    outlets: list[dict[str, Any]],
    run_number: int,
) -> None:
    """Mutate the canonical synthetic forecast for one deterministic run.

    Keeping this outside the NiceGUI page makes the use case testable and gives
    the future repository-backed implementation one application-service seam.
    """

    for outlet in outlets:
        rng = random.Random(
            _stable_seed(str(outlet['store_id'])) + int(run_number) * 307
        )
        outlet['growth_pct'] = round(
            max(
                -12.0,
                min(
                    16.0,
                    float(outlet['growth_pct']) + rng.uniform(-2.2, 2.8),
                ),
            ),
            1,
        )
        outlet['next_month_revenue'] = round(
            float(outlet['monthly_revenue'])
            * (1 + float(outlet['growth_pct']) / 100),
            2,
        )

def summarize_network(outlets: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Derive brand-level KPIs from the canonical outlet rows."""

    rows = list(outlets)
    revenue = sum(float(row['monthly_revenue']) for row in rows)
    profit = sum(float(row['operating_profit']) for row in rows)
    forecast = sum(float(row['next_month_revenue']) for row in rows)
    employees = sum(int(row['employees']) for row in rows)

    return {
        'outlet_count': len(rows),
        'monthly_revenue': round(revenue, 2),
        'operating_profit': round(profit, 2),
        'next_month_revenue': round(forecast, 2),
        'forecast_growth_pct': round(
            ((forecast / revenue) - 1) * 100 if revenue else 0.0,
            1,
        ),
        'operating_margin_pct': round(
            profit / revenue * 100 if revenue else 0.0,
            1,
        ),
        'employees': employees,
        'underperforming_count': sum(
            1 for row in rows if row['status'] == 'Underperforming'
        ),
        'above_target_count': sum(
            1 for row in rows if row['status'] == 'Above target'
        ),
        'newly_opened_count': sum(
            1 for row in rows if row['status'] == 'Newly opened'
        ),
    }


def money_unit(profile: dict[str, Any]) -> tuple[float, str]:
    """Return the compact table divisor/label for the tenant currency."""

    if profile['currency_code'] == 'INR':
        return 100_000.0, '₹L'
    if profile['currency_code'] == 'CAD':
        return 1_000.0, 'C$K'
    return 1_000.0, f"{profile['currency_code']} K"


def build_network_view_rows(
    outlets: Iterable[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build UI rows while leaving canonical money values untouched."""

    divisor, _ = money_unit(profile)
    rows: list[dict[str, Any]] = []

    for outlet in outlets:
        row = deepcopy(outlet)
        employees = max(1, int(outlet['employees']))
        row.update(
            {
                'revenue_unit': round(float(outlet['monthly_revenue']) / divisor, 1),
                'profit_unit': round(float(outlet['operating_profit']) / divisor, 1),
                'forecast_unit': round(float(outlet['next_month_revenue']) / divisor, 1),
                'revenue_per_employee_unit': round(
                    float(outlet['monthly_revenue']) / employees / divisor,
                    2,
                ),
                'rent_unit': round(float(outlet['monthly_rent']) / divisor, 1),
            }
        )
        rows.append(row)

    return rows


def build_table_columns(profile: dict[str, Any]) -> list[dict[str, Any]]:
    _, unit_label = money_unit(profile)
    return [
        {
            'name': 'outlet',
            'label': 'Outlet',
            'field': 'outlet',
            'align': 'left',
            'sortable': True,
        },
        {
            'name': 'city',
            'label': 'City',
            'field': 'city',
            'align': 'left',
            'sortable': True,
        },
        {
            'name': 'revenue_unit',
            'label': f'Revenue {unit_label}',
            'field': 'revenue_unit',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'profit_unit',
            'label': f'Profit {unit_label}',
            'field': 'profit_unit',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'margin_pct',
            'label': 'Margin %',
            'field': 'margin_pct',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'forecast_unit',
            'label': f'Next month {unit_label}',
            'field': 'forecast_unit',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'growth_pct',
            'label': 'Forecast %',
            'field': 'growth_pct',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'employees',
            'label': 'Employees',
            'field': 'employees',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'revenue_per_employee_unit',
            'label': f'Rev/employee {unit_label}',
            'field': 'revenue_per_employee_unit',
            'align': 'right',
            'sortable': True,
        },
        {
            'name': 'status',
            'label': 'Status',
            'field': 'status',
            'align': 'left',
            'sortable': True,
        },
    ]


def build_region_centers(
    outlets: Iterable[dict[str, Any]],
    profile: dict[str, Any],
) -> dict[str, tuple[float, float, int]]:
    """Build tenant-specific map centers without hardcoding countries."""

    rows = list(outlets)
    result: dict[str, tuple[float, float, int]] = {
        'All regions': (
            float(profile['map_center_lat']),
            float(profile['map_center_lon']),
            int(profile['map_zoom']),
        )
    }

    for region in sorted({str(row['region']) for row in rows}):
        region_rows = [row for row in rows if row['region'] == region]
        latitude = sum(float(row['lat']) for row in region_rows) / len(region_rows)
        longitude = sum(float(row['lon']) for row in region_rows) / len(region_rows)
        zoom = 6 if profile['country_code'] == 'IN' else 5
        result[region] = (round(latitude, 4), round(longitude, 4), zoom)

    return result


def build_priority_actions(
    outlets: Iterable[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create deterministic executive actions from the current brand network."""

    rows = list(outlets)
    if not rows:
        return []

    inventory_outlet = max(
        rows,
        key=lambda row: (float(row['stockout_pct']), float(row['monthly_revenue'])),
    )
    margin_outlet = min(
        rows,
        key=lambda row: (float(row['margin_pct']), -float(row['monthly_revenue'])),
    )

    inventory_risk = max(
        0.0,
        float(inventory_outlet['monthly_revenue'])
        * float(inventory_outlet['stockout_pct'])
        / 100
        * 0.45,
    )
    target_margin = 15.0
    margin_gap = max(0.0, target_margin - float(margin_outlet['margin_pct']))
    margin_risk = max(
        0.0,
        float(margin_outlet['monthly_revenue']) * margin_gap / 100,
    )

    is_canada = profile['country_code'] == 'CA'
    product_title = (
        'Maple Protein Cold Brew'
        if is_canada
        else 'High-Protein Chocolate Shake'
    )
    product_score = 87 if is_canada else 89
    pilot_count = 4 if is_canada else 6

    return [
        {
            'id': 'inventory_risk',
            'priority': 'HIGH',
            'title': f"{inventory_outlet['outlet']} inventory shortage",
            'impact': f"{format_money(inventory_risk, profile)} sales at risk",
            'impact_amount': round(inventory_risk, 2),
            'action': 'Approve stock transfer',
            'button': 'Approve transfer',
            'icon': 'inventory_2',
            'route': '/demand-inventory',
            'approved_status': 'Approved · Transfer task created',
            'outlet_id': inventory_outlet['store_id'],
        },
        {
            'id': 'margin_risk',
            'priority': 'HIGH',
            'title': f"{margin_outlet['outlet']} margin decline",
            'impact': f"{format_money(margin_risk, profile)} monthly profit at risk",
            'impact_amount': round(margin_risk, 2),
            'action': 'Start outlet recovery review',
            'button': 'Start review',
            'icon': 'storefront',
            'route': '/network-intelligence',
            'approved_status': 'Assigned · Recovery review started',
            'outlet_id': margin_outlet['store_id'],
        },
        {
            'id': 'product_pilot',
            'priority': 'MEDIUM',
            'title': product_title,
            'impact': f'{product_score} / 100 product opportunity score',
            'impact_amount': 0.0,
            'action': f'Approve {pilot_count}-outlet pilot',
            'button': 'Approve pilot',
            'icon': 'science',
            'route': '/product-innovation',
            'approved_status': 'Approved · Pilot brief created',
            'opportunity_score': product_score,
        },
    ]


def build_command_center_snapshot(
    outlets: Iterable[dict[str, Any]],
    profile: dict[str, Any],
) -> dict[str, Any]:
    rows = list(outlets)
    summary = summarize_network(rows)
    actions = build_priority_actions(rows, profile)
    revenue_at_risk = sum(float(action.get('impact_amount', 0.0)) for action in actions)

    return {
        'summary': summary,
        'actions': actions,
        'revenue_at_risk': round(revenue_at_risk, 2),
    }
