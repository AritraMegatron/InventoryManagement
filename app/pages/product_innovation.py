
from __future__ import annotations

import asyncio
import csv
import io
import random
from datetime import datetime
from typing import Any

from nicegui import events, ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS

from app.theme import BURGUNDY, GOLD, GREEN, MUTED, RED, apply_theme


SOURCE_CATALOG = {
    'menus': {
        'name': 'Competitor menu monitor',
        'type': 'Public menu and visible product listings',
        'freshness': 'Mock refresh: today',
        'description': (
            'Tracks visible product launches, pricing, category expansion, '
            'and recurring menu formats across selected competitors.'
        ),
    },
    'reviews': {
        'name': 'Consumer review analysis',
        'type': 'Public customer-language intelligence',
        'freshness': 'Mock refresh: today',
        'description': (
            'Clusters recurring preferences, complaints, dietary requests, '
            'and product attributes from public review text.'
        ),
    },
    'search': {
        'name': 'Search-interest monitor',
        'type': 'Public directional demand signals',
        'freshness': 'Mock refresh: this week',
        'description': (
            'Measures directional interest for product categories and '
            'flavors across selected markets.'
        ),
    },
    'social': {
        'name': 'Social trend monitor',
        'type': 'Public conversation intelligence',
        'freshness': 'Mock refresh: today',
        'description': (
            'Identifies fast-growing visual formats, flavor combinations, '
            'and customer vocabulary from public content.'
        ),
    },
    'sales': {
        'name': 'Internal product sales history',
        'type': 'Internal business data',
        'freshness': 'Current mock snapshot',
        'description': (
            'Measures sales of related products, geographic fit, repeat '
            'purchase, and performance of previous launches.'
        ),
    },
    'ingredients': {
        'name': 'Recipe and ingredient master',
        'type': 'Internal operational data',
        'freshness': 'Current mock snapshot',
        'description': (
            'Estimates ingredient reuse, new sourcing requirements, '
            'preparation complexity, and unit economics.'
        ),
    },
}


