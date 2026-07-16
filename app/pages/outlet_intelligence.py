from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS

from app.theme import BURGUNDY, GOLD, GREEN, MUTED, RED, apply_theme


SOURCE_CATALOG = {
    'team': ('Expansion team site notes', 'Internal unstructured document', 'Uploaded by team'),
    'broker': ('Broker quotation / lease proposal', 'Internal uploaded document', 'Uploaded by team'),
    'places': ('Nearby business listings', 'External competition intelligence', 'Mock refresh: today'),
    'osm': ('OpenStreetMap points of interest', 'External location data', 'Mock refresh: today'),
    'mobility': ('Transit and mobility dataset', 'External mobility data', 'Mock refresh: today'),
    'delivery': ('Delivery-demand heatmap', 'External channel signal', 'Mock refresh: today'),
    'rent': ('Commercial rent benchmark', 'External property estimate', 'Mock refresh: today'),
    'network': ('Existing outlet master', 'Internal structured database', 'Current mock snapshot'),
}


CANDIDATES: dict[str, dict[str, Any]] = {
    'noida': {
        'name': 'Sector 62, Noida',
        'city': 'Noida, Uttar Pradesh',
        'lat': 28.6280,
        'lng': 77.3649,
        'status': 'Recommended',
        'address': 'Electronic City Metro corridor, Sector 62, Noida, Uttar Pradesh',
        'rent': 3.25,
        'sqft': 680,
        'optional': {'Frontage': '24 ft.', 'Floor': 'Ground floor', 'Parking': 'Paid parking within 250 m'},
        'notes': (
            'Strong office crowd on weekdays and visible from the metro exit. '
            'The site feels larger than required for a takeaway-led outlet.'
        ),
        'documents': ['Broker quotation.pdf', 'Site visit notes.docx', '12 storefront photographs'],
        'score': 84,
        'sales': 19.4,
        'margin': 21.0,
        'break_even': 17,
        'cannibalization': 'Low',
        'verdict': 'Proceed with conditions',
        'summary': 'Demand is attractive, but the footprint is oversized. Negotiate rent and reduce the format.',
        'format': 'Compact takeaway outlet · 350–425 sq. ft.',
        'signals': [
            ('Weekday office demand', 'High concentration', 'positive', '+11 points', 'osm', 'Dense office and coworking locations within the trade area.'),
            ('Metro access', '430 m walking distance', 'positive', '+8 points', 'mobility', 'A major metro access point is approximately 430 m away.'),
            ('Delivery demand', '82 / 100', 'positive', '+7 points', 'delivery', 'Strong evening delivery demand is expected in the local catchment.'),
            ('Direct competition', '2 outlets within 800 m', 'risk', '-6 points', 'places', 'Two relevant beverage or dessert operators were identified nearby.'),
            ('Rent benchmark', '12% above local median', 'risk', '-5 points', 'rent', 'The submitted rent is above the modeled local benchmark.'),
            ('Network overlap', 'Nearest outlet 6.8 km', 'positive', '+5 points', 'network', 'The location has limited overlap with the current outlet network.'),
        ],
    },
    'gurugram': {
        'name': 'Golf Course Road, Gurugram',
        'city': 'Gurugram, Haryana',
        'lat': 28.4446,
        'lng': 77.0996,
        'status': 'Review',
        'address': 'Golf Course Road commercial belt, Sector 54, Gurugram, Haryana',
        'rent': 5.60,
        'sqft': 920,
        'optional': {'Frontage': '31 ft.', 'Floor': 'Ground floor', 'Parking': 'Valet available'},
        'notes': (
            'Premium catchment and excellent visibility. The broker is positioning it as a flagship, '
            'but rent and security deposit are aggressive.'
        ),
        'documents': ['Commercial lease proposal.pdf', 'Broker WhatsApp summary.txt'],
        'score': 72,
        'sales': 26.8,
        'margin': 16.5,
        'break_even': 29,
        'cannibalization': 'Medium',
        'verdict': 'Review economics',
        'summary': 'Premium revenue potential is strong, but occupancy cost materially weakens returns.',
        'format': 'Premium compact café · 500–600 sq. ft.',
        'signals': [
            ('Premium customer fit', 'Very high', 'positive', '+13 points', 'osm', 'Premium residential, office and retail density is high.'),
            ('Delivery demand', '88 / 100', 'positive', '+9 points', 'delivery', 'The area supports strong evening delivery volume and order value.'),
            ('Brand visibility', 'Excellent', 'positive', '+7 points', 'team', 'The team reported high frontage visibility from the main corridor.'),
            ('Rent benchmark', '19% above local median', 'risk', '-14 points', 'rent', 'The quoted lease rate is materially above the modeled benchmark.'),
            ('Competition', '5 dessert brands within 1.2 km', 'risk', '-8 points', 'places', 'The immediate trade area is highly competitive.'),
            ('Network overlap', 'Nearest outlet 3.1 km', 'risk', '-7 points', 'network', 'Delivery-radius overlap with an existing outlet is meaningful.'),
        ],
    },
    'kolkata': {
        'name': 'Sector V, Salt Lake',
        'city': 'Kolkata, West Bengal',
        'lat': 22.5726,
        'lng': 88.4331,
        'status': 'Recommended',
        'address': 'College More commercial cluster, Sector V, Salt Lake, Kolkata',
        'rent': 2.45,
        'sqft': 520,
        'optional': {'Frontage': '18 ft.', 'Floor': 'Ground floor', 'Parking': 'Shared commercial parking'},
        'notes': (
            'Strong office cluster. Weekends are visibly quiet. The site may work best as a '
            'weekday-led compact store with corporate-order capability.'
        ),
        'documents': ['Kolkata market visit notes.docx', 'Broker rent sheet.xlsx'],
        'score': 81,
        'sales': 16.8,
        'margin': 22.4,
        'break_even': 16,
        'cannibalization': 'Low',
        'verdict': 'Proceed with weekday-led format',
        'summary': 'Strong weekday economics and favorable rent support a compact outlet.',
        'format': 'Office-cluster takeaway outlet · 400–500 sq. ft.',
        'signals': [
            ('Office density', 'Very high', 'positive', '+12 points', 'osm', 'A large office and technology-company concentration exists within 2 km.'),
            ('Rent benchmark', '8% below local median', 'positive', '+9 points', 'rent', 'The proposed rent is favorable relative to local commercial benchmarks.'),
            ('Cannibalization', 'Nearest outlet 9.4 km', 'positive', '+6 points', 'network', 'The candidate has limited overlap with the existing network.'),
            ('Weekend activity', 'Low', 'risk', '-6 points', 'team', 'The team observed low Saturday afternoon pedestrian activity.'),
            ('Competition', '3 beverage outlets within 1 km', 'risk', '-4 points', 'places', 'Three relevant operators compete in the local trade area.'),
            ('Delivery demand', '75 / 100', 'positive', '+5 points', 'delivery', 'Delivery demand is healthy but concentrated on weekdays.'),
        ],
    },
    'bengaluru': {
        'name': 'Indiranagar 100 Feet Road',
        'city': 'Bengaluru, Karnataka',
        'lat': 12.9719,
        'lng': 77.6412,
        'status': 'High risk',
        'address': '100 Feet Road retail corridor, Indiranagar, Bengaluru, Karnataka',
        'rent': 6.80,
        'sqft': 740,
        'optional': {'Frontage': '22 ft.', 'Floor': 'Ground floor', 'Parking': 'Very limited'},
        'notes': (
            'Excellent brand visibility and youth traffic, but the street is saturated with cafés, '
            'dessert stores and beverage brands. Rent is aggressive.'
        ),
        'documents': ['Bengaluru broker proposal.pdf', 'Competitor walk-through notes.txt'],
        'score': 61,
        'sales': 24.1,
        'margin': 11.8,
        'break_even': 38,
        'cannibalization': 'Medium',
        'verdict': 'Do not proceed at current terms',
        'summary': 'High demand is outweighed by rent, competition and capital requirements.',
        'format': 'Small-format test store only · 300–400 sq. ft.',
        'signals': [
            ('Target customer density', 'Exceptional', 'positive', '+15 points', 'osm', 'Youth, dining and nightlife activity is extremely strong.'),
            ('Brand visibility', 'Excellent', 'positive', '+8 points', 'team', 'The team identified strong frontage and high evening pedestrian activity.'),
            ('Competition', '9 brands within 1 km', 'risk', '-15 points', 'places', 'Nine relevant dessert or beverage concepts operate nearby.'),
            ('Rent benchmark', '26% above local median', 'risk', '-17 points', 'rent', 'The proposed lease rate is significantly above the modeled benchmark.'),
            ('Parking', 'Poor', 'risk', '-5 points', 'mobility', 'Limited parking reduces convenience for longer café visits.'),
            ('Network overlap', 'Nearest outlet 4.2 km', 'risk', '-5 points', 'network', 'The location creates moderate delivery-radius overlap.'),
        ],
    },
}


