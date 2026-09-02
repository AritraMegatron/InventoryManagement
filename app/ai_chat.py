from __future__ import annotations

from typing import Any, Callable, Coroutine, MutableMapping

from nicegui import app, ui

from app.openai_service import (
    OpenAIConfigurationError,
    OpenAIResponseError,
    VesperOpenAIService,
)
from app.services.ai_live_state_service import build_live_state_context
from app.services.auth_service import get_authenticated_brand_id
from app.state.demo_state import get_brand_state


CHAT_STORAGE_KEY = 'vesper_ai_chat'
MAX_STORED_MESSAGES = 30


class AIChatController:
    """
    Floating Vesper AI chat that persists between NiceGUI pages.

    NiceGUI rebuilds page elements after route navigation. The chat UI is
    recreated on each page, while its open state, minimized state, and
    conversation history are restored from app.storage.user.
    """

    def __init__(
        self,
        page_name: str,
        page_context: str,
    ) -> None:
        self.page_name = page_name
        self.page_context = page_context

        self.service = VesperOpenAIService()

        self.is_busy = False
        self.refs: dict[str, Any] = {}

        # This storage belongs to the current browser/user and survives
        # navigation between NiceGUI pages.
        self.storage: MutableMapping[str, Any] = app.storage.user
        stored_state = self._read_stored_state()

        self.history: list[dict[str, str]] = stored_state['history']
        self.is_open: bool = stored_state['is_open']
        self.is_minimized: bool = stored_state['is_minimized']

        self._build()
        self._apply_window_state()

    def _read_stored_state(self) -> dict[str, Any]:
        raw_state = self.storage.get(
            CHAT_STORAGE_KEY,
            {},
        )

        if not isinstance(raw_state, dict):
            raw_state = {}

        history: list[dict[str, str]] = []

        raw_history = raw_state.get(
            'history',
            [],
        )

        if isinstance(raw_history, list):
            for message in raw_history[-MAX_STORED_MESSAGES:]:
                if not isinstance(message, dict):
                    continue

                role = str(
                    message.get('role', '')
                ).strip()

                content = str(
                    message.get('content', '')
                ).strip()

                if (
                    role in {'user', 'assistant'}
                    and content
                ):
                    history.append(
                        {
                            'role': role,
                            'content': content,
                        }
                    )

        return {
            'history': history,
            'is_open': bool(
                raw_state.get(
                    'is_open',
                    False,
                )
            ),
            'is_minimized': bool(
                raw_state.get(
                    'is_minimized',
                    False,
                )
            ),
        }

    def _save_state(self) -> None:
        """
        Save a completely new dictionary.

        Assigning a new dictionary ensures NiceGUI recognizes that the
        user storage has changed.
        """

        self.storage[CHAT_STORAGE_KEY] = {
            'history': [
                {
                    'role': message['role'],
                    'content': message['content'],
                }
                for message in self.history[-MAX_STORED_MESSAGES:]
            ],
            'is_open': self.is_open,
            'is_minimized': self.is_minimized,
        }

    def _build(self) -> None:
        ui.add_css(
            """
            .vesper-chat-window {
                position: fixed;
                right: 22px;
                bottom: 20px;
                width: min(390px, calc(100vw - 28px));
                max-height: min(650px, calc(100vh - 92px));
                z-index: 7000;
                padding: 0;
                overflow: hidden;
                border-radius: 20px;
                border: 1px solid rgba(90, 21, 52, 0.16);
                box-shadow: 0 24px 70px rgba(43, 8, 24, 0.28);
                background: #fffdf9;
            }

            .vesper-chat-header {
                background: linear-gradient(145deg, #3B0D22, #5A1534);
                color: white;
            }

            .vesper-chat-user {
                max-width: 84%;
                background: #5A1534;
                color: white;
                border-radius: 16px 16px 4px 16px;
            }

            .vesper-chat-assistant {
                max-width: 88%;
                background: #F5ECEF;
                color: #2E1721;
                border-radius: 16px 16px 16px 4px;
                border: 1px solid rgba(90, 21, 52, 0.08);
            }

            .vesper-chat-assistant p,
            .vesper-chat-assistant ul,
            .vesper-chat-assistant ol {
                margin-top: 0.25rem;
                margin-bottom: 0.25rem;
            }
            """
        )

        self.refs['window'] = ui.card().classes(
            'vesper-chat-window'
        )

        with self.refs['window']:
            self._build_header()

            self.refs['body'] = ui.column().classes(
                'w-full gap-0'
            )

            with self.refs['body']:
                self._build_message_area()
                self._build_loading_indicator()
                self._build_input_area()

        self._render_messages()

    def _build_header(self) -> None:
        with ui.row().classes(
            'vesper-chat-header w-full items-center '
            'justify-between px-4 py-3 no-wrap'
        ):
            with ui.row().classes(
                'items-center gap-3 no-wrap'
            ):
                with ui.element('div').style(
                    'width:34px;'
                    'height:34px;'
                    'border-radius:50%;'
                    'background:rgba(242,181,68,.18);'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                ):
                    ui.icon(
                        'auto_awesome'
                    ).classes(
                        'text-amber-200 text-lg'
                    )

                with ui.column().classes('gap-0'):
                    ui.label(
                        'Vesper AI'
                    ).classes(
                        'text-sm font-bold'
                    )

                    # The current page changes after navigation, while the
                    # chat history remains the same.
                    ui.label(
                        self.page_name
                    ).classes(
                        'text-[10px] text-white/65'
                    )

            with ui.row().classes(
                'items-center gap-0 no-wrap'
            ):
                self.refs['minimize_button'] = ui.button(
                    icon='remove',
                    on_click=self.toggle_minimize,
                ).props(
                    'flat round dense color=white'
                ).tooltip(
                    'Minimize'
                )

                ui.button(
                    icon='close',
                    on_click=self.close,
                ).props(
                    'flat round dense color=white'
                ).tooltip(
                    'Close and clear chat'
                )

    def _build_message_area(self) -> None:
        with ui.scroll_area().classes(
            'w-full h-[390px] bg-[#fffdf9]'
        ):
            self.refs['messages'] = ui.column().classes(
                'w-full gap-3 p-4'
            )

    def _build_loading_indicator(self) -> None:
        self.refs['loading'] = ui.row().classes(
            'w-full items-center gap-2 px-4 py-2 '
            'border-t border-[#eee4e8]'
        )

        with self.refs['loading']:
            ui.spinner(
                size='sm',
                color='primary',
            )

            ui.label(
                'Vesper is thinking…'
            ).classes(
                'text-xs muted'
            )

        self.refs['loading'].set_visibility(
            False
        )

    def _build_input_area(self) -> None:
        with ui.row().classes(
            'w-full items-end gap-2 px-3 py-3 '
            'border-t border-[#eee4e8] '
            'bg-white no-wrap'
        ):
            self.refs['input'] = ui.textarea(
                placeholder=(
                    'Ask about revenue, outlets, inventory, '
                    'market ideas, or a new product…'
                )
            ).props(
                'outlined dense autogrow '
                'rows=1 maxlength=1200'
            ).classes(
                'flex-1 text-sm'
            )

            self.refs['send_button'] = ui.button(
                icon='send',
                on_click=self.send,
            ).props(
                'unelevated round'
            )

        self.refs['input'].on(
            'keydown.enter',
            self._handle_enter,
        )

    def _apply_window_state(self) -> None:
        self.refs['window'].set_visibility(
            self.is_open
        )

        self.refs['body'].set_visibility(
            not self.is_minimized
        )

        self.refs['minimize_button'].props(
            'icon=expand_less'
            if self.is_minimized
            else 'icon=remove'
        )

    async def _handle_enter(
        self,
        event: Any,
    ) -> None:
        event_arguments = getattr(
            event,
            'args',
            {},
        ) or {}

        # Shift+Enter remains available for a new line.
        if (
            isinstance(event_arguments, dict)
            and event_arguments.get('shiftKey')
        ):
            return

        await self.send()

    def _render_messages(self) -> None:
        self.refs['messages'].clear()

        with self.refs['messages']:
            if not self.history:
                self._render_welcome_message()
                return

            for message in self.history:
                self._render_message(
                    message
                )

    def _render_welcome_message(self) -> None:
        with ui.row().classes(
            'w-full justify-start'
        ):
            with ui.card().classes(
                'vesper-chat-assistant '
                'p-3 shadow-none'
            ):
                ui.label(
                    'Ask me about the live Vesper workspace: business performance, '
                    'inventory risks and plans, outlet economics, approvals, '
                    'location candidates, or product opportunities.'
                ).classes(
                    'text-sm leading-relaxed'
                )

        with ui.row().classes(
            'w-full gap-2 flex-wrap'
        ):
            suggestions = [
                'How is the business performing?',
                'What needs attention?',
                'Suggest a new product idea',
            ]

            for suggestion in suggestions:
                ui.button(
                    suggestion,
                    on_click=self._suggestion_handler(suggestion),
                ).props(
                    'outline dense no-caps'
                ).classes(
                    'rounded-xl text-xs'
                )

    def _render_message(
        self,
        message: dict[str, str],
    ) -> None:
        is_user = (
            message['role'] == 'user'
        )

        with ui.row().classes(
            'w-full justify-end'
            if is_user
            else 'w-full justify-start'
        ):
            with ui.card().classes(
                (
                    'vesper-chat-user '
                    'p-3 shadow-none'
                    if is_user
                    else
                    'vesper-chat-assistant '
                    'p-3 shadow-none'
                )
            ):
                if is_user:
                    ui.label(
                        message['content']
                    ).classes(
                        'text-sm whitespace-pre-wrap '
                        'leading-relaxed'
                    )
                else:
                    ui.markdown(
                        message['content']
                    ).classes(
                        'text-sm leading-relaxed'
                    )

    def _suggestion_handler(
        self,
        text: str,
    ) -> Callable[[], Coroutine[Any, Any, None]]:
        async def handler() -> None:
            await self.ask_suggestion(text)

        return handler

    async def ask_suggestion(
        self,
        text: str,
    ) -> None:
        self.refs['input'].value = text
        self.refs['input'].update()
        await self.send()

    async def send(self) -> None:
        if self.is_busy:
            return

        message = str(
            self.refs['input'].value
            or ''
        ).strip()

        if not message:
            return

        self.refs['input'].value = ''
        self.refs['input'].update()

        self.history.append(
            {
                'role': 'user',
                'content': message,
            }
        )

        self.history = self.history[
            -MAX_STORED_MESSAGES:
        ]

        # Save immediately so the user's latest message remains available
        # even if they navigate while the API call is running.
        self._save_state()

        self._render_messages()
        self._set_busy(True)

        try:
            brand_id = get_authenticated_brand_id(self.storage)
            if brand_id is None:
                raise OpenAIResponseError(
                    'The Vesper brand session is no longer available. Please sign in again.'
                )

            brand_state = get_brand_state(self.storage, brand_id)
            # The live-state service reads only canonical, JSON-safe brand
            # state. AI chat must never resolve app.storage.tab: tab storage
            # requires an active NiceGUI client/slot and is not safe to access
            # during async model calls or during initial HTTP page rendering.
            live_state_context = build_live_state_context(
                brand_state,
                user_query=message,
                page_name=self.page_name,
            )

            answer = await self.service.answer(
                history=self.history,
                page_name=self.page_name,
                page_context=self.page_context,
                live_state_context=live_state_context,
            )

            self.history.append(
                {
                    'role': 'assistant',
                    'content': answer,
                }
            )

        except OpenAIConfigurationError as exc:
            print('[Vesper AI] Configuration error:', exc)
            self.history.append(
                {
                    'role': 'assistant',
                    'content': (
                        '**Vesper AI is not configured for this environment.** '
                        'Check the server AI settings and try again.'
                    ),
                }
            )

        except OpenAIResponseError as exc:
            print('[Vesper AI] Request error:', exc)
            self.history.append(
                {
                    'role': 'assistant',
                    'content': (
                        '**Vesper AI could not complete that request.** '
                        'Please try again in a moment.'
                    ),
                }
            )

        finally:
            self.history = self.history[
                -MAX_STORED_MESSAGES:
            ]

            self._save_state()
            self._set_busy(False)
            self._render_messages()

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        self.is_busy = busy

        self.refs['loading'].set_visibility(
            busy
        )

        if busy:
            self.refs['send_button'].disable()
            self.refs['input'].disable()
        else:
            self.refs['send_button'].enable()
            self.refs['input'].enable()

    def open(self) -> None:
        """
        Open the chat and persist its state across all pages.
        """

        self.is_open = True
        self.is_minimized = False

        self.refs['window'].set_visibility(
            True
        )

        self.refs['body'].set_visibility(
            True
        )

        self.refs['minimize_button'].props(
            'icon=remove'
        )

        self._save_state()

    def toggle_minimize(self) -> None:
        """
        Minimize or expand the chat without clearing the conversation.
        """

        self.is_minimized = (
            not self.is_minimized
        )

        self.refs['body'].set_visibility(
            not self.is_minimized
        )

        self.refs['minimize_button'].props(
            'icon=expand_less'
            if self.is_minimized
            else 'icon=remove'
        )

        self._save_state()

    def reset(self) -> None:
        """
        Clear the current conversation.
        """

        self.history.clear()
        self.is_minimized = False
        self.is_busy = False

        self.refs['body'].set_visibility(
            True
        )

        self.refs['minimize_button'].props(
            'icon=remove'
        )

        self.refs['input'].value = ''
        self.refs['input'].update()

        self.refs['loading'].set_visibility(
            False
        )

        self.refs['send_button'].enable()
        self.refs['input'].enable()

        self._render_messages()

    def close(self) -> None:
        """
        Close hides the chat across every page and clears the conversation.

        Pressing Ask AI again starts a fresh conversation.
        """

        self.reset()

        self.is_open = False

        self.refs['window'].set_visibility(
            False
        )

        self._save_state()


def create_ai_chat(
    page_name: str,
    page_context: str,
) -> AIChatController:
    return AIChatController(
        page_name=page_name,
        page_context=page_context,
    )