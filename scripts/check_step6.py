from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.product_innovation_service import (
    ensure_product_innovation_state,
    get_product_concepts,
    refresh_market_scan,
    save_pilot_plan,
)
from app.state.demo_state import build_brand_state


def show_brand(brand_id: str) -> None:
    state = build_brand_state(brand_id)
    workflow = ensure_product_innovation_state(state)
    concepts = get_product_concepts(state)
    profile = state['profile']

    print(profile['display_name'])
    print(f"  Currency: {profile['currency_code']} ({profile['currency_symbol']})")
    print(f"  Concepts: {len(concepts)}")
    for concept in concepts.values():
        print(
            f"  - {concept['name']} | {concept['price']} | "
            f"{concept['verdict']} | {', '.join(concept['markets'])}"
        )

    first_id = next(iter(concepts))
    before = concepts[first_id]['score'], concepts[first_id]['momentum']
    run = refresh_market_scan(state)
    after = concepts[first_id]['score'], concepts[first_id]['momentum']
    print(f'  Market scan {run}: {before} -> {after}')

    if brand_id == CANADA_BRAND_ID:
        plan = save_pilot_plan(
            state,
            concept_id='maple_protein_cold_brew',
            markets=['Toronto', 'Vancouver'],
            outlet_count=5,
            duration_weeks=4,
            test_price=7.45,
        )
        assert plan['test_price'] == 7.45
        assert len(state['artifacts']['product_pilots']) == 1
        print('  Canadian pilot persistence: PASS')

    print()


if __name__ == '__main__':
    show_brand(INDIA_BRAND_ID)
    show_brand(CANADA_BRAND_ID)
    print('STEP 6 CHECK: PASS')
