
from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS

from app.theme import apply_theme


PRIORITY_COLORS = {
    'HIGH': '#B33A3A',
    'MEDIUM': '#D99A1A',
}


EXECUTIVE_KPIS = [
    {
        'title': 'Monthly revenue',
        'value': '₹12.8 crore',
        'subtitle': 'Current network run rate',
        'icon': 'payments',
    },
    {
        'title': 'Next-month forecast',
        'value': '₹13.4 crore',
        'subtitle': '+4.8% projected growth',
        'icon': 'trending_up',
    },
    {
        'title': 'Operating profit',
        'value': '₹2.3 crore',
        'subtitle': '18.0% operating margin',
        'icon': 'account_balance_wallet',
    },
    {
        'title': 'Underperforming outlets',
        'value': '9',
        'subtitle': 'Across 63 active outlets',
        'icon': 'storefront',
    },
    {
        'title': 'Revenue at risk',
        'value': '₹4.6 lakh',
        'subtitle': 'Top active operational risks',
        'icon': 'warning',
    },
]


ACTION_ITEMS = [
    {
        'id': 'noida_inventory',
        'priority': 'HIGH',
        'title': 'Noida inventory shortage',
        'impact': '₹1.8 lakh sales at risk',
        'action': 'Approve stock transfer',
        'button': 'Approve transfer',
        'icon': 'inventory_2',
        'route': '/demand-inventory',
        'approved_status': 'Approved · Transfer task created',
    },
    {
        'id': 'indiranagar_margin',
        'priority': 'HIGH',
        'title': 'Indiranagar margin decline',
        'impact': '₹1.1 lakh monthly profit at risk',
        'action': 'Start outlet recovery review',
        'button': 'Start review',
        'icon': 'storefront',
        'route': '/network-intelligence',
        'approved_status': 'Assigned · Recovery review started',
    },
    {
        'id': 'protein_shake_pilot',
        'priority': 'MEDIUM',
        'title': 'High-Protein Chocolate Shake',
        'impact': '89 / 100 product opportunity score',
        'action': 'Approve six-outlet pilot',
        'button': 'Approve pilot',
        'icon': 'science',
        'route': '/product-innovation',
        'approved_status': 'Approved · Pilot brief created',
    },
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
                active=True,
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
                'EXECUTIVE VIEW',
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
) -> None:
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

                ui.label(
                    value
                ).classes(
                    'text-2xl font-bold tracking-tight'
                )

                ui.label(
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


@ui.page('/command-center')
def command_center_page() -> None:
    apply_theme()

    ui.add_css(
        '''
        .executive-briefing {
            background: linear-gradient(150deg, #3B0D22, #5A1534);
            color: white;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(59, 13, 34, 0.18);
        }

        .executive-action-card {
            border: 1px solid rgba(90, 21, 52, 0.10);
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 10px 30px rgba(59, 13, 34, 0.05);
        }

        .executive-action-card-approved {
            border: 1px solid rgba(25, 122, 89, 0.28);
            background: rgba(25, 122, 89, 0.04);
        }
        '''
    )

    ai_chat = create_ai_chat(
        page_name='Command Center',
        page_context=PAGE_CONTEXTS['command_center'],
    )
    _render_shell(ai_chat)

    state: dict[str, Any] = {
        'statuses': {
            item['id']: 'Awaiting decision'
            for item in ACTION_ITEMS
        },
    }

    refs: dict[str, Any] = {
        'action_cards': {},
        'status_labels': {},
        'action_buttons': {},
    }

    def pending_count() -> int:
        return sum(
            1
            for status in state['statuses'].values()
            if status == 'Awaiting decision'
        )

    def update_pending_count() -> None:
        remaining = pending_count()

        refs['pending_count'].set_text(
            str(remaining)
        )

        refs['pending_subtitle'].set_text(
            (
                'Executive decisions awaiting response'
                if remaining != 1
                else 'Executive decision awaiting response'
            )
        )

    def approve_action(
        action_id: str,
    ) -> None:
        item = next(
            action
            for action in ACTION_ITEMS
            if action['id'] == action_id
        )

        state['statuses'][action_id] = (
            item['approved_status']
        )

        refs['status_labels'][action_id].set_text(
            item['approved_status']
        )

        refs['status_labels'][action_id].classes(
            remove='text-xs muted',
            add='text-xs font-semibold text-positive',
        )

        refs['action_buttons'][action_id].disable()

        refs['action_cards'][action_id].classes(
            add='executive-action-card-approved'
        )

        update_pending_count()

        ui.notify(
            item['approved_status'],
            type='positive',
            icon='task_alt',
            position='top',
        )

    def open_details(
        route: str,
    ) -> None:
        ui.navigate.to(route)

    with ui.column().classes(
        'w-full max-w-[1500px] mx-auto '
        'px-4 md:px-7 py-6 gap-5'
    ):
        with ui.row().classes(
            'w-full items-start justify-between gap-4'
        ):
            with ui.column().classes('gap-1'):
                ui.label(
                    'COMMAND CENTER'
                ).classes(
                    'section-kicker'
                )

                ui.label(
                    'Executive business overview'
                ).classes(
                    'text-2xl md:text-3xl '
                    'font-extrabold tracking-tight'
                )

                ui.label(
                    'The numbers that matter and the decisions '
                    'that need attention.'
                ).classes(
                    'text-sm muted'
                )

            with ui.column().classes(
                'items-end gap-1 desktop-only'
            ):
                ui.badge(
                    'LIVE CONCEPT VIEW',
                    color='positive',
                ).props(
                    'outline'
                )

                ui.label(
                    f"Updated {datetime.now():%H:%M}"
                ).classes(
                    'text-xs muted'
                )

        with ui.grid(
            columns=5
        ).classes(
            'w-full gap-4 '
            'max-[1150px]:grid-cols-3 '
            'max-[800px]:grid-cols-2 '
            'max-[520px]:grid-cols-1'
        ):
            for kpi in EXECUTIVE_KPIS:
                _metric_card(
                    kpi['title'],
                    kpi['value'],
                    kpi['subtitle'],
                    kpi['icon'],
                )

        with ui.grid(
            columns=12
        ).classes(
            'w-full gap-4 '
            'max-[1000px]:grid-cols-1'
        ):
            with ui.card().classes(
                'executive-briefing col-span-9 '
                'p-6 w-full max-[1000px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-center justify-between gap-3'
                ):
                    ui.label(
                        'AI EXECUTIVE BRIEFING'
                    ).classes(
                        'ai-badge'
                    )

                    ui.icon(
                        'auto_awesome'
                    ).classes(
                        'text-amber-200 text-xl'
                    )

                ui.label(
                    'Revenue is projected to grow 4.8% next month. '
                    'Nine outlets are underperforming, while the most '
                    'immediate operational risk is a Noida inventory '
                    'shortage. One product concept is ready for an '
                    'executive pilot decision.'
                ).classes(
                    'text-lg md:text-xl font-semibold '
                    'leading-relaxed text-white/90 mt-4'
                )

            with ui.card().classes(
                'metric-card col-span-3 p-5 w-full '
                'max-[1000px]:col-span-1'
            ):
                ui.label(
                    'DECISIONS PENDING'
                ).classes(
                    'text-xs font-semibold muted'
                )

                refs['pending_count'] = ui.label(
                    str(pending_count())
                ).classes(
                    'text-4xl font-extrabold mt-2'
                )

                refs['pending_subtitle'] = ui.label(
                    'Executive decisions awaiting response'
                ).classes(
                    'text-xs muted mt-1'
                )

        with ui.row().classes(
            'w-full items-end justify-between gap-4 mt-1'
        ):
            with ui.column().classes('gap-0'):
                ui.label(
                    'PRIORITY ACTIONS'
                ).classes(
                    'section-kicker'
                )

                ui.label(
                    'What needs your attention'
                ).classes(
                    'text-xl font-bold'
                )

            ui.label(
                'Simulated approval workflow'
            ).classes(
                'text-xs muted desktop-only'
            )

        with ui.grid(
            columns=3
        ).classes(
            'w-full gap-4 '
            'max-[1100px]:grid-cols-1'
        ):
            for item in ACTION_ITEMS:
                with ui.card().classes(
                    'executive-action-card w-full p-5'
                ) as action_card:
                    refs['action_cards'][
                        item['id']
                    ] = action_card

                    with ui.row().classes(
                        'w-full items-start justify-between gap-3'
                    ):
                        with ui.row().classes(
                            'items-center gap-3 no-wrap'
                        ):
                            with ui.element('div').classes(
                                'metric-icon'
                            ):
                                ui.icon(
                                    item['icon']
                                ).classes(
                                    'text-xl'
                                )

                            ui.badge(
                                item['priority']
                            ).style(
                                f"background:"
                                f"{PRIORITY_COLORS[item['priority']]};"
                                f"color:white;"
                            )

                        ui.button(
                            icon='open_in_new',
                            on_click=lambda route=item['route']: (
                                open_details(route)
                            ),
                        ).props(
                            'flat round dense'
                        ).tooltip(
                            'Open details'
                        )

                    ui.label(
                        item['title']
                    ).classes(
                        'text-lg font-bold mt-4'
                    )

                    ui.label(
                        item['impact']
                    ).classes(
                        'text-sm font-semibold text-negative mt-1'
                    )

                    ui.separator().classes(
                        'my-4'
                    )

                    ui.label(
                        'ACTION'
                    ).classes(
                        'text-[10px] font-bold tracking-[0.14em] muted'
                    )

                    ui.label(
                        item['action']
                    ).classes(
                        'text-sm font-semibold mt-1'
                    )

                    refs['status_labels'][
                        item['id']
                    ] = ui.label(
                        'Awaiting decision'
                    ).classes(
                        'text-xs muted mt-3'
                    )

                    refs['action_buttons'][
                        item['id']
                    ] = ui.button(
                        item['button'],
                        icon='check',
                        on_click=lambda action_id=item['id']: (
                            approve_action(action_id)
                        ),
                    ).props(
                        'unelevated no-caps'
                    ).classes(
                        'w-full rounded-xl mt-4'
                    )

        ui.label(
            'Prototype only · Financial values and actions are simulated.'
        ).classes(
            'text-[11px] muted pb-3'
        )
