from __future__ import annotations

from pathlib import Path

from app.data.brand_catalog import get_brand_profile
from app.data.outlet_candidates import DEFAULT_CANDIDATES
from app.data.outlet_candidates_canada import CANADA_DEFAULT_CANDIDATES
from app.data.demo_document_loader import DEMO_DOCUMENT_ROOT
from app.services.outlet_document_analysis import OutletDocumentAnalysisService


def check_catalog(label: str, candidates: dict[str, dict]) -> int:
    count = 0
    for candidate_id, candidate in candidates.items():
        documents = candidate.get('documents') or []
        assert len(documents) == 3, (label, candidate_id, len(documents))
        for document in documents:
            content = document.get('content')
            assert isinstance(content, (bytes, bytearray)) and content
            assert len(content) == int(document.get('size_bytes') or 0)
            assert len(content) < 100_000
            path = DEMO_DOCUMENT_ROOT / str(document.get('demo_file') or '')
            assert path.is_file(), path
            assert path.read_bytes() == bytes(content)
            count += 1
    print(f'{label}: {len(candidates)} candidates · {count} downloadable documents · PASS')
    return count


def main() -> None:
    total = 0
    total += check_catalog('India', DEFAULT_CANDIDATES)
    total += check_catalog('Canada', CANADA_DEFAULT_CANDIDATES)
    assert total == 24

    service = OutletDocumentAnalysisService()
    canada_profile = get_brand_profile('maple_mason_canada')
    canada_prompt = service._candidate_prompt(
        CANADA_DEFAULT_CANDIDATES['toronto_eaton'],
        canada_profile,
    )
    assert 'Country: Canada' in canada_prompt
    assert 'Currency: CAD' in canada_prompt
    assert 'Province: Ontario' in canada_prompt
    assert 'Postal code: M5B 2H1' in canada_prompt
    assert 'C$13,800.00 / month' in canada_prompt

    india_profile = get_brand_profile('northstar_india')
    india_prompt = service._candidate_prompt(
        DEFAULT_CANDIDATES['noida'],
        india_profile,
    )
    assert 'Country: India' in india_prompt
    assert 'Currency: INR' in india_prompt
    assert 'State: Uttar Pradesh' in india_prompt
    assert 'PIN code: 201309' in india_prompt
    assert 'INR 3.25 lakh / month' in india_prompt

    print('Country-aware RAG prompt: PASS')
    print('DEMO DOCUMENT CHECK: PASS')


if __name__ == '__main__':
    main()
