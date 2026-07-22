from __future__ import annotations

from copy import deepcopy
from typing import Any


OUTLET_STATE_SCHEMA_VERSION = 2

SOURCE_CATALOG = {
    'team': (
        'Expansion team site notes',
        'Internal unstructured information',
        'Uploaded or entered by team',
    ),
    'broker': (
        'Broker quotation / lease proposal',
        'Internal uploaded document',
        'Uploaded by team',
    ),
    'documents': (
        'Candidate documents',
        'AI document extraction',
        'Latest candidate analysis',
    ),
    'places': (
        'Nearby business listings',
        'External competition intelligence',
        'Simulated demo snapshot',
    ),
    'osm': (
        'OpenStreetMap points of interest',
        'External location data',
        'Simulated demo snapshot',
    ),
    'mobility': (
        'Transit and mobility dataset',
        'External mobility data',
        'Simulated demo snapshot',
    ),
    'delivery': (
        'Delivery-demand heatmap',
        'External channel signal',
        'Simulated demo snapshot',
    ),
    'rent': (
        'Commercial rent benchmark',
        'External property estimate',
        'Simulated demo snapshot',
    ),
    'network': (
        'Existing outlet master',
        'Internal structured database',
        'Current mock snapshot',
    ),
}


def _demo_document(
    document_id: str,
    name: str,
    content_type: str,
    size_bytes: int,
    mock_extract: str,
) -> dict[str, Any]:
    """Create metadata for a preloaded demo document.

    The original binary is intentionally not embedded in source code. These
    records make every initial candidate look complete while the analysis
    panel remains explicit that the document content is simulated.
    """

    return {
        'id': document_id,
        'name': name,
        'content_type': content_type,
        'size_bytes': size_bytes,
        'content': None,
        'source': 'demo',
        'mock_extract': mock_extract,
        'analysis_status': 'Analyzed demo document',
    }


def _demo_analysis(
    *,
    summary: str,
    positive_signals: list[str],
    risks: list[str],
    lease_obligations: list[str],
    accessibility_notes: list[str],
    missing_information: list[str],
    follow_up_questions: list[str],
    evidence: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        'summary': summary,
        'positive_signals': positive_signals,
        'risks': risks,
        'lease_obligations': lease_obligations,
        'accessibility_notes': accessibility_notes,
        'missing_information': missing_information,
        'follow_up_questions': follow_up_questions,
        'evidence': evidence,
        'source_mode': 'demo',
        'warnings': [
            'The preloaded files are representative demo records; no original '
            'binary file was supplied with the prototype.',
        ],
    }


