from copy import deepcopy

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.data.product_innovation_catalog import build_product_concepts
from app.services.product_innovation_service import (
    ensure_product_innovation_state,
    get_product_concepts,
    refresh_market_scan,
    save_pilot_plan,
)
from app.state.demo_state import build_brand_state


def test_product_catalogs_are_brand_specific():
    india = build_product_concepts(INDIA_BRAND_ID)
    canada = build_product_concepts(CANADA_BRAND_ID)

    assert len(india) == 6
    assert len(canada) == 6
    assert india.keys() != canada.keys()
    assert any('₹' in concept['price'] for concept in india.values())
    assert all('C$' in concept['price'] for concept in canada.values())
    assert 'Maple Protein Cold Brew' in {c['name'] for c in canada.values()}
    assert 'High-Protein Chocolate Shake' in {c['name'] for c in india.values()}


def test_product_state_is_mutable_per_brand_not_module_global():
    india_state = build_brand_state(INDIA_BRAND_ID)
    canada_state = build_brand_state(CANADA_BRAND_ID)

    india_concepts = get_product_concepts(india_state)
    canada_concepts = get_product_concepts(canada_state)
    canada_before = deepcopy(canada_concepts)

    refresh_market_scan(india_state)

    assert canada_concepts == canada_before
    assert india_state['workflows']['product_innovation']['market_scan_run_number'] == 1
    assert canada_state['workflows']['product_innovation']['market_scan_run_number'] == 0


def test_market_scan_is_deterministic_for_fresh_brand_state():
    left = build_brand_state(CANADA_BRAND_ID)
    right = build_brand_state(CANADA_BRAND_ID)

    refresh_market_scan(left)
    refresh_market_scan(right)

    assert get_product_concepts(left) == get_product_concepts(right)


def test_canadian_pilot_persists_in_canonical_brand_state_only():
    canada_state = build_brand_state(CANADA_BRAND_ID)
    india_state = build_brand_state(INDIA_BRAND_ID)

    plan = save_pilot_plan(
        canada_state,
        concept_id='maple_protein_cold_brew',
        markets=['Toronto', 'Vancouver'],
        outlet_count=5,
        duration_weeks=4,
        test_price=7.45,
    )

    workflow = ensure_product_innovation_state(canada_state)
    assert plan['test_price'] == 7.45
    assert workflow['pilot_plans']['maple_protein_cold_brew']['markets'] == [
        'Toronto', 'Vancouver'
    ]
    assert canada_state['artifacts']['product_pilots'][0]['concept_name'] == (
        'Maple Protein Cold Brew'
    )
    assert ensure_product_innovation_state(india_state)['pilot_plans'] == {}
    assert india_state['artifacts']['product_pilots'] == []


def test_existing_step5_session_lazily_migrates_product_state():
    state = build_brand_state(CANADA_BRAND_ID)
    state['workflows']['product_innovation'] = {'market_scan_run_number': 3}

    workflow = ensure_product_innovation_state(state)

    assert workflow['market_scan_run_number'] == 3
    assert workflow['catalog_brand_id'] == CANADA_BRAND_ID
    assert len(workflow['concepts']) == 6
    assert workflow['pilot_plans'] == {}
