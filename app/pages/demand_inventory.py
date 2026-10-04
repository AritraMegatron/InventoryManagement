from __future__ import annotations
from copy import deepcopy

import asyncio
from typing import Any

from nicegui import app, ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS
from app.session_ui import require_brand_login, render_brand_session_controls

from app.services.demand_inventory_service import (
    build_dashboard_snapshot,
    build_inventory_planning_data,
    build_plan_summary,
    default_demand_selection,
    ensure_usable_stock,
    format_demand_money,
    get_demand_outlet,
    get_demand_regions,
    outlets_for_region,
)
from app.services.ingredient_planning_service import build_ingredient_equivalent_rows
from app.services.workflow_persistence_service import (
    approve_replenishment_plan,
    clear_demand_action_workflow,
    clear_generated_replenishment_plan,
    ensure_demand_inventory_workspace,
    save_generated_replenishment_plan,
    save_inventory_rows,
)
from app.state.demo_state import get_brand_state
from app.theme import (
    BURGUNDY,
    GOLD,
    MUTED,
    RED,
    apply_theme,
)



INVENTORY_COLUMNS = [
    {
        'name': 'product',
        'label': 'Product',
        'field': 'product',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'forecast',
        'label': 'Forecast demand',
        'field': 'forecast',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'on_hand',
        'label': 'On hand',
        'field': 'on_hand',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'safety_stock',
        'label': 'Safety stock',
        'field': 'safety_stock',
        'align': 'right',
    },
    {
        'name': 'coverage',
        'label': 'Coverage',
        'field': 'coverage',
        'align': 'right',
    },
    {
        'name': 'status',
        'label': 'Risk status',
        'field': 'status',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'action',
        'label': 'Recommended action',
        'field': 'action',
        'align': 'left',
    },
    {
        'name': 'action_taken',
        'label': 'Action taken',
        'field': 'action_taken',
        'align': 'left',
    },
]


PLAN_COLUMNS = [
    {
        'name': 'plan',
        'label': 'Plan',
        'field': 'plan',
        'align': 'left',
    },
    {
        'name': 'scope',
        'label': 'Scope',
        'field': 'scope',
        'align': 'left',
    },
    {
        'name': 'source_summary',
        'label': 'Source',
        'field': 'source_summary',
        'align': 'left',
    },
    {
        'name': 'expected_completion',
        'label': 'Expected completion',
        'field': 'expected_completion',
        'align': 'left',
    },
    {
        'name': 'cost',
        'label': 'Cost',
        'field': 'cost',
        'align': 'right',
    },
    {
        'name': 'status',
        'label': 'Status',
        'field': 'status',
        'align': 'left',
    },
]


def _forecast_chart_options(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        'animationDuration': 650,
        'tooltip': {
            'trigger': 'axis',
        },
        'legend': {
            'data': [
                'Actual demand',
                'AI forecast',
                'Upper bound',
                'Lower bound',
            ],
            'bottom': 0,
            'textStyle': {
                'color': MUTED,
                'fontSize': 11,
            },
        },
        'grid': {
            'left': 48,
            'right': 24,
            'top': 34,
            'bottom': 58,
        },
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': snapshot['categories'],
            'axisLine': {
                'lineStyle': {
                    'color': '#D8CED2',
                },
            },
            'axisLabel': {
                'color': MUTED,
                'fontSize': 11,
            },
        },
        'yAxis': {
            'type': 'value',
            'name': 'Units / day',
            'nameTextStyle': {
                'color': MUTED,
                'fontSize': 11,
            },
            'splitLine': {
                'lineStyle': {
                    'color': '#EEE7E8',
                },
            },
            'axisLabel': {
                'color': MUTED,
                'fontSize': 11,
            },
        },
        'series': [
            {
                'name': 'Actual demand',
                'type': 'line',
                'data': snapshot['actual'],
                'smooth': True,
                'symbolSize': 7,
                'lineStyle': {
                    'width': 3,
                    'color': BURGUNDY,
                },
                'itemStyle': {
                    'color': BURGUNDY,
                },
            },
            {
                'name': 'AI forecast',
                'type': 'line',
                'data': snapshot['forecast'],
                'smooth': True,
                'symbolSize': 7,
                'lineStyle': {
                    'width': 3,
                    'type': 'dashed',
                    'color': GOLD,
                },
                'itemStyle': {
                    'color': GOLD,
                },
                'areaStyle': {
                    'color': 'rgba(242,181,68,0.10)',
                },
            },
            {
                'name': 'Upper bound',
                'type': 'line',
                'data': snapshot['upper'],
                'smooth': True,
                'symbol': 'none',
                'lineStyle': {
                    'width': 1,
                    'type': 'dotted',
                    'color': '#C8A24D',
                },
            },
            {
                'name': 'Lower bound',
                'type': 'line',
                'data': snapshot['lower'],
                'smooth': True,
                'symbol': 'none',
                'lineStyle': {
                    'width': 1,
                    'type': 'dotted',
                    'color': '#C8A24D',
                },
            },
        ],
    }



def _risk_chart_options(
    planning_data: dict[str, Any],
) -> dict[str, Any]:
    rows = planning_data['inventory_rows']
    horizon = planning_data['horizon']

    products = [
        row['product']
        for row in rows
    ]

    forecast = [
        row['forecast']
        for row in rows
    ]

    usable_stock = [
        row.get(
            'usable_stock',
            max(0, int(row['on_hand']) - int(row['safety_stock'])),
        )
        for row in rows
    ]

    return {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow',
            },
        },
        'legend': {
            'data': [
                f'Next {horizon} days demand',
                'Usable stock',
            ],
            'bottom': 0,
            'textStyle': {
                'color': MUTED,
                'fontSize': 11,
            },
        },
        'grid': {
            'left': 150,
            'right': 24,
            'top': 16,
            'bottom': 54,
        },
        'xAxis': {
            'type': 'value',
            'splitLine': {
                'lineStyle': {
                    'color': '#EEE7E8',
                },
            },
            'axisLabel': {
                'color': MUTED,
                'fontSize': 10,
            },
        },
        'yAxis': {
            'type': 'category',
            'data': products,
            'axisLabel': {
                'color': MUTED,
                'fontSize': 10,
                'width': 130,
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
                'name': f'Next {horizon} days demand',
                'type': 'bar',
                'data': forecast,
                'barWidth': 9,
                'itemStyle': {
                    'color': BURGUNDY,
                    'borderRadius': [0, 5, 5, 0],
                },
            },
            {
                'name': 'Usable stock',
                'type': 'bar',
                'data': usable_stock,
                'barWidth': 9,
                'itemStyle': {
                    'color': GOLD,
                    'borderRadius': [0, 5, 5, 0],
                },
            },
        ],
    }