CONCEPTS: dict[str, dict[str, Any]] = {
    'protein_chocolate': {
        'name': 'High-Protein Chocolate Shake',
        'category': 'Functional beverages',
        'score': 89,
        'momentum': 91,
        'overlap': 82,
        'margin': 66,
        'complexity': 'Low',
        'competition': 'Medium',
        'confidence': 'High',
        'verdict': 'Pilot',
        'price': '₹339–₹369',
        'markets': ['Bengaluru', 'Gurugram', 'Pune'],
        'outlets': 6,
        'weeks': 4,
        'customer': (
            'Urban customers aged 20–35 seeking indulgence with a '
            'functional benefit.'
        ),
        'summary': (
            'A premium chocolate shake with a clear protein proposition '
            'and minimal change to the existing preparation workflow.'
        ),
        'ingredients': [
            ('Chocolate base', 'Existing'),
            ('Milk / dairy base', 'Existing'),
            ('Protein blend', 'New'),
            ('Low-sugar support', 'Minor adjustment'),
        ],
        'signals': [
            {
                'title': 'Functional beverage momentum',
                'value': '+24% directional interest',
                'impact': '+14 points',
                'tone': 'positive',
                'source': 'search',
                'evidence': (
                    'Protein drinks and functional shakes show sustained '
                    'interest across premium urban markets in the mock scan.'
                ),
            },
            {
                'title': 'Competitor adoption',
                'value': '14 tracked menu appearances',
                'impact': '+10 points',
                'tone': 'positive',
                'source': 'menus',
                'evidence': (
                    'Protein-positioned beverages appear across a growing '
                    'set of premium café and dessert menus.'
                ),
            },
            {
                'title': 'Internal flavor fit',
                'value': 'Chocolate is a top-performing base',
                'impact': '+12 points',
                'tone': 'positive',
                'source': 'sales',
                'evidence': (
                    'Existing chocolate products show strong revenue and '
                    'repeat purchase in the mock internal dataset.'
                ),
            },
            {
                'title': 'Ingredient reuse',
                'value': '82% existing ingredient overlap',
                'impact': '+8 points',
                'tone': 'positive',
                'source': 'ingredients',
                'evidence': (
                    'Only the protein blend requires meaningful incremental '
                    'sourcing in the mock recipe assessment.'
                ),
            },
            {
                'title': 'Cost sensitivity',
                'value': 'Protein input raises unit cost',
                'impact': '-5 points',
                'tone': 'risk',
                'source': 'ingredients',
                'evidence': (
                    'Premium pricing is required to preserve the target '
                    'margin after adding the protein ingredient.'
                ),
            },
        ],
    },
    'mini_shake_flight': {
        'name': 'Mini Shake Flight',
        'category': 'Format innovation',
        'score': 86,
        'momentum': 82,
        'overlap': 96,
        'margin': 69,
        'complexity': 'Medium',
        'competition': 'Low',
        'confidence': 'High',
        'verdict': 'Pilot',
        'price': '₹449–₹499',
        'markets': ['Delhi NCR', 'Mumbai', 'Bengaluru'],
        'outlets': 10,
        'weeks': 4,
        'customer': (
            'Groups and younger customers seeking variety and a '
            'shareable product experience.'
        ),
        'summary': (
            'A tasting format that repackages proven best sellers into '
            'a shareable premium experience.'
        ),
        'ingredients': [
            ('Chocolate shake base', 'Existing'),
            ('Cold coffee base', 'Existing'),
            ('Mango base', 'Existing'),
            ('Mini serving cups', 'New packaging'),
        ],
        'signals': [
            {
                'title': 'Variety-seeking behavior',
                'value': 'Strong customer-language cluster',
                'impact': '+12 points',
                'tone': 'positive',
                'source': 'reviews',
                'evidence': (
                    'Customers frequently mention wanting to try several '
                    'flavors without purchasing full portions.'
                ),
            },
            {
                'title': 'Ingredient reuse',
                'value': '96% existing overlap',
                'impact': '+14 points',
                'tone': 'positive',
                'source': 'ingredients',
                'evidence': (
                    'The concept primarily repackages existing recipes and '
                    'requires only new serving packaging.'
                ),
            },
            {
                'title': 'Internal product fit',
                'value': 'Uses three proven best sellers',
                'impact': '+12 points',
                'tone': 'positive',
                'source': 'sales',
                'evidence': (
                    'The proposed flight uses products with strong historical '
                    'performance in the mock internal dataset.'
                ),
            },
            {
                'title': 'Service-time risk',
                'value': 'Multiple cups per order',
                'impact': '-5 points',
                'tone': 'risk',
                'source': 'ingredients',
                'evidence': (
                    'Assembly may slow peak-period service unless the '
                    'preparation process is standardized.'
                ),
            },
        ],
    },
    'rose_falooda': {
        'name': 'Rose Falooda Sundae',
        'category': 'Regional indulgence',
        'score': 84,
        'momentum': 79,
        'overlap': 74,
        'margin': 64,
        'complexity': 'Medium',
        'competition': 'Medium',
        'confidence': 'High',
        'verdict': 'Pilot',
        'price': '₹299–₹329',
        'markets': ['Delhi NCR', 'Mumbai', 'Jaipur'],
        'outlets': 8,
        'weeks': 5,
        'customer': (
            'Families and young consumers seeking familiar regional '
            'flavors in a modern presentation.'
        ),
        'summary': (
            'A visually distinctive sundae combining a familiar Indian '
            'dessert format with premium presentation.'
        ),
        'ingredients': [
            ('Vanilla ice cream', 'Existing'),
            ('Rose syrup', 'New'),
            ('Falooda sev', 'New'),
            ('Basil seeds', 'New'),
            ('Nut garnish', 'Existing'),
        ],
        'signals': [
            {
                'title': 'Regional flavor interest',
                'value': '+18% review-language growth',
                'impact': '+11 points',
                'tone': 'positive',
                'source': 'reviews',
                'evidence': (
                    'Regional dessert flavors appear more frequently in '
                    'positive customer-language clusters.'
                ),
            },
            {
                'title': 'Visual social potential',
                'value': 'High shareable-format score',
                'impact': '+8 points',
                'tone': 'positive',
                'source': 'social',
                'evidence': (
                    'Layered desserts with strong color and texture perform '
                    'well in the mock public-content scan.'
                ),
            },
            {
                'title': 'Brand fit',
                'value': 'Strong heritage compatibility',
                'impact': '+13 points',
                'tone': 'positive',
                'source': 'sales',
                'evidence': (
                    'The concept remains close to the brand’s indulgent '
                    'beverage and dessert positioning.'
                ),
            },
            {
                'title': 'Preparation complexity',
                'value': 'Three incremental components',
                'impact': '-7 points',
                'tone': 'risk',
                'source': 'ingredients',
                'evidence': (
                    'Falooda sev, soaked seeds, and layered assembly increase '
                    'preparation and holding complexity.'
                ),
            },
        ],
    },
    'low_sugar_mango': {
        'name': 'Low-Sugar Alphonso Shake',
        'category': 'Better-for-you',
        'score': 81,
        'momentum': 85,
        'overlap': 88,
        'margin': 63,
        'complexity': 'Low',
        'competition': 'Medium',
        'confidence': 'High',
        'verdict': 'Pilot',
        'price': '₹299–₹329',
        'markets': ['Mumbai', 'Pune', 'Bengaluru'],
        'outlets': 8,
        'weeks': 5,
        'customer': (
            'Existing shake customers seeking a lower-sugar alternative '
            'without abandoning indulgence.'
        ),
        'summary': (
            'A familiar seasonal product adjusted for consumers seeking '
            'less sugar and a lighter sweetness profile.'
        ),
        'ingredients': [
            ('Alphonso mango pulp', 'Existing'),
            ('Milk base', 'Existing'),
            ('Reduced-sugar support', 'Minor adjustment'),
            ('Sweetness balancing', 'Minor adjustment'),
        ],
        'signals': [
            {
                'title': 'Lower-sugar demand',
                'value': '+21% request-language growth',
                'impact': '+12 points',
                'tone': 'positive',
                'source': 'reviews',
                'evidence': (
                    'Requests for lower-sugar and less-sweet options appear '
                    'more frequently across the mock review scan.'
                ),
            },
            {
                'title': 'Existing seasonal strength',
                'value': 'Mango is a proven seasonal seller',
                'impact': '+11 points',
                'tone': 'positive',
                'source': 'sales',
                'evidence': (
                    'Mango products perform strongly during warm-season '
                    'periods in the mock internal history.'
                ),
            },
            {
                'title': 'Ingredient reuse',
                'value': '88% existing overlap',
                'impact': '+9 points',
                'tone': 'positive',
                'source': 'ingredients',
                'evidence': (
                    'The concept needs recipe tuning rather than a new '
                    'ingredient and equipment ecosystem.'
                ),
            },
            {
                'title': 'Taste expectation risk',
                'value': 'Requires sensory validation',
                'impact': '-6 points',
                'tone': 'risk',
                'source': 'reviews',
                'evidence': (
                    'Customers may reject the product if lower sugar changes '
                    'the expected Alphonso flavor experience.'
                ),
            },
        ],
    },
    'mango_boba': {
        'name': 'Mango Cheesecake Boba Shake',
        'category': 'Youth trend',
        'score': 73,
        'momentum': 88,
        'overlap': 51,
        'margin': 57,
        'complexity': 'High',
        'competition': 'High',
        'confidence': 'Medium',
        'verdict': 'Research',
        'price': '₹379–₹419',
        'markets': ['Delhi NCR', 'Bengaluru', 'Mumbai'],
        'outlets': 4,
        'weeks': 3,
        'customer': (
            'Gen Z consumers seeking novelty and visually distinctive '
            'products.'
        ),
        'summary': (
            'A high-novelty concept with strong trend momentum but '
            'meaningful sourcing, preparation, and margin complexity.'
        ),
        'ingredients': [
            ('Mango pulp', 'Existing'),
            ('Cream-cheese base', 'New'),
            ('Boba pearls', 'New'),
            ('Crumb topping', 'New'),
            ('Milk base', 'Existing'),
        ],
        'signals': [
            {
                'title': 'Youth-category momentum',
                'value': '+31% social velocity',
                'impact': '+15 points',
                'tone': 'positive',
                'source': 'social',
                'evidence': (
                    'Boba and cheesecake combinations show strong short-term '
                    'conversation growth in the mock scan.'
                ),
            },
            {
                'title': 'Visible menu growth',
                'value': '22 new listings observed',
                'impact': '+10 points',
                'tone': 'positive',
                'source': 'menus',
                'evidence': (
                    'Novel boba products appear more frequently across '
                    'visible competitor assortments.'
                ),
            },
            {
                'title': 'Ingredient overlap',
                'value': 'Only 51% existing overlap',
                'impact': '-10 points',
                'tone': 'risk',
                'source': 'ingredients',
                'evidence': (
                    'Three important components are not part of the current '
                    'mock ingredient master.'
                ),
            },
            {
                'title': 'Competitive crowding',
                'value': 'High in premium urban markets',
                'impact': '-8 points',
                'tone': 'risk',
                'source': 'menus',
                'evidence': (
                    'The product would enter a crowded novelty-beverage space.'
                ),
            },
        ],
    },
    'matcha_coffee': {
        'name': 'Matcha Cold Coffee',
        'category': 'Premium experimentation',
        'score': 64,
        'momentum': 76,
        'overlap': 68,
        'margin': 61,
        'complexity': 'Medium',
        'competition': 'Low',
        'confidence': 'Medium',
        'verdict': 'Watch',
        'price': '₹349–₹389',
        'markets': ['Bengaluru', 'Mumbai', 'Gurugram'],
        'outlets': 3,
        'weeks': 3,
        'customer': (
            'Premium experimental consumers in major metropolitan markets.'
        ),
        'summary': (
            'A niche premium concept with interesting momentum but '
            'uncertain brand fit and a polarizing flavor profile.'
        ),
        'ingredients': [
            ('Cold coffee base', 'Existing'),
            ('Matcha powder', 'New'),
            ('Vanilla support', 'Existing'),
            ('Premium milk option', 'Existing'),
        ],
        'signals': [
            {
                'title': 'Premium search momentum',
                'value': '+17% directional interest',
                'impact': '+9 points',
                'tone': 'positive',
                'source': 'search',
                'evidence': (
                    'Matcha-related beverage interest is growing in selected '
                    'premium urban catchments.'
                ),
            },
            {
                'title': 'Low direct competition',
                'value': 'Limited comparable menu overlap',
                'impact': '+6 points',
                'tone': 'positive',
                'source': 'menus',
                'evidence': (
                    'Few directly comparable matcha-coffee combinations were '
                    'found in the mock competitor scan.'
                ),
            },
            {
                'title': 'Customer polarization',
                'value': 'Mixed taste-language clusters',
                'impact': '-9 points',
                'tone': 'risk',
                'source': 'reviews',
                'evidence': (
                    'Matcha flavor generates both strong enthusiasm and '
                    'strong dislike in review-language clusters.'
                ),
            },
            {
                'title': 'Brand fit',
                'value': 'Moderate',
                'impact': '-7 points',
                'tone': 'risk',
                'source': 'sales',
                'evidence': (
                    'Current best-performing flavors are more familiar and '
                    'indulgent than matcha.'
                ),
            },
        ],
    },
}


