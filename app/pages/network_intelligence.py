from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime
from typing import Any

from nicegui import events, ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS

from app.theme import BURGUNDY, GOLD, apply_theme


STATUS_COLORS = {
    'Above target': '#197A59',
    'Needs attention': '#F2B544',
    'Underperforming': '#B33A3A',
    'Newly opened': '#2A608D',
}

REGION_CENTERS = {
    'All regions': (22.8, 79.0, 5),
    'Delhi NCR': (28.55, 77.20, 9),
    'North': (29.2, 76.8, 6),
    'West': (20.8, 73.6, 6),
    'South': (13.2, 78.2, 6),
    'East': (22.8, 86.0, 6),
    'Central': (23.5, 78.8, 6),
}

# 21 city clusters × 3 outlets = 63 stores across India.
# Coordinates and outlet data are mock values for the prototype.
CITY_CLUSTERS = [
    (
        'Delhi NCR',
        'New Delhi',
        28.6139,
        77.2090,
        ['Connaught Place', 'Saket', 'Aerocity'],
    ),
    (
        'Delhi NCR',
        'Gurugram',
        28.4595,
        77.0266,
        ['Cyber Hub', 'Golf Course Road', 'Sector 29'],
    ),
    (
        'Delhi NCR',
        'Noida',
        28.5355,
        77.3910,
        ['DLF Mall of India', 'Sector 18', 'Sector 62'],
    ),
    (
        'West',
        'Mumbai',
        19.0760,
        72.8777,
        ['Phoenix Palladium', 'Bandra Linking Road', 'Powai'],
    ),
    (
        'West',
        'Pune',
        18.5204,
        73.8567,
        ['Phoenix Marketcity', 'Koregaon Park', 'Baner'],
    ),
    (
        'South',
        'Bengaluru',
        12.9716,
        77.5946,
        ['Indiranagar', 'Koramangala', 'Whitefield'],
    ),
    (
        'South',
        'Hyderabad',
        17.3850,
        78.4867,
        ['Jubilee Hills', 'Banjara Hills', 'HITEC City'],
    ),
    (
        'South',
        'Chennai',
        13.0827,
        80.2707,
        ['Phoenix Marketcity', 'T Nagar', 'Anna Nagar'],
    ),
    (
        'East',
        'Kolkata',
        22.5726,
        88.3639,
        ['Park Street', 'Salt Lake Sector V', 'New Town'],
    ),
    (
        'North',
        'Chandigarh',
        30.7333,
        76.7794,
        ['Elante Mall', 'Sector 17', 'Madhya Marg'],
    ),
    (
        'North',
        'Jaipur',
        26.9124,
        75.7873,
        ['C Scheme', 'World Trade Park', 'Vaishali Nagar'],
    ),
    (
        'West',
        'Ahmedabad',
        23.0225,
        72.5714,
        ['Ahmedabad One', 'SG Highway', 'Prahlad Nagar'],
    ),
    (
        'North',
        'Lucknow',
        26.8467,
        80.9462,
        ['Hazratganj', 'Gomti Nagar', 'Aliganj'],
    ),
    (
        'South',
        'Kochi',
        9.9312,
        76.2673,
        ['Lulu Mall', 'Panampilly Nagar', 'Marine Drive'],
    ),
    (
        'Central',
        'Indore',
        22.7196,
        75.8577,
        ['Vijay Nagar', 'Palasia', 'Treasure Island'],
    ),
    (
        'East',
        'Bhubaneswar',
        20.2961,
        85.8245,
        ['Saheed Nagar', 'Patia', 'Esplanade Mall'],
    ),
    (
        'East',
        'Guwahati',
        26.1445,
        91.7362,
        ['GS Road', 'Christian Basti', 'City Center'],
    ),
    (
        'West',
        'Surat',
        21.1702,
        72.8311,
        ['VR Surat', 'Vesu', 'Adajan'],
    ),
    (
        'Central',
        'Nagpur',
        21.1458,
        79.0882,
        ['Dharampeth', 'Civil Lines', 'Wardha Road'],
    ),
    (
        'South',
        'Coimbatore',
        11.0168,
        76.9558,
        ['RS Puram', 'Peelamedu', 'Brookefields'],
    ),
    (
        'East',
        'Patna',
        25.5941,
        85.1376,
        ['Fraser Road', 'Boring Road', 'Patliputra'],
    ),
]