def _ingredient_chart_options(rows: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    # Each category states its unit: litres, kilograms, or packaging count.
    options = _risk_chart_options({'horizon': horizon, 'inventory_rows': [
        {'product': f"{r['ingredient']} ({r['unit']})", 'forecast': r['demand_equivalent'],
         'on_hand': r['usable_stock_equivalent'], 'safety_stock': 0,
         'usable_stock': r['usable_stock_equivalent']}
        for r in rows
    ]})
    demand_label = f'Next {horizon} days demand'
    options['legend']['data'] = [demand_label, 'Usable stock equivalent']
    options['series'][0]['name'] = demand_label
    options['series'][1]['name'] = 'Usable stock equivalent'
    options['grid']['left'] = 185
    options['yAxis']['axisLabel']['width'] = 170
    return options


def _replace_echart_options(
    chart: Any,
    new_options: dict[str, Any],
) -> None:
    """Update an EChart without assigning its read-only options property."""

    chart.options.clear()
    chart.options.update(new_options)
    chart.update()


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
                active=True,
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
            render_brand_session_controls()

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




@ui.page('/demand-inventory')
def demand_inventory_page() -> None:
    profile = require_brand_login()
    if profile is None:
        return

    brand_state = get_brand_state(
        app.storage.user,
        profile['brand_id'],
    )
    regions = get_demand_regions(brand_state)
    default_region, default_outlet_id = default_demand_selection(brand_state)
    workflow_state = ensure_demand_inventory_workspace(
        brand_state,
        default_region=default_region,
        default_outlet_id=default_outlet_id,
    )

    persisted_region = str(workflow_state.get('region', default_region))
    if persisted_region not in regions:
        persisted_region = default_region

    persisted_outlet_options = outlets_for_region(brand_state, persisted_region)
    persisted_outlet_id = str(workflow_state.get('outlet_id', default_outlet_id))
    if persisted_outlet_id not in persisted_outlet_options:
        persisted_outlet_id = next(iter(persisted_outlet_options))

    workflow_state['region'] = persisted_region
    workflow_state['outlet_id'] = persisted_outlet_id

    apply_theme()
    ui.add_css("""
        .vesper-view-switch .q-toggle__inner {
            width: 54px;
            height: 32px;
            min-width: 54px;
            padding: 0;
        }
        .vesper-view-switch .q-toggle__track {
            position: absolute;
            top: 3px;
            left: 0;
            width: 54px;
            height: 26px;
            border-radius: 6px;
            background: #eee5e8;
            border: 1px solid #cdb9c1;
            opacity: 1;
            box-shadow: inset 0 1px 3px rgba(59, 13, 34, .12);
            transition: background .2s ease, border-color .2s ease;
        }
        .vesper-view-switch .q-toggle__thumb {
            top: 7px;
            left: 4px;
            width: 18px;
            height: 18px;
            transition: left .2s ease;
        }
        .vesper-view-switch .q-toggle__thumb:after {
            border-radius: 4px;
            background: linear-gradient(145deg, #f5dba3, #c69b43);
            box-shadow: 0 1px 4px rgba(59, 13, 34, .28);
        }
        .vesper-view-switch .q-toggle__thumb:before {
            display: none;
        }
        .vesper-view-switch .q-toggle__inner--truthy .q-toggle__track {
            background: #5a1534;
            border-color: #5a1534;
        }
        .vesper-view-switch .q-toggle__inner--truthy .q-toggle__thumb {
            left: 32px;
        }
        .vesper-view-switch:focus-visible {
            outline: 2px solid #c69b43;
            outline-offset: 4px;
            border-radius: 6px;
        }
        @media (prefers-reduced-motion: reduce) {
            .vesper-view-switch .q-toggle__thumb,
            .vesper-view-switch .q-toggle__track { transition: none; }
        }
    """)
    ai_chat = create_ai_chat(
        page_name='Demand & Inventory',
        page_context=PAGE_CONTEXTS['demand_inventory'],
    )
    _render_shell(ai_chat)


    state: dict[str, Any] = {
        'region': persisted_region,
        'outlet_id': persisted_outlet_id,
        'horizon': int(workflow_state.get('forecast_horizon', 7)),
        'planning_horizon': int(workflow_state.get('planning_horizon', 7)),
        'forecast_run_number': int(workflow_state.get('forecast_run_number', 0)),
        'planning_run_number': int(workflow_state.get('planning_run_number', 0)),
        'inventory_built': bool(workflow_state.get('inventory_built', False)),
        'plan_generated': bool(workflow_state.get('plan_generated', False)),
        'plan_approved': bool(workflow_state.get('plan_approved', False)),
        'loaded': bool(workflow_state.get('forecast_loaded', False)),
        'selection_version': 0,
        'ingredient_view': False,
        'selected_inventory_row_id': None,
    }

    snapshot = build_dashboard_snapshot(
        brand_state=brand_state,
        outlet_id=state['outlet_id'],
        horizon=state['horizon'],
        run_number=state['forecast_run_number'],
    )

    planning_data = ensure_usable_stock(
        build_inventory_planning_data(
            brand_state=brand_state,
            outlet_id=state['outlet_id'],
            horizon=state['planning_horizon'],
            run_number=state['planning_run_number'],
        )
    )

    state['signal_labels'] = {
        signal['label']
        for signal in snapshot['signals']
    }

    refs: dict[str, Any] = {}

    def create_snapshot(
        outlet_id: str,
        horizon: int,
        run_number: int,
    ) -> dict[str, Any]:
        """Read the stable forecast snapshot for this outlet and horizon."""

        new_snapshot = build_dashboard_snapshot(
            brand_state=brand_state,
            outlet_id=outlet_id,
            horizon=horizon,
            run_number=run_number,
            excluded_signal_labels=state.get(
                'signal_labels',
                set(),
            ),
        )

        state['signal_labels'] = {
            signal['label']
            for signal in new_snapshot['signals']
        }

        return new_snapshot

    def render_demand_signals(
        signals: list[dict[str, Any]],
    ) -> None:
        """Rebuild the demand-signal cards, including icons and percentages."""

        signal_grid = refs.get('signal_grid')

        if signal_grid is None:
            return

        signal_grid.clear()

        with signal_grid:
            for signal in signals:
                impact_pct = signal.get(
                    'impact_pct',
                    0,
                )

                if impact_pct >= 0:
                    impact_classes = (
                        'text-xs font-semibold text-positive'
                    )
                else:
                    impact_classes = (
                        'text-xs font-semibold text-negative'
                    )

                with ui.card().classes(
                    'p-4 border border-[#eee4e8] '
                    'rounded-2xl shadow-none'
                ):
                    with ui.row().classes(
                        'items-center gap-3 no-wrap'
                    ):
                        with ui.element('div').classes(
                            'metric-icon'
                        ):
                            ui.icon(
                                signal['icon']
                            ).classes(
                                'text-lg'
                            )

                        with ui.column().classes('gap-0'):
                            ui.label(
                                signal['label']
                            ).classes(
                                'text-sm font-bold'
                            )

                            ui.label(
                                signal['detail']
                            ).classes(
                                impact_classes
                            )


    def render_inventory_risks(
        risks: list[dict[str, Any]],
    ) -> None:
        risk_queue = refs.get('risk_queue')

        if risk_queue is None:
            return

        risk_queue.clear()

        with risk_queue:
            if not risks:
                ui.label(
                    'No inventory exceptions for the selected planning horizon.'
                ).classes(
                    'text-sm muted'
                )
                return

            for risk in risks[:4]:
                if risk['severity'] == 'High':
                    color = RED
                elif risk['severity'] == 'Medium':
                    color = GOLD
                else:
                    color = '#2E8B57'

                with ui.card().classes(
                    'w-full p-3 rounded-xl '
                    'shadow-none border '
                    'border-[#eee4e8]'
                ):
                    with ui.row().classes(
                        'w-full justify-between '
                        'items-start no-wrap'
                    ):
                        with ui.column().classes(
                            'gap-0'
                        ):
                            ui.label(
                                risk['product']
                            ).classes(
                                'text-sm font-bold'
                            )

                            ui.label(
                                risk['detail']
                            ).classes(
                                'text-xs muted '
                                'leading-relaxed'
                            )

                        ui.badge(
                            risk['severity']
                        ).style(
                            f'background:{color};'
                            f'color:white;'
                        )

    def clear_action_workflow() -> None:
        clear_demand_action_workflow(brand_state)
        state['inventory_built'] = False
        state['plan_generated'] = False
        state['plan_approved'] = False
        state['selected_inventory_row_id'] = None

        refs['inventory_table'].rows = []
        refs['inventory_table'].update()

        refs['inventory_status'].set_text(
            'Build the action plan to load the latest inventory position.'
        )

        refs['plan_table'].rows = []
        refs['plan_table'].update()

        refs['plan_status'].set_text(
            'No plan generated'
        )

        refs['generate_plan_button'].disable()
        refs['approve_button'].disable()

    def clear_chart(chart_key: str) -> None:
        options = deepcopy(refs[chart_key].options)
        for series in options.get('series', []):
            series['data'] = []
        for axis in ('xAxis', 'yAxis'):
            if isinstance(options.get(axis), dict) and options[axis].get('type') == 'category':
                options[axis]['data'] = []
        _replace_echart_options(refs[chart_key], options)

    def blank_dashboard() -> None:
        state['loaded'] = False
        workflow_state['forecast_loaded'] = False
        state['selection_version'] += 1
        clear_action_workflow()
        for key in ('predicted_units', 'expected_revenue', 'service_level', 'risk_count',
                    'avoidable_waste', 'rec_impact', 'rec_waste', 'rec_priority'):
            refs[key].set_text('—')
        refs['rec_headline'].set_text('Run AI forecast to load this outlet')
        refs['rec_body'].set_text('')
        refs['last_run'].set_text('Waiting for forecast')
        refs['planning_subtitle'].set_text('Run AI forecast to load availability')
        clear_chart('forecast_chart')
        clear_chart('risk_chart')
        render_demand_signals([])
        render_inventory_risks([])
        refs['build_action_button'].disable()
        refs['emergency_transfer_button'].disable()
        for key in ('action_dialog', 'approve_dialog', 'transfer_dialog', 'plan_detail_dialog'):
            refs[key].close()

    def refresh_availability_chart() -> None:
        if not state['loaded']:
            clear_chart('risk_chart')
            return
        ingredient_view = state['ingredient_view']
        ingredients = build_ingredient_equivalent_rows(
            brand_state, planning_data['inventory_rows'],
        )
        options = (_ingredient_chart_options(ingredients, state['planning_horizon'])
                   if ingredient_view else _risk_chart_options(planning_data))
        height = max(360, len(ingredients) * 42 + 100) if ingredient_view else 360
        refs['risk_chart'].style(f'height: {height}px; min-height: {height}px')
        _replace_echart_options(refs['risk_chart'], options)
        refs['availability_title'].set_text(
            'Ingredient availability vs demand' if ingredient_view
            else 'Product availability vs demand')
        refs['planning_subtitle'].set_text(
            f"Next {state['planning_horizon']} days · BOM equivalents of item demand and usable stock"
            if ingredient_view else
            f"Next {state['planning_horizon']} days demand compared with current usable stock")

    def toggle_availability(event: Any) -> None:
        state['ingredient_view'] = bool(event.value)
        refresh_availability_chart()

    def update_planning_view() -> None:
        nonlocal planning_data

        planning_data = ensure_usable_stock(
            build_inventory_planning_data(
                brand_state=brand_state,
                outlet_id=state['outlet_id'],
                horizon=state['planning_horizon'],
                run_number=state['planning_run_number'],
            )
        )

        _replace_echart_options(
            refs['risk_chart'],
            _risk_chart_options(planning_data),
        )

        refs['planning_subtitle'].set_text(
            f"Next {planning_data['horizon']} days demand "
            f"compared with current usable stock"
        )

        refs['inventory_horizon_badge'].set_text(
            f"NEXT {planning_data['horizon']} DAYS"
        )

        recommendation = planning_data['recommendation']

        refs['rec_priority'].set_text(
            f"{recommendation['priority'].upper()} PRIORITY"
        )
        refs['rec_headline'].set_text(
            recommendation['headline']
        )
        refs['rec_body'].set_text(
            recommendation['body']
        )
        refs['rec_impact'].set_text(
            recommendation['impact']
        )
        refs['rec_waste'].set_text(
            recommendation['waste']
        )

        refs['service_level'].set_text(
            f"{planning_data['service_level']:.1f}%"
        )
        refs['risk_count'].set_text(
            str(planning_data['at_risk_count'])
        )
        refs['avoidable_waste'].set_text(
            format_demand_money(
                planning_data['avoidable_waste'],
                profile,
            )
        )

        render_inventory_risks(
            planning_data['risks']
        )

        clear_action_workflow()
        refresh_availability_chart()

    async def run_forecast() -> None:
        token = state['selection_version']
        outlet_id = state['outlet_id']
        refs['run_button'].disable()
        progress = ui.notification('Loading outlet forecast…', spinner=True,
            type='ongoing', timeout=None, position='top')
        try:
            await asyncio.sleep(0.85)
            if token != state['selection_version'] or outlet_id != state['outlet_id']:
                return
            new_snapshot = create_snapshot(outlet_id, state['horizon'], 0)
            state['loaded'] = True
            workflow_state['forecast_loaded'] = True
            apply_snapshot(new_snapshot)
            update_planning_view()
            refs['build_action_button'].enable()
            refs['emergency_transfer_button'].enable()
            ui.notify(f"Forecast loaded for {new_snapshot['outlet'].name}", type='positive')
        finally:
            progress.dismiss()
            refs['run_button'].enable()

    def apply_snapshot(
        new_snapshot: dict[str, Any],
    ) -> None:
        nonlocal snapshot

        snapshot = new_snapshot

        outlet = snapshot['outlet']
        kpis = snapshot['kpis']

        refs['context'].set_text(
            f"{outlet.city} · "
            f"{outlet.outlet_format} · "
            f"{outlet.delivery_share}% delivery mix"
        )

        refs['last_run'].set_text(
            f"Updated just now · "
            f"{kpis['confidence']:.1f}% model confidence"
        )

        refs['predicted_units'].set_text(
            f"{kpis['predicted_units']:,}"
        )

        refs['predicted_units_sub'].set_text(
            f"Next {snapshot['horizon']} days"
        )

        refs['expected_revenue'].set_text(
            format_demand_money(
                kpis['expected_revenue'],
                profile,
            )
        )

        refs['expected_revenue_sub'].set_text(
            'Forecast gross sales'
        )

        _replace_echart_options(
            refs['forecast_chart'],
            _forecast_chart_options(snapshot),
        )

        render_demand_signals(
            snapshot['signals']
        )


    def clear_demand_forecast_chart() -> None:
        """Clear only the plotted demand series while keeping the card intact."""

        cleared_options = deepcopy(
            refs['forecast_chart'].options
        )

        for series in cleared_options.get(
            'series',
            [],
        ):
            series['data'] = []

        _replace_echart_options(
            refs['forecast_chart'],
            cleared_options,
        )

        ui.notify(
            'Demand forecast chart cleared',
            type='info',
            icon='delete_sweep',
            position='top',
        )

    def on_region_change(
        event: Any,
    ) -> None:
        state['region'] = event.value
        workflow_state['region'] = state['region']

        options = outlets_for_region(
            brand_state,
            state['region'],
        )

        refs['outlet_select'].options = options

        if state['outlet_id'] not in options:
            state['outlet_id'] = next(
                iter(options)
            )

            refs['outlet_select'].value = (
                state['outlet_id']
            )

        refs['outlet_select'].update()

        on_outlet_change_value(
            state['outlet_id']
        )

    def on_outlet_change(
        event: Any,
    ) -> None:
        on_outlet_change_value(
            event.value
        )

    def on_outlet_change_value(
        outlet_id: str,
    ) -> None:
        state['outlet_id'] = outlet_id
        workflow_state['outlet_id'] = outlet_id

        outlet = get_demand_outlet(brand_state, outlet_id)
        refs['context'].set_text(f'{outlet.city} · {outlet.outlet_format} · {outlet.delivery_share}% delivery mix')
        blank_dashboard()

    def on_horizon_change(event: Any) -> None:
        state['horizon'] = int(event.value)
        workflow_state['forecast_horizon'] = state['horizon']
        if state['loaded']:
            apply_snapshot(create_snapshot(state['outlet_id'], state['horizon'], 0))

    def on_planning_horizon_change(event: Any) -> None:
        state['planning_horizon'] = int(event.value)
        workflow_state['planning_horizon'] = state['planning_horizon']
        if state['loaded']:
            # Invalidates an in-flight build/generation for the previous horizon.
            state['selection_version'] += 1
            update_planning_view()
            refs['build_action_button'].enable()

    async def build_action_plan() -> None:
        if not state['loaded']:
            return
        token = state['selection_version']
        refs['build_action_button'].disable()

        progress = ui.notification(
            'Loading the latest inventory position…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(0.45)
        if token != state['selection_version'] or not state['loaded']:
            progress.dismiss()
            return

        rows = deepcopy(
            planning_data['inventory_rows']
        )

        for row in rows:
            quantity = max(0, int(row['forecast']) - int(row['on_hand']))
            row['action_type'] = 'Order' if quantity else ''
            row['action_quantity'] = quantity
            row['action_taken'] = f'Produce {quantity} units · net ingredient procurement' if quantity else 'No action'
        refs['inventory_table'].rows = rows
        refs['inventory_table'].update()

        save_inventory_rows(brand_state, rows)
        clear_generated_replenishment_plan(brand_state)
        refresh_availability_chart()
        state['inventory_built'] = True
        state['plan_generated'] = False
        state['plan_approved'] = False

        refs['inventory_status'].set_text(
            f"{len(rows)} products loaded for the next "
            f"{state['planning_horizon']} days. "
            f"Production quantities prefilled; click a row to adjust or transfer."
        )

        refs['plan_table'].rows = []
        refs['plan_table'].update()
        refs['plan_status'].set_text(
            'No plan generated'
        )
        refs['generate_plan_button'].enable()
        refs['approve_button'].disable()
        refs['build_action_button'].enable()

        progress.dismiss()

        ui.notify(
            'Latest outlet inventory position loaded',
            type='positive',
            icon='inventory_2',
            position='top',
        )

    def _event_row_id(
        event: Any,
    ) -> int | str | None:
        arguments = (
            event.args
            if isinstance(event.args, list)
            else [event.args]
        )

        for argument in arguments:
            if (
                isinstance(argument, dict)
                and argument.get('id') is not None
            ):
                return argument['id']

        return None

    def _selected_inventory_row() -> dict[str, Any] | None:
        selected_id = state.get(
            'selected_inventory_row_id'
        )

        return next(
            (
                row
                for row in refs['inventory_table'].rows
                if row['id'] == selected_id
            ),
            None,
        )

    def update_action_controls(
        _: Any = None,
    ) -> None:
        row = _selected_inventory_row()

        if row is None:
            return

        mode = refs['action_mode'].value
        transfer_visible = mode == 'Transfer'

        refs['transfer_action_fields'].set_visibility(
            transfer_visible
        )

        if transfer_visible:
            options = row.get(
                'transfer_options',
                {},
            )

            refs['action_source'].options = list(
                options.keys()
            )

            if (
                refs['action_source'].value
                not in options
            ):
                refs['action_source'].value = next(
                    iter(options),
                    None,
                )

            refs['action_source'].update()
            update_transfer_capacity()
        else:
            refs['action_quantity'].max = 5000
            refs['safe_transfer_label'].set_text(
                ''
            )

    def update_transfer_capacity(
        _: Any = None,
    ) -> None:
        row = _selected_inventory_row()

        if row is None:
            return

        source = refs['action_source'].value
        safe_quantity = int(
            row.get(
                'transfer_options',
                {},
            ).get(
                source,
                0,
            )
        )

        refs['safe_transfer_label'].set_text(
            f'{safe_quantity} units can be safely transferred '
            f'from {source}.'
            if source
            else 'Select a source outlet.'
        )

        refs['action_quantity'].max = safe_quantity

        current_quantity = int(
            refs['action_quantity'].value
            or 0
        )

        if current_quantity > safe_quantity:
            refs['action_quantity'].value = (
                safe_quantity
            )
            refs['action_quantity'].update()

    def open_inventory_action_dialog(
        event: Any,
    ) -> None:
        row_id = _event_row_id(
            event
        )

        if row_id is None:
            return

        state['selected_inventory_row_id'] = (
            row_id
        )

        row = _selected_inventory_row()

        if row is None:
            return

        refs['action_product'].set_text(
            row['product']
        )
        refs['action_recommendation'].set_text(
            row['action']
        )

        mode = (
            row.get('action_type')
            or row.get('recommended_mode')
            or 'Order'
        )

        refs['action_mode'].value = mode
        refs['action_quantity'].value = int(
            row.get('action_quantity', max(0, int(row['forecast']) - int(row['on_hand'])))
        )

        source_options = row.get(
            'transfer_options',
            {},
        )

        refs['action_source'].options = list(
            source_options.keys()
        )
        refs['action_source'].value = (
            row.get('transfer_source')
            or next(
                iter(source_options),
                None,
            )
        )

        refs['action_mode'].update()
        refs['action_quantity'].update()
        refs['action_source'].update()

        update_action_controls()
        refs['action_dialog'].open()

    def save_inventory_action() -> None:
        row = _selected_inventory_row()

        if row is None:
            return

        mode = refs['action_mode'].value
        quantity = int(
            refs['action_quantity'].value
            or 0
        )

        if quantity <= 0:
            row['action_type'] = ''
            row['action_quantity'] = 0
            row['transfer_source'] = ''
            row['action_taken'] = 'No action'
        elif mode == 'Order':
            row['action_type'] = 'Order'
            row['action_quantity'] = quantity
            row['transfer_source'] = ''
            row['action_taken'] = (
                f'Produce {quantity} units · net ingredient procurement'
            )
        else:
            source = refs['action_source'].value
            safe_quantity = int(
                row.get(
                    'transfer_options',
                    {},
                ).get(
                    source,
                    0,
                )
            )

            if not source:
                ui.notify(
                    'Select a source outlet.',
                    type='warning',
                )
                return

            if quantity > safe_quantity:
                ui.notify(
                    f'Only {safe_quantity} units can be safely '
                    f'transferred from {source}.',
                    type='warning',
                )
                return

            row['action_type'] = 'Transfer'
            row['action_quantity'] = quantity
            row['transfer_source'] = source
            row['action_taken'] = (
                f'Transfer {quantity} units from {source}'
            )

        row['production_override'] = mode == 'Order' or quantity <= 0
        refs['inventory_table'].update()
        refs['action_dialog'].close()

        save_inventory_rows(brand_state, refs['inventory_table'].rows)
        refresh_availability_chart()
        clear_generated_replenishment_plan(brand_state)
        state['plan_generated'] = False
        state['plan_approved'] = False

        refs['plan_table'].rows = []
        refs['plan_table'].update()
        refs['plan_status'].set_text(
            'Actions changed · generate the plan again'
        )
        refs['approve_button'].disable()

        ui.notify(
            f"Action saved for {row['product']}",
            type='positive',
            position='top',
        )

    async def generate_replenishment_plan() -> None:
        if not state['loaded']:
            return
        token = state['selection_version']
        if not state['inventory_built']:
            ui.notify(
                'Build the action plan first.',
                type='warning',
            )
            return

        refs['generate_plan_button'].disable()

        progress = ui.notification(
            'Converting selected actions into purchase and transfer plans…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(0.55)
        if token != state['selection_version'] or not state['loaded']:
            progress.dismiss()
            return

        plan_rows = build_plan_summary(
            brand_state=brand_state,
            outlet_id=state['outlet_id'],
            inventory_rows=refs['inventory_table'].rows,
        )

        refs['plan_table'].rows = plan_rows
        refs['plan_table'].update()

        ready_count = sum(
            1
            for row in plan_rows
            if row['status'] == 'Ready for approval'
        )

        state['plan_generated'] = ready_count > 0
        state['plan_approved'] = False
        save_generated_replenishment_plan(
            brand_state,
            outlet_id=state['outlet_id'],
            plan_rows=plan_rows,
        )

        total_plan_cost = sum(
            float(row.get('total_cost_value', 0))
            for row in plan_rows
            if row['status'] == 'Ready for approval'
        )

        plan_word = (
            'plan'
            if ready_count == 1
            else 'plans'
        )

        refs['plan_status'].set_text(
            (
                f'{ready_count} coordinated {plan_word} · '
                f'{format_demand_money(total_plan_cost, profile)} total cost · '
                f'click a row for details'
                if ready_count
                else 'No procurement or transfer actions were selected'
            )
        )

        if ready_count:
            refs['approve_button'].enable()
        else:
            refs['approve_button'].disable()

        refs['generate_plan_button'].enable()
        progress.dismiss()

        ui.notify(
            'Purchase and transfer plans generated',
            type='positive',
            icon='route',
            position='top',
        )


    def open_plan_detail_dialog(
        event: Any,
    ) -> None:
        row_id = _event_row_id(
            event
        )
    
        plan_row = next(
            (
                row
                for row in refs['plan_table'].rows
                if row['id'] == row_id
            ),
            None,
        )
    
        if plan_row is None:
            return
    
        document_type = (
            'PURCHASE ORDER'
            if plan_row['plan_type'] == 'purchase'
            else 'STOCK TRANSFER NOTE'
        )
    
        refs['plan_detail_title'].set_text(
            document_type.title()
        )
        refs['plan_detail_summary'].set_text(
            f"{plan_row['document_number']} · "
            f"{plan_row['status']}"
        )
    
        body = refs['plan_detail_body']
        body.clear()
    
        with body:
            details = plan_row.get(
                'details',
                [],
            )
    
            if not details:
                ui.label(
                    'No actions were selected for this plan.'
                ).classes(
                    'text-sm muted py-4'
                )
            else:
                with ui.card().classes(
                    'w-full p-5 rounded-xl shadow-none '
                    'border border-[#ded4d8] bg-[#fffdf9]'
                ):
                    with ui.row().classes(
                        'w-full items-start justify-between gap-5'
                    ):
                        with ui.column().classes(
                            'gap-1 max-w-[62%]'
                        ):
                            ui.label(
                                plan_row['company_name']
                            ).classes(
                                'text-xl font-extrabold text-primary'
                            )
    
                            ui.label(
                                plan_row['company_address']
                            ).classes(
                                'text-xs muted leading-relaxed'
                            )
    
                            ui.label(
                                plan_row['company_phone']
                            ).classes(
                                'text-xs font-semibold'
                            )
    
                        with ui.column().classes(
                            'items-end gap-1'
                        ):
                            ui.label(
                                document_type
                            ).classes(
                                'text-lg font-black tracking-[0.12em]'
                            )
    
                            ui.label(
                                plan_row['document_number']
                            ).classes(
                                'text-sm font-bold'
                            )
    
                            ui.label(
                                f"Issue date: {plan_row['document_date']}"
                            ).classes(
                                'text-xs muted'
                            )
    
                            ui.badge(
                                plan_row['status'],
                                color=(
                                    'positive'
                                    if plan_row['status'] == 'Approved'
                                    else 'secondary'
                                ),
                            ).props(
                                'outline'
                            )
    
                    ui.separator().classes(
                        'my-4'
                    )
    
                    with ui.grid(
                        columns=2
                    ).classes(
                        'w-full gap-4 max-[700px]:grid-cols-1'
                    ):
                        with ui.card().classes(
                            'p-4 rounded-xl shadow-none '
                            'border border-[#eee4e8]'
                        ):
                            ui.label(
                                'DELIVER TO'
                            ).classes(
                                'text-[10px] font-bold tracking-wider muted'
                            )
    
                            ui.label(
                                plan_row['outlet_name']
                            ).classes(
                                'text-sm font-bold mt-1'
                            )
    
                            ui.label(
                                plan_row['outlet_address']
                            ).classes(
                                'text-xs muted leading-relaxed'
                            )
    
                            ui.label(
                                plan_row['outlet_phone']
                            ).classes(
                                'text-xs font-semibold mt-1'
                            )
    
                        with ui.card().classes(
                            'p-4 rounded-xl shadow-none '
                            'border border-[#eee4e8]'
                        ):
                            ui.label(
                                'PROCUREMENT CONTACT'
                            ).classes(
                                'text-[10px] font-bold tracking-wider muted'
                            )
    
                            ui.label(
                                plan_row['manager_name']
                            ).classes(
                                'text-sm font-bold mt-1'
                            )
    
                            ui.label(
                                plan_row['manager_title']
                            ).classes(
                                'text-xs muted'
                            )
    
                            ui.label(
                                plan_row['manager_phone']
                            ).classes(
                                'text-xs font-semibold mt-1'
                            )
    
                    ui.label(
                        (
                            'Vendor purchase lines'
                            if plan_row['plan_type'] == 'purchase'
                            else 'Authorized store-transfer lines'
                        )
                    ).classes(
                        'text-sm font-bold mt-5'
                    )
    
                    if plan_row['plan_type'] == 'purchase':
                        columns = [
                            {
                                'name': 'vendor',
                                'label': 'Vendor',
                                'field': 'vendor',
                                'align': 'left',
                            },
                            {
                                'name': 'vendor_phone',
                                'label': 'Vendor phone',
                                'field': 'vendor_phone',
                                'align': 'left',
                            },
                            {
                                'name': 'item',
                                'label': 'Ingredient',
                                'field': 'item',
                                'align': 'left',
                            },
                            {'name': 'required_quantity', 'label': 'Required',
                             'field': 'required_quantity', 'align': 'right'},
                            {'name': 'on_hand_quantity', 'label': 'On hand',
                             'field': 'on_hand_quantity', 'align': 'right'},
                            {
                                'name': 'quantity',
                                'label': 'Order qty',
                                'field': 'quantity',
                                'align': 'right',
                            },
                            {
                                'name': 'unit',
                                'label': 'Unit',
                                'field': 'unit',
                                'align': 'left',
                            },
                            {
                                'name': 'cost',
                                'label': 'Amount',
                                'field': 'cost',
                                'align': 'right',
                            },
                        ]
                    else:
                        columns = [
                            {
                                'name': 'product',
                                'label': 'Product',
                                'field': 'product',
                                'align': 'left',
                            },
                            {
                                'name': 'source',
                                'label': 'Source outlet',
                                'field': 'source',
                                'align': 'left',
                            },
                            {
                                'name': 'quantity',
                                'label': 'Qty',
                                'field': 'quantity',
                                'align': 'right',
                            },
                            {
                                'name': 'driver',
                                'label': 'Driver',
                                'field': 'driver',
                                'align': 'left',
                            },
                            {
                                'name': 'driver_phone',
                                'label': 'Driver phone',
                                'field': 'driver_phone',
                                'align': 'left',
                            },
                            {
                                'name': 'vehicle',
                                'label': 'Vehicle',
                                'field': 'vehicle',
                                'align': 'left',
                            },
                            {
                                'name': 'eta',
                                'label': 'ETA',
                                'field': 'eta',
                                'align': 'left',
                            },
                            {
                                'name': 'cost',
                                'label': 'Amount',
                                'field': 'cost',
                                'align': 'right',
                            },
                        ]
    
                    ui.table(
                        columns=columns,
                        rows=details,
                        row_key='id',
                        pagination={
                            'rowsPerPage': 20,
                        },
                    ).props(
                        'flat bordered dense separator=horizontal '
                        'hide-pagination'
                    ).classes(
                        'w-full mt-2'
                    )
    
                    with ui.row().classes(
                        'w-full justify-end mt-4'
                    ):
                        with ui.card().classes(
                            'min-w-[260px] p-4 rounded-xl shadow-none '
                            'border border-[#ded4d8] bg-[#f8f2f4]'
                        ):
                            with ui.row().classes(
                                'w-full justify-between gap-8'
                            ):
                                ui.label(
                                    'TOTAL'
                                ).classes(
                                    'text-sm font-bold'
                                )
    
                                ui.label(
                                    plan_row['cost']
                                ).classes(
                                    'text-xl font-extrabold text-primary'
                                )
    
                    ui.label(
                        (
                            'Terms: Delivery quantities are subject to '
                            'receiving inspection and vendor invoice matching.'
                            if plan_row['plan_type'] == 'purchase'
                            else
                            'Terms: Driver must obtain source and destination '
                            'store acknowledgements before closing the trip.'
                        )
                    ).classes(
                        'text-[11px] muted mt-4'
                    )
    
                    ui.separator().classes(
                        'my-5'
                    )
    
                    ui.label(
                        'PROCUREMENT MANAGER AUTHORIZATION'
                    ).classes(
                        'text-[10px] font-bold tracking-wider muted'
                    )
    
                    with ui.grid(
                        columns=2
                    ).classes(
                        'w-full gap-8 mt-5 max-[700px]:grid-cols-1'
                    ):
                        with ui.column().classes(
                            'gap-1'
                        ):
                            ui.label(
                                plan_row['manager_name']
                            ).classes(
                                'text-sm font-bold'
                            )
    
                            ui.label(
                                plan_row['manager_title']
                            ).classes(
                                'text-xs muted'
                            )
    
                            ui.label(
                                plan_row['manager_phone']
                            ).classes(
                                'text-xs'
                            )
    
                        with ui.column().classes(
                            'gap-2'
                        ):
                            ui.element('div').style(
                                'height:34px;'
                                'border-bottom:1px solid #6b5960;'
                            )
    
                            ui.label(
                                'Authorized signature and date'
                            ).classes(
                                'text-[10px] muted'
                            )
    
        refs['plan_detail_dialog'].open()

    def open_approval_dialog() -> None:
        if not state['plan_generated']:
            ui.notify(
                'Generate a plan first.',
                type='warning',
            )
            return

        ready_rows = [
            row
            for row in refs['plan_table'].rows
            if row['status'] == 'Ready for approval'
        ]

        refs['approval_outlet'].set_text(
            snapshot['outlet'].name
        )

        refs['approval_actions'].set_text(
            f"{len(ready_rows)} plan groups will be released."
        )

        refs['approve_dialog'].open()

    def approve_plan() -> None:
        approved_rows = approve_replenishment_plan(brand_state)
        state['plan_approved'] = True
        state['plan_generated'] = bool(approved_rows)
        refs['plan_table'].rows = deepcopy(approved_rows)
        refs['plan_table'].update()

        refs['plan_status'].set_text(
            'Approved · Ingredients ordered (awaiting receipt); transfers awaiting dispatch'
        )

        refs['approve_dialog'].close()
        refs['approve_button'].disable()

        ui.notify(
            'Plan approved and tasks released',
            type='positive',
            icon='task_alt',
            position='top',
        )

    def open_transfer_dialog() -> None:
        if not state['loaded']:
            return
        high_risk = next(
            (
                risk
                for risk in planning_data['risks']
                if risk['severity'] == 'High'
            ),
            planning_data['primary_risk'],
        )

        refs['transfer_product'].set_text(
            high_risk['product']
        )

        refs['transfer_quantity'].value = max(
            10,
            int(
                high_risk['recommended_qty']
            ),
        )

        refs['transfer_dialog'].open()

    def confirm_transfer() -> None:
        quantity = int(
            refs['transfer_quantity'].value
            or 0
        )

        source = refs['transfer_source'].value

        refs['transfer_dialog'].close()

        ui.notify(
            f'{quantity} units reserved from '
            f'{source}; simulated ETA within 24 hours.',
            type='positive',
            icon='local_shipping',
            position='top',
        )


    with ui.dialog() as action_dialog:
        with ui.card().classes(
            'w-[560px] max-w-[94vw] '
            'p-6 rounded-2xl'
        ):
            refs['action_dialog'] = action_dialog

            ui.label(
                'Record inventory action'
            ).classes(
                'text-lg font-bold'
            )

            refs['action_product'] = ui.label(
                ''
            ).classes(
                'text-base font-bold mt-1'
            )

            refs['action_recommendation'] = ui.label(
                ''
            ).classes(
                'text-xs muted'
            )

            ui.separator().classes(
                'my-4'
            )

            refs['action_mode'] = ui.radio(
                ['Order', 'Transfer'],
                value='Order',
                on_change=update_action_controls,
            ).props(
                'inline'
            )

            refs['action_quantity'] = ui.number(
                label='Units',
                value=0,
                min=0,
                max=5000,
                step=1,
            ).props(
                'outlined dense'
            ).classes(
                'w-full mt-2'
            )

            refs['transfer_action_fields'] = ui.column().classes(
                'w-full gap-2'
            )

            with refs['transfer_action_fields']:
                refs['action_source'] = ui.select(
                    [],
                    label='Source outlet',
                    on_change=update_transfer_capacity,
                ).props(
                    'outlined dense'
                ).classes(
                    'w-full'
                )

                refs['safe_transfer_label'] = ui.label(
                    ''
                ).classes(
                    'text-xs muted'
                )

            with ui.row().classes(
                'w-full justify-end gap-2 mt-4'
            ):
                ui.button(
                    'Cancel',
                    on_click=action_dialog.close,
                ).props(
                    'flat no-caps'
                )

                ui.button(
                    'Save action',
                    icon='check',
                    on_click=save_inventory_action,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

    with ui.dialog() as plan_detail_dialog:
        with ui.card().classes(
            'w-[1120px] max-w-[97vw] '
            'p-6 rounded-2xl'
        ):
            refs['plan_detail_dialog'] = (
                plan_detail_dialog
            )

            refs['plan_detail_title'] = ui.label(
                ''
            ).classes(
                'text-lg font-bold'
            )

            refs['plan_detail_summary'] = ui.label(
                ''
            ).classes(
                'text-sm muted'
            )

            ui.separator().classes(
                'my-3'
            )

            refs['plan_detail_body'] = ui.column().classes(
                'w-full gap-3'
            )

            with ui.row().classes(
                'w-full justify-end mt-4'
            ):
                ui.button(
                    'Close',
                    on_click=plan_detail_dialog.close,
                ).props(
                    'flat no-caps'
                )

    with ui.dialog() as approve_dialog:
        with ui.card().classes(
            'w-[520px] max-w-[92vw] '
            'p-6 rounded-2xl'
        ):
            refs['approve_dialog'] = (
                approve_dialog
            )

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

                with ui.column().classes(
                    'gap-0'
                ):
                    ui.label(
                        'Approve replenishment plan'
                    ).classes(
                        'text-lg font-bold'
                    )

                    refs['approval_outlet'] = ui.label(
                        ''
                    ).classes(
                        'text-sm muted'
                    )

            ui.separator().classes(
                'my-3'
            )

            refs['approval_actions'] = ui.label(
                ''
            ).classes(
                'text-sm'
            )

            ui.label(
                'Approval releases the simulated purchase orders '
                'and store-transfer dispatch tasks.'
            ).classes(
                'text-xs muted'
            )

            with ui.row().classes(
                'w-full justify-end gap-2 mt-4'
            ):
                ui.button(
                    'Cancel',
                    on_click=approve_dialog.close,
                ).props(
                    'flat no-caps'
                )

                ui.button(
                    'Approve & release',
                    icon='check',
                    on_click=approve_plan,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

    with ui.dialog() as transfer_dialog:
        with ui.card().classes(
            'w-[520px] max-w-[92vw] '
            'p-6 rounded-2xl'
        ):
            refs['transfer_dialog'] = (
                transfer_dialog
            )

            ui.label(
                'Simulate emergency stock transfer'
            ).classes(
                'text-lg font-bold'
            )

            ui.label(
                'Reserve inventory from a nearby outlet '
                'without changing any real system.'
            ).classes(
                'text-sm muted'
            )

            ui.separator().classes(
                'my-3'
            )

            ui.label(
                'At-risk product'
            ).classes(
                'text-xs font-semibold muted'
            )

            refs['transfer_product'] = ui.label(
                ''
            ).classes(
                'text-base font-bold'
            )

            refs['transfer_source'] = ui.select(
                [
                    'Select Citywalk',
                    'Connaught Place',
                    'Cyber Hub',
                    'Ambience Mall',
                ],
                value='Select Citywalk',
                label='Source outlet',
            ).props(
                'outlined dense'
            ).classes(
                'w-full mt-2'
            )

            refs['transfer_quantity'] = ui.number(
                label='Quantity',
                value=40,
                min=1,
                max=500,
                step=1,
            ).props(
                'outlined dense'
            ).classes(
                'w-full'
            )

            with ui.row().classes(
                'w-full justify-end gap-2 mt-4'
            ):
                ui.button(
                    'Cancel',
                    on_click=transfer_dialog.close,
                ).props(
                    'flat no-caps'
                )

                ui.button(
                    'Reserve stock',
                    icon='local_shipping',
                    on_click=confirm_transfer,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

    with ui.column().classes(
        'w-full max-w-[1540px] mx-auto '
        'px-4 md:px-7 py-6 gap-5'
    ):
        with ui.row().classes(
            'w-full items-start justify-between gap-4'
        ):
            with ui.column().classes(
                'gap-1'
            ):
                ui.label(
                    'DEMAND & INVENTORY'
                ).classes(
                    'section-kicker'
                )

                ui.label(
                    'Daily demand command center'
                ).classes(
                    'text-2xl md:text-3xl '
                    'font-extrabold tracking-tight'
                )

                refs['context'] = ui.label(
                    f"{snapshot['outlet'].city} · "
                    f"{snapshot['outlet'].outlet_format} · "
                    f"{snapshot['outlet'].delivery_share}% "
                    f"delivery mix"
                ).classes(
                    'text-sm muted'
                )

            with ui.column().classes(
                'items-end gap-1 desktop-only'
            ):
                ui.badge(
                    'SIMULATED LIVE WORKSPACE',
                    color='positive',
                ).props(
                    'outline'
                )

                refs['last_run'] = ui.label(
                    f"Ready to run · "
                    f"{snapshot['kpis']['confidence']:.1f}% "
                    f"model confidence"
                ).classes(
                    'text-xs muted'
                )

        with ui.row().classes(
            'action-bar w-full p-3 gap-3 items-center'
        ):
            refs['region_select'] = ui.select(
                regions,
                value=state['region'],
                label='Region',
                on_change=on_region_change,
            ).props(
                'outlined dense options-dense'
            ).classes(
                'w-44'
            )

            refs['outlet_select'] = ui.select(
                outlets_for_region(
                    brand_state,
                    state['region'],
                ),
                value=state['outlet_id'],
                label='Outlet',
                on_change=on_outlet_change,
            ).props(
                'outlined dense options-dense'
            ).classes(
                'w-64'
            )

            refs['horizon_select'] = ui.select(
                {
                    7: 'Next 7 days',
                    14: 'Next 14 days',
                    30: 'Next 30 days',
                },
                value=state['horizon'],
                label='Forecast horizon',
                on_change=on_horizon_change,
            ).props(
                'outlined dense options-dense'
            ).classes(
                'w-44'
            )

            ui.space()

            refs['emergency_transfer_button'] = ui.button(
                'Emergency transfer',
                icon='local_shipping',
                on_click=open_transfer_dialog,
            ).props(
                'outline no-caps'
            ).classes(
                'rounded-xl'
            )

            refs['run_button'] = ui.button(
                'Run AI forecast',
                icon='auto_graph',
                on_click=run_forecast,
            ).props(
                'unelevated no-caps'
            ).classes(
                'rounded-xl px-5'
            )

        with ui.grid(
            columns=5
        ).classes(
            'w-full gap-4 '
            'max-[1100px]:grid-cols-2 '
            'max-[650px]:grid-cols-1'
        ):
            (
                refs['predicted_units'],
                refs['predicted_units_sub'],
            ) = _metric_card(
                'Predicted demand',
                f"{snapshot['kpis']['predicted_units']:,}",
                f"Next {snapshot['horizon']} days",
                'shopping_basket',
            )

            (
                refs['expected_revenue'],
                refs['expected_revenue_sub'],
            ) = _metric_card(
                'Expected revenue',
                format_demand_money(
                    snapshot['kpis']['expected_revenue'],
                    profile,
                ),
                'Forecast gross sales',
                'payments',
            )

            (
                refs['service_level'],
                refs['service_level_sub'],
            ) = _metric_card(
                'Projected service level',
                f"{planning_data['service_level']:.1f}%",
                'Product availability',
                'verified',
            )

            (
                refs['risk_count'],
                refs['risk_count_sub'],
            ) = _metric_card(
                'Inventory risks',
                str(
                    planning_data['at_risk_count']
                ),
                'SKUs need attention',
                'warning_amber',
            )

            (
                refs['avoidable_waste'],
                refs['avoidable_waste_sub'],
            ) = _metric_card(
                'Avoidable waste',
                format_demand_money(
                    planning_data['avoidable_waste'],
                    profile,
                ),
                'Potential waste avoided',
                'compost',
            )

        with ui.grid(
            columns=12
        ).classes(
            'w-full gap-4 '
            'max-[1050px]:grid-cols-1'
        ):
            with ui.card().classes(
                'surface col-span-8 p-5 w-full relative '
                'max-[1050px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes(
                        'gap-0'
                    ):
                        ui.label(
                            'Demand forecast'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Historical demand, AI forecast, '
                            'and confidence bounds'
                        ).classes(
                            'text-xs muted'
                        )

                    ui.badge(
                        'Weather + events + channel signals',
                        color='secondary',
                    ).props(
                        'outline'
                    )

                refs['forecast_chart'] = ui.echart(
                    _forecast_chart_options(
                        snapshot
                    )
                ).classes(
                    'w-full h-[340px] mt-2'
                )

                ui.button(
                    'Clear chart',
                    icon='delete_sweep',
                    on_click=clear_demand_forecast_chart,
                ).props(
                    'outline no-caps dense color=secondary'
                ).classes(
                    'absolute bottom-4 right-5 z-10 '
                    'rounded-lg px-3 bg-white'
                )

            with ui.card().classes(
                'recommendation-panel col-span-4 '
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

                    refs['rec_priority'] = ui.label(
                        f"{planning_data['recommendation']['priority'].upper()} "
                        f"PRIORITY"
                    ).classes(
                        'text-[10px] font-bold '
                        'text-amber-200'
                    )

                refs['rec_headline'] = ui.label(
                    planning_data['recommendation']['headline']
                ).classes(
                    'text-xl font-extrabold '
                    'leading-tight mt-4'
                )

                refs['rec_body'] = ui.label(
                    planning_data['recommendation']['body']
                ).classes(
                    'text-sm leading-relaxed '
                    'text-white/75 mt-1'
                )

                ui.separator().classes(
                    'opacity-20 my-4'
                )

                with ui.grid(
                    columns=2
                ).classes(
                    'w-full gap-3'
                ):
                    with ui.column().classes(
                        'gap-0'
                    ):
                        ui.label(
                            'SALES PROTECTED'
                        ).classes(
                            'text-[10px] tracking-wider '
                            'text-white/55'
                        )

                        refs['rec_impact'] = ui.label(
                            planning_data['recommendation']['impact']
                        ).classes(
                            'text-xl font-bold text-amber-200'
                        )

                    with ui.column().classes(
                        'gap-0'
                    ):
                        ui.label(
                            'WASTE AVOIDED'
                        ).classes(
                            'text-[10px] tracking-wider '
                            'text-white/55'
                        )

                        refs['rec_waste'] = ui.label(
                            planning_data['recommendation']['waste']
                        ).classes(
                            'text-xl font-bold'
                        )

                refs['build_action_button'] = ui.button(
                    'Build action plan',
                    icon='route',
                    on_click=build_action_plan,
                ).props(
                    'unelevated no-caps '
                    'color=secondary text-color=dark'
                ).classes(
                    'w-full rounded-xl mt-5'
                )

        with ui.card().classes(
            'surface w-full p-5'
        ):
            with ui.row().classes(
                'w-full items-center justify-between'
            ):
                with ui.column().classes(
                    'gap-0'
                ):
                    ui.label(
                        'Demand signals behind the forecast'
                    ).classes(
                        'text-base font-bold'
                    )

                    ui.label(
                        'Explainability layer for store '
                        'and regional managers'
                    ).classes(
                        'text-xs muted'
                    )

                ui.badge(
                    'MODEL EXPLAINABILITY',
                    color='primary',
                ).props(
                    'outline'
                )

            refs['signal_grid'] = ui.grid(
                columns=3
            ).classes(
                'w-full gap-3 mt-3 '
                'max-[800px]:grid-cols-1'
            )

            render_demand_signals(
                snapshot['signals']
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
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes(
                        'gap-0'
                    ):
                        refs['availability_title'] = ui.label(
                            'Product availability vs demand'
                        ).classes(
                            'text-lg font-bold'
                        )

                        refs['planning_subtitle'] = ui.label(
                            f"Next {planning_data['horizon']} days demand "
                            f"compared with current usable stock"
                        ).classes(
                            'text-xs muted'
                        ).tooltip(
                            'Ingredient view converts item demand and usable finished-item stock through the BOM. '
                            'Stock equivalent is not raw ingredient inventory; purchase orders separately deduct raw stock.'
                        )

                    with ui.row().classes(
                        'items-center gap-2'
                    ):
                        refs['planning_horizon_select'] = ui.select(
                            {
                                7: 'Next 7 days',
                                14: 'Next 14 days',
                            },
                            value=state['planning_horizon'],
                            label='Inventory horizon',
                            on_change=on_planning_horizon_change,
                        ).props(
                            'outlined dense options-dense'
                        ).classes(
                            'w-40'
                        )

                        ui.switch(value=False, on_change=toggle_availability).props(
                            'dense color=primary size=sm aria-label="Show ingredient view"'
                        ).classes('vesper-view-switch').tooltip(
                            'Switch between item and ingredient availability'
                        )

                with ui.element('div').classes('w-full mt-2').style(
                    'height: 360px; min-height: 360px; max-height: 360px; overflow-y: auto; overflow-x: hidden'
                ):
                    refs['risk_chart'] = ui.echart(
                        _risk_chart_options(planning_data)
                    ).classes('w-full').style('height: 360px; min-height: 360px')

            with ui.card().classes(
                'surface col-span-5 p-5 w-full '
                'max-[1050px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes(
                        'gap-0'
                    ):
                        ui.label(
                            'Inventory risk queue'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Highest-impact exceptions first'
                        ).classes(
                            'text-xs muted'
                        )

                    ui.icon(
                        'priority_high'
                    ).classes(
                        'text-2xl text-negative'
                    )

                refs['risk_queue'] = ui.column().classes(
                    'w-full gap-3 mt-4'
                )

                render_inventory_risks(
                    planning_data['risks']
                )


        with ui.card().classes(
            'surface w-full p-5 table-shell'
        ):
            with ui.row().classes(
                'w-full items-start justify-between gap-4'
            ):
                with ui.column().classes(
                    'gap-0'
                ):
                    ui.label(
                        'Outlet inventory position'
                    ).classes(
                        'text-lg font-bold'
                    )

                    persisted_inventory_rows = deepcopy(
                        workflow_state.get('inventory_rows', [])
                    )
                    inventory_status_text = (
                        f"{len(persisted_inventory_rows)} products loaded for the next "
                        f"{state['planning_horizon']} days. Click a row to record an action."
                        if state['inventory_built'] and persisted_inventory_rows
                        else 'Build the action plan to load the latest inventory position.'
                    )
                    refs['inventory_status'] = ui.label(
                        inventory_status_text
                    ).classes(
                        'text-xs muted'
                    )

                with ui.row().classes(
                    'gap-2 items-center'
                ):
                    ui.badge(
                        '7 PRODUCTS',
                        color='primary',
                    ).props(
                        'outline'
                    )

                    refs['inventory_horizon_badge'] = ui.badge(
                        f"NEXT {planning_data['horizon']} DAYS",
                        color='secondary',
                    ).props(
                        'outline'
                    )

                    refs['generate_plan_button'] = ui.button(
                        'Generate Plan',
                        icon='route',
                        on_click=generate_replenishment_plan,
                    ).props(
                        'outline no-caps'
                    ).classes(
                        'rounded-xl'
                    )

                    if not state['inventory_built']:
                        refs['generate_plan_button'].disable()

            refs['inventory_table'] = ui.table(
                columns=INVENTORY_COLUMNS,
                rows=deepcopy(workflow_state.get('inventory_rows', [])),
                row_key='id',
                pagination={
                    'rowsPerPage': 7,
                },
            ).props(
                'flat bordered dense '
                'separator=horizontal'
            ).classes(
                'w-full mt-3 cursor-pointer'
            )

            refs['inventory_table'].on(
                'rowClick',
                open_inventory_action_dialog,
                [
                    [],
                    ['id'],
                    None,
                ],
            )


        with ui.card().classes(
            'surface w-full p-5 table-shell'
        ):
            with ui.row().classes(
                'w-full items-start justify-between gap-4'
            ):
                with ui.column().classes(
                    'gap-0'
                ):
                    ui.label(
                        'Replenishment & transfer planner'
                    ).classes(
                        'text-lg font-bold'
                    )

                    persisted_plan_rows = deepcopy(workflow_state.get('plan_rows', []))
                    persisted_ready_count = sum(
                        1 for row in persisted_plan_rows
                        if row.get('status') == 'Ready for approval'
                    )
                    persisted_approved_count = sum(
                        1 for row in persisted_plan_rows
                        if row.get('status') == 'Approved'
                    )
                    if state['plan_approved'] and persisted_approved_count:
                        plan_status_text = 'Approved · Ingredients ordered (awaiting receipt); transfers awaiting dispatch'
                    elif state['plan_generated'] and persisted_ready_count:
                        persisted_total_cost = sum(
                            float(row.get('total_cost_value', 0))
                            for row in persisted_plan_rows
                            if row.get('status') == 'Ready for approval'
                        )
                        plan_word = 'plan' if persisted_ready_count == 1 else 'plans'
                        plan_status_text = (
                            f"{persisted_ready_count} coordinated {plan_word} · "
                            f"{format_demand_money(persisted_total_cost, profile)} total cost · "
                            'click a row for details'
                        )
                    else:
                        plan_status_text = 'No plan generated'

                    refs['plan_status'] = ui.label(
                        plan_status_text
                    ).classes(
                        'text-xs muted'
                    )

                refs['approve_button'] = ui.button(
                    'Approve plan',
                    icon='check_circle',
                    on_click=open_approval_dialog,
                ).props(
                    'unelevated no-caps'
                ).classes(
                    'rounded-xl'
                )

                if not (state['plan_generated'] and not state['plan_approved']):
                    refs['approve_button'].disable()

            refs['plan_table'] = ui.table(
                columns=PLAN_COLUMNS,
                rows=deepcopy(workflow_state.get('plan_rows', [])),
                row_key='id',
                pagination={
                    'rowsPerPage': 2,
                },
            ).props(
                'flat bordered dense '
                'separator=horizontal'
            ).classes(
                'w-full mt-3 cursor-pointer'
            )

            refs['plan_table'].on(
                'rowClick',
                open_plan_detail_dialog,
                [
                    [],
                    ['id'],
                    None,
                ],
            )

        with ui.row().classes(
            'w-full justify-between items-center '
            'px-1 pb-3 gap-3'
        ):
            ui.label(
                'Prototype only · All values are simulated '
                'and are not operational business data.'
            ).classes(
                'text-[11px] muted'
            )

            ui.label(
                'Designed by Inventide'
            ).classes(
                'text-[11px] font-bold text-primary'
            )

    # Clear before the initial page response is sent; switching back to a loaded
    # workspace can retain its last completed snapshot.
    if not state['loaded']:
        blank_dashboard()
