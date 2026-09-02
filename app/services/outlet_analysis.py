from __future__ import annotations

import hashlib
import math
from copy import deepcopy
from typing import Any

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.data.outlet_candidates import get_default_candidates
from app.services.currency_service import format_money


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _stable_fraction(*parts: object) -> float:
    text = '|'.join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    integer = int.from_bytes(digest[:8], 'big')
    return integer / float((1 << 64) - 1)


def _document_names(candidate: dict[str, Any]) -> list[str]:
    return sorted(
        str(document.get('name', '')).strip()
        for document in candidate.get('documents', [])
        if isinstance(document, dict) and document.get('name')
    )


def _brand_id(candidate: dict[str, Any], profile: dict[str, Any] | None) -> str:
    if profile and profile.get('brand_id'):
        return str(profile['brand_id'])
    return str(candidate.get('brand_id') or INDIA_BRAND_ID)


def _matches_default(
    candidate: dict[str, Any],
    brand_id: str,
) -> bool:
    candidate_id = str(candidate.get('id', ''))
    original = get_default_candidates(brand_id).get(candidate_id)
    if original is None:
        return False

    return all(
        (
            candidate.get('address') == original.get('address'),
            float(candidate.get('rent') or 0) == float(original.get('rent') or 0),
            int(candidate.get('sqft') or 0) == int(original.get('sqft') or 0),
            candidate.get('notes') == original.get('notes'),
            candidate.get('optional') == original.get('optional'),
            _document_names(candidate) == _document_names(original),
        )
    )


def _restore_default_outputs(
    candidate: dict[str, Any],
    brand_id: str,
) -> dict[str, Any]:
    original = get_default_candidates(brand_id)[str(candidate['id'])]
    for key in (
        'status',
        'score',
        'sales',
        'margin',
        'break_even',
        'cannibalization',
        'verdict',
        'summary',
        'format',
        'signals',
    ):
        candidate[key] = deepcopy(original[key])
    candidate['analysis_status'] = 'Analyzed'
    candidate['brand_id'] = brand_id
    return candidate


def _calculate_canada_economics(
    *,
    candidate: dict[str, Any],
    demand_index: int,
    seed_two: float,
    sqft: int,
    rent: float,
) -> tuple[float, float, int, float, int]:
    """Return sales, margin, break-even, rent/sqft, and rent benchmark delta.

    Canadian candidate monetary values are stored in native CAD. This model is
    intentionally deterministic demo logic, not live commercial underwriting.
    """

    rent_per_sqft = rent / sqft
    area_factor = _clamp(sqft / 600, 0.62, 1.40)
    monthly_sales = (
        72_000
        + (demand_index - 60) * 2_250
        + 34_000 * area_factor
        + (seed_two - 0.5) * 18_000
    )
    monthly_sales = round(_clamp(monthly_sales, 70_000, 220_000), 0)

    rent_to_sales = rent / monthly_sales
    margin = (
        29.5
        - rent_to_sales * 78
        - max(0.0, sqft - 680) / 42
        + (demand_index - 75) * 0.09
    )
    margin = round(_clamp(margin, 8.5, 25.0), 1)

    monthly_contribution = max(4_500.0, monthly_sales * margin / 100)
    setup_cost = 120_000 + sqft * 145 + rent * 1.8
    break_even = int(round(_clamp(setup_cost / monthly_contribution, 12, 42)))

    benchmark = 18.0
    rent_difference = int(round((rent_per_sqft - benchmark) / benchmark * 100))
    return monthly_sales, margin, break_even, rent_per_sqft, rent_difference


def _calculate_india_economics(
    *,
    candidate: dict[str, Any],
    demand_index: int,
    seed_two: float,
    sqft: int,
    rent_lakh: float,
) -> tuple[float, float, int, float, int]:
    """Preserve the established India MVP economics in lakh INR units."""

    rent_per_sqft = rent_lakh * 100_000 / sqft
    area_factor = _clamp(sqft / 520, 0.62, 1.45)
    monthly_sales = (
        10.2
        + (demand_index - 60) * 0.28
        + 6.1 * area_factor
        + (seed_two - 0.5) * 2.2
    )
    monthly_sales = round(_clamp(monthly_sales, 8.5, 31.5), 1)

    rent_to_sales = rent_lakh / monthly_sales
    margin = (
        29.0
        - rent_to_sales * 57
        - max(0.0, sqft - 650) / 140
        + (demand_index - 75) * 0.08
    )
    margin = round(_clamp(margin, 8.5, 25.0), 1)

    monthly_contribution = max(0.45, monthly_sales * margin / 100)
    setup_cost = 26 + sqft * 0.031 + rent_lakh * 2.4
    break_even = int(round(_clamp(setup_cost / monthly_contribution, 12, 42)))

    rent_difference = int(round((rent_per_sqft - 620) / 620 * 100))
    return monthly_sales, margin, break_even, rent_per_sqft, rent_difference


