from __future__ import annotations

from copy import deepcopy
import random
from typing import Any

from app.data.product_innovation_catalog import build_product_concepts


PRODUCT_STATE_VERSION = 1


def _stable_seed(text: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(text))


def ensure_product_innovation_state(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Return a brand-isolated mutable Product Innovation workflow.

    The initializer is deliberately lazy so an existing browser session created
    by Steps 1-5 migrates cleanly without requiring users to clear NiceGUI
    storage after this patch.
    """

    workflow = brand_state.setdefault('workflows', {}).setdefault(
        'product_innovation', {}
    )
    brand_id = str(brand_state['brand_id'])

    if (
        workflow.get('state_version') != PRODUCT_STATE_VERSION
        or workflow.get('catalog_brand_id') != brand_id
        or not isinstance(workflow.get('concepts'), dict)
    ):
        existing_run_number = int(workflow.get('market_scan_run_number', 0) or 0)
        workflow.clear()
        workflow.update(
            {
                'state_version': PRODUCT_STATE_VERSION,
                'catalog_brand_id': brand_id,
                'market_scan_run_number': existing_run_number,
                'concepts': build_product_concepts(brand_id),
                'pilot_plans': {},
            }
        )

    workflow.setdefault('pilot_plans', {})
    return workflow


def get_product_concepts(brand_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return ensure_product_innovation_state(brand_state)['concepts']


def get_pilot_plans(brand_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return ensure_product_innovation_state(brand_state)['pilot_plans']


def build_product_rows(
    concepts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            'concept_id': concept_id,
            'name': concept['name'],
            'category': concept['category'],
            'score': int(concept['score']),
            'momentum': int(concept['momentum']),
            'overlap_text': f"{concept['overlap']}%",
            'margin_text': f"{concept['margin']}%",
            'complexity': concept['complexity'],
            'verdict': concept['verdict'],
        }
        for concept_id, concept in concepts.items()
    ]


def refresh_market_scan(brand_state: dict[str, Any]) -> int:
    """Advance and apply one deterministic tenant-specific market scan."""

    workflow = ensure_product_innovation_state(brand_state)
    workflow['market_scan_run_number'] = int(
        workflow.get('market_scan_run_number', 0)
    ) + 1
    run_number = int(workflow['market_scan_run_number'])
    concepts = workflow['concepts']
    brand_seed = _stable_seed(str(brand_state['brand_id']))

    for concept_id, concept in concepts.items():
        rng = random.Random(
            brand_seed
            + _stable_seed(concept_id)
            + run_number * 733
        )
        concept['momentum'] = max(
            45,
            min(98, int(concept['momentum']) + rng.randint(-4, 5)),
        )
        concept['score'] = max(
            50,
            min(95, int(concept['score']) + rng.randint(-2, 3)),
        )

    return run_number


def save_pilot_plan(
    brand_state: dict[str, Any],
    *,
    concept_id: str,
    markets: list[str],
    outlet_count: int,
    duration_weeks: int,
    test_price: float,
) -> dict[str, Any]:
    """Persist a synthetic pilot in canonical per-brand demo state."""

    workflow = ensure_product_innovation_state(brand_state)
    concepts = workflow['concepts']
    if concept_id not in concepts:
        raise KeyError(f'Unknown product concept: {concept_id}')

    plan = {
        'concept_id': concept_id,
        'concept_name': concepts[concept_id]['name'],
        'markets': list(markets),
        'outlet_count': int(outlet_count),
        'duration_weeks': int(duration_weeks),
        'test_price': float(test_price),
        'status': 'Planned',
    }
    workflow['pilot_plans'][concept_id] = deepcopy(plan)

    artifacts = brand_state.setdefault('artifacts', {}).setdefault(
        'product_pilots', []
    )
    # One current demo plan per concept. Re-planning replaces the old artifact.
    artifacts[:] = [
        item for item in artifacts
        if item.get('concept_id') != concept_id
    ]
    artifacts.append(deepcopy(plan))
    return plan


def reset_product_innovation_state(brand_state: dict[str, Any]) -> dict[str, Any]:
    """Reset only this brand's Product Innovation workflow to baseline."""

    workflow = brand_state.setdefault('workflows', {}).setdefault(
        'product_innovation', {}
    )
    workflow.clear()
    workflow.update(
        {
            'state_version': PRODUCT_STATE_VERSION,
            'catalog_brand_id': brand_state['brand_id'],
            'market_scan_run_number': 0,
            'concepts': build_product_concepts(str(brand_state['brand_id'])),
            'pilot_plans': {},
        }
    )
    brand_state.setdefault('artifacts', {})['product_pilots'] = []
    return workflow