DEFAULT_CANDIDATES: dict[str, dict[str, Any]] = {
    'noida': {
        'id': 'noida',
        'name': 'Sector 62, Noida',
        'city': 'Noida',
        'state': 'Uttar Pradesh',
        'pincode': '201309',
        'lat': 28.6280,
        'lng': 77.3649,
        'address_provider': 'demo',
        'provider_place_id': 'DEMO-NOIDA-62',
        'address_confirmed': True,
        'status': 'Recommended',
        'address': (
            'Electronic City Metro corridor, Sector 62, Noida, '
            'Uttar Pradesh 201309'
        ),
        'rent': 3.25,
        'sqft': 680,
        'optional': {
            'Frontage': '24 ft.',
            'Floor': 'Ground floor',
            'Parking': 'Paid parking within 250 m',
        },
        'notes': (
            'Strong office crowd on weekdays and clear visibility from the '
            'metro exit. The site feels larger than required for a '
            'takeaway-led outlet. The landlord is open to a nine-year lease '
            'with a three-year lock-in, subject to final negotiation.'
        ),
        'documents': [
            _demo_document(
                'noida-broker',
                'Broker quotation.pdf',
                'application/pdf',
                348_200,
                'Quoted rent is ₹3.25 lakh per month. The proposal describes '
                'a three-year lock-in, annual escalation and a refundable '
                'security deposit.',
            ),
            _demo_document(
                'noida-notes',
                'Site visit notes.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                42_100,
                'The team observed heavy weekday office traffic, metro access '
                'and an oversized back-of-house area.',
            ),
            _demo_document(
                'noida-locality',
                'Locality observations.txt',
                'text/plain',
                6_320,
                'Evening delivery activity appears healthy. Weekend footfall '
                'is lower than weekday traffic.',
            ),
        ],
        'document_analysis': _demo_analysis(
            summary=(
                'The submitted material supports a weekday office-led outlet. '
                'The strongest concerns are footprint efficiency and the '
                'lease escalation terms.'
            ),
            positive_signals=[
                'Metro access and office density are repeatedly described.',
                'The landlord appears willing to negotiate layout and fit-out.',
            ],
            risks=[
                'The proposed footprint is larger than the likely operating format.',
                'Annual escalation and lock-in terms need financial review.',
            ],
            lease_obligations=[
                'Three-year lock-in is proposed.',
                'Security deposit and annual escalation require confirmation.',
            ],
            accessibility_notes=[
                'Visible from the metro approach.',
                'Paid parking is available within walking distance.',
            ],
            missing_information=[
                'Final common-area maintenance charge.',
                'Electrical load and exhaust permissions.',
            ],
            follow_up_questions=[
                'Can the leased area be reduced to approximately 400 sq. ft.?',
                'Will the landlord cap rent escalation during the lock-in?',
            ],
            evidence=[
                {
                    'document_name': 'Broker quotation.pdf',
                    'finding': 'Rent and initial lease obligations were stated.',
                    'confidence': 'high',
                },
                {
                    'document_name': 'Site visit notes.docx',
                    'finding': 'Office and metro demand generators were observed.',
                    'confidence': 'high',
                },
            ],
        ),
        'analysis_status': 'Analyzed',
        'analysis_mode': 'demo',
        'score': 84,
        'sales': 19.4,
        'margin': 21.0,
        'break_even': 17,
        'cannibalization': 'Low',
        'verdict': 'Proceed with conditions',
        'summary': (
            'Demand is attractive, but the footprint is oversized. Negotiate '
            'rent and reduce the operating format.'
        ),
        'format': 'Compact takeaway outlet · 350–425 sq. ft.',
        'signals': [
            (
                'Weekday office demand', 'High concentration', 'positive',
                '+11 points', 'osm',
                'Dense office and coworking locations are simulated within '
                'the trade area.',
            ),
            (
                'Metro access', '430 m walking distance', 'positive',
                '+8 points', 'mobility',
                'A major metro access point is modeled approximately 430 m away.',
            ),
            (
                'Delivery demand', '82 / 100', 'positive', '+7 points',
                'delivery',
                'The demo heatmap indicates strong evening delivery potential.',
            ),
            (
                'Direct competition', '2 outlets within 800 m', 'risk',
                '-6 points', 'places',
                'Two relevant beverage or dessert operators are represented '
                'in the simulated catchment.',
            ),
            (
                'Rent benchmark', '12% above local median', 'risk',
                '-5 points', 'rent',
                'The submitted rent is above the modeled local benchmark.',
            ),
            (
                'Document readiness', '3 sources reviewed', 'positive',
                '+5 points', 'documents',
                'Lease, site and locality information are available for review.',
            ),
        ],
    },
    'gurugram': {
        'id': 'gurugram',
        'name': 'Golf Course Road, Gurugram',
        'city': 'Gurugram',
        'state': 'Haryana',
        'pincode': '122011',
        'lat': 28.4446,
        'lng': 77.0996,
        'address_provider': 'demo',
        'provider_place_id': 'DEMO-GGM-54',
        'address_confirmed': True,
        'status': 'Review',
        'address': (
            'Golf Course Road commercial belt, Sector 54, Gurugram, '
            'Haryana 122011'
        ),
        'rent': 5.60,
        'sqft': 920,
        'optional': {
            'Frontage': '31 ft.',
            'Floor': 'Ground floor',
            'Parking': 'Valet available',
        },
        'notes': (
            'Premium catchment and excellent visibility. The broker is '
            'positioning the unit as a flagship, but rent, security deposit '
            'and fit-out obligations are aggressive. Evening demand is '
            'expected to be stronger than lunch demand.'
        ),
        'documents': [
            _demo_document(
                'gurugram-lease',
                'Commercial lease proposal.pdf',
                'application/pdf',
                521_400,
                'The proposal contains ₹5.60 lakh monthly rent, a six-month '
                'deposit, escalation and restrictions on external signage.',
            ),
            _demo_document(
                'gurugram-summary',
                'Broker discussion summary.txt',
                'text/plain',
                8_510,
                'The broker describes a premium mixed office and residential '
                'catchment with valet access.',
            ),
            _demo_document(
                'gurugram-site',
                'Flagship format assessment.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                51_300,
                'The expansion team recommends reducing customer seating and '
                'retaining a delivery pickup zone.',
            ),
        ],
        'document_analysis': _demo_analysis(
            summary=(
                'The documents support a premium catchment but indicate high '
                'fixed occupancy cost and restrictive lease terms.'
            ),
            positive_signals=[
                'Premium customer profile and strong visibility are consistent across notes.',
                'Valet and delivery pickup access improve convenience.',
            ],
            risks=[
                'Rent and security deposit materially increase capital exposure.',
                'Signage restrictions could weaken storefront impact.',
            ],
            lease_obligations=[
                'Six-month security deposit is proposed.',
                'External signage requires landlord approval.',
            ],
            accessibility_notes=[
                'Valet access is available.',
                'The road supports strong vehicle traffic but pedestrian access varies.',
            ],
            missing_information=[
                'Definitive common-area maintenance charges.',
                'Permitted operating hours for delivery pickup.',
            ],
            follow_up_questions=[
                'Can rent be linked to a revenue threshold during the launch period?',
                'Can the landlord relax external-signage restrictions?',
            ],
            evidence=[
                {
                    'document_name': 'Commercial lease proposal.pdf',
                    'finding': 'High deposit and signage controls were identified.',
                    'confidence': 'high',
                },
                {
                    'document_name': 'Flagship format assessment.docx',
                    'finding': 'The proposed footprint can be reduced operationally.',
                    'confidence': 'medium',
                },
            ],
        ),
        'analysis_status': 'Analyzed',
        'analysis_mode': 'demo',
        'score': 72,
        'sales': 26.8,
        'margin': 16.5,
        'break_even': 29,
        'cannibalization': 'Medium',
        'verdict': 'Review economics',
        'summary': (
            'Premium revenue potential is strong, but occupancy cost '
            'materially weakens returns.'
        ),
        'format': 'Premium compact café · 500–600 sq. ft.',
        'signals': [
            (
                'Premium customer fit', 'Very high', 'positive', '+13 points',
                'osm',
                'Premium residential, office and retail density is high in '
                'the simulated catchment.',
            ),
            (
                'Delivery demand', '88 / 100', 'positive', '+9 points',
                'delivery',
                'The demo model indicates strong evening delivery volume and '
                'average order value.',
            ),
            (
                'Brand visibility', 'Excellent', 'positive', '+7 points',
                'team',
                'The team reported high frontage visibility from the main corridor.',
            ),
            (
                'Rent benchmark', '19% above local median', 'risk',
                '-14 points', 'rent',
                'The quoted lease rate is materially above the modeled benchmark.',
            ),
            (
                'Competition', '5 dessert brands within 1.2 km', 'risk',
                '-8 points', 'places',
                'The simulated immediate trade area is highly competitive.',
            ),
            (
                'Document readiness', '3 sources reviewed', 'positive',
                '+4 points', 'documents',
                'Lease and format information are available, though key costs '
                'remain unresolved.',
            ),
        ],
    },
    'kolkata': {
        'id': 'kolkata',
        'name': 'Sector V, Salt Lake',
        'city': 'Kolkata',
        'state': 'West Bengal',
        'pincode': '700091',
        'lat': 22.5726,
        'lng': 88.4331,
        'address_provider': 'demo',
        'provider_place_id': 'DEMO-KOL-SV',
        'address_confirmed': True,
        'status': 'Recommended',
        'address': (
            'College More commercial cluster, Sector V, Salt Lake, '
            'Kolkata, West Bengal 700091'
        ),
        'rent': 2.45,
        'sqft': 520,
        'optional': {
            'Frontage': '18 ft.',
            'Floor': 'Ground floor',
            'Parking': 'Shared commercial parking',
        },
        'notes': (
            'Strong office cluster. Weekends are visibly quiet. The site may '
            'work best as a weekday-led compact store with corporate-order '
            'capability. The landlord has indicated a short fit-out period.'
        ),
        'documents': [
            _demo_document(
                'kolkata-visit',
                'Kolkata market visit notes.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                38_000,
                'Weekday office traffic is strong around lunch and evening. '
                'Saturday activity is significantly lower.',
            ),
            _demo_document(
                'kolkata-rent',
                'Broker rent proposal.pdf',
                'application/pdf',
                276_100,
                'Rent is ₹2.45 lakh per month with a relatively moderate '
                'deposit and a short rent-free fit-out period.',
            ),
            _demo_document(
                'kolkata-corporate',
                'Corporate order observations.txt',
                'text/plain',
                7_220,
                'Nearby offices may support preordered beverage and dessert '
                'bundles for meetings.',
            ),
        ],
        'document_analysis': _demo_analysis(
            summary=(
                'The records support a compact, weekday-led outlet with '
                'corporate-order capability and favorable occupancy cost.'
            ),
            positive_signals=[
                'Rent appears reasonable relative to the submitted site profile.',
                'Office demand is described consistently across team materials.',
            ],
            risks=[
                'Weekend traffic is substantially weaker.',
                'Corporate sales capability will be important to smooth demand.',
            ],
            lease_obligations=[
                'Fit-out period and deposit are stated but require final legal review.',
            ],
            accessibility_notes=[
                'Shared commercial parking is available.',
                'The site is located inside a major office cluster.',
            ],
            missing_information=[
                'Weekend delivery demand by hour.',
                'Permission for external pickup signage.',
            ],
            follow_up_questions=[
                'Can corporate preorder delivery be served from this unit?',
                'What is the expected Saturday operating schedule?',
            ],
            evidence=[
                {
                    'document_name': 'Kolkata market visit notes.docx',
                    'finding': 'Weekday and weekend demand patterns differ materially.',
                    'confidence': 'high',
                },
                {
                    'document_name': 'Broker rent proposal.pdf',
                    'finding': 'Occupancy cost is comparatively favorable.',
                    'confidence': 'high',
                },
            ],
        ),
        'analysis_status': 'Analyzed',
        'analysis_mode': 'demo',
        'score': 81,
        'sales': 16.8,
        'margin': 22.4,
        'break_even': 16,
        'cannibalization': 'Low',
        'verdict': 'Proceed with weekday-led format',
        'summary': (
            'Strong weekday economics and favorable rent support a compact outlet.'
        ),
        'format': 'Office-cluster takeaway outlet · 400–500 sq. ft.',
        'signals': [
            (
                'Office density', 'Very high', 'positive', '+12 points', 'osm',
                'A large office and technology-company concentration is '
                'represented within the simulated trade area.',
            ),
            (
                'Rent benchmark', '8% below local median', 'positive',
                '+9 points', 'rent',
                'The proposed rent is favorable relative to the demo benchmark.',
            ),
            (
                'Network overlap', 'Nearest outlet 9.4 km', 'positive',
                '+6 points', 'network',
                'The candidate has limited modeled overlap with the network.',
            ),
            (
                'Weekend activity', 'Low', 'risk', '-6 points', 'team',
                'The team observed low Saturday afternoon pedestrian activity.',
            ),
            (
                'Competition', '3 beverage outlets within 1 km', 'risk',
                '-4 points', 'places',
                'Three relevant operators are represented in the local demo data.',
            ),
            (
                'Document readiness', '3 sources reviewed', 'positive',
                '+5 points', 'documents',
                'Rent, site observations and corporate-order notes are available.',
            ),
        ],
    },
    'bengaluru': {
        'id': 'bengaluru',
        'name': 'Indiranagar 100 Feet Road',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'pincode': '560038',
        'lat': 12.9719,
        'lng': 77.6412,
        'address_provider': 'demo',
        'provider_place_id': 'DEMO-BLR-100FT',
        'address_confirmed': True,
        'status': 'High risk',
        'address': (
            '100 Feet Road retail corridor, Indiranagar, Bengaluru, '
            'Karnataka 560038'
        ),
        'rent': 6.80,
        'sqft': 740,
        'optional': {
            'Frontage': '22 ft.',
            'Floor': 'Ground floor',
            'Parking': 'Very limited',
        },
        'notes': (
            'Excellent brand visibility and youth traffic, but the street is '
            'saturated with cafés, dessert stores and beverage brands. Rent '
            'is aggressive, parking is poor and the landlord expects a long '
            'lock-in.'
        ),
        'documents': [
            _demo_document(
                'bengaluru-proposal',
                'Bengaluru broker proposal.pdf',
                'application/pdf',
                497_900,
                'The proposal quotes ₹6.80 lakh monthly rent, a long lock-in '
                'and substantial fit-out responsibility.',
            ),
            _demo_document(
                'bengaluru-competition',
                'Competitor walk-through notes.txt',
                'text/plain',
                12_400,
                'The team counted many direct café and dessert competitors '
                'within the immediate corridor.',
            ),
            _demo_document(
                'bengaluru-access',
                'Access and parking assessment.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                33_550,
                'Parking and delivery-rider waiting space are both constrained.',
            ),
        ],
        'document_analysis': _demo_analysis(
            summary=(
                'The records confirm strong visibility but also reinforce the '
                'high-rent, high-competition and access risks.'
            ),
            positive_signals=[
                'Youth traffic and brand visibility are consistently described as strong.',
            ],
            risks=[
                'High rent and long lock-in create downside exposure.',
                'Parking, rider staging and direct competition are material constraints.',
            ],
            lease_obligations=[
                'Long lock-in and substantial fit-out responsibility are proposed.',
            ],
            accessibility_notes=[
                'Pedestrian visibility is high.',
                'Parking and delivery-rider waiting space are limited.',
            ],
            missing_information=[
                'Landlord contribution to fit-out.',
                'Late-night loading and unloading permission.',
            ],
            follow_up_questions=[
                'Will the landlord reduce both rent and lock-in duration?',
                'Can a smaller test-store footprint be secured nearby?',
            ],
            evidence=[
                {
                    'document_name': 'Bengaluru broker proposal.pdf',
                    'finding': 'Rent and lease exposure are materially high.',
                    'confidence': 'high',
                },
                {
                    'document_name': 'Competitor walk-through notes.txt',
                    'finding': 'The immediate corridor is heavily saturated.',
                    'confidence': 'high',
                },
            ],
        ),
        'analysis_status': 'Analyzed',
        'analysis_mode': 'demo',
        'score': 61,
        'sales': 24.1,
        'margin': 11.8,
        'break_even': 38,
        'cannibalization': 'Medium',
        'verdict': 'Do not proceed at current terms',
        'summary': (
            'High demand is outweighed by rent, competition and capital requirements.'
        ),
        'format': 'Small-format test store only · 300–400 sq. ft.',
        'signals': [
            (
                'Target customer density', 'Exceptional', 'positive',
                '+15 points', 'osm',
                'Youth, dining and nightlife activity is extremely strong in '
                'the simulated catchment.',
            ),
            (
                'Brand visibility', 'Excellent', 'positive', '+8 points',
                'team',
                'The team identified strong frontage and high evening pedestrian activity.',
            ),
            (
                'Competition', '8 direct brands within 1 km', 'risk',
                '-16 points', 'places',
                'The modeled corridor contains a dense set of direct competitors.',
            ),
            (
                'Rent benchmark', '26% above local median', 'risk',
                '-17 points', 'rent',
                'The proposed lease rate is significantly above the demo benchmark.',
            ),
            (
                'Parking', 'Poor', 'risk', '-5 points', 'mobility',
                'Limited parking reduces convenience and rider staging capacity.',
            ),
            (
                'Document readiness', '3 sources reviewed', 'positive',
                '+3 points', 'documents',
                'The material is sufficiently detailed to expose the major risks.',
            ),
        ],
    },
}


def clone_default_candidates() -> dict[str, dict[str, Any]]:
    """Return an independent copy suitable for per-tab mutable demo state."""

    return deepcopy(DEFAULT_CANDIDATES)


def create_empty_candidate(candidate_id: str) -> dict[str, Any]:
    """Create a complete schema for a newly added candidate."""

    return {
        'id': candidate_id,
        'name': '',
        'city': '',
        'state': '',
        'pincode': '',
        'lat': None,
        'lng': None,
        'address_provider': 'manual',
        'provider_place_id': '',
        'address_confirmed': False,
        'status': 'Review',
        'address': '',
        'rent': 0.0,
        'sqft': 0,
        'optional': {
            'Frontage': '',
            'Floor': '',
            'Parking': '',
        },
        'notes': '',
        'documents': [],
        'document_analysis': None,
        'analysis_status': 'Not analyzed',
        'analysis_mode': 'none',
        'score': 0,
        'sales': 0.0,
        'margin': 0.0,
        'break_even': 0,
        'cannibalization': 'Unknown',
        'verdict': 'Analysis required',
        'summary': (
            'Save the candidate, then run Analyze to combine the structured '
            'inputs, documents and simulated market intelligence.'
        ),
        'format': 'To be determined',
        'signals': [],
    }