def calculate_location_analysis(
    candidate: dict[str, Any],
    all_candidates: dict[str, dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate deterministic prototype economics and explainable signals.

    Critical numbers are calculated in code. The Vesper RAG Engine remains
    limited to qualitative extraction, contradiction detection and narrative.
    """

    brand_id = _brand_id(candidate, profile)
    candidate['brand_id'] = brand_id
    if _matches_default(candidate, brand_id):
        return _restore_default_outputs(candidate, brand_id)

    is_canada = brand_id == CANADA_BRAND_ID
    rent = max(0.01, float(candidate.get('rent') or 0.0))
    sqft = max(1, int(candidate.get('sqft') or 0))
    address = str(candidate.get('address') or '').strip()
    notes = str(candidate.get('notes') or '').strip()
    documents = [
        document
        for document in candidate.get('documents', [])
        if isinstance(document, dict)
    ]
    document_analysis = candidate.get('document_analysis') or {}

    seed = _stable_fraction(address.lower(), round(rent, 2), sqft, len(documents))
    seed_two = _stable_fraction(
        candidate.get('city', ''),
        candidate.get('state', ''),
        notes[:160],
    )
    demand_index = round(62 + seed * 29)

    if is_canada:
        if rent / sqft <= 14:
            rent_score = 10.0
        elif rent / sqft <= 20:
            rent_score = 7.0
        elif rent / sqft <= 28:
            rent_score = 2.0
        else:
            rent_score = -8.0
        monthly_sales, margin, break_even, rent_per_sqft, rent_difference = (
            _calculate_canada_economics(
                candidate=candidate,
                demand_index=demand_index,
                seed_two=seed_two,
                sqft=sqft,
                rent=rent,
            )
        )
        ideal_sqft = 600.0
        footprint_divisor = 70.0
    else:
        rent_per_sqft = rent * 100_000 / sqft
        if rent_per_sqft <= 420:
            rent_score = 10.0
        elif rent_per_sqft <= 650:
            rent_score = 7.0
        elif rent_per_sqft <= 900:
            rent_score = 2.0
        else:
            rent_score = -8.0
        monthly_sales, margin, break_even, rent_per_sqft, rent_difference = (
            _calculate_india_economics(
                candidate=candidate,
                demand_index=demand_index,
                seed_two=seed_two,
                sqft=sqft,
                rent_lakh=rent,
            )
        )
        ideal_sqft = 480.0
        footprint_divisor = 55.0

    footprint_gap = abs(sqft - ideal_sqft)
    footprint_score = _clamp(10 - footprint_gap / footprint_divisor, -6, 10)

    evidence_score = min(8.0, len(documents) * 1.5)
    if len(notes) >= 80:
        evidence_score += 2.0
    if document_analysis:
        evidence_score += 2.0
    evidence_score = min(11.0, evidence_score)

    address_score = 5.0 if candidate.get('address_confirmed') else 1.0
    base_score = (
        38
        + (demand_index - 60) * 0.72
        + rent_score
        + footprint_score
        + evidence_score
        + address_score
    )
    score = int(round(_clamp(base_score, 45, 93)))

    nearby = 0
    lat = candidate.get('lat')
    lng = candidate.get('lng')
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        for other_id, other in all_candidates.items():
            if other_id == candidate.get('id'):
                continue
            other_lat = other.get('lat')
            other_lng = other.get('lng')
            if not isinstance(other_lat, (int, float)) or not isinstance(
                other_lng, (int, float)
            ):
                continue
            lat_km = (float(lat) - float(other_lat)) * 111
            lng_km = (
                (float(lng) - float(other_lng))
                * 111
                * math.cos(math.radians(float(lat)))
            )
            if math.hypot(lat_km, lng_km) <= 7.5:
                nearby += 1

    if nearby >= 2:
        cannibalization = 'High'
    elif nearby == 1 or seed_two > 0.72:
        cannibalization = 'Medium'
    else:
        cannibalization = 'Low'

    if score >= 80 and margin >= 17.5 and break_even <= 24:
        status = 'Recommended'
        verdict = 'Proceed with conditions'
    elif score >= 67 and margin >= 13.0 and break_even <= 34:
        status = 'Review'
        verdict = 'Review economics and operating format'
    else:
        status = 'High risk'
        verdict = 'Do not proceed at current terms'

    if is_canada:
        if sqft <= 450:
            recommended_format = 'Lean takeaway café · 350–450 sq. ft.'
        elif sqft <= 680:
            recommended_format = 'Compact café and takeaway · 450–650 sq. ft.'
        else:
            recommended_format = 'Reduce to compact café · 500–650 sq. ft.'
    else:
        if sqft <= 425:
            recommended_format = 'Lean takeaway outlet · 300–400 sq. ft.'
        elif sqft <= 650:
            recommended_format = 'Compact café and takeaway · 400–550 sq. ft.'
        else:
            recommended_format = 'Reduce to a compact format · 450–600 sq. ft.'

    if status == 'Recommended':
        summary = (
            'The modeled demand and occupancy economics support further '
            'negotiation. Confirm the remaining document gaps before approval.'
        )
    elif status == 'Review':
        summary = (
            'The opportunity is plausible, but rent, footprint or evidence '
            'quality requires management review before investment.'
        )
    else:
        summary = (
            'The current rent, footprint and modeled economics create too much '
            'downside. Renegotiate materially or test a smaller format.'
        )

    competition_count = 1 + int(seed * 7)
    delivery_index = int(round(60 + seed_two * 33))
    rent_tone = 'positive' if rent_difference <= 0 else 'risk'
    rent_points = (
        f'+{min(9, max(3, abs(rent_difference) // 2))} points'
        if rent_tone == 'positive'
        else f'-{min(15, max(4, abs(rent_difference) // 2))} points'
    )
    doc_tone = 'positive' if len(documents) >= 2 else 'risk'
    doc_points = '+6 points' if doc_tone == 'positive' else '-5 points'

    if is_canada:
        rent_evidence = (
            f'The submitted rent equals approximately C${rent_per_sqft:,.2f} '
            'per sq. ft. per month in the prototype calculation.'
        )
    else:
        rent_evidence = (
            f'The submitted rent equals approximately ₹{rent_per_sqft:,.0f} '
            'per sq. ft. per month in the prototype calculation.'
        )

    candidate.update(
        {
            'status': status,
            'score': score,
            'sales': monthly_sales,
            'margin': margin,
            'break_even': break_even,
            'cannibalization': cannibalization,
            'verdict': verdict,
            'summary': summary,
            'format': recommended_format,
            'analysis_status': 'Analyzed',
            'signals': [
                (
                    'Modeled local demand',
                    f'{demand_index} / 100',
                    'positive' if demand_index >= 75 else 'risk',
                    '+10 points' if demand_index >= 75 else '-4 points',
                    'delivery',
                    'A deterministic prototype demand index was generated from '
                    'the candidate profile. It is not live market research.',
                ),
                (
                    'Delivery potential',
                    f'{delivery_index} / 100',
                    'positive' if delivery_index >= 72 else 'risk',
                    '+7 points' if delivery_index >= 72 else '-3 points',
                    'delivery',
                    'The demo model estimates delivery-channel suitability for '
                    'the selected catchment.',
                ),
                (
                    'Rent efficiency',
                    (
                        f'{abs(rent_difference)}% below benchmark'
                        if rent_difference <= 0
                        else f'{rent_difference}% above benchmark'
                    ),
                    rent_tone,
                    rent_points,
                    'rent',
                    rent_evidence,
                ),
                (
                    'Footprint efficiency',
                    f'{sqft:,} sq. ft.',
                    'positive' if 325 <= sqft <= 680 else 'risk',
                    '+6 points' if 325 <= sqft <= 680 else '-6 points',
                    'team',
                    'The submitted area is compared with the compact operating '
                    'formats used by this demo.',
                ),
                (
                    'Direct competition',
                    f'{competition_count} modeled competitors',
                    'positive' if competition_count <= 3 else 'risk',
                    '+4 points' if competition_count <= 3 else '-8 points',
                    'places',
                    'Competitor count is simulated until a live POI data source '
                    'is connected.',
                ),
                (
                    'Document readiness',
                    f'{len(documents)} document(s) · notes '
                    f'{"available" if notes else "missing"}',
                    doc_tone,
                    doc_points,
                    'documents',
                    'Uploaded files and typed site information are used for '
                    'qualitative evidence extraction.',
                ),
            ],
        }
    )
    return candidate
