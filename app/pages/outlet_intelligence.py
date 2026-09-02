from __future__ import annotations

import asyncio
import json
import uuid
from copy import deepcopy
from typing import Any

from nicegui import app, ui

from app.ai_chat import AIChatController, create_ai_chat
from app.company_context import PAGE_CONTEXTS
from app.session_ui import require_brand_login, render_brand_session_controls
from app.data.outlet_candidates import (
    OUTLET_STATE_SCHEMA_VERSION,
    SOURCE_CATALOG,
    clone_default_candidates,
    create_empty_candidate,
)
from app.services.currency_service import format_money
from app.services.location_service import (
    LocationSuggestion,
    create_location_service,
)
from app.services.outlet_analysis import calculate_location_analysis
from app.services.outlet_state_service import (
    OUTLET_PROCESS_BOOT_ID,
    persist_outlet_ai_snapshot,
)
from app.services.outlet_document_analysis import (
    MAX_DOCUMENTS,
    MAX_FILE_BYTES,
    MAX_TOTAL_BYTES,
    SUPPORTED_EXTENSIONS,
    OutletDocumentAnalysisService,
    OutletDocumentAnalysisError,
    validate_document,
)
from app.state.demo_state import get_brand_state
from app.theme import BURGUNDY, GOLD, GREEN, RED, apply_theme


OUTLET_STORAGE_KEY = 'vesper_outlet_intelligence_v2'
STATUS_COLORS = {
    'Recommended': GREEN,
    'Review': GOLD,
    'High risk': RED,
}


def _format_candidate_money(
    value: float,
    profile: dict[str, Any],
) -> str:
    # India candidate economics currently preserve the established MVP lakh
    # units; Canadian candidates use native CAD. Both are formatted here so
    # country-specific presentation never leaks into the page logic.
    if profile.get('currency_code') == 'INR':
        return f'₹{value:.1f} lakh'
    return format_money(value, profile, compact=True)


def _coordinate_bounds(profile: dict[str, Any]) -> tuple[float, float, float, float]:
    if profile.get('country_code') == 'CA':
        return 41.0, 84.0, -141.0, -52.0
    return 6.0, 38.0, 68.0, 98.0


