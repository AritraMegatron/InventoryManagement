from __future__ import annotations

import asyncio
import csv
import io
from typing import Any

from nicegui import ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS

from app.mock_data import (
    OUTLETS,
    REGIONS,
    build_dashboard_snapshot,
    build_replenishment_plan,
    format_inr,
    outlets_for_region,
)
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
        'label': 'Tomorrow forecast',
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
]


PLAN_COLUMNS = [
    {
        'name': 'product',
        'label': 'Product',
        'field': 'product',
        'align': 'left',
    },
    {
        'name': 'method',
        'label': 'Action',
        'field': 'method',
        'align': 'left',
    },
    {
        'name': 'from',
        'label': 'Source / destination',
        'field': 'from',
        'align': 'left',
    },
    {
        'name': 'quantity',
        'label': 'Qty',
        'field': 'quantity',
        'align': 'right',
    },
    {
        'name': 'eta',
        'label': 'ETA',
        'field': 'eta',
        'align': 'left',
    },
    {
        'name': 'impact',
        'label': 'Value protected',
        'field': 'impact',
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
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    rows = snapshot['inventory_rows']

    products = [
        row['product']
        for row in rows
    ]

    forecast = [
        row['forecast']
        for row in rows
    ]

    on_hand = [
        row['on_hand']
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
                'Tomorrow forecast',
                'On hand',
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
                'name': 'Tomorrow forecast',
                'type': 'bar',
                'data': forecast,
                'barWidth': 9,
                'itemStyle': {
                    'color': BURGUNDY,
                    'borderRadius': [0, 5, 5, 0],
                },
            },
            {
                'name': 'On hand',
                'type': 'bar',
                'data': on_hand,
                'barWidth': 9,
                'itemStyle': {
                    'color': GOLD,
                    'borderRadius': [0, 5, 5, 0],
                },
            },
        ],
    }


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
    apply_theme()
    ai_chat = create_ai_chat(
        page_name='Demand & Inventory',
        page_context=PAGE_CONTEXTS['demand_inventory'],
    )
    _render_shell(ai_chat)

    state: dict[str, Any] = {
        'region': 'Delhi NCR',
        'outlet_id': 'dlf_noida',
        'horizon': 7,
        'run_number': 0,
        'plan_generated': False,
        'plan_approved': False,
    }

    snapshot = build_dashboard_snapshot(
        outlet_id=state['outlet_id'],
        horizon=state['horizon'],
        run_number=state['run_number'],
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
        """Create a snapshot with three signals different from the current set."""

        new_snapshot = build_dashboard_snapshot(
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

    async def run_forecast() -> None:
        refs['run_button'].disable()

        progress = ui.notification(
            'Refreshing demand signals and outlet forecast…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(0.85)

        state['run_number'] += 1
        state['plan_generated'] = False
        state['plan_approved'] = False

        new_snapshot = create_snapshot(
            outlet_id=state['outlet_id'],
            horizon=state['horizon'],
            run_number=state['run_number'],
        )

        apply_snapshot(new_snapshot)

        progress.dismiss()
        refs['run_button'].enable()

        ui.notify(
            f"Forecast refreshed for "
            f"{new_snapshot['outlet'].name}",
            type='positive',
            icon='check_circle',
            position='top',
        )

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
            format_inr(
                kpis['expected_revenue']
            )
        )

        refs['expected_revenue_sub'].set_text(
            'Forecast gross sales'
        )

        refs['service_level'].set_text(
            f"{kpis['service_level']:.1f}%"
        )

        refs['service_level_sub'].set_text(
            'Projected product availability'
        )

        refs['risk_count'].set_text(
            str(kpis['at_risk_count'])
        )

        refs['risk_count_sub'].set_text(
            'SKUs need attention'
        )

        refs['avoidable_waste'].set_text(
            format_inr(
                kpis['avoidable_waste']
            )
        )

        refs['avoidable_waste_sub'].set_text(
            'Potential waste avoided'
        )

        _replace_echart_options(
            refs['forecast_chart'],
            _forecast_chart_options(snapshot),
        )

        _replace_echart_options(
            refs['risk_chart'],
            _risk_chart_options(snapshot),
        )

        refs['inventory_table'].rows = (
            snapshot['inventory_rows']
        )
        refs['inventory_table'].update()

        recommendation = snapshot['recommendation']

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

        render_demand_signals(
            snapshot['signals']
        )

        refs['plan_table'].rows = []
        refs['plan_table'].update()

        refs['plan_status'].set_text(
            'No plan generated'
        )

        refs['approve_button'].disable()
        refs['export_button'].disable()

    def on_region_change(
        event: Any,
    ) -> None:
        state['region'] = event.value

        options = outlets_for_region(
            state['region']
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
        state['run_number'] += 1
        state['plan_generated'] = False
        state['plan_approved'] = False

        new_snapshot = create_snapshot(
            outlet_id=outlet_id,
            horizon=state['horizon'],
            run_number=state['run_number'],
        )

        apply_snapshot(
            new_snapshot
        )

        ui.notify(
            f"Loaded {OUTLETS[outlet_id].name}",
            type='info',
            position='top',
        )

    def on_horizon_change(
        event: Any,
    ) -> None:
        state['horizon'] = int(
            event.value
        )

        state['run_number'] += 1
        state['plan_generated'] = False
        state['plan_approved'] = False

        new_snapshot = create_snapshot(
            outlet_id=state['outlet_id'],
            horizon=state['horizon'],
            run_number=state['run_number'],
        )

        apply_snapshot(
            new_snapshot
        )

    async def generate_plan() -> None:
        refs['plan_button'].disable()

        progress = ui.notification(
            'Checking available stock across nearby outlets…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(0.65)

        plan = build_replenishment_plan(
            snapshot
        )

        state['plan_generated'] = True
        state['plan_approved'] = False

        refs['plan_table'].rows = plan
        refs['plan_table'].update()

        refs['plan_status'].set_text(
            f"{len(plan)} actions ready · "
            f"Awaiting regional manager approval"
        )

        refs['approve_button'].enable()
        refs['export_button'].enable()
        refs['plan_button'].enable()

        progress.dismiss()

        ui.notify(
            'Replenishment plan generated',
            type='positive',
            icon='route',
            position='top',
        )

    def open_approval_dialog() -> None:
        if not state['plan_generated']:
            ui.notify(
                'Generate a plan first.',
                type='warning',
            )
            return

        refs['approval_outlet'].set_text(
            snapshot['outlet'].name
        )

        refs['approval_actions'].set_text(
            f"{len(refs['plan_table'].rows)} "
            f"inventory actions will be released."
        )

        refs['approve_dialog'].open()

    def approve_plan() -> None:
        state['plan_approved'] = True

        for row in refs['plan_table'].rows:
            row['status'] = 'Approved'

        refs['plan_table'].update()

        refs['plan_status'].set_text(
            'Approved · Dispatch and procurement tasks created'
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
        high_risk = next(
            (
                risk
                for risk in snapshot['risks']
                if risk['severity'] == 'High'
            ),
            snapshot['primary_risk'],
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

        source = (
            refs['transfer_source'].value
        )

        refs['transfer_dialog'].close()

        ui.notify(
            f'{quantity} units reserved from '
            f'{source}; simulated ETA 62 minutes.',
            type='positive',
            icon='local_shipping',
            position='top',
        )

    def export_plan() -> None:
        rows = refs['plan_table'].rows

        if not rows:
            ui.notify(
                'Generate a plan first.',
                type='warning',
            )
            return

        buffer = io.StringIO()

        fieldnames = [
            'product',
            'method',
            'from',
            'quantity',
            'eta',
            'impact',
            'status',
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
            for row in rows
        )

        ui.download(
            buffer.getvalue().encode(
                'utf-8'
            ),
            filename=(
                f"replenishment_plan_"
                f"{state['outlet_id']}.csv"
            ),
            media_type='text/csv',
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
                'This concept keeps the final operational '
                'decision with the regional manager.'
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
                REGIONS,
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
                    state['region']
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

            ui.button(
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
                format_inr(
                    snapshot['kpis']['expected_revenue']
                ),
                'Forecast gross sales',
                'currency_rupee',
            )

            (
                refs['service_level'],
                refs['service_level_sub'],
            ) = _metric_card(
                'Projected service level',
                f"{snapshot['kpis']['service_level']:.1f}%",
                'Product availability',
                'verified',
            )

            (
                refs['risk_count'],
                refs['risk_count_sub'],
            ) = _metric_card(
                'Inventory risks',
                str(
                    snapshot['kpis']['at_risk_count']
                ),
                'SKUs need attention',
                'warning_amber',
            )

            (
                refs['avoidable_waste'],
                refs['avoidable_waste_sub'],
            ) = _metric_card(
                'Avoidable waste',
                format_inr(
                    snapshot['kpis']['avoidable_waste']
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
                'surface col-span-8 p-5 w-full '
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
                        f"{snapshot['recommendation']['priority'].upper()} "
                        f"PRIORITY"
                    ).classes(
                        'text-[10px] font-bold '
                        'text-amber-200'
                    )

                refs['rec_headline'] = ui.label(
                    snapshot['recommendation']['headline']
                ).classes(
                    'text-xl font-extrabold '
                    'leading-tight mt-4'
                )

                refs['rec_body'] = ui.label(
                    snapshot['recommendation']['body']
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
                            snapshot['recommendation']['impact']
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
                            snapshot['recommendation']['waste']
                        ).classes(
                            'text-xl font-bold'
                        )

                ui.button(
                    'Build action plan',
                    icon='route',
                    on_click=generate_plan,
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
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes(
                        'gap-0'
                    ):
                        ui.label(
                            'Product availability vs demand'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Tomorrow forecast compared '
                            'with current usable stock'
                        ).classes(
                            'text-xs muted'
                        )

                    ui.badge(
                        'OUTLET LEVEL',
                        color='primary',
                    ).props(
                        'outline'
                    )

                refs['risk_chart'] = ui.echart(
                    _risk_chart_options(
                        snapshot
                    )
                ).classes(
                    'w-full h-[360px] mt-2'
                )

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

                with ui.column().classes(
                    'w-full gap-3 mt-4'
                ):
                    for risk in snapshot['risks'][:4]:
                        color = (
                            RED
                            if risk['severity'] == 'High'
                            else GOLD
                        )

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

                    ui.label(
                        'Demand-adjusted coverage by product '
                        '· simulated quantities'
                    ).classes(
                        'text-xs muted'
                    )

                with ui.row().classes(
                    'gap-2'
                ):
                    ui.badge(
                        '7 PRODUCTS',
                        color='primary',
                    ).props(
                        'outline'
                    )

                    ui.badge(
                        'Tomorrow 18:00 peak',
                        color='secondary',
                    ).props(
                        'outline'
                    )

            refs['inventory_table'] = ui.table(
                columns=INVENTORY_COLUMNS,
                rows=snapshot['inventory_rows'],
                row_key='id',
                pagination={
                    'rowsPerPage': 7,
                },
            ).props(
                'flat bordered dense '
                'separator=horizontal'
            ).classes(
                'w-full mt-3'
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

                    refs['plan_status'] = ui.label(
                        'No plan generated'
                    ).classes(
                        'text-xs muted'
                    )

                with ui.row().classes(
                    'gap-2'
                ):
                    refs['export_button'] = ui.button(
                        'Export CSV',
                        icon='download',
                        on_click=export_plan,
                    ).props(
                        'outline no-caps'
                    ).classes(
                        'rounded-xl'
                    )

                    refs['export_button'].disable()

                    refs['plan_button'] = ui.button(
                        'Generate plan',
                        icon='route',
                        on_click=generate_plan,
                    ).props(
                        'outline no-caps'
                    ).classes(
                        'rounded-xl'
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

                    refs['approve_button'].disable()

            refs['plan_table'] = ui.table(
                columns=PLAN_COLUMNS,
                rows=[],
                row_key='id',
                pagination={
                    'rowsPerPage': 5,
                },
            ).props(
                'flat bordered dense '
                'separator=horizontal'
            ).classes(
                'w-full mt-3'
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