STATUS_COLORS = {'Recommended': GREEN, 'Review': GOLD, 'High risk': RED}


def _format_lakh(value: float) -> str:
    return f'₹{value:.1f} lakh'



def _nav_item(
    label: str,
    icon: str,
    route: str | None = None,
    active: bool = False,
) -> None:
    """Render a bright, readable sidebar navigation option."""
    classes = 'nav-button'

    if active:
        classes += ' nav-button-active'

    def handle_click() -> None:
        if route:
            ui.navigate.to(route)
        else:
            ui.notify(
                f'{label} will be added as another module.',
                type='info',
            )

    button = ui.button(
        label,
        icon=icon,
        on_click=handle_click,
    ).props(
        'flat no-caps align=left'
    ).classes(
        classes
    )

    button.style(
        'color: #FFFFFF !important; font-weight: 700;'
        if active
        else 'color: rgba(255,255,255,0.90) !important; font-weight: 600;'
    )





def _render_shell(ai_chat: AIChatController) -> None:
    ui.add_css(
        """
        .app-drawer .nav-button .q-btn__content {
            color: rgba(255, 255, 255, 0.90) !important;
        }

        .app-drawer .nav-button-active .q-btn__content {
            color: #FFFFFF !important;
        }
        """
    )

    drawer = ui.left_drawer(
        value=True
    ).classes(
        'app-drawer p-4'
    ).props(
        'width=260 bordered'
    )

    with drawer:
        with ui.column().classes(
            'w-full h-full gap-2'
        ):
            ui.label(
                'OPERATIONS'
            ).classes(
                'text-[10px] font-bold tracking-[0.18em] '
                'opacity-50 px-3 mt-3 mb-1'
            )

            _nav_item(
                'Command Center',
                'space_dashboard',
                route='/command-center',
                active=False,
            )

            _nav_item(
                'Demand & Inventory',
                'inventory_2',
                route='/demand-inventory',
                active=False,
            )

            _nav_item(
                'Outlet Intelligence',
                'location_on',
                route='/outlet-intelligence',
                active=True,
            )

            _nav_item(
                'Network Intelligence',
                'storefront',
                route='/network-intelligence',
                active=False,
            )

            ui.label(
                'INNOVATE'
            ).classes(
                'text-[10px] font-bold tracking-[0.18em] '
                'opacity-50 px-3 mt-5 mb-1'
            )

            _nav_item(
                'Product Innovation',
                'science',
                route='/product-innovation',
                active=False,
            )

            ui.space()

            with ui.card().classes(
                'w-full p-4 bg-white/10 border-0 '
                'rounded-2xl text-white'
            ):
                with ui.row().classes(
                    'items-center gap-3 no-wrap w-full'
                ):
                    ui.image(
                        '/assets/inventide_logo.png'
                    ).classes(
                        'w-10 h-10 object-cover rounded-full shrink-0'
                    )

                    with ui.column().classes(
                        'gap-0 min-w-0'
                    ):
                        ui.label(
                            'VESPER'
                        ).classes(
                            'text-sm font-black tracking-[0.16em] text-white'
                        )

                        ui.label(
                            'Supply Chain Intelligence'
                        ).classes(
                            'text-[11px] text-white/90 whitespace-nowrap'
                        )

                ui.separator().classes(
                    'opacity-20 my-3'
                )

                ui.label(
                    'AI-powered supply chain engine'
                ).classes(
                    'text-xs text-white/90 leading-relaxed'
                )

                ui.label(
                    'Demo workspace · v0.1'
                ).classes(
                    'text-[10px] text-white/70 mt-2'
                )

    with ui.header().classes(
        'app-header h-16 px-4 md:px-7 '
        'items-center justify-between'
    ):
        with ui.row().classes(
            'items-center gap-3 no-wrap'
        ):
            ui.button(
                icon='menu',
                on_click=drawer.toggle,
            ).props(
                'flat round dense'
            ).classes(
                'lg:hidden'
            )

            ui.image(
                '/assets/inventide_logo.png'
            ).classes(
                'w-11 h-11 object-cover rounded-full'
            )

            with ui.column().classes('gap-0'):
                ui.label(
                    'SUPPLY CHAIN INTELLIGENCE'
                ).classes(
                    'text-sm font-extrabold tracking-wide'
                )

                ui.label(
                    'Powered by Inventide'
                ).classes(
                    'text-[11px] muted'
                )

        with ui.row().classes(
            'items-center gap-3'
        ):
            ui.badge(
                'CONCEPT DATA',
                color='secondary',
            ).props(
                'outline'
            ).classes(
                'desktop-only'
            )

            ui.button(
                'Ask AI',
                icon='auto_awesome',
                on_click=ai_chat.open,
            ).props(
                'unelevated no-caps'
            ).classes(
                'rounded-xl'
            )