def _format_bytes(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f'{size_bytes} B'
    if size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    return f'{size_bytes / (1024 * 1024):.1f} MB'


def _document_source_label(document: dict[str, Any]) -> str:
    size = _format_bytes(int(document.get('size_bytes') or 0))
    if document.get('source') == 'demo':
        if isinstance(document.get('content'), (bytes, bytearray)):
            return f'Preloaded demo document · {size}'
        return 'Preloaded demo metadata'
    return size


def _download_document(document: dict[str, Any]) -> None:
    content = document.get('content')
    if not isinstance(content, (bytes, bytearray)):
        ui.notify(
            'This record does not contain a downloadable file.',
            type='warning',
        )
        return

    ui.download(
        bytes(content),
        filename=str(document.get('name') or 'document'),
        media_type=str(
            document.get('content_type') or 'application/octet-stream'
        ),
    )


def _status(status: str) -> None:
    color = STATUS_COLORS.get(status, BURGUNDY)
    ui.badge(status).style(f'background:{color};color:white;')


def _metric(title: str, value: str, subtitle: str, icon: str) -> None:
    with ui.card().classes('metric-card p-4 w-full'):
        with ui.row().classes(
            'w-full items-start justify-between no-wrap'
        ):
            with ui.column().classes('gap-1'):
                ui.label(title).classes('text-xs font-semibold muted')
                ui.label(value).classes('text-xl font-bold tracking-tight')
                ui.label(subtitle).classes('text-[11px] muted')
            with ui.element('div').classes('metric-icon'):
                ui.icon(icon).classes('text-xl')


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
    ).props('flat no-caps align=left').classes(classes)
    button.style(
        'color: #FFFFFF !important; font-weight: 700;'
        if active
        else (
            'color: rgba(255,255,255,0.90) !important; '
            'font-weight: 600;'
        )
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

    drawer = ui.left_drawer(value=True).classes(
        'app-drawer p-4'
    ).props('width=260 bordered')

    with drawer:
        with ui.column().classes('w-full h-full gap-2'):
            ui.label('OPERATIONS').classes(
                'text-[10px] font-bold tracking-[0.18em] '
                'opacity-50 px-3 mt-3 mb-1'
            )
            _nav_item(
                'Command Center',
                'space_dashboard',
                route='/command-center',
            )
            _nav_item(
                'Demand & Inventory',
                'inventory_2',
                route='/demand-inventory',
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
            )

            ui.label('INNOVATE').classes(
                'text-[10px] font-bold tracking-[0.18em] '
                'opacity-50 px-3 mt-5 mb-1'
            )
            _nav_item(
                'Product Innovation',
                'science',
                route='/product-innovation',
            )

            ui.space()
            with ui.card().classes(
                'w-full p-4 bg-white/10 border-0 rounded-2xl text-white'
            ):
                with ui.row().classes(
                    'items-center gap-3 no-wrap w-full'
                ):
                    ui.image('/assets/inventide_logo.png').classes(
                        'w-10 h-10 object-cover rounded-full shrink-0'
                    )
                    with ui.column().classes('gap-0 min-w-0'):
                        ui.label('VESPER').classes(
                            'text-sm font-black tracking-[0.16em] text-white'
                        )
                        ui.label('Supply Chain Intelligence').classes(
                            'text-[11px] text-white/90 whitespace-nowrap'
                        )
                ui.separator().classes('opacity-20 my-3')
                ui.label('AI-powered supply chain engine').classes(
                    'text-xs text-white/90 leading-relaxed'
                )
                ui.label('Demo workspace · v0.1').classes(
                    'text-[10px] text-white/70 mt-2'
                )

    with ui.header().classes(
        'app-header h-16 px-4 md:px-7 items-center justify-between'
    ):
        with ui.row().classes('items-center gap-3 no-wrap'):
            ui.button(
                icon='menu',
                on_click=drawer.toggle,
            ).props('flat round dense').classes('lg:hidden')
            ui.image('/assets/inventide_logo.png').classes(
                'w-11 h-11 object-cover rounded-full'
            )
            with ui.column().classes('gap-0'):
                ui.label('SUPPLY CHAIN INTELLIGENCE').classes(
                    'text-sm font-extrabold tracking-wide'
                )
                ui.label('Powered by Inventide').classes(
                    'text-[11px] muted'
                )

        with ui.row().classes('items-center gap-3'):
            render_brand_session_controls()

            ui.badge('CONCEPT DATA', color='secondary').props(
                'outline'
            ).classes('desktop-only')
            ui.button(
                'Ask AI',
                icon='auto_awesome',
                on_click=ai_chat.open,
            ).props('unelevated no-caps').classes('rounded-xl')


def _get_tab_state(brand_id: str) -> dict[str, Any]:
    storage_key = f'{OUTLET_STORAGE_KEY}:{brand_id}'
    stored = app.storage.tab.get(storage_key)
    if (
        not isinstance(stored, dict)
        or stored.get('schema_version') != OUTLET_STATE_SCHEMA_VERSION
        or stored.get('process_boot_id') != OUTLET_PROCESS_BOOT_ID
        or stored.get('brand_id') != brand_id
        or not isinstance(stored.get('candidates'), dict)
    ):
        stored = {
            'schema_version': OUTLET_STATE_SCHEMA_VERSION,
            'process_boot_id': OUTLET_PROCESS_BOOT_ID,
            'brand_id': brand_id,
            'candidates': clone_default_candidates(brand_id),
            'decisions': {},
            'selected': None,
        }
        app.storage.tab[storage_key] = stored
    return stored


@ui.page('/outlet-intelligence')
async def outlet_intelligence_page() -> None:
    brand_profile = require_brand_login()
    if brand_profile is None:
        return
    brand_id = str(brand_profile['brand_id'])
    brand_state = get_brand_state(app.storage.user, brand_id)

    apply_theme()
    ui.add_css(
        '''
        .location-map {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(90,21,52,.09);
        }
        .candidate-row {
            border: 1px solid rgba(90,21,52,.09);
            border-radius: 14px;
            background: #fffdf8;
            transition: 160ms ease;
        }
        .candidate-row:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(59,13,34,.07);
        }
        .verdict-panel {
            background: linear-gradient(150deg,#3B0D22,#5A1534);
            color: white;
            border-radius: 18px;
        }
        .address-suggestion {
            border: 1px solid rgba(90,21,52,.10);
            border-radius: 12px;
            background: #fffdf8;
        }
        .address-suggestion:hover {
            background: rgba(90,21,52,.04);
        }
        .document-row {
            border: 1px solid rgba(90,21,52,.09);
            border-radius: 12px;
            background: rgba(255,253,248,.8);
        }
        .evidence-column {
            border-left: 3px solid rgba(90,21,52,.18);
            padding-left: 12px;
        }
        '''
    )

    ai_chat = create_ai_chat(
        page_name='Outlet Intelligence',
        page_context=PAGE_CONTEXTS['outlet_intelligence'],
    )
    _render_shell(ai_chat)

    # ``app.storage.tab`` is intentionally volatile and unique to this browser
    # tab, but NiceGUI only exposes it after the WebSocket is connected.
    # This is what lets edits survive route navigation while a server restart
    # restores the original four demo candidates.
    await ui.context.client.connected()
    tab_state = _get_tab_state(brand_id)
    candidates: dict[str, dict[str, Any]] = tab_state['candidates']
    decisions: dict[str, str] = tab_state.setdefault('decisions', {})
    page_state = {
        'selected': tab_state.get('selected'),
        'analysis_run': 0,
    }
    persist_outlet_ai_snapshot(
        brand_state,
        candidates=candidates,
        decisions=decisions,
        selected=page_state['selected'],
    )
    refs: dict[str, Any] = {}
    marker_layers: dict[str, Any] = {}
    map_event_name = f'outlet-candidate-{uuid.uuid4().hex}'
    location_service = create_location_service(brand_profile)
    document_service = OutletDocumentAnalysisService()

    def persist_state() -> None:
        tab_state['selected'] = page_state['selected']
        tab_state['candidates'] = candidates
        tab_state['decisions'] = decisions
        app.storage.tab[f'{OUTLET_STORAGE_KEY}:{brand_id}'] = tab_state

        # Publish only the small AI-safe view to canonical brand state. Raw
        # uploaded document bytes remain in tab storage and are never copied
        # into app.storage.user.
        persist_outlet_ai_snapshot(
            brand_state,
            candidates=candidates,
            decisions=decisions,
            selected=page_state['selected'],
        )

    def update_candidate_count() -> None:
        if 'candidate_count' in refs:
            refs['candidate_count'].set_text(
                f'{len(candidates)} CANDIDATE'
                f'{"S" if len(candidates) != 1 else ""}'
            )

    def show_sources(
        signal: tuple[str, str, str, str, str, str]
    ) -> None:
        title, value, _tone, points, source_key, evidence = signal
        source_name, source_type, freshness = SOURCE_CATALOG.get(
            source_key,
            ('Prototype source', 'Simulated evidence', 'Current demo'),
        )
        refs['source_content'].clear()
        with refs['source_content']:
            ui.label(title).classes('text-lg font-bold')
            ui.label(f'{value} · {points}').classes('text-sm muted')
            ui.separator().classes('my-3')
            ui.label(source_name).classes('text-sm font-bold')
            ui.label(source_type).classes('text-xs muted')
            ui.badge(freshness, color='primary').props(
                'outline'
            ).classes('mt-2')
            ui.label(evidence).classes(
                'text-sm leading-relaxed mt-3'
            )
        refs['source_dialog'].open()

    def set_decision(decision: str) -> None:
        candidate_id = page_state['selected']
        if candidate_id not in candidates:
            return
        decisions[candidate_id] = decision
        persist_state()
        if 'decision' in refs:
            refs['decision'].set_text(f'Workflow status: {decision}')
        ui.notify(
            f"{candidates[candidate_id]['name']} marked as {decision}.",
            type='positive',
        )

    def render_document_analysis(candidate: dict[str, Any]) -> None:
        raw = candidate.get('document_analysis')
        if not isinstance(raw, dict):
            with ui.card().classes('surface w-full p-5 mt-4'):
                ui.label('DOCUMENT INTELLIGENCE').classes(
                    'section-kicker'
                )
                ui.label('No document analysis yet').classes(
                    'text-lg font-bold'
                )
                ui.label(
                    'Upload source files or add site notes, save the '
                    'candidate, and run Analyze.',
                ).classes('text-sm muted mt-1')
            return

        source_mode = str(raw.get('source_mode') or 'demo')
        mode_label = (
            'VESPER RAG ENGINE'
            if source_mode == 'openai'
            else 'VESPER LOCAL RAG FALLBACK'
        )
        mode_color = 'positive' if source_mode == 'openai' else 'secondary'

        with ui.card().classes('surface w-full p-5 mt-4'):
            with ui.row().classes(
                'w-full items-start justify-between gap-3'
            ):
                with ui.column().classes('gap-0'):
                    ui.label('DOCUMENT INTELLIGENCE').classes(
                        'section-kicker'
                    )
                    ui.label('Evidence extracted from candidate files').classes(
                        'text-lg font-bold'
                    )
                ui.badge(mode_label, color=mode_color).props('outline')

            ui.label(str(raw.get('summary') or '')).classes(
                'text-sm leading-relaxed mt-3'
            )

            with ui.grid(columns=2).classes(
                'w-full gap-4 mt-4 max-[850px]:grid-cols-1'
            ):
                with ui.column().classes('gap-2'):
                    ui.label('Positive signals').classes('text-sm font-bold')
                    values = raw.get('positive_signals') or []
                    if not values:
                        ui.label('None extracted.').classes('text-xs muted')
                    for value in values:
                        with ui.row().classes('items-start gap-2 no-wrap'):
                            ui.icon('check_circle').style(f'color:{GREEN};')
                            ui.label(str(value)).classes(
                                'text-sm leading-relaxed'
                            )

                with ui.column().classes('gap-2'):
                    ui.label('Risks and constraints').classes(
                        'text-sm font-bold'
                    )
                    values = raw.get('risks') or []
                    if not values:
                        ui.label('None extracted.').classes('text-xs muted')
                    for value in values:
                        with ui.row().classes('items-start gap-2 no-wrap'):
                            ui.icon('warning_amber').style(f'color:{RED};')
                            ui.label(str(value)).classes(
                                'text-sm leading-relaxed'
                            )

                with ui.column().classes('gap-2'):
                    ui.label('Lease obligations').classes(
                        'text-sm font-bold'
                    )
                    values = raw.get('lease_obligations') or []
                    if not values:
                        ui.label('None explicitly extracted.').classes(
                            'text-xs muted'
                        )
                    for value in values:
                        ui.label(f'• {value}').classes(
                            'text-sm leading-relaxed'
                        )

                with ui.column().classes('gap-2'):
                    ui.label('Accessibility notes').classes(
                        'text-sm font-bold'
                    )
                    values = raw.get('accessibility_notes') or []
                    if not values:
                        ui.label('None explicitly extracted.').classes(
                            'text-xs muted'
                        )
                    for value in values:
                        ui.label(f'• {value}').classes(
                            'text-sm leading-relaxed'
                        )

                with ui.column().classes('gap-2'):
                    ui.label('Missing information').classes(
                        'text-sm font-bold'
                    )
                    for value in raw.get('missing_information') or []:
                        ui.label(f'• {value}').classes(
                            'text-sm leading-relaxed'
                        )

                with ui.column().classes('gap-2'):
                    ui.label('Recommended follow-up').classes(
                        'text-sm font-bold'
                    )
                    for value in raw.get('follow_up_questions') or []:
                        ui.label(f'• {value}').classes(
                            'text-sm leading-relaxed'
                        )

            evidence = raw.get('evidence') or []
            if evidence:
                ui.separator().classes('my-4')
                ui.label('File-level evidence').classes('text-sm font-bold')
                with ui.column().classes('w-full gap-3 mt-2'):
                    for item in evidence:
                        if not isinstance(item, dict):
                            continue
                        with ui.column().classes('gap-0 evidence-column'):
                            with ui.row().classes(
                                'items-center gap-2 flex-wrap'
                            ):
                                ui.label(
                                    str(item.get('document_name') or 'Document')
                                ).classes('text-sm font-bold')
                                ui.badge(
                                    str(item.get('confidence') or 'low').upper(),
                                    color='primary',
                                ).props('outline')
                            ui.label(
                                str(item.get('finding') or '')
                            ).classes('text-xs muted leading-relaxed')

            warnings = raw.get('warnings') or []
            for warning in warnings:
                with ui.row().classes(
                    'items-start gap-2 no-wrap mt-3 p-3 rounded-xl '
                    'bg-amber-50 border border-amber-200'
                ):
                    ui.icon('info').classes('text-amber-700')
                    ui.label(str(warning)).classes(
                        'text-xs text-amber-900 leading-relaxed'
                    )

    def render_details(candidate_id: str) -> None:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            refs['details'].clear()
            return

        page_state['selected'] = candidate_id
        persist_state()
        refs['details'].clear()
        with refs['details']:
            with ui.row().classes(
                'w-full items-start justify-between gap-3'
            ):
                with ui.column().classes('gap-1'):
                    ui.label('AI LOCATION VERDICT').classes('section-kicker')
                    ui.label(candidate['name']).classes(
                        'text-2xl font-extrabold'
                    )
                    ui.label(candidate['address']).classes('text-sm muted')
                with ui.column().classes('items-end gap-1'):
                    _status(candidate['status'])
                    refs['decision'] = ui.label(
                        'Workflow status: '
                        f"{decisions.get(candidate_id, 'Not decided')}"
                    ).classes('text-xs muted')

            with ui.grid(columns=5).classes(
                'w-full gap-4 mt-4 max-[1100px]:grid-cols-2 '
                'max-[650px]:grid-cols-1'
            ):
                _metric(
                    'Location score',
                    f"{candidate['score']} / 100",
                    'Deterministic composite score',
                    'stars',
                )
                _metric(
                    'Expected monthly sales',
                    _format_candidate_money(float(candidate['sales']), brand_profile),
                    'Simulated base scenario',
                    'payments',
                )
                _metric(
                    'Contribution margin',
                    f"{float(candidate['margin']):.1f}%",
                    'Prototype operating model',
                    'percent',
                )
                _metric(
                    'Break-even',
                    f"{candidate['break_even']} months",
                    'Prototype payback estimate',
                    'schedule',
                )
                _metric(
                    'Cannibalization',
                    str(candidate['cannibalization']),
                    'Simulated network overlap',
                    'hub',
                )

            with ui.grid(columns=5).classes(
                'w-full gap-4 mt-4 max-[1050px]:grid-cols-1'
            ):
                with ui.card().classes(
                    'surface col-span-2 p-5 w-full max-[1050px]:col-span-1'
                ):
                    with ui.row().classes(
                        'w-full items-start justify-between gap-3'
                    ):
                        with ui.column().classes('gap-0'):
                            ui.label('SUBMITTED LOCATION RECORD').classes(
                                'section-kicker'
                            )
                            ui.label('Team inputs and files').classes(
                                'text-lg font-bold'
                            )
                        ui.button(
                            'Edit',
                            icon='edit',
                            on_click=lambda cid=candidate_id: (
                                open_candidate_editor(cid)
                            ),
                        ).props('outline dense no-caps')

                    with ui.grid(columns=2).classes(
                        'w-full gap-3 mt-4 max-[650px]:grid-cols-1'
                    ):
                        for label, value in (
                            ('Monthly rent', _format_candidate_money(float(candidate['rent']), brand_profile)),
                            ('Square footage', f"{candidate['sqft']:,} sq. ft."),
                            ('City', candidate.get('city') or 'Not supplied'),
                            (
                                'Postal code'
                                if brand_profile.get('country_code') == 'CA'
                                else 'PIN code',
                                candidate.get('pincode') or 'Not supplied',
                            ),
                        ):
                            with ui.column().classes('gap-0'):
                                ui.label(label).classes(
                                    'text-[10px] font-bold tracking-wide muted'
                                )
                                ui.label(str(value)).classes('text-sm font-bold')

                    optional = candidate.get('optional') or {}
                    ui.separator().classes('my-4')
                    for key in ('Frontage', 'Floor', 'Parking'):
                        value = optional.get(key) or 'Not supplied'
                        ui.label(f'{key}: {value}').classes('text-sm')

                    ui.label('Location notes').classes(
                        'text-sm font-bold mt-4'
                    )
                    ui.label(
                        candidate.get('notes') or 'No notes supplied.'
                    ).classes('text-sm muted leading-relaxed')

                    ui.label('Documents').classes('text-sm font-bold mt-4')
                    documents = candidate.get('documents') or []
                    if not documents:
                        ui.label('No documents uploaded.').classes(
                            'text-xs muted'
                        )
                    for document in documents:
                        with ui.row().classes(
                            'w-full items-center justify-between gap-2 no-wrap mt-1'
                        ):
                            with ui.row().classes(
                                'items-center gap-2 no-wrap min-w-0'
                            ):
                                ui.icon('description').classes('text-primary')
                                with ui.column().classes('gap-0 min-w-0'):
                                    ui.label(
                                        str(document.get('name') or 'Document')
                                    ).classes('text-sm font-medium truncate')
                                    ui.label(
                                        _document_source_label(document)
                                    ).classes('text-[10px] muted')
                            if isinstance(
                                document.get('content'),
                                (bytes, bytearray),
                            ):
                                ui.button(
                                    icon='download',
                                    on_click=lambda _event=None, doc=document: (
                                        _download_document(doc)
                                    ),
                                ).props(
                                    'flat round dense color=primary'
                                ).tooltip('Download demo document')

                with ui.card().classes(
                    'verdict-panel col-span-3 p-5 w-full '
                    'max-[1050px]:col-span-1'
                ):
                    with ui.row().classes(
                        'w-full items-center justify-between gap-3'
                    ):
                        ui.label('AI RECOMMENDATION').classes('ai-badge')
                        ui.label(
                            f"{candidate['score']} / 100"
                        ).classes('text-xl font-black text-amber-200')
                    ui.label(candidate['verdict']).classes(
                        'text-2xl font-extrabold mt-4'
                    )
                    ui.label(candidate['summary']).classes(
                        'text-sm text-white/75 leading-relaxed mt-2'
                    )
                    ui.separator().classes('opacity-20 my-4')
                    ui.label('RECOMMENDED FORMAT').classes(
                        'text-[10px] tracking-wider text-white/55'
                    )
                    ui.label(candidate['format']).classes(
                        'text-lg font-bold text-amber-200'
                    )
                    ui.label(
                        f"Analysis status: {candidate.get('analysis_status', 'Unknown')}"
                    ).classes('text-xs text-white/60 mt-4')

            render_document_analysis(candidate)

            signals = candidate.get('signals') or []
            with ui.card().classes('surface w-full p-5 mt-4'):
                with ui.row().classes(
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(
                            'Explainable verdict and source evidence'
                        ).classes('text-lg font-bold')
                        ui.label(
                            'Numerical outputs are calculated by deterministic '
                            'prototype logic; external location signals remain simulated.',
                        ).classes('text-xs muted')
                    ui.badge(
                        f'{len(signals)} SIGNALS',
                        color='primary',
                    ).props('outline')

                with ui.grid(columns=3).classes(
                    'w-full gap-3 mt-4 max-[1000px]:grid-cols-2 '
                    'max-[700px]:grid-cols-1'
                ):
                    for signal in signals:
                        title, value, tone, points, _source_key, evidence = signal
                        positive = tone == 'positive'
                        color = GREEN if positive else RED
                        icon = 'trending_up' if positive else 'warning_amber'
                        with ui.card().classes(
                            'p-4 rounded-xl shadow-none border '
                            'border-[#eee4e8]'
                        ).style(f'border-left:4px solid {color};'):
                            with ui.row().classes(
                                'w-full items-start justify-between gap-2'
                            ):
                                with ui.row().classes(
                                    'items-start gap-2 no-wrap'
                                ):
                                    ui.icon(icon).style(f'color:{color};')
                                    with ui.column().classes('gap-0'):
                                        ui.label(title).classes(
                                            'text-sm font-bold'
                                        )
                                        ui.label(value).classes('text-xs muted')
                                ui.badge(points).style(
                                    f'background:{color};color:white;'
                                )
                            ui.label(evidence).classes(
                                'text-xs muted leading-relaxed mt-3'
                            )
                            ui.button(
                                'View source',
                                icon='source',
                                on_click=lambda s=signal: show_sources(s),
                            ).props(
                                'flat dense no-caps color=primary'
                            ).classes('text-xs mt-2')

            with ui.row().classes('w-full justify-end gap-2 mt-4 flex-wrap'):
                ui.button(
                    'Request more information',
                    icon='help_outline',
                    on_click=lambda: set_decision(
                        'More information requested'
                    ),
                ).props('outline no-caps').classes('rounded-xl')
                ui.button(
                    'Reject candidate',
                    icon='close',
                    on_click=lambda: set_decision('Rejected'),
                ).props('outline no-caps color=negative').classes(
                    'rounded-xl'
                )
                ui.button(
                    'Shortlist candidate',
                    icon='bookmark_added',
                    on_click=lambda: set_decision('Shortlisted'),
                ).props('unelevated no-caps').classes('rounded-xl')

    async def bind_marker(candidate_id: str, layer: Any) -> None:
        candidate = candidates[candidate_id]
        await candidate_map.initialized()
        candidate_map.run_layer_method(
            layer.id,
            'bindTooltip',
            f"{candidate['name']} · {candidate['status']}",
        )
        cid_json = json.dumps(candidate_id)
        event_json = json.dumps(map_event_name)
        candidate_map.run_layer_method(
            layer.id,
            ':on',
            '"click"',
            (
                'function() {'
                f' emitEvent({event_json}, {{candidate_id: {cid_json}}});'
                ' }'
            ),
        )

    async def rebuild_markers(
        *,
        focus_candidate_id: str | None = None,
    ) -> None:
        await candidate_map.initialized()
        for layer in list(marker_layers.values()):
            try:
                candidate_map.remove_layer(layer)
            except Exception:
                # A layer may already have been removed after a reconnect.
                pass
        marker_layers.clear()

        for candidate_id, candidate in candidates.items():
            lat = candidate.get('lat')
            lng = candidate.get('lng')
            if not isinstance(lat, (int, float)) or not isinstance(
                lng,
                (int, float),
            ):
                continue
            layer = candidate_map.generic_layer(
                name='circleMarker',
                args=[
                    [float(lat), float(lng)],
                    {
                        'radius': 10,
                        'color': '#FFFFFF',
                        'weight': 3,
                        'fillColor': STATUS_COLORS.get(
                            str(candidate.get('status')),
                            BURGUNDY,
                        ),
                        'fillOpacity': 1.0,
                    },
                ],
            )
            marker_layers[candidate_id] = layer
            await bind_marker(candidate_id, layer)

        if focus_candidate_id in candidates:
            focused = candidates[focus_candidate_id]
            if isinstance(focused.get('lat'), (int, float)) and isinstance(
                focused.get('lng'),
                (int, float),
            ):
                candidate_map.run_map_method(
                    'setView',
                    [float(focused['lat']), float(focused['lng'])],
                    12,
                )
        elif not candidates:
            candidate_map.run_map_method(
                'setView',
                [
                    float(brand_profile['map_center_lat']),
                    float(brand_profile['map_center_lon']),
                ],
                int(brand_profile['map_zoom']),
            )

    async def analyze(candidate_id: str) -> None:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            return

        page_state['selected'] = candidate_id
        page_state['analysis_run'] += 1
        run_id = page_state['analysis_run']
        persist_state()

        refs['analysis'].clear()
        refs['details'].clear()
        with refs['analysis']:
            with ui.card().classes('surface w-full p-5'):
                ui.label('AI LOCATION ANALYSIS').classes('section-kicker')
                ui.label(f"Evaluating {candidate['name']}").classes(
                    'text-xl font-bold'
                )
                progress_text = ui.label(
                    'Validating the candidate record…'
                ).classes('text-sm muted')
                progress = ui.linear_progress(value=0).props(
                    'rounded color=primary track-color=grey-3'
                ).classes('w-full mt-4')

        async def set_progress(value: float, text: str) -> bool:
            if run_id != page_state['analysis_run']:
                return False
            progress_text.set_text(text)
            progress.value = value
            progress.update()
            await asyncio.sleep(0.18)
            return True

        if not await set_progress(0.15, 'Reading structured site inputs…'):
            return
        if not await set_progress(0.32, 'Preparing uploaded files…'):
            return

        try:
            document_analysis = await document_service.analyze(
                candidate,
                profile=brand_profile,
            )
        except OutletDocumentAnalysisError as exc:
            refs['analysis'].clear()
            ui.notify(str(exc), type='negative')
            return

        if run_id != page_state['analysis_run']:
            return
        candidate['document_analysis'] = document_analysis.model_dump()
        candidate['analysis_mode'] = document_analysis.source_mode

        if not await set_progress(
            0.67,
            'Calculating location economics and risk signals…',
        ):
            return
        calculate_location_analysis(candidate, candidates, brand_profile)

        if not await set_progress(
            0.86,
            'Building the explainable management verdict…',
        ):
            return
        persist_state()
        candidate_list.refresh()
        update_candidate_count()
        await rebuild_markers(focus_candidate_id=candidate_id)

        if run_id == page_state['analysis_run']:
            refs['analysis'].clear()
            render_details(candidate_id)
            analysis_label = (
                'Vesper RAG Engine'
                if document_analysis.source_mode == 'openai'
                else 'Vesper local RAG fallback'
            )
            ui.notify(
                f"Verdict generated for {candidate['name']} using "
                f'{analysis_label}.',
                type='positive',
                icon='verified',
            )

    async def marker_event(event: Any) -> None:
        args = event.args if isinstance(event.args, dict) else {}
        candidate_id = args.get('candidate_id')
        if candidate_id in candidates:
            await analyze(candidate_id)

    def open_candidate_editor(candidate_id: str | None = None) -> None:
        is_new = candidate_id is None
        if is_new:
            working_id = f'candidate-{uuid.uuid4().hex[:10]}'
            draft = create_empty_candidate(working_id, brand_id)
        else:
            if candidate_id not in candidates:
                ui.notify('Candidate no longer exists.', type='warning')
                return
            working_id = str(candidate_id)
            draft = deepcopy(candidates[working_id])

        original = deepcopy(draft)
        search_state: dict[str, Any] = {
            'generation': 0,
            'suggestions': [],
            'suppress_value': '',
            'resolved_address': str(draft.get('address') or ''),
        }

        with ui.dialog() as dialog:
            dialog.props('persistent')
            with ui.card().classes(
                'w-[920px] max-w-[96vw] max-h-[92vh] overflow-auto '
                'p-6 rounded-2xl'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(
                            'ADD SHORTLISTED LOCATION'
                            if is_new
                            else 'EDIT SHORTLISTED LOCATION'
                        ).classes('section-kicker')
                        ui.label(
                            'Create a candidate record'
                            if is_new
                            else f"Update {draft.get('name', 'candidate')}"
                        ).classes('text-2xl font-extrabold')
                        ui.label(
                            'Address, monthly rent and square footage are '
                            'required. Location name, files and site notes are '
                            'optional.',
                        ).classes('text-sm muted')
                    ui.button(
                        icon='close',
                        on_click=dialog.close,
                    ).props('flat round dense')

                ui.separator().classes('my-4')

                with ui.grid(columns=2).classes(
                    'w-full gap-4 max-[760px]:grid-cols-1'
                ):
                    name_input = ui.input(
                        'Location name',
                        value=str(draft.get('name') or ''),
                        placeholder=(
                            'Example: CF Toronto Eaton Centre'
                            if brand_profile.get('country_code') == 'CA'
                            else 'Example: Phoenix Marketcity, Pune'
                        ),
                    ).props('outlined')
                    rent_input = ui.number(
                        (
                            'Monthly rent in CAD *'
                            if brand_profile.get('country_code') == 'CA'
                            else 'Monthly rent in lakh INR *'
                        ),
                        value=float(draft.get('rent') or 0.0),
                        min=(100.0 if brand_profile.get('country_code') == 'CA' else 0.01),
                        step=(100.0 if brand_profile.get('country_code') == 'CA' else 0.05),
                    ).props('outlined')

                address_input = ui.input(
                    'Full address *',
                    value=str(draft.get('address') or ''),
                    placeholder=(
                        'Start typing a Canadian city, mall or address'
                        if brand_profile.get('country_code') == 'CA'
                        else 'Start typing an Indian locality, road or POI'
                    ),
                ).props('outlined clearable').classes('w-full mt-3')

                with ui.row().classes(
                    'w-full items-center justify-between gap-3 mt-1'
                ):
                    provider_text = (
                        f'Live suggestions: {location_service.provider_label}'
                        if location_service.is_live
                        else (
                            'Offline Canadian demo suggestions active.'
                            if brand_profile.get('country_code') == 'CA'
                            else (
                                'Offline demo suggestions active. Add '
                                'MAPPLS_REST_KEY for live Indian search.'
                            )
                        )
                    )
                    address_status = ui.label(provider_text).classes(
                        'text-[11px] muted'
                    )
                    ui.label('Type at least 3 characters').classes(
                        'text-[11px] muted'
                    )

                @ui.refreshable
                def suggestion_list() -> None:
                    suggestions: list[LocationSuggestion] = search_state[
                        'suggestions'
                    ]
                    if not suggestions:
                        return
                    with ui.card().classes(
                        'w-full p-2 mt-2 shadow-none rounded-xl '
                        'border border-[#eee4e8]'
                    ):
                        for suggestion in suggestions:
                            async def choose(
                                selected: LocationSuggestion = suggestion,
                            ) -> None:
                                address_status.set_text(
                                    f'Resolving {selected.display_name}…'
                                )
                                resolved = await location_service.resolve(
                                    selected
                                )
                                address = (
                                    resolved.formatted_address
                                    or selected.formatted_address
                                )
                                search_state['suppress_value'] = address
                                search_state['resolved_address'] = address
                                address_input.set_value(address)
                                if is_new and not str(name_input.value or '').strip():
                                    name_input.set_value(
                                        resolved.display_name
                                        or selected.display_name
                                    )
                                city_input.set_value(resolved.city)
                                state_input.set_value(resolved.state)
                                pincode_input.set_value(resolved.postal_code)
                                if resolved.latitude is not None:
                                    latitude_input.set_value(
                                        resolved.latitude
                                    )
                                if resolved.longitude is not None:
                                    longitude_input.set_value(
                                        resolved.longitude
                                    )
                                draft['address_provider'] = resolved.provider
                                draft['provider_place_id'] = (
                                    resolved.provider_id
                                )
                                draft['address_confirmed'] = True
                                search_state['suggestions'] = []
                                suggestion_list.refresh()
                                if resolved.has_coordinates:
                                    address_status.set_text(
                                        'Address selected and map coordinates resolved.'
                                    )
                                else:
                                    warning = location_service.last_warning
                                    address_status.set_text(
                                        warning
                                        or (
                                            'Address selected. Coordinate access '
                                            'is unavailable; enter latitude and '
                                            'longitude below.'
                                        )
                                    )

                            with ui.button(
                                on_click=choose,
                            ).props(
                                'flat no-caps align=left'
                            ).classes(
                                'address-suggestion w-full p-2 text-left'
                            ):
                                with ui.row().classes(
                                    'items-start gap-2 no-wrap w-full'
                                ):
                                    ui.icon('location_on').classes(
                                        'text-primary mt-1'
                                    )
                                    with ui.column().classes(
                                        'gap-0 items-start min-w-0'
                                    ):
                                        ui.label(
                                            suggestion.display_name
                                        ).classes(
                                            'text-sm font-bold text-left'
                                        )
                                        ui.label(
                                            suggestion.formatted_address
                                        ).classes(
                                            'text-xs muted text-left '
                                            'whitespace-normal'
                                        )
                                        ui.label(
                                            suggestion.provider.upper()
                                        ).classes(
                                            'text-[9px] font-bold tracking-wide muted'
                                        )

                suggestion_list()

                async def address_changed(event: Any) -> None:
                    value = str(event.value or '').strip()
                    if value == search_state.get('suppress_value'):
                        search_state['suppress_value'] = ''
                        return
                    draft['address_confirmed'] = False
                    draft['address_provider'] = 'manual'
                    draft['provider_place_id'] = ''
                    if value != search_state.get('resolved_address'):
                        # Never keep a stale map point after the user edits the
                        # address manually. A suggestion, geocode result, or
                        # explicit coordinate entry must establish the new pin.
                        latitude_input.set_value(None)
                        longitude_input.set_value(None)
                        search_state['resolved_address'] = ''
                    search_state['generation'] += 1
                    generation = search_state['generation']
                    search_state['suggestions'] = []
                    suggestion_list.refresh()
                    if len(value) < 3:
                        address_status.set_text(
                            'Type at least 3 characters for suggestions.'
                        )
                        return
                    address_status.set_text(
                        f"Searching {brand_profile['country']} addresses…"
                    )
                    await asyncio.sleep(0.40)
                    if generation != search_state['generation']:
                        return
                    suggestions = await location_service.suggest(value, limit=6)
                    if generation != search_state['generation']:
                        return
                    search_state['suggestions'] = suggestions
                    suggestion_list.refresh()
                    if suggestions:
                        message = f'{len(suggestions)} probable address(es) found.'
                    else:
                        message = (
                            location_service.last_warning
                            or (
                                'No suggestions found. You can keep the '
                                'address and enter map coordinates manually.'
                            )
                        )
                    address_status.set_text(message)

                address_input.on_value_change(address_changed)

                with ui.grid(columns=3).classes(
                    'w-full gap-4 mt-3 max-[760px]:grid-cols-1'
                ):
                    city_input = ui.input(
                        'City',
                        value=str(draft.get('city') or ''),
                    ).props('outlined')
                    state_input = ui.input(
                        (
                            'Province'
                            if brand_profile.get('country_code') == 'CA'
                            else 'State'
                        ),
                        value=str(draft.get('state') or ''),
                    ).props('outlined')
                    pincode_input = ui.input(
                        (
                            'Postal code'
                            if brand_profile.get('country_code') == 'CA'
                            else 'PIN code'
                        ),
                        value=str(draft.get('pincode') or ''),
                    )
                    if brand_profile.get('country_code') == 'CA':
                        pincode_input.props('outlined')
                    else:
                        pincode_input.props('outlined mask=######')

                with ui.grid(columns=2).classes(
                    'w-full gap-4 mt-3 max-[760px]:grid-cols-1'
                ):
                    sqft_input = ui.number(
                        'Square footage *',
                        value=int(draft.get('sqft') or 0),
                        min=1,
                        step=10,
                    ).props('outlined')
                    frontage_input = ui.input(
                        'Frontage',
                        value=str(
                            (draft.get('optional') or {}).get(
                                'Frontage',
                                '',
                            )
                        ),
                        placeholder='Example: 22 ft.',
                    ).props('outlined')
                    floor_input = ui.input(
                        'Floor',
                        value=str(
                            (draft.get('optional') or {}).get('Floor', '')
                        ),
                        placeholder='Example: Ground floor',
                    ).props('outlined')
                    parking_input = ui.input(
                        'Parking / access',
                        value=str(
                            (draft.get('optional') or {}).get('Parking', '')
                        ),
                        placeholder='Example: Mall parking available',
                    ).props('outlined')

                notes_input = ui.textarea(
                    'Location notes and unstructured information',
                    value=str(draft.get('notes') or ''),
                    placeholder=(
                        'Add broker comments, trade-area observations, lease '
                        'terms, access constraints, nearby offices, competitor '
                        'notes or anything else the ground team collected.'
                    ),
                ).props('outlined autogrow').classes('w-full mt-3')

                with ui.expansion(
                    'Map coordinates and address confirmation',
                    icon='map',
                ).classes('w-full mt-3'):
                    ui.label(
                        'Coordinates are filled automatically when the address '
                        'provider returns them. Enter them manually when the '
                        'provider account does not include coordinate access.',
                    ).classes('text-xs muted')
                    with ui.grid(columns=2).classes(
                        'w-full gap-4 mt-3 max-[650px]:grid-cols-1'
                    ):
                        latitude_input = ui.number(
                            'Latitude *',
                            value=draft.get('lat'),
                            min=6.0,
                            max=38.0,
                            step=0.000001,
                            format='%.6f',
                        ).props('outlined')
                        longitude_input = ui.number(
                            'Longitude *',
                            value=draft.get('lng'),
                            min=68.0,
                            max=98.0,
                            step=0.000001,
                            format='%.6f',
                        ).props('outlined')

                ui.separator().classes('my-5')
                with ui.row().classes(
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label('Supporting documents').classes(
                            'text-lg font-bold'
                        )
                        ui.label(
                            'Optional · PDF, DOC, DOCX or TXT · up to 8 files · '
                            '10 MB each · 25 MB total',
                        ).classes('text-xs muted')
                    ui.badge(
                        'ANALYZED ONLY WHEN YOU CLICK ANALYZE',
                        color='primary',
                    ).props('outline')

                @ui.refreshable
                def document_list() -> None:
                    documents = draft.get('documents') or []
                    if not documents:
                        with ui.row().classes(
                            'w-full items-center gap-2 p-4 mt-3 rounded-xl '
                            'border border-dashed border-[#d9cbd1]'
                        ):
                            ui.icon('upload_file').classes('text-primary')
                            ui.label('No documents attached.').classes(
                                'text-sm muted'
                            )
                        return

                    with ui.column().classes('w-full gap-2 mt-3'):
                        for document in list(documents):
                            document_id = str(document.get('id') or '')

                            def remove_document(
                                doc_id: str = document_id,
                            ) -> None:
                                draft['documents'] = [
                                    item
                                    for item in draft.get('documents', [])
                                    if str(item.get('id') or '') != doc_id
                                ]
                                document_list.refresh()

                            with ui.row().classes(
                                'document-row w-full items-center '
                                'justify-between gap-3 p-3 no-wrap'
                            ):
                                with ui.row().classes(
                                    'items-center gap-3 no-wrap min-w-0'
                                ):
                                    ui.icon('description').classes(
                                        'text-primary shrink-0'
                                    )
                                    with ui.column().classes('gap-0 min-w-0'):
                                        ui.label(
                                            str(document.get('name') or 'Document')
                                        ).classes(
                                            'text-sm font-bold truncate'
                                        )
                                        ui.label(
                                            _document_source_label(document)
                                        ).classes(
                                            'text-[10px] muted'
                                        )
                                with ui.row().classes(
                                    'items-center gap-1 no-wrap shrink-0'
                                ):
                                    if isinstance(
                                        document.get('content'),
                                        (bytes, bytearray),
                                    ):
                                        ui.button(
                                            icon='download',
                                            on_click=lambda _event=None, doc=document: (
                                                _download_document(doc)
                                            ),
                                        ).props(
                                            'flat round dense color=primary'
                                        ).tooltip('Download document')
                                    ui.button(
                                        icon='delete_outline',
                                        on_click=remove_document,
                                    ).props(
                                        'flat round dense color=negative'
                                    )

                document_list()

                async def upload_document(event: Any) -> None:
                    try:
                        upload_file = event.file
                        name = str(upload_file.name or '').strip()
                        content_type = str(
                            upload_file.content_type
                            or 'application/octet-stream'
                        )
                        content = await upload_file.read()
                        validate_document(
                            name=name,
                            size_bytes=len(content),
                        )
                        # Re-uploading the same filename replaces the previous
                        # uploaded copy but does not silently remove a demo file.
                        prospective_documents = [
                            document
                            for document in draft.get('documents', [])
                            if not (
                                document.get('source') == 'upload'
                                and document.get('name') == name
                            )
                        ]
                        if len(prospective_documents) >= MAX_DOCUMENTS:
                            raise OutletDocumentAnalysisError(
                                f'Only {MAX_DOCUMENTS} documents can be attached.'
                            )
                        current_actual_bytes = sum(
                            int(document.get('size_bytes') or 0)
                            for document in prospective_documents
                            if document.get('source') == 'upload'
                        )
                        if current_actual_bytes + len(content) > MAX_TOTAL_BYTES:
                            raise OutletDocumentAnalysisError(
                                'Uploaded files exceed the 25 MB total limit.'
                            )
                        draft['documents'] = prospective_documents
                        draft['documents'].append(
                            {
                                'id': f'doc-{uuid.uuid4().hex[:12]}',
                                'name': name,
                                'content_type': content_type,
                                'size_bytes': len(content),
                                'content': content,
                                'source': 'upload',
                                'mock_extract': '',
                                'analysis_status': 'Ready for analysis',
                            }
                        )
                        document_list.refresh()
                        ui.notify(
                            f'{name} attached.',
                            type='positive',
                        )
                    except OutletDocumentAnalysisError as exc:
                        ui.notify(str(exc), type='negative')
                    except Exception as exc:
                        ui.notify(
                            f'Could not read uploaded file: {str(exc)[:180]}',
                            type='negative',
                        )

                ui.upload(
                    label='Choose supporting documents',
                    multiple=True,
                    auto_upload=True,
                    max_file_size=MAX_FILE_BYTES,
                    max_total_size=MAX_TOTAL_BYTES,
                    max_files=MAX_DOCUMENTS,
                    on_upload=upload_document,
                    on_rejected=lambda _event: ui.notify(
                        'A file was rejected. Check type, size and file count.',
                        type='warning',
                    ),
                ).props(
                    'accept=.pdf,.doc,.docx,.txt color=primary flat bordered'
                ).classes('w-full mt-3')
                ui.label(
                    'When the Vesper RAG Engine is enabled, clicking Analyze '
                    'sends the attached file contents and typed site notes to '
                    'the configured document-intelligence service. If the '
                    'Vesper RAG Engine is unavailable, Vesper uses its '
                    'transparent local fallback.',
                ).classes('text-[10px] muted leading-relaxed mt-2')

                async def save_candidate() -> None:
                    name = str(name_input.value or '').strip()
                    address = str(address_input.value or '').strip()
                    try:
                        rent = float(rent_input.value or 0)
                        sqft = int(float(sqft_input.value or 0))
                    except (TypeError, ValueError):
                        ui.notify(
                            'Rent and square footage must be valid numbers.',
                            type='negative',
                        )
                        return

                    if not address:
                        ui.notify('Full address is required.', type='negative')
                        return
                    if rent <= 0:
                        ui.notify('Monthly rent must be greater than zero.', type='negative')
                        return
                    if sqft <= 0:
                        ui.notify('Square footage must be greater than zero.', type='negative')
                        return

                    lat = latitude_input.value
                    lng = longitude_input.value
                    if lat in (None, '') or lng in (None, ''):
                        address_status.set_text(
                            'Resolving map coordinates before saving…'
                        )
                        resolved = await location_service.geocode(address)
                        if resolved is not None and resolved.has_coordinates:
                            lat = resolved.latitude
                            lng = resolved.longitude
                            latitude_input.set_value(lat)
                            longitude_input.set_value(lng)
                            if not city_input.value:
                                city_input.set_value(resolved.city)
                            if not state_input.value:
                                state_input.set_value(resolved.state)
                            if not pincode_input.value:
                                pincode_input.set_value(
                                    resolved.postal_code
                                )
                            draft['address_provider'] = resolved.provider
                            draft['provider_place_id'] = resolved.provider_id
                            draft['address_confirmed'] = True

                    try:
                        lat_float = float(lat)
                        lng_float = float(lng)
                    except (TypeError, ValueError):
                        ui.notify(
                            'A map point is required. Select an address '
                            'suggestion or enter latitude and longitude.',
                            type='negative',
                        )
                        return
                    min_lat, max_lat, min_lng, max_lng = _coordinate_bounds(
                        brand_profile
                    )
                    if not (
                        min_lat <= lat_float <= max_lat
                        and min_lng <= lng_float <= max_lng
                    ):
                        ui.notify(
                            'Coordinates must fall within the supported '
                            f"{brand_profile['country']} demo bounds.",
                            type='negative',
                        )
                        return

                    if not name:
                        name = (
                            str(city_input.value or '').strip()
                            or address.split(',', maxsplit=1)[0].strip()
                            or 'New shortlisted location'
                        )[:80]

                    draft.update(
                        {
                            'id': working_id,
                            'name': name,
                            'address': address,
                            'rent': round(rent, 2),
                            'sqft': sqft,
                            'city': str(city_input.value or '').strip(),
                            'state': str(state_input.value or '').strip(),
                            'pincode': str(pincode_input.value or '').strip(),
                            'lat': lat_float,
                            'lng': lng_float,
                            'notes': str(notes_input.value or '').strip(),
                            'optional': {
                                'Frontage': str(
                                    frontage_input.value or ''
                                ).strip(),
                                'Floor': str(floor_input.value or '').strip(),
                                'Parking': str(
                                    parking_input.value or ''
                                ).strip(),
                            },
                        }
                    )

                    material_fields = (
                        'address',
                        'rent',
                        'sqft',
                        'notes',
                        'optional',
                        'documents',
                    )
                    materially_changed = is_new or any(
                        draft.get(field) != original.get(field)
                        for field in material_fields
                    )
                    if materially_changed:
                        draft['document_analysis'] = None
                        draft['analysis_mode'] = 'none'
                        draft['analysis_status'] = (
                            'Saved · run Analyze for document review'
                        )

                    calculate_location_analysis(draft, candidates, brand_profile)
                    if materially_changed:
                        draft['analysis_status'] = (
                            'Preliminary · document analysis pending'
                        )

                    candidates[working_id] = draft
                    page_state['selected'] = working_id
                    persist_state()
                    candidate_list.refresh()
                    update_candidate_count()
                    dialog.close()
                    await rebuild_markers(
                        focus_candidate_id=working_id
                    )
                    refs['analysis'].clear()
                    render_details(working_id)
                    ui.notify(
                        f'{name} saved. Click Analyze to review its '
                        'documents and refresh the final verdict.',
                        type='positive',
                    )

                with ui.row().classes(
                    'w-full justify-end gap-2 mt-6 flex-wrap'
                ):
                    ui.button(
                        'Cancel',
                        on_click=dialog.close,
                    ).props('flat no-caps')
                    ui.button(
                        'Save candidate',
                        icon='save',
                        on_click=save_candidate,
                    ).props('unelevated no-caps').classes('rounded-xl')

        dialog.open()

    def request_delete(candidate_id: str) -> None:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            return

        with ui.dialog() as dialog:
            with ui.card().classes(
                'w-[520px] max-w-[94vw] p-6 rounded-2xl'
            ):
                ui.label('Delete shortlisted location?').classes(
                    'text-xl font-bold'
                )
                ui.label(
                    f"{candidate['name']} and its map point will be removed "
                    'from this demo tab.',
                ).classes('text-sm muted mt-2')
                ui.label(
                    'Restarting the server or using Reset restores the '
                    'original four candidates.',
                ).classes('text-xs muted mt-2')

                async def confirm_delete() -> None:
                    candidates.pop(candidate_id, None)
                    decisions.pop(candidate_id, None)
                    if page_state['selected'] == candidate_id:
                        page_state['selected'] = None
                        refs['details'].clear()
                        refs['analysis'].clear()
                    persist_state()
                    candidate_list.refresh()
                    update_candidate_count()
                    dialog.close()
                    await rebuild_markers()
                    ui.notify(
                        f"{candidate['name']} deleted.",
                        type='positive',
                    )

                with ui.row().classes('w-full justify-end gap-2 mt-5'):
                    ui.button(
                        'Cancel',
                        on_click=dialog.close,
                    ).props('flat no-caps')
                    ui.button(
                        'Delete',
                        icon='delete',
                        on_click=confirm_delete,
                    ).props(
                        'unelevated no-caps color=negative'
                    )
        dialog.open()

    def request_reset() -> None:
        with ui.dialog() as dialog:
            with ui.card().classes(
                'w-[520px] max-w-[94vw] p-6 rounded-2xl'
            ):
                ui.label('Reset Outlet Intelligence?').classes(
                    'text-xl font-bold'
                )
                ui.label(
                    'All added candidates, edits, uploaded files, deletions '
                    'and workflow decisions in this browser tab will be '
                    'discarded.',
                ).classes('text-sm muted mt-2')

                async def confirm_reset() -> None:
                    candidates.clear()
                    candidates.update(clone_default_candidates(brand_id))
                    decisions.clear()
                    page_state['selected'] = None
                    page_state['analysis_run'] += 1
                    persist_state()
                    candidate_list.refresh()
                    update_candidate_count()
                    refs['details'].clear()
                    refs['analysis'].clear()
                    dialog.close()
                    await rebuild_markers()
                    ui.notify(
                        'Outlet Intelligence restored to its original demo state.',
                        type='positive',
                    )

                with ui.row().classes('w-full justify-end gap-2 mt-5'):
                    ui.button(
                        'Cancel',
                        on_click=dialog.close,
                    ).props('flat no-caps')
                    ui.button(
                        'Reset',
                        icon='restart_alt',
                        on_click=confirm_reset,
                    ).props('unelevated no-caps color=negative')
        dialog.open()

    @ui.refreshable
    def candidate_list() -> None:
        with ui.column().classes(
            'w-full gap-3 max-h-[500px] overflow-auto pr-1'
        ):
            if not candidates:
                with ui.card().classes(
                    'candidate-row w-full p-5 shadow-none'
                ):
                    ui.icon('add_location_alt').classes(
                        'text-3xl text-primary'
                    )
                    ui.label('No candidates in the shortlist.').classes(
                        'text-sm font-bold mt-2'
                    )
                    ui.label(
                        'Use Add entry to create the first location and map point.'
                    ).classes('text-xs muted')
                return

            for candidate_id, candidate in candidates.items():
                with ui.card().classes(
                    'candidate-row w-full p-3 shadow-none'
                ):
                    with ui.row().classes(
                        'w-full items-start justify-between gap-2 no-wrap'
                    ):
                        with ui.column().classes('gap-0 min-w-0'):
                            ui.label(candidate['name']).classes(
                                'text-sm font-bold truncate'
                            )
                            ui.label(
                                f"{_format_candidate_money(float(candidate['rent']), brand_profile)}/month "
                                f"· {int(candidate['sqft']):,} sq. ft."
                            ).classes('text-[11px] muted')
                            ui.label(
                                str(candidate.get('analysis_status') or '')
                            ).classes('text-[10px] muted mt-1')
                        _status(str(candidate.get('status') or 'Review'))

                    with ui.row().classes(
                        'w-full items-center gap-1 mt-2 flex-wrap'
                    ):
                        ui.button(
                            'Analyze',
                            icon='auto_awesome',
                            on_click=lambda cid=candidate_id: analyze(cid),
                        ).props(
                            'flat dense no-caps color=primary'
                        ).classes('text-xs')
                        ui.button(
                            'Edit',
                            icon='edit',
                            on_click=lambda cid=candidate_id: (
                                open_candidate_editor(cid)
                            ),
                        ).props(
                            'flat dense no-caps color=primary'
                        ).classes('text-xs')
                        ui.space()
                        ui.button(
                            'Delete',
                            icon='delete_outline',
                            on_click=lambda cid=candidate_id: (
                                request_delete(cid)
                            ),
                        ).props(
                            'flat dense no-caps color=negative'
                        ).classes('text-xs')

    with ui.dialog() as source_dialog:
        refs['source_dialog'] = source_dialog
        with ui.card().classes(
            'w-[650px] max-w-[94vw] p-6 rounded-2xl'
        ):
            refs['source_content'] = ui.column().classes('w-full gap-1')
            with ui.row().classes('w-full justify-end mt-3'):
                ui.button(
                    'Close',
                    on_click=source_dialog.close,
                ).props('flat no-caps')

    with ui.column().classes(
        'w-full max-w-[1540px] mx-auto px-4 md:px-7 py-6 gap-5'
    ):
        with ui.row().classes(
            'w-full items-start justify-between gap-3 flex-wrap'
        ):
            with ui.column().classes('gap-1'):
                ui.label('OUTLET INTELLIGENCE').classes('section-kicker')
                ui.label('AI-assisted location investment studio').classes(
                    'text-2xl md:text-3xl font-extrabold'
                )
                ui.label(
                    'Create, edit and analyze shortlisted properties using '
                    'structured inputs, uploaded documents and location intelligence.',
                ).classes('text-sm muted')
            with ui.row().classes('items-center gap-2 flex-wrap'):
                refs['candidate_count'] = ui.badge(
                    f'{len(candidates)} CANDIDATES',
                    color='positive',
                ).props('outline')
                ui.button(
                    'Reset',
                    icon='restart_alt',
                    on_click=request_reset,
                ).props('outline no-caps').classes('rounded-xl')
                ui.button(
                    'Add entry',
                    icon='add_location_alt',
                    on_click=lambda: open_candidate_editor(),
                ).props('unelevated no-caps').classes('rounded-xl')

        with ui.grid(columns=12).classes(
            'w-full gap-4 max-[1050px]:grid-cols-1'
        ):
            with ui.card().classes(
                'surface col-span-8 p-5 w-full max-[1050px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label(f"{brand_profile['country']} candidate map").classes(
                            'text-lg font-bold'
                        )
                        ui.label(
                            'Each saved entry has a map point. Click a dot to '
                            'run its latest analysis.',
                        ).classes('text-xs muted')
                    with ui.row().classes('gap-2 flex-wrap'):
                        for label, color in STATUS_COLORS.items():
                            with ui.row().classes('items-center gap-1'):
                                ui.element('span').style(
                                    'width:9px;height:9px;border-radius:50%;'
                                    f'background:{color};display:inline-block;'
                                )
                                ui.label(label).classes('text-[10px] muted')

                candidate_map = ui.leaflet(
                    center=(
                        float(brand_profile['map_center_lat']),
                        float(brand_profile['map_center_lon']),
                    ),
                    zoom=int(brand_profile['map_zoom']),
                    options={
                        'scrollWheelZoom': True,
                        'zoomControl': True,
                    },
                ).classes('location-map w-full h-[540px] mt-4')

            with ui.card().classes(
                'surface col-span-4 p-5 w-full max-[1050px]:col-span-1'
            ):
                with ui.row().classes(
                    'w-full items-start justify-between gap-3'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label('Shortlisted candidates').classes(
                            'text-lg font-bold'
                        )
                        ui.label(
                            'Required: address, rent, square footage and map point'
                        ).classes('text-xs muted')
                    ui.button(
                        icon='add',
                        on_click=lambda: open_candidate_editor(),
                    ).props('flat round dense color=primary')
                candidate_list()

        refs['analysis'] = ui.column().classes('w-full')
        refs['details'] = ui.column().classes('w-full')
        ui.label(
            'Prototype only · Uploaded files are held in per-tab server memory '
            'and disappear when the demo server restarts. Location-market '
            'signals and financial outputs are simulated.',
        ).classes('text-[11px] muted')

    ui.on(map_event_name, marker_event)
    await rebuild_markers()

    selected = page_state.get('selected')
    if selected in candidates:
        render_details(str(selected))