VERDICT_COLORS = {
    'Pilot': GREEN,
    'Research': GOLD,
    'Watch': '#2A608D',
}


TABLE_COLUMNS = [
    {
        'name': 'name',
        'label': 'Product concept',
        'field': 'name',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'category',
        'label': 'Opportunity area',
        'field': 'category',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'score',
        'label': 'Score',
        'field': 'score',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'momentum',
        'label': 'Momentum',
        'field': 'momentum',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'overlap_text',
        'label': 'Ingredient overlap',
        'field': 'overlap_text',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'margin_text',
        'label': 'Est. margin',
        'field': 'margin_text',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'complexity',
        'label': 'Complexity',
        'field': 'complexity',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'verdict',
        'label': 'Verdict',
        'field': 'verdict',
        'align': 'left',
        'sortable': True,
    },
]


def _rows() -> list[dict[str, Any]]:
    return [
        {
            'concept_id': concept_id,
            'name': concept['name'],
            'category': concept['category'],
            'score': concept['score'],
            'momentum': concept['momentum'],
            'overlap_text': f"{concept['overlap']}%",
            'margin_text': f"{concept['margin']}%",
            'complexity': concept['complexity'],
            'verdict': concept['verdict'],
        }
        for concept_id, concept in CONCEPTS.items()
    ]


def _nav_item(
    label: str,
    icon: str,
    route: str | None = None,
    active: bool = False,
) -> None:
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
                active=False,
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
                active=True,
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



def _metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
) -> tuple[Any, Any]:
    with ui.card().classes(
        'metric-card p-4 w-full'
    ):
        with ui.row().classes(
            'w-full items-start justify-between no-wrap'
        ):
            with ui.column().classes('gap-1'):
                ui.label(
                    title
                ).classes(
                    'text-xs font-semibold muted'
                )

                value_label = ui.label(
                    value
                ).classes(
                    'text-2xl font-bold tracking-tight'
                )

                subtitle_label = ui.label(
                    subtitle
                ).classes(
                    'text-xs muted'
                )

            with ui.element('div').classes(
                'metric-icon'
            ):
                ui.icon(
                    icon
                ).classes(
                    'text-xl'
                )

    return value_label, subtitle_label