TABLE_COLUMNS = [
    {
        'name': 'outlet',
        'label': 'Outlet',
        'field': 'outlet',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'city',
        'label': 'City',
        'field': 'city',
        'align': 'left',
        'sortable': True,
    },
    {
        'name': 'revenue_lakh',
        'label': 'Revenue ₹L',
        'field': 'revenue_lakh',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'profit_lakh',
        'label': 'Profit ₹L',
        'field': 'profit_lakh',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'margin_pct',
        'label': 'Margin %',
        'field': 'margin_pct',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'forecast_lakh',
        'label': 'Next month ₹L',
        'field': 'forecast_lakh',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'growth_pct',
        'label': 'Forecast %',
        'field': 'growth_pct',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'employees',
        'label': 'Employees',
        'field': 'employees',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'revenue_per_employee',
        'label': 'Rev/employee ₹L',
        'field': 'revenue_per_employee',
        'align': 'right',
        'sortable': True,
    },
    {
        'name': 'status',
        'label': 'Status',
        'field': 'status',
        'align': 'left',
        'sortable': True,
    },
]

FORMATS = [
    'Mall kiosk',
    'High-street café',
    'Compact takeaway',
    'Premium café',
    'Delivery-led store',
]


def _stable_seed(text: str) -> int:
    return sum(
        (index + 1) * ord(character)
        for index, character in enumerate(text)
    )


def _build_store_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    tier_one = {
        'New Delhi',
        'Gurugram',
        'Noida',
        'Mumbai',
        'Pune',
        'Bengaluru',
        'Hyderabad',
        'Chennai',
        'Kolkata',
    }

    format_multiplier = {
        'Mall kiosk': 0.96,
        'High-street café': 1.04,
        'Compact takeaway': 0.88,
        'Premium café': 1.18,
        'Delivery-led store': 0.82,
    }

    size_ranges = {
        'Mall kiosk': (260, 430),
        'High-street café': (520, 850),
        'Compact takeaway': (300, 500),
        'Premium café': (700, 1100),
        'Delivery-led store': (260, 450),
    }

    store_number = 0

    for (
        region,
        city,
        city_latitude,
        city_longitude,
        outlets,
    ) in CITY_CLUSTERS:
        for local_index, outlet in enumerate(outlets):
            store_number += 1

            store_id = (
                f'{city.lower().replace(" ", "-")}-'
                f'{local_index + 1}'
            )

            rng = random.Random(
                _stable_seed(store_id)
            )

            outlet_format = FORMATS[
                (store_number + local_index) % len(FORMATS)
            ]

            latitude = city_latitude + rng.uniform(
                -0.055,
                0.055,
            )

            longitude = city_longitude + rng.uniform(
                -0.055,
                0.055,
            )

            city_factor = (
                1.15
                if city in tier_one
                else 0.92
            )

            revenue = (
                rng.uniform(15.0, 25.0)
                * city_factor
                * format_multiplier[outlet_format]
            )

            age_months = rng.randint(10, 72)

            # Force a few outlets to be newly opened.
            if store_number in {
                13,
                28,
                41,
                54,
                61,
            }:
                age_months = rng.randint(2, 6)

            growth = rng.uniform(-7.5, 12.5)
            margin = rng.uniform(8.0, 24.0)

            if age_months <= 6:
                status = 'Newly opened'
            elif margin < 10.5 or growth < -4.5:
                status = 'Underperforming'
            elif margin > 17.0 and growth > 4.0:
                status = 'Above target'
            else:
                status = 'Needs attention'

            size_minimum, size_maximum = (
                size_ranges[outlet_format]
            )

            square_feet = rng.randint(
                size_minimum,
                size_maximum,
            )

            rent_per_square_foot = (
                rng.uniform(330, 720)
                if city in tier_one
                else rng.uniform(180, 430)
            )

            monthly_rent_lakh = (
                square_feet
                * rent_per_square_foot
                / 100_000
            )

            employees = max(
                6,
                int(
                    square_feet
                    / rng.uniform(55, 78)
                ),
            )

            average_ticket = rng.randint(
                245,
                335,
            )

            monthly_orders = int(
                revenue
                * 100_000
                / average_ticket
            )

            operating_profit = (
                revenue
                * margin
                / 100
            )

            rows.append(
                {
                    'store_id': store_id,
                    'outlet': outlet,
                    'city': city,
                    'region': region,
                    'lat': round(latitude, 5),
                    'lon': round(longitude, 5),
                    'format': outlet_format,
                    'age_months': age_months,
                    'square_feet': square_feet,
                    'revenue_lakh': round(
                        revenue,
                        1,
                    ),
                    'profit_lakh': round(
                        operating_profit,
                        1,
                    ),
                    'margin_pct': round(
                        margin,
                        1,
                    ),
                    'growth_pct': round(
                        growth,
                        1,
                    ),
                    'forecast_lakh': round(
                        revenue
                        * (1 + growth / 100),
                        1,
                    ),
                    'employees': employees,
                    'revenue_per_employee': round(
                        revenue / employees,
                        2,
                    ),
                    'monthly_orders': monthly_orders,
                    'average_ticket': average_ticket,
                    'delivery_share_pct': rng.randint(
                        19,
                        51,
                    ),
                    'rent_lakh': round(
                        monthly_rent_lakh,
                        1,
                    ),
                    'rent_ratio_pct': round(
                        monthly_rent_lakh
                        / revenue
                        * 100,
                        1,
                    ),
                    'waste_pct': round(
                        rng.uniform(1.4, 5.8),
                        1,
                    ),
                    'stockout_pct': round(
                        rng.uniform(1.0, 8.5),
                        1,
                    ),
                    'rating': round(
                        rng.uniform(3.8, 4.8),
                        1,
                    ),
                    'status': status,
                }
            )

    return rows


