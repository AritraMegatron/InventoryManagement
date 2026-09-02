from __future__ import annotations

from typing import Any

from app.data.demo_document_loader import load_demo_document


def _demo_document(
    document_id: str,
    name: str,
    content_type: str,
    size_bytes: int,
    mock_extract: str,
) -> dict[str, Any]:
    _ = size_bytes
    return load_demo_document(
        country_folder='canada',
        document_id=document_id,
        name=name,
        content_type=content_type,
        mock_extract=mock_extract,
    )


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
            'These are synthetic demo documents created for the Vesper presentation; '
            'all commercial and site details are fictional.',
        ],
    }


def _candidate(
    *,
    candidate_id: str,
    name: str,
    address: str,
    city: str,
    province: str,
    postal_code: str,
    lat: float,
    lng: float,
    rent: float,
    sqft: int,
    status: str,
    score: int,
    sales: float,
    margin: float,
    break_even: int,
    cannibalization: str,
    verdict: str,
    summary: str,
    format_name: str,
    notes: str,
    frontage: str,
    floor: str,
    parking: str,
    document_summary: str,
    risks: list[str],
    positives: list[str],
    signals: list[tuple[str, str, str, str, str, str]],
) -> dict[str, Any]:
    return {
        'id': candidate_id,
        'brand_id': 'maple_mason_canada',
        'name': name,
        'city': city,
        'state': province,
        'pincode': postal_code,
        'lat': lat,
        'lng': lng,
        'address_provider': 'demo-ca',
        'provider_place_id': f'DEMO-CA-{candidate_id.upper()}',
        'address_confirmed': True,
        'status': status,
        'address': address,
        # Canada demo values are stored in native CAD.
        'rent': rent,
        'sqft': sqft,
        'optional': {
            'Frontage': frontage,
            'Floor': floor,
            'Parking': parking,
        },
        'notes': notes,
        'documents': [
            _demo_document(
                f'{candidate_id}-broker',
                'Broker property brief.pdf',
                'application/pdf',
                296_000,
                f'The proposal quotes C${rent:,.0f} monthly base rent plus '
                'additional occupancy charges. Lease term, deposit and fit-out '
                'conditions are summarized for management review.',
            ),
            _demo_document(
                f'{candidate_id}-visit',
                'Site visit notes.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                39_800,
                notes,
            ),
            _demo_document(
                f'{candidate_id}-tradearea',
                'Trade area observations.txt',
                'text/plain',
                7_100,
                document_summary,
            ),
        ],
        'document_analysis': _demo_analysis(
            summary=document_summary,
            positive_signals=positives,
            risks=risks,
            lease_obligations=[
                'Confirm total occupancy cost including additional rent/CAM.',
                'Confirm deposit, renewal options and landlord work before approval.',
            ],
            accessibility_notes=[
                'Transit, pedestrian access and delivery staging were reviewed in the demo.',
                'Accessibility observations remain subject to physical due diligence.',
            ],
            missing_information=[
                'Final utilities and HVAC responsibility matrix.',
                'Confirmed food-service approvals and signage package.',
            ],
            follow_up_questions=[
                'What is the all-in occupancy cost after additional rent and recoveries?',
                'Can the landlord improve the fit-out or fixturing allowance?',
            ],
            evidence=[
                {
                    'document_name': 'Broker property brief.pdf',
                    'finding': 'Commercial terms and occupancy obligations were summarized.',
                    'confidence': 'high',
                },
                {
                    'document_name': 'Site visit notes.docx',
                    'finding': 'Demand generators and operating constraints were observed.',
                    'confidence': 'high',
                },
            ],
        ),
        'analysis_status': 'Analyzed',
        'analysis_mode': 'demo',
        'score': score,
        'sales': sales,
        'margin': margin,
        'break_even': break_even,
        'cannibalization': cannibalization,
        'verdict': verdict,
        'summary': summary,
        'format': format_name,
        'signals': signals,
    }


