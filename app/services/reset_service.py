from __future__ import annotations

from typing import Any, MutableMapping

from app.state.demo_state import reset_brand_state


AI_CHAT_STORAGE_KEY = 'vesper_ai_chat'
OUTLET_STORAGE_KEY = 'vesper_outlet_intelligence_v2'


def reset_demo_workspace(
    user_storage: MutableMapping[str, Any],
    tab_storage: MutableMapping[str, Any] | None,
    brand_id: str,
) -> dict[str, Any]:
    """Restore one demo brand to its deterministic baseline.

    Authentication is intentionally preserved.  Only mutable demo/business
    state for ``brand_id`` is replaced.  Brand-scoped tab state (currently
    Outlet Intelligence) and the AI conversation are cleared so a presenter
    sees a coherent fresh workspace immediately after reset.
    """

    fresh_state = reset_brand_state(user_storage, brand_id)

    # A prior conversation may contain answers based on mutated state.  Clear
    # it when the underlying demo data is reset so Vesper AI cannot appear to
    # carry stale business facts into the fresh baseline.
    user_storage.pop(AI_CHAT_STORAGE_KEY, None)

    if tab_storage is not None:
        tab_storage.pop(f'{OUTLET_STORAGE_KEY}:{brand_id}', None)

    return fresh_state
