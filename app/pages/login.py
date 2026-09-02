from __future__ import annotations

from nicegui import app, ui

from app.services.auth_service import (
    authenticate_demo_account,
    is_authenticated,
)
from app.theme import BURGUNDY, BURGUNDY_DARK, GOLD, apply_theme


@ui.page('/login')
def login_page() -> None:
    if is_authenticated(app.storage.user):
        ui.navigate.to('/command-center')
        return

    apply_theme()
    ui.add_css(
        f'''
        .login-page {{
            min-height: 100vh;
            width: 100%;
            background:
                radial-gradient(circle at 12% 8%, rgba(242,181,68,.18), transparent 27%),
                radial-gradient(circle at 88% 88%, rgba(90,21,52,.15), transparent 30%),
                #F7F3EA;
        }}
        .login-card {{
            width: min(460px, calc(100vw - 32px));
            border-radius: 24px;
            border: 1px solid rgba(90,21,52,.10);
            box-shadow: 0 26px 70px rgba(59,13,34,.12);
            background: rgba(255,252,246,.97);
        }}
        .login-hero {{
            background: linear-gradient(145deg, {BURGUNDY_DARK}, {BURGUNDY});
            color: white;
            border-radius: 24px;
            box-shadow: 0 28px 80px rgba(59,13,34,.24);
        }}
        .login-country-pill {{
            border: 1px solid rgba(255,255,255,.18);
            background: rgba(255,255,255,.08);
            border-radius: 999px;
            padding: 7px 11px;
        }}
        '''
    )

    with ui.element('div').classes(
        'login-page flex items-center justify-center p-4 md:p-8'
    ):
        with ui.row().classes(
            'w-full max-w-6xl items-stretch justify-center gap-6 lg:gap-10'
        ):
            with ui.card().classes(
                'login-hero hidden lg:flex flex-1 max-w-xl p-10 border-0'
            ):
                with ui.column().classes('h-full w-full gap-6'):
                    with ui.row().classes('items-center gap-4'):
                        ui.image('/assets/inventide_logo.png').classes(
                            'w-14 h-14 object-cover rounded-full'
                        )
                        with ui.column().classes('gap-0'):
                            ui.label('VESPER').classes(
                                'text-xl font-black tracking-[0.18em] text-white'
                            )
                            ui.label('Supply Chain Intelligence').classes(
                                'text-sm text-white/75'
                            )

                    ui.space()
                    ui.label('One intelligence layer. Multiple operating markets.').classes(
                        'text-4xl font-black leading-tight max-w-lg text-white'
                    )
                    ui.label(
                        'Each brand workspace carries its own network, market context, '
                        'currency, operational state and decision history.'
                    ).classes('text-base leading-relaxed text-white/75 max-w-lg')

                    with ui.row().classes('gap-2 flex-wrap mt-2'):
                        with ui.row().classes('login-country-pill items-center gap-2'):
                            ui.icon('public', size='18px')
                            ui.label('India · INR')
                        with ui.row().classes('login-country-pill items-center gap-2'):
                            ui.icon('public', size='18px')
                            ui.label('Canada · CAD')

                    ui.space()
                    ui.label('Inventide · Demo environment').classes(
                        'text-xs uppercase tracking-[0.15em] text-white/50'
                    )

            with ui.card().classes('login-card p-7 md:p-9'):
                with ui.column().classes('w-full gap-5'):
                    with ui.row().classes('items-center gap-3 lg:hidden'):
                        ui.image('/assets/inventide_logo.png').classes(
                            'w-11 h-11 object-cover rounded-full'
                        )
                        with ui.column().classes('gap-0'):
                            ui.label('VESPER').classes(
                                'text-sm font-black tracking-[0.16em]'
                            )
                            ui.label('Supply Chain Intelligence').classes(
                                'text-[11px] muted'
                            )

                    with ui.column().classes('gap-1'):
                        ui.label('Brand workspace login').classes(
                            'text-2xl font-bold tracking-tight'
                        )
                        ui.label(
                            'Sign in with the workspace credentials assigned to this brand.'
                        ).classes('text-sm muted leading-relaxed')

                    login_id = ui.input(
                        'Workspace ID',
                        placeholder='Enter workspace ID',
                    ).props('outlined autocomplete=username').classes('w-full')

                    password = ui.input(
                        'Password',
                        password=True,
                        password_toggle_button=True,
                    ).props('outlined autocomplete=current-password').classes('w-full')

                    error_label = ui.label('').classes(
                        'text-sm font-semibold text-negative min-h-[20px]'
                    )

                    def attempt_login() -> None:
                        error_label.set_text('')
                        ok = authenticate_demo_account(
                            app.storage.user,
                            login_id.value or '',
                            password.value or '',
                        )
                        if not ok:
                            error_label.set_text(
                                'Workspace ID or password is incorrect.'
                            )
                            password.value = ''
                            return

                        ui.navigate.to('/command-center')

                    ui.button(
                        'Sign in',
                        icon='login',
                        on_click=attempt_login,
                    ).props('unelevated no-caps').classes(
                        'w-full h-12 rounded-xl text-base font-bold'
                    )

                    ui.separator().classes('my-1')
                    with ui.row().classes('items-start gap-2 no-wrap'):
                        ui.icon('info', color='secondary', size='18px').classes('mt-0.5')
                        ui.label(
                            'This is an MVP demo workspace. Production authentication '
                            'and role-based access will be added with the persistent backend.'
                        ).classes('text-xs muted leading-relaxed')
