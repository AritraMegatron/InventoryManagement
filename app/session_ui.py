from __future__ import annotations

from typing import Any

from nicegui import app, ui

from app.services.auth_service import (
    get_authenticated_brand_profile,
    is_authenticated,
    logout_demo_account,
)
from app.services.reset_service import AI_CHAT_STORAGE_KEY, reset_demo_workspace
from app.state.demo_state import select_brand


def require_brand_login() -> dict[str, Any] | None:
    """Guard a Vesper application page and return its brand profile."""

    storage = app.storage.user
    if not is_authenticated(storage):
        ui.navigate.to('/login')
        return None

    profile = get_authenticated_brand_profile(storage)
    if profile is None:
        logout_demo_account(storage)
        ui.navigate.to('/login')
        return None

    # Keep selected demo state synchronized with the authenticated tenant.
    select_brand(storage, profile['brand_id'])
    return profile


def render_brand_session_controls() -> None:
    """Render compact tenant context + logout controls in an app header."""

    profile = get_authenticated_brand_profile(app.storage.user)
    if profile is None:
        return

    ui.badge(
        f"{profile['short_name']} · {profile['country']} · {profile['currency_code']}",
        color='primary',
    ).props('outline').classes('desktop-only')

    with ui.dialog() as reset_dialog, ui.card().classes('w-full max-w-md p-5'):
        ui.label('Reset demo data?').classes('text-lg font-bold')
        ui.label(
            f"This restores {profile['short_name']} to its original synthetic "
            'dataset and clears current approvals, plans, pilots, location edits, '
            'analysis runs, and the Ask AI conversation. The other brand is not changed.'
        ).classes('text-sm muted leading-relaxed')

        with ui.row().classes('w-full justify-end gap-2 mt-3'):
            ui.button(
                'Cancel',
                on_click=reset_dialog.close,
            ).props('flat no-caps')

            def confirm_reset() -> None:
                reset_demo_workspace(
                    app.storage.user,
                    app.storage.tab,
                    str(profile['brand_id']),
                )
                reset_dialog.close()
                ui.notify(
                    f"{profile['short_name']} demo data reset.",
                    type='positive',
                )
                ui.run_javascript(
                    'window.setTimeout(() => window.location.reload(), 250)'
                )

            ui.button(
                'Reset',
                icon='restart_alt',
                on_click=confirm_reset,
            ).props('unelevated no-caps')

    ui.button(
        'Reset',
        icon='restart_alt',
        on_click=reset_dialog.open,
    ).props('outline dense no-caps').classes('rounded-lg')

    def sign_out() -> None:
        logout_demo_account(app.storage.user)

        # Do not carry AI conversation or page-tab state into a different
        # tenant if a presenter signs out and then uses another demo account.
        app.storage.user.pop(AI_CHAT_STORAGE_KEY, None)
        app.storage.tab.clear()
        ui.navigate.to('/login')

    ui.button(
        icon='logout',
        on_click=sign_out,
    ).props('flat round dense').tooltip('Sign out')