def _chart_options() -> dict[str, Any]:
    concepts = sorted(
        CONCEPTS.values(),
        key=lambda item: item['momentum'],
    )

    return {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow',
            },
        },
        'grid': {
            'left': 190,
            'right': 32,
            'top': 20,
            'bottom': 34,
        },
        'xAxis': {
            'type': 'value',
            'min': 0,
            'max': 100,
            'axisLabel': {
                'color': MUTED,
                'fontSize': 10,
            },
            'splitLine': {
                'lineStyle': {
                    'color': '#EEE7E8',
                },
            },
        },
        'yAxis': {
            'type': 'category',
            'data': [
                item['name']
                for item in concepts
            ],
            'axisLabel': {
                'color': MUTED,
                'fontSize': 10,
                'width': 175,
                'overflow': 'truncate',
            },
            'axisLine': {
                'show': False,
            },
            'axisTick': {
                'show': False,
            },
        },
        'series': [
            {
                'name': 'Market momentum',
                'type': 'bar',
                'data': [
                    item['momentum']
                    for item in concepts
                ],
                'barWidth': 13,
                'itemStyle': {
                    'color': GOLD,
                    'borderRadius': [0, 7, 7, 0],
                },
                'label': {
                    'show': True,
                    'position': 'right',
                    'color': BURGUNDY,
                    'fontWeight': 'bold',
                },
            },
        ],
    }


def _replace_chart(
    chart: Any,
    new_options: dict[str, Any],
) -> None:
    chart.options.clear()
    chart.options.update(new_options)
    chart.update()