def _format_lakh(value: float) -> str:
    return f'₹{value:,.1f} lakh'


def _haversine_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    radius_km = 6371.0

    phi_1 = math.radians(latitude_1)
    phi_2 = math.radians(latitude_2)

    delta_phi = math.radians(
        latitude_2 - latitude_1
    )

    delta_lambda = math.radians(
        longitude_2 - longitude_1
    )

    calculation = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi_1)
        * math.cos(phi_2)
        * math.sin(delta_lambda / 2) ** 2
    )

    return (
        2
        * radius_km
        * math.atan2(
            math.sqrt(calculation),
            math.sqrt(1 - calculation),
        )
    )


def _ai_observation(
    store: dict[str, Any],
) -> tuple[str, str]:
    if store['status'] == 'Above target':
        observation = (
            f"{store['outlet']} combines a "
            f"{store['margin_pct']:.1f}% operating margin "
            f"with {_format_lakh(store['revenue_per_employee'])} "
            f"revenue per employee. The next-month model "
            f"projects {store['growth_pct']:+.1f}% growth."
        )

        action = (
            'Maintain staffing and protect product availability '
            'during peak periods. Test a small premium assortment '
            'expansion.'
        )

        return observation, action

    if store['status'] == 'Underperforming':
        observation = (
            f"The outlet is generating "
            f"{store['margin_pct']:.1f}% operating margin. "
            f"Rent consumes {store['rent_ratio_pct']:.1f}% "
            f"of revenue and the next-month outlook is "
            f"{store['growth_pct']:+.1f}%."
        )

        action = (
            'Review off-peak staffing, promotion efficiency, '
            'and lease economics. Create a six-week recovery plan.'
        )

        return observation, action

    if store['status'] == 'Newly opened':
        observation = (
            f"This outlet is {store['age_months']} months old "
            f"and remains in its ramp-up period. Current revenue "
            f"is {_format_lakh(store['revenue_lakh'])}; next month "
            f"is projected at "
            f"{_format_lakh(store['forecast_lakh'])}."
        )

        action = (
            'Track weekly customer acquisition, repeat purchases, '
            'and daypart demand before making major staffing or '
            'assortment changes.'
        )

        return observation, action

    observation = (
        f"The outlet is stable but below the strongest network "
        f"performance band. Waste is "
        f"{store['waste_pct']:.1f}% and stockouts are "
        f"{store['stockout_pct']:.1f}%, suggesting an opportunity "
        f"to improve availability without adding headcount."
    )

    action = (
        'Rebalance inventory around peak demand and compare labor '
        'scheduling with similar outlets in the same region.'
    )

    return observation, action


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
                active=True,
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




