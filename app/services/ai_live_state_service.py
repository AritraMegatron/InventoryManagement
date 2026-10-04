from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Mapping

from app.data.outlet_candidates import clone_default_candidates
from app.services.currency_service import format_money
from app.services.ingredient_planning_service import build_ingredient_rows, build_ingredient_equivalent_rows
from app.services.demand_inventory_service import (
    build_dashboard_snapshot,
    build_inventory_planning_data,
    default_demand_selection,
    ensure_usable_stock,
    get_demand_outlet,
)
from app.services.network_service import summarize_network
from app.services.outlet_state_service import get_outlet_ai_snapshot
from app.services.product_innovation_service import (
    ensure_product_innovation_state,
    get_pilot_plans,
    get_product_concepts,
)
from app.services.workflow_persistence_service import ensure_demand_inventory_workspace


LIVE_STATE_SCHEMA_VERSION = 1
MAX_NETWORK_ROWS = 8


def _safe_text(value: object) -> str:
    return str(value or '').strip()


def _normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def _query_tokens(query: str) -> set[str]:
    return {
        token
        for token in _normalize(query).split()
        if len(token) >= 3
    }


def _candidate_records(
    brand_state: dict[str, Any],
    outlet_candidate_state: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    raw_candidates: Any = None
    raw_decisions: Any = None

    if isinstance(outlet_candidate_state, Mapping):
        raw_candidates = outlet_candidate_state.get('candidates')
        raw_decisions = outlet_candidate_state.get('decisions')
    else:
        # Outlet Intelligence keeps raw uploaded files in tab storage, but it
        # publishes a sanitized candidate snapshot to canonical brand state.
        # Ask AI reads that snapshot so it never needs NiceGUI client context.
        canonical_snapshot = get_outlet_ai_snapshot(brand_state)
        if isinstance(canonical_snapshot, Mapping):
            raw_candidates = canonical_snapshot.get('candidates')
            raw_decisions = canonical_snapshot.get('decisions')

    if not isinstance(raw_candidates, Mapping):
        raw_candidates = clone_default_candidates(str(brand_state['brand_id']))

    decisions = raw_decisions if isinstance(raw_decisions, Mapping) else {}
    profile = brand_state['profile']
    rows: list[dict[str, Any]] = []

    for candidate_id, candidate_value in raw_candidates.items():
        if not isinstance(candidate_value, Mapping):
            continue
        candidate = dict(candidate_value)
        rent_value = float(candidate.get('rent', 0.0) or 0.0)
        sales_value = float(candidate.get('sales', 0.0) or 0.0)

        # The India Outlet Intelligence MVP still stores candidate rent/sales
        # in lakh units.  Canada stores native CAD.  Convert only for display
        # here so the AI sees exactly the same economics as the UI.
        if profile['currency_code'] == 'INR':
            rent_display = f"₹{rent_value:.1f} lakh/month"
            sales_display = f"₹{sales_value:.1f} lakh/month"
        else:
            rent_display = f"{format_money(rent_value, profile)}/month"
            sales_display = f"{format_money(sales_value, profile)}/month"

        rows.append(
            {
                'candidate_id': str(candidate_id),
                'name': _safe_text(candidate.get('name')),
                'city': _safe_text(candidate.get('city')),
                'region': _safe_text(candidate.get('state') or candidate.get('province')),
                'address': _safe_text(candidate.get('address')),
                'status': _safe_text(candidate.get('status')),
                'location_score': candidate.get('score'),
                'expected_monthly_sales': sales_display,
                'monthly_rent': rent_display,
                'contribution_margin_pct': candidate.get('margin'),
                'break_even_months': candidate.get('break_even'),
                'cannibalization': _safe_text(candidate.get('cannibalization')),
                'management_decision': _safe_text(decisions.get(candidate_id) or 'Not decided'),
                'analysis_status': _safe_text(candidate.get('analysis_status')),
            }
        )

    return rows


def get_company_summary(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Read-only executive summary derived from the canonical network."""

    profile = brand_state['profile']
    summary = summarize_network(brand_state['network']['outlets'])
    return {
        'brand': profile['display_name'],
        'country': profile['country'],
        'currency': profile['currency_code'],
        'outlets': summary['outlet_count'],
        'monthly_revenue': format_money(summary['monthly_revenue'], profile),
        'next_month_revenue': format_money(summary['next_month_revenue'], profile),
        'forecast_growth_pct': summary['forecast_growth_pct'],
        'operating_profit': format_money(summary['operating_profit'], profile),
        'operating_margin_pct': summary['operating_margin_pct'],
        'underperforming_outlets': summary['underperforming_count'],
        'above_target_outlets': summary['above_target_count'],
        'newly_opened_outlets': summary['newly_opened_count'],
    }


def get_outlet_performance(
    brand_state: dict[str, Any],
    user_query: str = '',
    limit: int = MAX_NETWORK_ROWS,
) -> list[dict[str, Any]]:
    """Return the most relevant existing outlets for an AI question."""

    profile = brand_state['profile']
    outlets = list(brand_state['network']['outlets'])
    tokens = _query_tokens(user_query)
    normalized_query = _normalize(user_query)

    def searchable(row: Mapping[str, Any]) -> str:
        return _normalize(
            ' '.join(
                [
                    _safe_text(row.get('outlet')),
                    _safe_text(row.get('city')),
                    _safe_text(row.get('region')),
                    _safe_text(row.get('store_id')),
                ]
            )
        )

    # Prefer explicit outlet/city/region phrases. This avoids common words such
    # as "are" accidentally matching an unrelated place name like "Square".
    matched = []
    if normalized_query:
        for row in outlets:
            phrases = [
                _normalize(_safe_text(row.get('outlet'))),
                _normalize(_safe_text(row.get('city'))),
                _normalize(_safe_text(row.get('region'))),
            ]
            if any(phrase and phrase in normalized_query for phrase in phrases):
                matched.append(row)

    if not matched and tokens:
        stopwords = {
            'the', 'are', 'how', 'what', 'which', 'where', 'outlet', 'outlets',
            'performing', 'performance', 'current', 'needs', 'attention', 'show',
            'tell', 'about', 'give', 'with', 'from', 'that', 'this', 'have',
        }
        meaningful_tokens = tokens - stopwords
        matched = [
            row for row in outlets
            if meaningful_tokens
            and any(token in searchable(row) for token in meaningful_tokens)
        ]

    if matched:
        selected = matched[:limit]
    else:
        # Default to the outlets with the strongest operational concern so
        # generic questions such as "what needs attention?" are useful.
        selected = sorted(
            outlets,
            key=lambda row: (
                row.get('status') != 'Underperforming',
                float(row.get('margin_pct', 0.0)),
                float(row.get('growth_pct', 0.0)),
                -float(row.get('stockout_pct', 0.0)),
            ),
        )[:limit]

    return [
        {
            'store_id': row['store_id'],
            'outlet': row['outlet'],
            'city': row['city'],
            'region': row['region'],
            'status': row['status'],
            'monthly_revenue': format_money(float(row['monthly_revenue']), profile),
            'operating_profit': format_money(float(row['operating_profit']), profile),
            'margin_pct': row['margin_pct'],
            'forecast_growth_pct': row['growth_pct'],
            'stockout_pct': row['stockout_pct'],
            'waste_pct': row['waste_pct'],
            'rent_ratio_pct': row['rent_ratio_pct'],
            'rating': row['rating'],
        }
        for row in selected
    ]


def get_inventory_risks(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Return the current Demand & Inventory scenario without mutating plans."""

    default_region, default_outlet_id = default_demand_selection(brand_state)
    workflow = ensure_demand_inventory_workspace(
        brand_state,
        default_region=default_region,
        default_outlet_id=default_outlet_id,
    )

    if not workflow.get('forecast_loaded', False):
        return {
            'selected_region': workflow.get('region', default_region),
            'selected_outlet_id': workflow.get('outlet_id', default_outlet_id),
            'forecast_loaded': False,
            'status': 'Awaiting Run AI forecast; no demand, inventory KPIs, signals or plan loaded for this selection.',
        }

    outlet_id = str(workflow.get('outlet_id') or default_outlet_id)
    try:
        outlet = get_demand_outlet(brand_state, outlet_id)
    except KeyError:
        outlet_id = default_outlet_id
        workflow['outlet_id'] = outlet_id
        outlet = get_demand_outlet(brand_state, outlet_id)

    forecast_horizon = int(workflow.get('forecast_horizon', 7) or 7)
    planning_horizon = int(workflow.get('planning_horizon', 7) or 7)
    forecast_run = int(workflow.get('forecast_run_number', 0) or 0)
    planning_run = int(workflow.get('planning_run_number', 0) or 0)

    forecast_snapshot = build_dashboard_snapshot(
        brand_state=brand_state,
        outlet_id=outlet_id,
        horizon=forecast_horizon,
        run_number=forecast_run,
    )
    planning_snapshot = ensure_usable_stock(
        build_inventory_planning_data(
            brand_state=brand_state,
            outlet_id=outlet_id,
            horizon=planning_horizon,
            run_number=planning_run,
        )
    )

    persisted_rows = workflow.get('inventory_rows')
    inventory_rows = (
        deepcopy(persisted_rows)
        if workflow.get('inventory_built') and isinstance(persisted_rows, list)
        else deepcopy(planning_snapshot.get('inventory_rows', []))
    )

    return {
        'selected_region': workflow.get('region', default_region),
        'selected_outlet_id': outlet_id,
        'selected_outlet': f'{outlet.name} · {outlet.city}',
        'forecast_horizon_days': forecast_horizon,
        'planning_horizon_days': planning_horizon,
        'forecast_run_number': forecast_run,
        'planning_run_number': planning_run,
        'forecast_kpis': deepcopy(forecast_snapshot.get('kpis', {})),
        'demand_signals': deepcopy(forecast_snapshot.get('signals', [])),
        'planning_risks': deepcopy(planning_snapshot.get('risks', [])),
        'ingredient_chart_equivalents': build_ingredient_equivalent_rows(
            brand_state, planning_snapshot['inventory_rows'],
        ),
        'ingredient_chart_rule': (
            'The chart shows BOM equivalents of full item forecast and usable finished-item stock '
            '(item on hand minus item safety stock). It does not show raw ingredient inventory. '
            'The ingredient_availability field below is the separate raw-stock procurement calculation.'
        ),
        'ingredient_availability': build_ingredient_rows(brand_state, outlet_id, inventory_rows),
        'ingredient_planning_rule': (
            'Produce forecast minus actual finished-item on hand, adjusted by saved production '
            'overrides or incoming finished-item transfers. Explode the shared BOM, then '
            'procure required ingredients minus ingredient on hand. No ingredient safety buffer. '
            'Approved ingredient purchases are ordered, not received.'
        ),
        'inventory_actions_built': bool(workflow.get('inventory_built')),
        'inventory_actions': [
            {
                'product': row.get('product'),
                'status': row.get('status'),
                'action_type': row.get('action_type') or 'Not selected',
                'action_quantity': row.get('action_quantity', 0),
                'transfer_source': row.get('transfer_source') or '',
            }
            for row in inventory_rows
            if (
                row.get('status') in {'Stockout risk', 'Watch', 'Overstock'}
                or row.get('action_type')
            )
        ][:8],
        'plan_generated': bool(workflow.get('plan_generated')),
        'plan_approved': bool(workflow.get('plan_approved')),
        'plan_rows': [
            {
                'plan': row.get('plan'),
                'scope': row.get('scope'),
                'cost': row.get('cost'),
                'status': row.get('status'),
                'expected_completion': row.get('expected_completion'),
            }
            for row in workflow.get('plan_rows', [])
            if isinstance(row, Mapping)
        ],
    }


def get_purchase_plan(brand_state: dict[str, Any]) -> list[dict[str, Any]]:
    return deepcopy(brand_state.get('artifacts', {}).get('purchase_plans', []))


def get_transfer_plan(brand_state: dict[str, Any]) -> list[dict[str, Any]]:
    return deepcopy(brand_state.get('artifacts', {}).get('transfer_plans', []))


def get_replenishment_artifacts(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Return compact generated-document details useful for AI explanations."""

    purchase_rows = get_purchase_plan(brand_state)
    transfer_rows = get_transfer_plan(brand_state)

    return {
        'purchase_plans': [
            {
                'plan': row.get('plan'),
                'status': row.get('status'),
                'cost': row.get('cost'),
                'expected_completion': row.get('expected_completion'),
                'items': [
                    {
                        'vendor': detail.get('vendor'),
                        'item': detail.get('item'),
                        'quantity': detail.get('quantity'),
                        'unit': detail.get('unit'),
                        'cost': detail.get('cost'),
                    }
                    for detail in row.get('details', [])[:8]
                    if isinstance(detail, Mapping)
                ],
            }
            for row in purchase_rows
            if isinstance(row, Mapping)
        ],
        'transfer_plans': [
            {
                'plan': row.get('plan'),
                'status': row.get('status'),
                'cost': row.get('cost'),
                'expected_completion': row.get('expected_completion'),
                'items': [
                    {
                        'product': detail.get('product'),
                        'source': detail.get('source'),
                        'destination': detail.get('destination'),
                        'quantity': detail.get('quantity'),
                        'eta': detail.get('eta'),
                        'cost': detail.get('cost'),
                    }
                    for detail in row.get('details', [])[:8]
                    if isinstance(detail, Mapping)
                ],
            }
            for row in transfer_rows
            if isinstance(row, Mapping)
        ],
    }


def get_location_candidates(
    brand_state: dict[str, Any],
    outlet_candidate_state: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return _candidate_records(brand_state, outlet_candidate_state)


def get_product_opportunities(brand_state: dict[str, Any]) -> dict[str, Any]:
    workflow = ensure_product_innovation_state(brand_state)
    concepts = get_product_concepts(brand_state)
    pilots = get_pilot_plans(brand_state)

    rows = [
        {
            'concept_id': concept_id,
            'name': concept.get('name'),
            'score': concept.get('score'),
            'momentum': concept.get('momentum'),
            'verdict': concept.get('verdict'),
            'price': concept.get('price'),
            'margin_pct': concept.get('margin'),
            'ingredient_overlap_pct': concept.get('overlap'),
            'complexity': concept.get('complexity'),
            'markets': concept.get('markets'),
            'pilot': deepcopy(pilots.get(concept_id)),
        }
        for concept_id, concept in concepts.items()
    ]
    rows.sort(key=lambda row: int(row.get('score') or 0), reverse=True)

    return {
        'market_scan_run_number': int(workflow.get('market_scan_run_number', 0) or 0),
        'opportunities': rows,
    }


def get_decisions(brand_state: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(brand_state.get('decisions', {}))


def build_live_state_payload(
    brand_state: dict[str, Any],
    *,
    user_query: str = '',
    page_name: str = '',
    outlet_candidate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the controlled read-only state payload supplied to Vesper AI."""

    return {
        'schema_version': LIVE_STATE_SCHEMA_VERSION,
        'snapshot_scope': 'Current in-memory Vesper demo state for the authenticated brand',
        'current_page': page_name,
        'company_summary': get_company_summary(brand_state),
        'relevant_existing_outlets': get_outlet_performance(
            brand_state,
            user_query=user_query,
        ),
        'demand_inventory': get_inventory_risks(brand_state),
        'location_candidates': get_location_candidates(
            brand_state,
            outlet_candidate_state=outlet_candidate_state,
        ),
        'product_innovation': get_product_opportunities(brand_state),
        'decisions': get_decisions(brand_state),
        'replenishment_artifacts': get_replenishment_artifacts(brand_state),
        'artifact_counts': {
            'purchase_plans': len(get_purchase_plan(brand_state)),
            'transfer_plans': len(get_transfer_plan(brand_state)),
            'product_pilots': len(
                brand_state.get('artifacts', {}).get('product_pilots', [])
            ),
        },
    }


def build_live_state_context(
    brand_state: dict[str, Any],
    *,
    user_query: str = '',
    page_name: str = '',
    outlet_candidate_state: Mapping[str, Any] | None = None,
) -> str:
    payload = build_live_state_payload(
        brand_state,
        user_query=user_query,
        page_name=page_name,
        outlet_candidate_state=outlet_candidate_state,
    )
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