CANADA_DEFAULT_CANDIDATES: dict[str, dict[str, Any]] = {
    'toronto_eaton': _candidate(
        candidate_id='toronto_eaton',
        name='Yonge & Dundas, Toronto',
        address='220 Yonge Street, Toronto, Ontario M5B 2H1, Canada',
        city='Toronto',
        province='Ontario',
        postal_code='M5B 2H1',
        lat=43.6544,
        lng=-79.3807,
        rent=13_800.0,
        sqft=650,
        status='Recommended',
        score=86,
        sales=158_000.0,
        margin=20.8,
        break_even=18,
        cannibalization='Medium',
        verdict='Proceed with conditions',
        summary=(
            'High pedestrian and transit demand support a compact flagship-style '
            'café. Protect economics by capping the all-in occupancy package.'
        ),
        format_name='Compact high-throughput café · 500–650 sq. ft.',
        notes=(
            'Excellent all-day pedestrian traffic with strong office, student and '
            'tourist mix. Delivery access needs a tightly scheduled back-of-house '
            'process during peak downtown periods.'
        ),
        frontage='22 ft.',
        floor='Ground / concourse-connected',
        parking='Paid public parking nearby',
        document_summary=(
            'The location benefits from exceptional downtown demand and transit '
            'access. The primary diligence item is total occupancy cost.'
        ),
        positives=[
            'Strong all-day downtown pedestrian demand.',
            'Excellent subway and streetcar connectivity.',
        ],
        risks=[
            'High occupancy costs could compress contribution margin.',
            'Downtown delivery staging is constrained at peak periods.',
        ],
        signals=[
            ('Downtown demand', 'Exceptional', 'positive', '+14 points', 'osm',
             'The synthetic trade area models dense office, retail, student and tourist traffic.'),
            ('Transit access', 'Excellent', 'positive', '+9 points', 'mobility',
             'Multiple rapid-transit and surface-transit connections are represented nearby.'),
            ('Delivery demand', '88 / 100', 'positive', '+8 points', 'delivery',
             'The demo model indicates strong lunch and evening delivery potential.'),
            ('Competition', '6 direct brands nearby', 'risk', '-9 points', 'places',
             'The modeled downtown catchment contains a dense café and beverage set.'),
            ('Rent benchmark', 'Above local target', 'risk', '-7 points', 'rent',
             'The submitted rent is above the preferred occupancy-cost band for the prototype.'),
            ('Document readiness', '3 sources reviewed', 'positive', '+5 points', 'documents',
             'Broker, site-visit and trade-area information are available for review.'),
        ],
    ),
    'vancouver_pacific': _candidate(
        candidate_id='vancouver_pacific',
        name='Pacific Centre, Vancouver',
        address='701 West Georgia Street, Vancouver, British Columbia V7Y 1G5, Canada',
        city='Vancouver',
        province='British Columbia',
        postal_code='V7Y 1G5',
        lat=49.2832,
        lng=-123.1171,
        rent=15_400.0,
        sqft=720,
        status='Review',
        score=76,
        sales=151_000.0,
        margin=16.7,
        break_even=26,
        cannibalization='Low',
        verdict='Review economics and operating format',
        summary=(
            'Demand is attractive, but the proposed footprint and occupancy cost '
            'need to be tightened before the site reaches the target payback.'
        ),
        format_name='Compact café and takeaway · 500–600 sq. ft.',
        notes=(
            'Strong weekday office and shopping traffic with solid transit access. '
            'The proposed back-of-house area is larger than necessary for the '
            'beverage-led menu and could be reduced.'
        ),
        frontage='18 ft.',
        floor='Retail concourse',
        parking='Paid parkade in complex',
        document_summary=(
            'The site has strong downtown demand but requires a smaller footprint '
            'and clearer recovery charges to reach target economics.'
        ),
        positives=[
            'Strong downtown office and shopping demand.',
            'Direct access to major transit and pedestrian flows.',
        ],
        risks=[
            'Proposed footprint is larger than the target operating format.',
            'Occupancy recoveries need confirmation.',
        ],
        signals=[
            ('Office + retail demand', 'High', 'positive', '+11 points', 'osm',
             'The demo catchment combines dense employment and destination retail.'),
            ('Transit access', 'Excellent', 'positive', '+8 points', 'mobility',
             'Rapid-transit access is represented within the immediate catchment.'),
            ('Delivery demand', '79 / 100', 'positive', '+6 points', 'delivery',
             'The synthetic model indicates healthy delivery demand.'),
            ('Competition', '5 direct brands nearby', 'risk', '-8 points', 'places',
             'Downtown Vancouver is modeled as a competitive specialty-café market.'),
            ('Rent benchmark', 'High', 'risk', '-10 points', 'rent',
             'The current commercial proposal is above the preferred occupancy band.'),
            ('Document readiness', '3 sources reviewed', 'positive', '+5 points', 'documents',
             'Commercial and operating evidence is available for management review.'),
        ],
    ),
    'montreal_eaton': _candidate(
        candidate_id='montreal_eaton',
        name='Sainte-Catherine, Montréal',
        address='705 Rue Sainte-Catherine Ouest, Montréal, Québec H3B 4G5, Canada',
        city='Montréal',
        province='Québec',
        postal_code='H3B 4G5',
        lat=45.5037,
        lng=-73.5710,
        rent=11_200.0,
        sqft=610,
        status='Recommended',
        score=82,
        sales=137_000.0,
        margin=19.6,
        break_even=20,
        cannibalization='Low',
        verdict='Proceed with conditions',
        summary=(
            'Balanced occupancy economics and strong downtown footfall support '
            'further negotiation. Confirm bilingual signage and permitting details.'
        ),
        format_name='Compact café and takeaway · 450–600 sq. ft.',
        notes=(
            'Good mix of office, university, shopping and tourist traffic. '
            'A bilingual customer-facing operating package will be required for '
            'signage, menu content and local launch material.'
        ),
        frontage='20 ft.',
        floor='Street / mall-connected',
        parking='Paid public parking nearby',
        document_summary=(
            'The site combines healthy downtown demand with more balanced rent '
            'than the Toronto and Vancouver candidates.'
        ),
        positives=[
            'Strong mixed downtown demand throughout the week.',
            'Rent-to-sales outlook is within the prototype target band.',
        ],
        risks=[
            'Local language/signage requirements need operational planning.',
            'Seasonal winter access patterns should be validated.',
        ],
        signals=[
            ('Mixed downtown demand', 'High', 'positive', '+12 points', 'osm',
             'The synthetic catchment combines employment, university, retail and tourism.'),
            ('Transit access', 'Strong', 'positive', '+8 points', 'mobility',
             'Metro and underground-city access are represented in the demo.'),
            ('Delivery demand', '75 / 100', 'positive', '+5 points', 'delivery',
             'The modeled delivery channel is healthy but not the primary demand source.'),
            ('Competition', '4 direct brands nearby', 'risk', '-6 points', 'places',
             'A competitive café set is represented in the downtown catchment.'),
            ('Rent benchmark', 'Within target band', 'positive', '+7 points', 'rent',
             'The proposed rent is within the prototype target occupancy band.'),
            ('Document readiness', '3 sources reviewed', 'positive', '+5 points', 'documents',
             'Commercial, site and trade-area evidence is available.'),
        ],
    ),
    'calgary_chinook': _candidate(
        candidate_id='calgary_chinook',
        name='Chinook Centre, Calgary',
        address='6455 Macleod Trail SW, Calgary, Alberta T2H 0K8, Canada',
        city='Calgary',
        province='Alberta',
        postal_code='T2H 0K8',
        lat=50.9985,
        lng=-114.0744,
        rent=9_400.0,
        sqft=780,
        status='Review',
        score=71,
        sales=118_000.0,
        margin=15.8,
        break_even=30,
        cannibalization='Low',
        verdict='Review economics and operating format',
        summary=(
            'Occupancy cost is manageable, but the proposed area is oversized '
            'relative to the forecast. Test a smaller kiosk/café format.'
        ),
        format_name='Reduce to kiosk / compact café · 400–550 sq. ft.',
        notes=(
            'Strong destination retail traffic and easy vehicle access. Weekday '
            'morning demand is softer than downtown locations, so the current '
            '780 sq. ft. proposal creates unnecessary fixed-cost exposure.'
        ),
        frontage='26 ft.',
        floor='Main retail level',
        parking='Large on-site parking field',
        document_summary=(
            'The location has good destination traffic and parking, but the '
            'proposed footprint is too large for the modeled sales base.'
        ),
        positives=[
            'Strong destination retail traffic and vehicle access.',
            'Lower rent than the larger downtown candidates.',
        ],
        risks=[
            'Proposed area is oversized for forecast demand.',
            'Morning commuter demand is weaker than downtown alternatives.',
        ],
        signals=[
            ('Destination demand', 'High', 'positive', '+9 points', 'osm',
             'The synthetic catchment models strong shopping and weekend visitation.'),
            ('Parking access', 'Excellent', 'positive', '+7 points', 'mobility',
             'The location is modeled with strong vehicle access and parking supply.'),
            ('Delivery demand', '68 / 100', 'risk', '-2 points', 'delivery',
             'Delivery demand is modeled as moderate rather than exceptional.'),
            ('Competition', '3 direct brands nearby', 'positive', '+3 points', 'places',
             'The direct specialty-café competitive set is moderate in the demo.'),
            ('Rent benchmark', 'Favorable', 'positive', '+8 points', 'rent',
             'Rent is favorable relative to the Canadian demo benchmark.'),
            ('Footprint', '780 sq. ft.', 'risk', '-9 points', 'team',
             'The proposed area is larger than the preferred Maple & Mason format.'),
        ],
    ),
}