def _metric(title: str, value: str, subtitle: str, icon: str) -> None:
    with ui.card().classes('metric-card p-4 w-full'):
        with ui.row().classes('w-full items-start justify-between no-wrap'):
            with ui.column().classes('gap-1'):
                ui.label(title).classes('text-xs font-semibold muted')
                ui.label(value).classes('text-xl font-bold tracking-tight')
                ui.label(subtitle).classes('text-[11px] muted')
            with ui.element('div').classes('metric-icon'):
                ui.icon(icon).classes('text-xl')


def _status(status: str) -> None:
    ui.badge(status).style(f'background:{STATUS_COLORS[status]};color:white;')


@ui.page('/outlet-intelligence')
async def outlet_intelligence_page() -> None:
    apply_theme()
    ui.add_css('''
        .location-map{border-radius:16px;overflow:hidden;border:1px solid rgba(90,21,52,.09)}
        .candidate-row{border:1px solid rgba(90,21,52,.09);border-radius:14px;background:#fffdf8;transition:160ms ease}
        .candidate-row:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(59,13,34,.07)}
        .verdict-panel{background:linear-gradient(150deg,#3B0D22,#5A1534);color:white;border-radius:18px}
    ''')
    ai_chat = create_ai_chat(
        page_name='Outlet Intelligence',
        page_context=PAGE_CONTEXTS['outlet_intelligence'],
    )
    _render_shell(ai_chat)

    state = {'selected': None, 'run': 0, 'decisions': {}}
    refs: dict[str, Any] = {}
    marker_layers: dict[str, Any] = {}

    def show_sources(signal: tuple[str, str, str, str, str, str]) -> None:
        title, value, tone, points, source_key, evidence = signal
        source_name, source_type, freshness = SOURCE_CATALOG[source_key]
        refs['source_content'].clear()
        with refs['source_content']:
            ui.label(title).classes('text-lg font-bold')
            ui.label(f'{value} · {points}').classes('text-sm muted')
            ui.separator().classes('my-3')
            ui.label(source_name).classes('text-sm font-bold')
            ui.label(source_type).classes('text-xs muted')
            ui.badge(freshness, color='primary').props('outline').classes('mt-2')
            ui.label(evidence).classes('text-sm leading-relaxed mt-3')
        refs['source_dialog'].open()

    def set_decision(decision: str) -> None:
        candidate_id = state['selected']
        if candidate_id is None:
            return
        state['decisions'][candidate_id] = decision
        refs['decision'].set_text(f'Workflow status: {decision}')
        ui.notify(f"{CANDIDATES[candidate_id]['name']} marked as {decision}.", type='positive')

    def render_details(candidate_id: str) -> None:
        c = CANDIDATES[candidate_id]
        refs['details'].clear()
        with refs['details']:
            with ui.row().classes('w-full items-start justify-between'):
                with ui.column().classes('gap-1'):
                    ui.label('AI LOCATION VERDICT').classes('section-kicker')
                    ui.label(c['name']).classes('text-2xl font-extrabold')
                    ui.label(c['address']).classes('text-sm muted')
                with ui.column().classes('items-end gap-1'):
                    _status(c['status'])
                    refs['decision'] = ui.label(
                        f"Workflow status: {state['decisions'].get(candidate_id, 'Not decided')}"
                    ).classes('text-xs muted')

            with ui.grid(columns=5).classes('w-full gap-4 mt-4 max-[1100px]:grid-cols-2 max-[650px]:grid-cols-1'):
                _metric('Location score', f"{c['score']} / 100", 'AI composite score', 'stars')
                _metric('Expected monthly sales', _format_lakh(c['sales']), 'Base scenario', 'currency_rupee')
                _metric('Contribution margin', f"{c['margin']:.1f}%", 'After operating costs', 'percent')
                _metric('Break-even', f"{c['break_even']} months", 'Estimated payback', 'schedule')
                _metric('Cannibalization risk', c['cannibalization'], 'Existing network overlap', 'store')

            with ui.grid(columns=12).classes('w-full gap-4 mt-4 max-[1050px]:grid-cols-1'):
                with ui.card().classes('surface col-span-7 p-5 w-full max-[1050px]:col-span-1'):
                    ui.label('Information supplied by the expansion team').classes('text-lg font-bold')
                    ui.label('Required inputs plus optional structured and unstructured evidence').classes('text-xs muted')
                    fields = {
                        'Monthly rent': _format_lakh(c['rent']),
                        'Square footage': f"{c['sqft']:,} sq. ft.",
                        **c['optional'],
                        'Documents': f"{len(c['documents'])} uploaded items",
                    }
                    with ui.grid(columns=3).classes('w-full gap-3 mt-4 max-[750px]:grid-cols-1'):
                        for title, value in fields.items():
                            with ui.card().classes('p-3 rounded-xl shadow-none border border-[#eee4e8]'):
                                ui.label(title.upper()).classes('text-[9px] font-bold muted')
                                ui.label(value).classes('text-sm font-semibold')
                    ui.label('UNSTRUCTURED SITE NOTES').classes('section-kicker mt-4')
                    ui.label(c['notes']).classes('text-sm leading-relaxed')
                    ui.label('UPLOADED EVIDENCE').classes('section-kicker mt-4')
                    for document in c['documents']:
                        with ui.row().classes('items-center gap-2 mt-1'):
                            ui.icon('description').classes('text-primary')
                            ui.label(document).classes('text-sm')

                with ui.card().classes('verdict-panel col-span-5 p-5 w-full max-[1050px]:col-span-1'):
                    with ui.row().classes('w-full items-center justify-between'):
                        ui.label('AI RECOMMENDATION').classes('ai-badge')
                        ui.label(f"{c['score']} / 100").classes('text-xl font-black text-amber-200')
                    ui.label(c['verdict']).classes('text-2xl font-extrabold mt-4')
                    ui.label(c['summary']).classes('text-sm text-white/75 leading-relaxed mt-2')
                    ui.separator().classes('opacity-20 my-4')
                    ui.label('RECOMMENDED FORMAT').classes('text-[10px] tracking-wider text-white/55')
                    ui.label(c['format']).classes('text-lg font-bold text-amber-200')

            with ui.card().classes('surface w-full p-5 mt-4'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('gap-0'):
                        ui.label('Explainable verdict and source evidence').classes('text-lg font-bold')
                        ui.label('AI-enriched signals collected after candidate selection').classes('text-xs muted')
                    ui.badge(f"{len(c['signals'])} SIGNALS", color='primary').props('outline')

                with ui.grid(columns=3).classes('w-full gap-3 mt-4 max-[1000px]:grid-cols-2 max-[700px]:grid-cols-1'):
                    for signal in c['signals']:
                        title, value, tone, points, source_key, evidence = signal
                        positive = tone == 'positive'
                        color = GREEN if positive else RED
                        icon = 'trending_up' if positive else 'warning_amber'
                        with ui.card().classes('p-4 rounded-xl shadow-none border border-[#eee4e8]').style(
                            f'border-left:4px solid {color};'
                        ):
                            with ui.row().classes('w-full items-start justify-between gap-2'):
                                with ui.row().classes('items-start gap-2 no-wrap'):
                                    ui.icon(icon).style(f'color:{color};')
                                    with ui.column().classes('gap-0'):
                                        ui.label(title).classes('text-sm font-bold')
                                        ui.label(value).classes('text-xs muted')
                                ui.badge(points).style(f'background:{color};color:white;')
                            ui.label(evidence).classes('text-xs muted leading-relaxed mt-3')
                            ui.button(
                                'View source',
                                icon='source',
                                on_click=lambda s=signal: show_sources(s),
                            ).props('flat dense no-caps color=primary').classes('text-xs mt-2')

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Request more information', icon='help_outline', on_click=lambda: set_decision('More information requested')).props('outline no-caps').classes('rounded-xl')
                ui.button('Reject candidate', icon='close', on_click=lambda: set_decision('Rejected')).props('outline no-caps color=negative').classes('rounded-xl')
                ui.button('Shortlist candidate', icon='bookmark_added', on_click=lambda: set_decision('Shortlisted')).props('unelevated no-caps').classes('rounded-xl')

    async def analyze(candidate_id: str) -> None:
        c = CANDIDATES[candidate_id]
        state['selected'] = candidate_id
        state['run'] += 1
        run_id = state['run']
        refs['analysis'].clear()
        refs['details'].clear()
        with refs['analysis']:
            with ui.card().classes('surface w-full p-5'):
                ui.label('AI LOCATION ANALYSIS').classes('section-kicker')
                ui.label(f"Evaluating {c['name']}").classes('text-xl font-bold')
                progress_text = ui.label('Reading candidate record…').classes('text-sm muted')
                progress = ui.linear_progress(value=0).props('rounded color=primary track-color=grey-3').classes('w-full mt-4')
        steps = [
            'Reading team-submitted documents',
            'Resolving address and trade area',
            'Checking competition and demand generators',
            'Estimating sales and cannibalization',
            'Generating explainable investment verdict',
        ]
        for index, step in enumerate(steps, 1):
            if run_id != state['run']:
                return
            progress_text.set_text(f'{step}…')
            progress.value = index / len(steps)
            progress.update()
            await asyncio.sleep(0.45)
        if run_id == state['run']:
            refs['analysis'].clear()
            render_details(candidate_id)
            ui.notify(f"AI verdict generated for {c['name']}", type='positive', icon='verified')

    async def marker_event(event: Any) -> None:
        candidate_id = event.args.get('candidate_id') if event.args else None
        if candidate_id in CANDIDATES:
            await analyze(candidate_id)

    with ui.dialog() as source_dialog:
        refs['source_dialog'] = source_dialog
        with ui.card().classes('w-[650px] max-w-[94vw] p-6 rounded-2xl'):
            refs['source_content'] = ui.column().classes('w-full gap-1')
            with ui.row().classes('w-full justify-end mt-3'):
                ui.button('Close', on_click=source_dialog.close).props('flat no-caps')

    with ui.column().classes('w-full max-w-[1540px] mx-auto px-4 md:px-7 py-6 gap-5'):
        with ui.row().classes('w-full items-start justify-between'):
            with ui.column().classes('gap-1'):
                ui.label('OUTLET INTELLIGENCE').classes('section-kicker')
                ui.label('AI-assisted location investment studio').classes('text-2xl md:text-3xl font-extrabold')
                ui.label('Shortlisted properties enriched with location, competition and financial intelligence').classes('text-sm muted')
            ui.badge(f'{len(CANDIDATES)} MOCK CANDIDATES', color='positive').props('outline')

        with ui.grid(columns=12).classes('w-full gap-4 max-[1050px]:grid-cols-1'):
            with ui.card().classes('surface col-span-8 p-5 w-full max-[1050px]:col-span-1'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('gap-0'):
                        ui.label('India candidate map').classes('text-lg font-bold')
                        ui.label('Click a dot to run the mock AI evaluation').classes('text-xs muted')
                    with ui.row().classes('gap-2'):
                        for label, color in STATUS_COLORS.items():
                            with ui.row().classes('items-center gap-1'):
                                ui.element('span').style(f'width:9px;height:9px;border-radius:50%;background:{color};display:inline-block;')
                                ui.label(label).classes('text-[10px] muted')

                candidate_map = ui.leaflet(
                    center=(22.7, 79.4),
                    zoom=5,
                    options={'scrollWheelZoom': True, 'zoomControl': True},
                ).classes('location-map w-full h-[540px] mt-4')

                for candidate_id, c in CANDIDATES.items():
                    marker_layers[candidate_id] = candidate_map.generic_layer(
                        name='circleMarker',
                        args=[
                            [c['lat'], c['lng']],
                            {
                                'radius': 10,
                                'color': '#FFFFFF',
                                'weight': 3,
                                'fillColor': STATUS_COLORS[c['status']],
                                'fillOpacity': 1.0,
                            },
                        ],
                    )

            with ui.card().classes('surface col-span-4 p-5 w-full max-[1050px]:col-span-1'):
                ui.label('Shortlisted candidates').classes('text-lg font-bold')
                ui.label('Minimum inputs: address, rent and square footage').classes('text-xs muted')
                with ui.column().classes('w-full gap-3 mt-4 max-h-[500px] overflow-auto pr-1'):
                    for candidate_id, c in CANDIDATES.items():
                        with ui.card().classes('candidate-row w-full p-3 shadow-none'):
                            with ui.row().classes('w-full items-start justify-between gap-2'):
                                with ui.column().classes('gap-0'):
                                    ui.label(c['name']).classes('text-sm font-bold')
                                    ui.label(f"{_format_lakh(c['rent'])}/month · {c['sqft']} sq. ft.").classes('text-[11px] muted')
                                _status(c['status'])
                            ui.button('Analyze', icon='auto_awesome', on_click=lambda cid=candidate_id: analyze(cid)).props('flat dense no-caps color=primary').classes('text-xs mt-2')

        refs['analysis'] = ui.column().classes('w-full')
        refs['details'] = ui.column().classes('w-full')
        ui.label('Prototype only · All location, financial and source values are simulated.').classes('text-[11px] muted')

    ui.on('candidate-selected', marker_event)
    await candidate_map.initialized()
    for candidate_id, layer in marker_layers.items():
        c = CANDIDATES[candidate_id]
        candidate_map.run_layer_method(layer.id, 'bindTooltip', f"{c['name']} · {c['status']}")
        candidate_map.run_layer_method(
            layer.id,
            ':on',
            '"click"',
            f'function() {{ emitEvent("candidate-selected", {{candidate_id: "{candidate_id}"}}); }}',
        )
