from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
import uuid

from app.data.outlet_candidates import OUTLET_STATE_SCHEMA_VERSION


# One identifier per Python process. Outlet Intelligence already used this
# behavior to restore its volatile candidate workspace after a server restart.
# Keeping the identifier in a shared service lets the AI snapshot obey the same
# rule without importing NiceGUI or reading app.storage.tab.
OUTLET_PROCESS_BOOT_ID = uuid.uuid4().hex
OUTLET_AI_WORKFLOW_KEY = 'outlet_intelligence'

# Only fields needed for cross-page intelligence are copied into canonical
# brand state. In particular, uploaded document ``content`` bytes never leave
# tab storage.
_AI_CANDIDATE_FIELDS = (
    'id',
    'brand_id',
    'name',
    'city',
    'state',
    'pincode',
    'address',
    'status',
    'rent',
    'sqft',
    'score',
    'sales',
    'margin',
    'break_even',
    'cannibalization',
    'verdict',
    'summary',
    'analysis_status',
    'analysis_mode',
)


def _sanitize_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return the small JSON-safe candidate view needed by Vesper AI."""

    return {
        field: deepcopy(candidate.get(field))
        for field in _AI_CANDIDATE_FIELDS
    }


def persist_outlet_ai_snapshot(
    brand_state: dict[str, Any],
    *,
    candidates: Mapping[str, Mapping[str, Any]],
    decisions: Mapping[str, Any] | None = None,
    selected: str | None = None,
) -> dict[str, Any]:
    """Publish a sanitized Outlet Intelligence snapshot to canonical state.

    The interactive page continues to own its full working copy in
    ``app.storage.tab``. This snapshot deliberately excludes uploaded file
    content so it is safe to keep in the brand's persistent demo state and to
    supply to the read-only AI context from any page.
    """

    workflows = brand_state.setdefault('workflows', {})
    snapshot = {
        'schema_version': OUTLET_STATE_SCHEMA_VERSION,
        'process_boot_id': OUTLET_PROCESS_BOOT_ID,
        'brand_id': str(brand_state.get('brand_id') or ''),
        'selected': selected,
        'candidates': {
            str(candidate_id): _sanitize_candidate(candidate)
            for candidate_id, candidate in candidates.items()
            if isinstance(candidate, Mapping)
        },
        'decisions': {
            str(candidate_id): str(decision)
            for candidate_id, decision in (decisions or {}).items()
        },
    }
    workflows[OUTLET_AI_WORKFLOW_KEY] = snapshot
    return snapshot


def get_outlet_ai_snapshot(
    brand_state: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the current-process sanitized snapshot, if one exists.

    A snapshot produced by an older Python process is intentionally ignored so
    a server restart cannot make Ask AI describe stale candidate edits while
    the Outlet Intelligence tab has already reset to its baseline.
    """

    workflows = brand_state.get('workflows')
    if not isinstance(workflows, Mapping):
        return None

    snapshot = workflows.get(OUTLET_AI_WORKFLOW_KEY)
    if not isinstance(snapshot, Mapping):
        return None

    if snapshot.get('schema_version') != OUTLET_STATE_SCHEMA_VERSION:
        return None
    if snapshot.get('process_boot_id') != OUTLET_PROCESS_BOOT_ID:
        return None
    if str(snapshot.get('brand_id') or '') != str(brand_state.get('brand_id') or ''):
        return None
    if not isinstance(snapshot.get('candidates'), Mapping):
        return None

    return deepcopy(dict(snapshot))