@ui.page('/product-innovation')
def product_innovation_page() -> None:
    apply_theme()

    ui.add_css(
        '''
        .innovation-table .q-table tbody tr.q-tr--selected {
            background: rgba(90, 21, 52, 0.10) !important;
            box-shadow: inset 4px 0 0 #5A1534;
        }

        .innovation-detail {
            background: linear-gradient(155deg, #3B0D22, #5A1534);
            color: white;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(59, 13, 34, 0.20);
        }

        .evidence-card {
            border: 1px solid rgba(90, 21, 52, 0.09);
            border-radius: 14px;
            background: #FFFCF6;
        }
        '''
    )

    ai_chat = create_ai_chat(
        page_name='Product Innovation',
        page_context=PAGE_CONTEXTS['product_innovation'],
    )
    _render_shell(ai_chat)

    table_rows = _rows()

    rows_by_id = {
        row['concept_id']: row
        for row in table_rows
    }

    state: dict[str, Any] = {
        'selected_id': table_rows[0]['concept_id'],
        'category': 'All opportunities',
        'verdict': 'All verdicts',
        'search': '',
        'scan_number': 0,
        'pilot_concept_id': None,
        'pilot_plans': {},
    }

    refs: dict[str, Any] = {}

    def filtered_rows() -> list[dict[str, Any]]:
        query = state['search'].strip().lower()

        return [
            row
            for row in table_rows
            if (
                state['category'] == 'All opportunities'
                or row['category'] == state['category']
            )
            and (
                state['verdict'] == 'All verdicts'
                or row['verdict'] == state['verdict']
            )
            and (
                not query
                or query in row['name'].lower()
                or query in row['category'].lower()
                or query in row['verdict'].lower()
            )
        ]

    def replace_rows(
        visible_rows: list[dict[str, Any]],
    ) -> None:
        refs['table'].rows.clear()
        refs['table'].rows.extend(visible_rows)
        refs['table'].update()

    def show_source(
        signal: dict[str, Any],
    ) -> None:
        source = SOURCE_CATALOG[
            signal['source']
        ]

        refs['source_content'].clear()

        with refs['source_content']:
            ui.label(
                signal['title']
            ).classes(
                'text-lg font-bold'
            )

            ui.label(
                f"{signal['value']} · {signal['impact']}"
            ).classes(
                'text-sm muted'
            )

            ui.separator().classes(
                'my-3'
            )

            ui.label(
                source['name']
            ).classes(
                'text-sm font-bold'
            )

            ui.label(
                source['type']
            ).classes(
                'text-xs muted'
            )

            ui.badge(
                source['freshness'],
                color='primary',
            ).props(
                'outline'
            ).classes(
                'mt-2'
            )

            ui.label(
                signal['evidence']
            ).classes(
                'text-sm leading-relaxed mt-4'
            )

            ui.label(
                source['description']
            ).classes(
                'text-xs muted leading-relaxed mt-3'
            )

            ui.label(
                'Prototype note: this source and evidence are simulated.'
            ).classes(
                'text-[11px] text-negative mt-4'
            )

        refs['source_dialog'].open()

    def open_pilot_dialog(
        concept_id: str,
    ) -> None:
        concept = CONCEPTS[concept_id]

        state['pilot_concept_id'] = concept_id

        refs['pilot_title'].set_text(
            f"Build pilot · {concept['name']}"
        )

        refs['pilot_markets'].options = (
            concept['markets']
        )

        refs['pilot_markets'].value = (
            concept['markets'][:2]
        )

        refs['pilot_outlets'].value = (
            concept['outlets']
        )

        refs['pilot_duration'].value = (
            concept['weeks']
        )

        refs['pilot_price'].value = int(
            concept['price']
            .replace('₹', '')
            .split('–')[0]
        )

        refs['pilot_dialog'].open()

    def render_detail(
        concept_id: str,
    ) -> None:
        concept = CONCEPTS[concept_id]

        refs['detail'].clear()

        with refs['detail']:
            with ui.row().classes(
                'w-full items-start justify-between gap-3'
            ):
                with ui.column().classes('gap-1'):
                    ui.label(
                        'AI PRODUCT OPPORTUNITY'
                    ).classes(
                        'section-kicker'
                    )

                    ui.label(
                        concept['name']
                    ).classes(
                        'text-2xl font-extrabold'
                    )

                    ui.label(
                        concept['summary']
                    ).classes(
                        'text-sm muted leading-relaxed'
                    )

                with ui.column().classes(
                    'items-end gap-1'
                ):
                    ui.badge(
                        concept['verdict'].upper()
                    ).style(
                        f"background:"
                        f"{VERDICT_COLORS[concept['verdict']]};"
                        f"color:white;"
                    )

                    ui.label(
                        state['pilot_plans'].get(
                            concept_id,
                            'No pilot plan created',
                        )
                    ).classes(
                        'text-xs muted'
                    )

            with ui.grid(
                columns=5
            ).classes(
                'w-full gap-4 mt-4 '
                'max-[1100px]:grid-cols-2 '
                'max-[650px]:grid-cols-1'
            ):
                _metric_card(
                    'Opportunity score',
                    f"{concept['score']} / 100",
                    'Composite opportunity score',
                    'stars',
                )

                _metric_card(
                    'Market momentum',
                    f"{concept['momentum']} / 100",
                    'Directional market signal',
                    'trending_up',
                )

                _metric_card(
                    'Ingredient overlap',
                    f"{concept['overlap']}%",
                    'Reuse of current ingredients',
                    'inventory_2',
                )

                _metric_card(
                    'Estimated margin',
                    f"{concept['margin']}%",
                    'Mock gross margin',
                    'percent',
                )

                _metric_card(
                    'Complexity',
                    concept['complexity'],
                    'Preparation and sourcing',
                    'engineering',
                )

            with ui.grid(
                columns=12
            ).classes(
                'w-full gap-4 mt-4 '
                'max-[1050px]:grid-cols-1'
            ):
                with ui.card().classes(
                    'surface col-span-7 p-5 w-full '
                    'max-[1050px]:col-span-1'
                ):
                    with ui.row().classes(
                        'w-full items-start justify-between'
                    ):
                        with ui.column().classes('gap-0'):
                            ui.label(
                                'Market evidence and reasoning'
                            ).classes(
                                'text-lg font-bold'
                            )

                            ui.label(
                                'Click a signal to inspect its source'
                            ).classes(
                                'text-xs muted'
                            )

                        ui.badge(
                            f"{len(concept['signals'])} SIGNALS",
                            color='primary',
                        ).props(
                            'outline'
                        )

                    with ui.column().classes(
                        'w-full gap-3 mt-4'
                    ):
                        for signal in concept['signals']:
                            signal_color = (
                                GREEN
                                if signal['tone'] == 'positive'
                                else RED
                            )

                            with ui.card().classes(
                                'evidence-card w-full p-4 shadow-none'
                            ):
                                with ui.row().classes(
                                    'w-full items-start '
                                    'justify-between gap-3'
                                ):
                                    with ui.column().classes(
                                        'gap-1'
                                    ):
                                        ui.label(
                                            signal['title']
                                        ).classes(
                                            'text-sm font-bold'
                                        )

                                        ui.label(
                                            signal['value']
                                        ).classes(
                                            'text-xs muted'
                                        )

                                        ui.label(
                                            signal['evidence']
                                        ).classes(
                                            'text-xs muted '
                                            'leading-relaxed'
                                        )

                                    with ui.column().classes(
                                        'items-end gap-2'
                                    ):
                                        ui.badge(
                                            signal['impact']
                                        ).style(
                                            f'background:{signal_color};'
                                            f'color:white;'
                                        )

                                        ui.button(
                                            'View source',
                                            icon='source',
                                            on_click=lambda s=signal: (
                                                show_source(s)
                                            ),
                                        ).props(
                                            'flat dense no-caps'
                                        ).classes(
                                            'text-xs'
                                        )

                with ui.card().classes(
                    'innovation-detail col-span-5 '
                    'p-5 w-full '
                    'max-[1050px]:col-span-1'
                ):
                    with ui.row().classes(
                        'w-full items-center justify-between'
                    ):
                        ui.label(
                            'AI RECOMMENDATION'
                        ).classes(
                            'ai-badge'
                        )

                        ui.label(
                            f"{concept['score']} / 100"
                        ).classes(
                            'text-xl font-black text-amber-200'
                        )

                    ui.label(
                        concept['verdict']
                    ).classes(
                        'text-2xl font-extrabold mt-4'
                    )

                    ui.label(
                        concept['customer']
                    ).classes(
                        'text-sm text-white/75 '
                        'leading-relaxed mt-2'
                    )

                    ui.separator().classes(
                        'opacity-20 my-4'
                    )

                    details = [
                        ('Target price', concept['price']),
                        (
                            'Best markets',
                            ', '.join(concept['markets']),
                        ),
                        (
                            'Competitive intensity',
                            concept['competition'],
                        ),
                        (
                            'Evidence confidence',
                            concept['confidence'],
                        ),
                        (
                            'Recommended test',
                            (
                                f"{concept['outlets']} outlets · "
                                f"{concept['weeks']} weeks"
                            ),
                        ),
                    ]

                    for label, value in details:
                        ui.label(
                            label.upper()
                        ).classes(
                            'text-[10px] tracking-wider '
                            'text-white/45 mt-3'
                        )

                        ui.label(
                            value
                        ).classes(
                            'text-sm font-semibold text-white/90'
                        )

                    ui.button(
                        'Build pilot plan',
                        icon='science',
                        on_click=lambda cid=concept_id: (
                            open_pilot_dialog(cid)
                        ),
                    ).props(
                        'unelevated no-caps '
                        'color=secondary text-color=dark'
                    ).classes(
                        'w-full rounded-xl mt-6'
                    )

            with ui.card().classes(
                'surface w-full p-5 mt-4'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(
                            'Operational fit'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Existing ingredients and incremental requirements'
                        ).classes(
                            'text-xs muted'
                        )

                    ui.badge(
                        f"{concept['overlap']}% OVERLAP",
                        color='positive',
                    ).props(
                        'outline'
                    )

                with ui.grid(
                    columns=4
                ).classes(
                    'w-full gap-3 mt-4 '
                    'max-[850px]:grid-cols-2 '
                    'max-[550px]:grid-cols-1'
                ):
                    for ingredient, status in concept['ingredients']:
                        with ui.card().classes(
                            'p-4 rounded-xl shadow-none '
                            'border border-[#eee4e8]'
                        ):
                            ui.label(
                                ingredient
                            ).classes(
                                'text-sm font-bold'
                            )

                            ui.label(
                                status
                            ).classes(
                                (
                                    'text-xs text-positive'
                                    if status == 'Existing'
                                    else 'text-xs muted'
                                )
                            )

    def select_concept(
        concept_id: str,
    ) -> None:
        if concept_id not in CONCEPTS:
            return

        state['selected_id'] = concept_id

        refs['table'].selected.clear()
        refs['table'].selected.append(
            rows_by_id[concept_id]
        )
        refs['table'].update()

        render_detail(concept_id)

    def handle_table_click(
        event: events.GenericEventArguments,
    ) -> None:
        arguments = (
            event.args
            if isinstance(event.args, list)
            else [event.args]
        )

        for argument in arguments:
            if (
                isinstance(argument, dict)
                and argument.get('concept_id')
            ):
                select_concept(
                    argument['concept_id']
                )
                return

    def apply_filters(
        _: Any = None,
    ) -> None:
        state['category'] = (
            refs['category_select'].value
        )
        state['verdict'] = (
            refs['verdict_select'].value
        )
        state['search'] = (
            refs['search_input'].value
            or ''
        )

        visible_rows = filtered_rows()
        replace_rows(visible_rows)

        refs['result_count'].set_text(
            f'{len(visible_rows)} concepts shown'
        )

        if not visible_rows:
            refs['table'].selected.clear()
            refs['table'].update()
            return

        visible_ids = {
            row['concept_id']
            for row in visible_rows
        }

        selected_id = (
            state['selected_id']
            if state['selected_id'] in visible_ids
            else visible_rows[0]['concept_id']
        )

        select_concept(selected_id)

    async def run_market_scan() -> None:
        refs['scan_button'].disable()

        progress = ui.notification(
            'Scanning menus, reviews, search signals, and internal fit…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(1.25)

        state['scan_number'] += 1

        for concept_id, concept in CONCEPTS.items():
            rng = random.Random(
                sum(ord(char) for char in concept_id)
                + state['scan_number'] * 733
            )

            concept['momentum'] = max(
                45,
                min(
                    98,
                    concept['momentum']
                    + rng.randint(-4, 5),
                ),
            )

            concept['score'] = max(
                50,
                min(
                    95,
                    concept['score']
                    + rng.randint(-2, 3),
                ),
            )

            row = rows_by_id[concept_id]
            row['momentum'] = concept['momentum']
            row['score'] = concept['score']

        replace_rows(
            filtered_rows()
        )

        _replace_chart(
            refs['momentum_chart'],
            _chart_options(),
        )

        refs['signals_scanned'].set_text(
            f"{1840 + state['scan_number'] * 137:,}"
        )

        refs['last_scan'].set_text(
            f"Updated {datetime.now():%H:%M} · "
            f"Market scan {state['scan_number'] + 1}"
        )

        select_concept(
            state['selected_id']
        )

        progress.dismiss()
        refs['scan_button'].enable()

        ui.notify(
            'Market opportunity scan refreshed',
            type='positive',
            icon='travel_explore',
            position='top',
        )

    def save_pilot_plan() -> None:
        concept_id = state.get(
            'pilot_concept_id'
        )

        if concept_id not in CONCEPTS:
            return

        concept = CONCEPTS[concept_id]
        markets = refs['pilot_markets'].value or []

        state['pilot_plans'][concept_id] = (
            f"Pilot planned · "
            f"{int(refs['pilot_outlets'].value)} outlets · "
            f"{int(refs['pilot_duration'].value)} weeks"
        )

        refs['pilot_dialog'].close()
        render_detail(concept_id)

        refs['pilot_summary'].set_text(
            (
                f"{concept['name']} will be tested in "
                f"{', '.join(markets)} across "
                f"{int(refs['pilot_outlets'].value)} outlets "
                f"for {int(refs['pilot_duration'].value)} weeks "
                f"at a proposed price of ₹"
                f"{int(refs['pilot_price'].value)}."
            )
        )

        refs['pilot_summary_dialog'].open()

    def export_portfolio() -> None:
        buffer = io.StringIO()

        fieldnames = [
            'name',
            'category',
            'score',
            'momentum',
            'overlap_text',
            'margin_text',
            'complexity',
            'verdict',
        ]

        writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        writer.writerows(
            {
                key: row[key]
                for key in fieldnames
            }
            for row in filtered_rows()
        )

        ui.download(
            buffer.getvalue().encode('utf-8'),
            filename='product_opportunity_portfolio.csv',
            media_type='text/csv',
        )

    with ui.dialog() as source_dialog:
        refs['source_dialog'] = source_dialog

        with ui.card().classes(
            'w-[650px] max-w-[94vw] p-6 rounded-2xl'
        ):
            refs['source_content'] = ui.column().classes(
                'w-full gap-1'
            )

            with ui.row().classes(
                'w-full justify-end mt-4'
            ):
                ui.button(
                    'Close',
                    on_click=source_dialog.close,
                ).props(
                    'flat no-caps'
                )

    with ui.dialog() as pilot_dialog:
        refs['pilot_dialog'] = pilot_dialog

        with ui.card().classes(
            'w-[620px] max-w-[94vw] p-6 rounded-2xl'
        ):
            refs['pilot_title'] = ui.label(
                'Build pilot'
            ).classes(
                'text-xl font-bold'
            )

            ui.label(
                'Configure a controlled market test using '
                'simulated assumptions.'
            ).classes(
                'text-sm muted'
            )

            ui.separator().classes(
                'my-4'
            )

            refs['pilot_markets'] = ui.select(
                [],
                label='Pilot markets',
                multiple=True,
            ).props(
                'outlined dense use-chips'
            ).classes(
                'w-full'
            )

            with ui.grid(
                columns=3
            ).classes(
                'w-full gap-3 mt-3 '
                'max-[650px]:grid-cols-1'
            ):
                refs['pilot_outlets'] = ui.number(
                    label='Outlets',
                    value=6,
                    min=1,
                    max=30,
                    step=1,
                ).props(
                    'outlined dense'
                )

                refs['pilot_duration'] = ui.number(
                    label='Duration in weeks',
                    value=4,
                    min=2,
                    max=12,
                    step=1,
                ).props(
                    'outlined dense'
                )

                refs['pilot_price'] = ui.number(
                    label='Test price ₹',
                    value=349,
                    min=99,
                    max=999,
                    step=10,
                ).props(
                    'outlined dense'
                )

            ui.label(
                'SUCCESS THRESHOLDS'
            ).classes(
                'section-kicker mt-5'
            )

            with ui.grid(
                columns=3
            ).classes(
                'w-full gap-3 mt-2 '
                'max-[650px]:grid-cols-1'
            ):
                ui.number(
                    label='Category uplift %',
                    value=8,
                    min=0,
                    max=100,
                ).props(
                    'outlined dense'
                )

                ui.number(
                    label='Minimum margin %',
                    value=62,
                    min=0,
                    max=100,
                ).props(
                    'outlined dense'
                )

                ui.number(
                    label='Maximum waste %',
                    value=3,
                    min=0,
                    max=100,
                ).props(
                    'outlined dense'
                )

            with ui.row().classes(
                'w-full justify-end gap-2 mt-5'
            ):
                ui.button(
                    'Cancel',
                    on_click=pilot_dialog.close,
                ).props(
                    'flat no-caps'
                )

                ui.button(
                    'Create pilot plan',
                    icon='science',
                    on_click=save_pilot_plan,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

    with ui.dialog() as pilot_summary_dialog:
        refs['pilot_summary_dialog'] = (
            pilot_summary_dialog
        )

        with ui.card().classes(
            'w-[560px] max-w-[94vw] p-6 rounded-2xl'
        ):
            with ui.row().classes(
                'items-center gap-3'
            ):
                with ui.element('div').classes(
                    'metric-icon'
                ):
                    ui.icon(
                        'verified'
                    ).classes(
                        'text-xl'
                    )

                ui.label(
                    'Pilot plan created'
                ).classes(
                    'text-xl font-bold'
                )

            refs['pilot_summary'] = ui.label(
                ''
            ).classes(
                'text-sm leading-relaxed mt-4'
            )

            ui.label(
                'The production version would save the plan, assign '
                'outlets, and track pilot KPIs.'
            ).classes(
                'text-xs muted mt-3'
            )

            with ui.row().classes(
                'w-full justify-end mt-4'
            ):
                ui.button(
                    'Close',
                    on_click=pilot_summary_dialog.close,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

    selected_row = table_rows[0]

    with ui.column().classes(
        'w-full max-w-[1580px] mx-auto '
        'px-4 md:px-7 py-6 gap-5'
    ):
        with ui.row().classes(
            'w-full items-start justify-between gap-4'
        ):
            with ui.column().classes('gap-1'):
                ui.label(
                    'PRODUCT INNOVATION INTELLIGENCE'
                ).classes(
                    'section-kicker'
                )

                ui.label(
                    'Evidence-driven product opportunity studio'
                ).classes(
                    'text-2xl md:text-3xl '
                    'font-extrabold tracking-tight'
                )

                ui.label(
                    'Discover emerging consumer opportunities, '
                    'evaluate operational fit, and build measurable pilots.'
                ).classes(
                    'text-sm muted'
                )

            with ui.column().classes(
                'items-end gap-1 desktop-only'
            ):
                ui.badge(
                    f'{len(CONCEPTS)} MOCK CONCEPTS',
                    color='positive',
                ).props(
                    'outline'
                )

                refs['last_scan'] = ui.label(
                    'Simulated market scan · Ready'
                ).classes(
                    'text-xs muted'
                )

        with ui.row().classes(
            'action-bar w-full p-3 gap-3 items-center'
        ):
            refs['category_select'] = ui.select(
                [
                    'All opportunities',
                    *sorted(
                        {
                            concept['category']
                            for concept in CONCEPTS.values()
                        }
                    ),
                ],
                value='All opportunities',
                label='Opportunity area',
                on_change=apply_filters,
            ).props(
                'outlined dense'
            ).classes(
                'w-56'
            )

            refs['verdict_select'] = ui.select(
                [
                    'All verdicts',
                    'Pilot',
                    'Research',
                    'Watch',
                ],
                value='All verdicts',
                label='AI verdict',
                on_change=apply_filters,
            ).props(
                'outlined dense'
            ).classes(
                'w-44'
            )

            refs['search_input'] = ui.input(
                label='Search concept',
                on_change=apply_filters,
            ).props(
                'outlined dense clearable debounce=250'
            ).classes(
                'w-56'
            )

            refs['result_count'] = ui.label(
                f'{len(table_rows)} concepts shown'
            ).classes(
                'text-xs muted'
            )

            ui.space()

            ui.button(
                'Export',
                icon='download',
                on_click=export_portfolio,
            ).props(
                'outline no-caps'
            ).classes(
                'rounded-xl'
            )

            refs['scan_button'] = ui.button(
                'Run market scan',
                icon='travel_explore',
                on_click=run_market_scan,
            ).props(
                'unelevated no-caps'
            ).classes(
                'rounded-xl px-5'
            )

        pilot_ready = sum(
            1
            for concept in CONCEPTS.values()
            if concept['verdict'] == 'Pilot'
        )

        average_overlap = (
            sum(
                concept['overlap']
                for concept in CONCEPTS.values()
            )
            / len(CONCEPTS)
        )

        with ui.grid(
            columns=4
        ).classes(
            'w-full gap-4 '
            'max-[1000px]:grid-cols-2 '
            'max-[600px]:grid-cols-1'
        ):
            (
                refs['signals_scanned'],
                refs['signals_scanned_sub'],
            ) = _metric_card(
                'Signals scanned',
                '1,840',
                'Mock public and internal signals',
                'manage_search',
            )

            _metric_card(
                'Pilot-ready concepts',
                str(pilot_ready),
                'Recommended for controlled testing',
                'science',
            )

            _metric_card(
                'Average ingredient overlap',
                f'{average_overlap:.0f}%',
                'Use of existing ingredients',
                'inventory_2',
            )

            _metric_card(
                'Top opportunity score',
                f"{max(c['score'] for c in CONCEPTS.values())} / 100",
                'Highest current concept score',
                'stars',
            )

        with ui.grid(
            columns=12
        ).classes(
            'w-full gap-4 '
            'max-[1050px]:grid-cols-1'
        ):
            with ui.card().classes(
                'surface col-span-7 p-5 w-full '
                'max-[1050px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(
                            'Market opportunity momentum'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Directional strength across the current '
                            'mock opportunity set'
                        ).classes(
                            'text-xs muted'
                        )

                    ui.badge(
                        'MARKET SIGNALS',
                        color='secondary',
                    ).props(
                        'outline'
                    )

                refs['momentum_chart'] = ui.echart(
                    _chart_options()
                ).classes(
                    'w-full h-[390px] mt-2'
                )

            with ui.card().classes(
                'innovation-detail col-span-5 p-5 w-full '
                'max-[1050px]:col-span-1'
            ):
                ui.label(
                    'HOW THE ENGINE WORKS'
                ).classes(
                    'ai-badge'
                )

                ui.label(
                    'From market signal to testable product'
                ).classes(
                    'text-2xl font-extrabold mt-4'
                )

                steps = [
                    (
                        '1',
                        'Scan',
                        'Monitor menus, reviews, public trends, '
                        'and visible assortments.',
                    ),
                    (
                        '2',
                        'Evaluate',
                        'Compare momentum with brand fit, sales, '
                        'ingredients, margin, and complexity.',
                    ),
                    (
                        '3',
                        'Recommend',
                        'Generate concepts with evidence, risks, '
                        'confidence, and target markets.',
                    ),
                    (
                        '4',
                        'Pilot',
                        'Create a controlled outlet test with measurable '
                        'commercial thresholds.',
                    ),
                ]

                with ui.column().classes(
                    'w-full gap-4 mt-5'
                ):
                    for number, title, description in steps:
                        with ui.row().classes(
                            'items-start gap-3 no-wrap'
                        ):
                            with ui.element('div').style(
                                'width:30px;height:30px;'
                                'border-radius:50%;'
                                'background:rgba(242,181,68,.18);'
                                'color:#FFD985;display:flex;'
                                'align-items:center;justify-content:center;'
                                'font-weight:800;flex-shrink:0;'
                            ):
                                ui.label(number)

                            with ui.column().classes('gap-0'):
                                ui.label(
                                    title
                                ).classes(
                                    'text-sm font-bold'
                                )

                                ui.label(
                                    description
                                ).classes(
                                    'text-xs text-white/70 '
                                    'leading-relaxed'
                                )

        with ui.card().classes(
            'surface w-full p-5 table-shell '
            'innovation-table'
        ):
            with ui.row().classes(
                'w-full items-start justify-between gap-4'
            ):
                with ui.column().classes('gap-0'):
                    ui.label(
                        'Product opportunity portfolio'
                    ).classes(
                        'text-lg font-bold'
                    )

                    ui.label(
                        'Select a concept to inspect evidence, '
                        'operational fit, and pilot recommendation.'
                    ).classes(
                        'text-xs muted'
                    )

                ui.badge(
                    'PRIORITIZED PORTFOLIO',
                    color='primary',
                ).props(
                    'outline'
                )

            refs['table'] = ui.table(
                columns=TABLE_COLUMNS,
                rows=table_rows.copy(),
                row_key='concept_id',
                selection='single',
                pagination={
                    'rowsPerPage': 6,
                },
            ).props(
                'flat bordered dense separator=horizontal '
                'hide-selected-banner'
            ).classes(
                'w-full mt-3'
            )

            refs['table'].on(
                'rowClick',
                handle_table_click,
                [
                    [],
                    ['concept_id'],
                    None,
                ],
            )

            refs['table'].selected.append(
                selected_row
            )
            refs['table'].update()

        refs['detail'] = ui.column().classes(
            'w-full gap-0'
        )

        render_detail(
            selected_row['concept_id']
        )

        with ui.row().classes(
            'w-full justify-between items-center '
            'px-1 pb-3 gap-3'
        ):
            ui.label(
                'Prototype only · All market signals, sources, scores, '
                'and financial values are simulated concept data.'
            ).classes(
                'text-[11px] muted'
            )

            ui.label(
                'Designed by Inventide'
            ).classes(
                'text-[11px] font-bold text-primary'
            )