@ui.page('/network-intelligence')
def network_intelligence_page() -> None:
    apply_theme()

    ui.add_css(
        '''
        .network-table .q-table tbody tr.q-tr--selected {
            background: rgba(90, 21, 52, 0.10) !important;
            box-shadow: inset 4px 0 0 #5A1534;
        }

        .network-map .leaflet-container {
            border-radius: 16px;
        }

        .network-detail {
            background: linear-gradient(155deg, #3B0D22, #5A1534);
            color: white;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(59, 13, 34, 0.20);
        }
        '''
    )

    ai_chat = create_ai_chat(
        page_name='Network Intelligence',
        page_context=PAGE_CONTEXTS['network_intelligence'],
    )
    _render_shell(ai_chat)

    stores = _build_store_rows()

    stores_by_id = {
        store['store_id']: store
        for store in stores
    }

    state: dict[str, Any] = {
        'selected_id': stores[0]['store_id'],
        'region': 'All regions',
        'status': 'All statuses',
        'search': '',
        'analysis_run': 0,
    }

    refs: dict[str, Any] = {}

    def filtered_rows() -> list[dict[str, Any]]:
        query = state['search'].strip().lower()

        return [
            store
            for store in stores
            if (
                state['region'] == 'All regions'
                or store['region'] == state['region']
            )
            and (
                state['status'] == 'All statuses'
                or store['status'] == state['status']
            )
            and (
                not query
                or query in store['outlet'].lower()
                or query in store['city'].lower()
                or query in store['format'].lower()
            )
        ]

    def replace_table_rows(
        rows: list[dict[str, Any]],
    ) -> None:
        refs['table'].rows.clear()
        refs['table'].rows.extend(rows)
        refs['table'].update()

    def update_kpis(
        rows: list[dict[str, Any]],
    ) -> None:
        revenue = sum(
            row['revenue_lakh']
            for row in rows
        )

        profit = sum(
            row['profit_lakh']
            for row in rows
        )

        forecast = sum(
            row['forecast_lakh']
            for row in rows
        )

        employees = sum(
            row['employees']
            for row in rows
        )

        margin = (
            profit / revenue * 100
            if revenue
            else 0
        )

        refs['network_revenue'].set_text(
            f'₹{revenue / 100:.2f} crore'
        )

        refs['network_revenue_sub'].set_text(
            f'{len(rows)} visible outlets'
        )

        refs['network_profit'].set_text(
            f'₹{profit / 100:.2f} crore'
        )

        refs['network_forecast'].set_text(
            f'₹{forecast / 100:.2f} crore'
        )

        refs['network_margin'].set_text(
            f'{margin:.1f}%'
        )

        refs['network_employees'].set_text(
            f'{employees:,}'
        )

    def update_detail(
        store: dict[str, Any],
    ) -> None:
        observation, action = _ai_observation(
            store
        )

        values = {
            'selected_name': store['outlet'],
            'selected_location': (
                f"{store['city']} · "
                f"{store['region']} · "
                f"{store['format']}"
            ),
            'selected_revenue': _format_lakh(
                store['revenue_lakh']
            ),
            'selected_profit': _format_lakh(
                store['profit_lakh']
            ),
            'selected_forecast': _format_lakh(
                store['forecast_lakh']
            ),
            'selected_employees': str(
                store['employees']
            ),
            'selected_growth': (
                f"{store['growth_pct']:+.1f}%"
            ),
            'selected_margin': (
                f"{store['margin_pct']:.1f}%"
            ),
            'selected_orders': (
                f"{store['monthly_orders']:,}"
            ),
            'selected_ticket': (
                f"₹{store['average_ticket']}"
            ),
            'selected_delivery': (
                f"{store['delivery_share_pct']}%"
            ),
            'selected_rent': _format_lakh(
                store['rent_lakh']
            ),
            'selected_rent_ratio': (
                f"{store['rent_ratio_pct']:.1f}%"
            ),
            'selected_rating': (
                f"{store['rating']:.1f} / 5"
            ),
            'selected_waste': (
                f"{store['waste_pct']:.1f}%"
            ),
            'selected_stockout': (
                f"{store['stockout_pct']:.1f}%"
            ),
            'selected_observation': observation,
            'selected_action': action,
        }

        for reference_name, text in values.items():
            refs[reference_name].set_text(text)

        refs['selected_status'].set_text(
            store['status'].upper()
        )

        refs['selected_status'].style(
            f"background:{STATUS_COLORS[store['status']]};"
            f"color:white;"
        )

    def select_store(
        store_id: str,
        move_to_top: bool = False,
        notify: bool = False,
    ) -> None:
        if store_id not in stores_by_id:
            return

        state['selected_id'] = store_id
        selected = stores_by_id[store_id]
        rows = filtered_rows()

        # If a map click chooses a store excluded by the filters,
        # reset the filters so its row can be displayed.
        if selected not in rows:
            state.update(
                region='All regions',
                status='All statuses',
                search='',
            )

            refs['region_select'].value = (
                'All regions'
            )

            refs['status_select'].value = (
                'All statuses'
            )

            refs['search_input'].value = ''

            rows = filtered_rows()

        # When selected from the map, move the row to the top
        # so the highlighted row is immediately visible.
        if move_to_top:
            rows = [
                selected,
                *[
                    row
                    for row in rows
                    if row['store_id'] != store_id
                ],
            ]

        replace_table_rows(rows)

        refs['table'].selected.clear()
        refs['table'].selected.append(selected)
        refs['table'].update()

        update_detail(selected)

        refs['highlight_layer'].run_method(
            'setLatLng',
            [
                selected['lat'],
                selected['lon'],
            ],
        )

        if notify:
            ui.notify(
                f"Selected {selected['outlet']}",
                type='info',
                position='top',
            )

    def apply_filters(
        _: Any = None,
    ) -> None:
        state['region'] = (
            refs['region_select'].value
        )

        state['status'] = (
            refs['status_select'].value
        )

        state['search'] = (
            refs['search_input'].value
            or ''
        )

        rows = filtered_rows()

        update_kpis(rows)

        refs['filter_result'].set_text(
            f'{len(rows)} outlets shown'
            if rows
            else 'No matching outlets'
        )

        if not rows:
            replace_table_rows([])

            refs['table'].selected.clear()
            refs['table'].update()
            return

        visible_ids = {
            row['store_id']
            for row in rows
        }

        selected_id = (
            state['selected_id']
            if state['selected_id'] in visible_ids
            else rows[0]['store_id']
        )

        select_store(selected_id)

        region_center = REGION_CENTERS[
            state['region']
        ]

        refs['map'].set_center(
            (
                region_center[0],
                region_center[1],
            )
        )

        refs['map'].set_zoom(
            region_center[2]
        )

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
                and argument.get('store_id')
            ):
                select_store(
                    argument['store_id']
                )
                return

    def handle_map_click(
        event: events.GenericEventArguments,
    ) -> None:
        latitude_longitude = (
            event.args.get('latlng', {})
            if isinstance(event.args, dict)
            else {}
        )

        if (
            'lat' not in latitude_longitude
            or 'lng' not in latitude_longitude
        ):
            return

        nearest = min(
            stores,
            key=lambda store: _haversine_km(
                latitude_longitude['lat'],
                latitude_longitude['lng'],
                store['lat'],
                store['lon'],
            ),
        )

        distance = _haversine_km(
            latitude_longitude['lat'],
            latitude_longitude['lng'],
            nearest['lat'],
            nearest['lon'],
        )

        # Clicking directly on a dot gives a distance near zero.
        if distance <= 90:
            select_store(
                nearest['store_id'],
                move_to_top=True,
                notify=True,
            )

    async def run_network_analysis() -> None:
        refs['analysis_button'].disable()

        progress = ui.notification(
            'Refreshing outlet forecasts…',
            spinner=True,
            type='ongoing',
            timeout=None,
            position='top',
        )

        await asyncio.sleep(0.9)

        state['analysis_run'] += 1

        for store in stores:
            rng = random.Random(
                _stable_seed(store['store_id'])
                + state['analysis_run'] * 307
            )

            store['growth_pct'] = round(
                max(
                    -12.0,
                    min(
                        16.0,
                        store['growth_pct']
                        + rng.uniform(-2.2, 2.8),
                    ),
                ),
                1,
            )

            store['forecast_lakh'] = round(
                store['revenue_lakh']
                * (
                    1
                    + store['growth_pct']
                    / 100
                ),
                1,
            )

        update_kpis(
            filtered_rows()
        )

        select_store(
            state['selected_id']
        )

        refs['last_sync'].set_text(
            f"Updated {datetime.now():%H:%M} · "
            f"Forecast scenario "
            f"{state['analysis_run'] + 1}"
        )

        progress.dismiss()
        refs['analysis_button'].enable()

        ui.notify(
            'Network analysis refreshed',
            type='positive',
            icon='check_circle',
            position='top',
        )

    selected = stores[0]

    with ui.column().classes(
        'w-full max-w-[1580px] mx-auto '
        'px-4 md:px-7 py-6 gap-5'
    ):
        with ui.row().classes(
            'w-full items-start justify-between gap-4'
        ):
            with ui.column().classes('gap-1'):
                ui.label(
                    'NETWORK INTELLIGENCE'
                ).classes(
                    'section-kicker'
                )

                ui.label(
                    'National outlet performance command center'
                ).classes(
                    'text-2xl md:text-3xl '
                    'font-extrabold tracking-tight'
                )

                ui.label(
                    'Compare revenue, profitability, staffing, '
                    'and next-month outlook across the network.'
                ).classes(
                    'text-sm muted'
                )

            with ui.column().classes(
                'items-end gap-1 desktop-only'
            ):
                ui.badge(
                    f'{len(stores)} MOCK OUTLETS',
                    color='positive',
                ).props(
                    'outline'
                )

                refs['last_sync'] = ui.label(
                    'Simulated live data · Ready'
                ).classes(
                    'text-xs muted'
                )

        with ui.row().classes(
            'action-bar w-full p-3 gap-3 items-center'
        ):
            refs['region_select'] = ui.select(
                list(REGION_CENTERS),
                value='All regions',
                label='Region',
                on_change=apply_filters,
            ).props(
                'outlined dense'
            ).classes(
                'w-44'
            )

            refs['status_select'] = ui.select(
                [
                    'All statuses',
                    *STATUS_COLORS,
                ],
                value='All statuses',
                label='Performance status',
                on_change=apply_filters,
            ).props(
                'outlined dense'
            ).classes(
                'w-52'
            )

            refs['search_input'] = ui.input(
                label='Search outlet or city',
                on_change=apply_filters,
            ).props(
                'outlined dense clearable debounce=250'
            ).classes(
                'w-64'
            )

            refs['filter_result'] = ui.label(
                f'{len(stores)} outlets shown'
            ).classes(
                'text-xs muted'
            )

            ui.space()

            refs['analysis_button'] = ui.button(
                'Run network analysis',
                icon='analytics',
                on_click=run_network_analysis,
            ).props(
                'unelevated no-caps'
            ).classes(
                'rounded-xl px-5'
            )

        total_revenue = sum(
            row['revenue_lakh']
            for row in stores
        )

        total_profit = sum(
            row['profit_lakh']
            for row in stores
        )

        total_forecast = sum(
            row['forecast_lakh']
            for row in stores
        )

        with ui.grid(
            columns=5
        ).classes(
            'w-full gap-4 '
            'max-[1100px]:grid-cols-2 '
            'max-[650px]:grid-cols-1'
        ):
            (
                refs['network_revenue'],
                refs['network_revenue_sub'],
            ) = _metric_card(
                'Network revenue',
                f'₹{total_revenue / 100:.2f} crore',
                f'{len(stores)} visible outlets',
                'payments',
            )

            (
                refs['network_profit'],
                refs['network_profit_sub'],
            ) = _metric_card(
                'Operating profit',
                f'₹{total_profit / 100:.2f} crore',
                'Store operating profit',
                'account_balance_wallet',
            )

            (
                refs['network_forecast'],
                refs['network_forecast_sub'],
            ) = _metric_card(
                'Next-month forecast',
                f'₹{total_forecast / 100:.2f} crore',
                'Projected next month',
                'trending_up',
            )

            (
                refs['network_margin'],
                refs['network_margin_sub'],
            ) = _metric_card(
                'Weighted margin',
                (
                    f'{total_profit / total_revenue * 100:.1f}%'
                ),
                'Weighted operating margin',
                'percent',
            )

            (
                refs['network_employees'],
                refs['network_employees_sub'],
            ) = _metric_card(
                'Network employees',
                (
                    f"{sum(row['employees'] for row in stores):,}"
                ),
                'Employees in view',
                'groups',
            )

        with ui.grid(
            columns=12
        ).classes(
            'w-full gap-4 '
            'max-[1100px]:grid-cols-1'
        ):
            with ui.card().classes(
                    'surface col-span-8 p-5 w-full h-full '
                    'flex flex-col max-[1100px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(
                            'Outlet network map'
                        ).classes(
                            'text-lg font-bold'
                        )

                        ui.label(
                            'Click a store dot to select and '
                            'highlight its table row'
                        ).classes(
                            'text-xs muted'
                        )

                    with ui.row().classes(
                        'gap-2 items-center'
                    ):
                        for (
                            status,
                            color,
                        ) in STATUS_COLORS.items():
                            with ui.row().classes(
                                'gap-1 items-center no-wrap'
                            ):
                                ui.element(
                                    'span'
                                ).style(
                                    'width:9px;'
                                    'height:9px;'
                                    'border-radius:50%;'
                                    f'background:{color};'
                                    'display:inline-block;'
                                )

                                ui.label(
                                    status
                                ).classes(
                                    'text-[10px] muted'
                                )

                refs['map'] = ui.leaflet(
                    center=(22.8, 79.0),
                    zoom=5,
                ).classes(
                    'network-map '
                    'w-full flex-1 min-h-[700px] mt-3'
                )

                refs['map'].on(
                    'map-click',
                    handle_map_click,
                )

                for store in stores:
                    refs['map'].generic_layer(
                        name='circleMarker',
                        args=[
                            (
                                store['lat'],
                                store['lon'],
                            ),
                            {
                                'radius': 7,
                                'color': '#FFFFFF',
                                'weight': 2,
                                'fillColor': STATUS_COLORS[
                                    store['status']
                                ],
                                'fillOpacity': 0.92,
                                'bubblingMouseEvents': True,
                            },
                        ],
                    )

                refs[
                    'highlight_layer'
                ] = refs['map'].generic_layer(
                    name='circleMarker',
                    args=[
                        (
                            selected['lat'],
                            selected['lon'],
                        ),
                        {
                            'radius': 13,
                            'color': BURGUNDY,
                            'weight': 4,
                            'fillColor': GOLD,
                            'fillOpacity': 0.35,
                            'bubblingMouseEvents': True,
                        },
                    ],
                )

            with ui.card().classes(
                'network-detail col-span-4 p-5 w-full '
                'max-[1100px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start '
                    'justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        refs[
                            'selected_name'
                        ] = ui.label(
                            selected['outlet']
                        ).classes(
                            'text-xl font-extrabold '
                            'leading-tight'
                        )

                        refs[
                            'selected_location'
                        ] = ui.label(
                            f"{selected['city']} · "
                            f"{selected['region']} · "
                            f"{selected['format']}"
                        ).classes(
                            'text-xs text-white/65'
                        )

                    refs[
                        'selected_status'
                    ] = ui.badge(
                        selected['status'].upper()
                    ).style(
                        f"background:"
                        f"{STATUS_COLORS[selected['status']]};"
                        f"color:white;"
                    )

                ui.separator().classes(
                    'opacity-20 my-4'
                )

                with ui.grid(
                    columns=2
                ).classes(
                    'w-full gap-3'
                ):
                    summary_metrics = [
                        (
                            'CURRENT REVENUE',
                            'selected_revenue',
                            _format_lakh(
                                selected['revenue_lakh']
                            ),
                        ),
                        (
                            'OPERATING PROFIT',
                            'selected_profit',
                            _format_lakh(
                                selected['profit_lakh']
                            ),
                        ),
                        (
                            'NEXT MONTH',
                            'selected_forecast',
                            _format_lakh(
                                selected['forecast_lakh']
                            ),
                        ),
                        (
                            'EMPLOYEES',
                            'selected_employees',
                            str(selected['employees']),
                        ),
                    ]

                    for (
                        title,
                        reference_name,
                        value,
                    ) in summary_metrics:
                        with ui.column().classes('gap-0'):
                            ui.label(
                                title
                            ).classes(
                                'text-[10px] tracking-wider '
                                'text-white/55'
                            )

                            refs[
                                reference_name
                            ] = ui.label(
                                value
                            ).classes(
                                'text-lg font-bold'
                            )

                ui.separator().classes(
                    'opacity-20 my-4'
                )

                details = [
                    (
                        'Forecast growth',
                        'selected_growth',
                        f"{selected['growth_pct']:+.1f}%",
                    ),
                    (
                        'Operating margin',
                        'selected_margin',
                        f"{selected['margin_pct']:.1f}%",
                    ),
                    (
                        'Monthly orders',
                        'selected_orders',
                        f"{selected['monthly_orders']:,}",
                    ),
                    (
                        'Average ticket',
                        'selected_ticket',
                        f"₹{selected['average_ticket']}",
                    ),
                    (
                        'Delivery share',
                        'selected_delivery',
                        f"{selected['delivery_share_pct']}%",
                    ),
                    (
                        'Monthly rent',
                        'selected_rent',
                        _format_lakh(
                            selected['rent_lakh']
                        ),
                    ),
                    (
                        'Rent / revenue',
                        'selected_rent_ratio',
                        (
                            f"{selected['rent_ratio_pct']:.1f}%"
                        ),
                    ),
                    (
                        'Customer rating',
                        'selected_rating',
                        f"{selected['rating']:.1f} / 5",
                    ),
                    (
                        'Waste rate',
                        'selected_waste',
                        f"{selected['waste_pct']:.1f}%",
                    ),
                    (
                        'Stockout rate',
                        'selected_stockout',
                        (
                            f"{selected['stockout_pct']:.1f}%"
                        ),
                    ),
                ]

                with ui.grid(
                    columns=2
                ).classes(
                    'w-full gap-x-4 gap-y-3'
                ):
                    for (
                        label,
                        reference_name,
                        value,
                    ) in details:
                        with ui.column().classes('gap-0'):
                            ui.label(
                                label.upper()
                            ).classes(
                                'text-[9px] tracking-wider '
                                'text-white/45'
                            )

                            refs[
                                reference_name
                            ] = ui.label(
                                value
                            ).classes(
                                'text-sm font-semibold'
                            )

                observation, action = _ai_observation(
                    selected
                )

                ui.separator().classes(
                    'opacity-20 my-4'
                )

                ui.label(
                    'AI NETWORK OBSERVATION'
                ).classes(
                    'ai-badge'
                )

                refs[
                    'selected_observation'
                ] = ui.label(
                    observation
                ).classes(
                    'text-sm leading-relaxed '
                    'text-white/75 mt-3'
                )

                ui.label(
                    'RECOMMENDED ACTION'
                ).classes(
                    'text-[10px] tracking-wider '
                    'text-amber-200 font-bold mt-4'
                )

                refs[
                    'selected_action'
                ] = ui.label(
                    action
                ).classes(
                    'text-sm leading-relaxed '
                    'text-white/80'
                )

        with ui.card().classes(
            'surface w-full p-5 table-shell '
            'network-table'
        ):
            with ui.row().classes(
                'w-full items-start '
                'justify-between gap-4'
            ):
                with ui.column().classes('gap-0'):
                    ui.label(
                        'Outlet performance table'
                    ).classes(
                        'text-lg font-bold'
                    )

                    ui.label(
                        'Click a row to highlight the outlet '
                        'on the map and open its operating profile.'
                    ).classes(
                        'text-xs muted'
                    )

                ui.badge(
                    'MONTHLY VIEW',
                    color='primary',
                ).props(
                    'outline'
                )

            refs['table'] = ui.table(
                columns=TABLE_COLUMNS,
                rows=stores.copy(),
                row_key='store_id',
                selection='single',
                pagination={
                    'rowsPerPage': 12,
                },
            ).props(
                'flat bordered dense '
                'separator=horizontal '
                'hide-selected-banner'
            ).classes(
                'w-full mt-3'
            )

            refs['table'].on(
                'rowClick',
                handle_table_click,
                [
                    [],
                    ['store_id'],
                    None,
                ],
            )

            refs['table'].selected.append(
                selected
            )

            refs['table'].update()

        with ui.row().classes(
            'w-full justify-between items-center '
            'px-1 pb-3 gap-3'
        ):
            ui.label(
                'Prototype only · All outlet locations and '
                'financial values are simulated concept data.'
            ).classes(
                'text-[11px] muted'
            )

            ui.label(
                'Designed by Inventide'
            ).classes(
                'text-[11px] font-bold text-primary'
            )