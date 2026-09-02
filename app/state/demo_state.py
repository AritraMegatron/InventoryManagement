from __future__ import annotations

from copy import deepcopy
from typing import Any, MutableMapping

from app.data.brand_catalog import (
    DEFAULT_BRAND_ID,
    get_brand_profile,
    has_brand,
)
from app.data.network_demo_data import build_network_rows


STATE_SCHEMA_VERSION = 1
SESSION_STORAGE_KEY = 'vesper_demo_session_v1'


def build_brand_state(brand_id: str) -> dict[str, Any]:
    """Create a fresh, JSON-serializable state tree for a demo brand.

    The state intentionally contains only cross-application concepts. Page-local
    widgets should not be stored here. As each Vesper application is migrated,
    its durable demo state can move under ``workflows`` without changing the
    eventual repository/database boundary.
    """

    if not has_brand(brand_id):
        raise KeyError(f'Unknown Vesper demo brand: {brand_id}')

    profile = get_brand_profile(brand_id)
    outlets = build_network_rows(brand_id)

    return {
        'schema_version': STATE_SCHEMA_VERSION,
        'brand_id': brand_id,
        'profile': profile,
        'network': {
            'outlets': outlets,
        },
        'workflows': {
            'demand_inventory': {
                'forecast_run_number': 0,
                'planning_run_number': 0,
            },
            'network_intelligence': {
                'analysis_run_number': 0,
            },
            'product_innovation': {
                'market_scan_run_number': 0,
            },
        },
        'decisions': {
            'command_center': {},
            'demand_inventory': {},
            'product_innovation': {},
        },
        'artifacts': {
            'purchase_plans': [],
            'transfer_plans': [],
            'product_pilots': [],
        },
    }


def build_demo_session(selected_brand_id: str = DEFAULT_BRAND_ID) -> dict[str, Any]:
    """Create a fresh browser/user demo session.

    Only the selected brand is materialized initially. Other brand states are
    created lazily after login/brand switching so each browser gets isolated
    mutable copies of the deterministic baseline.
    """

    return {
        'schema_version': STATE_SCHEMA_VERSION,
        'selected_brand_id': selected_brand_id,
        'brands': {
            selected_brand_id: build_brand_state(selected_brand_id),
        },
    }


def ensure_demo_session(
    storage: MutableMapping[str, Any],
) -> dict[str, Any]:
    """Read or initialize Vesper state inside NiceGUI-compatible storage."""

    session = storage.get(SESSION_STORAGE_KEY)
    if not isinstance(session, dict) or session.get('schema_version') != STATE_SCHEMA_VERSION:
        session = build_demo_session()
        storage[SESSION_STORAGE_KEY] = session
    return session


def get_selected_brand_id(storage: MutableMapping[str, Any]) -> str:
    session = ensure_demo_session(storage)
    brand_id = session.get('selected_brand_id', DEFAULT_BRAND_ID)
    if not has_brand(brand_id):
        brand_id = DEFAULT_BRAND_ID
        session['selected_brand_id'] = brand_id
    return brand_id


def select_brand(
    storage: MutableMapping[str, Any],
    brand_id: str,
) -> dict[str, Any]:
    """Select a brand and return its isolated mutable state."""

    if not has_brand(brand_id):
        raise KeyError(f'Unknown Vesper demo brand: {brand_id}')

    session = ensure_demo_session(storage)
    session['selected_brand_id'] = brand_id

    if brand_id not in session['brands']:
        session['brands'][brand_id] = build_brand_state(brand_id)

    return session['brands'][brand_id]


def get_brand_state(
    storage: MutableMapping[str, Any],
    brand_id: str | None = None,
) -> dict[str, Any]:
    """Return the mutable state for the requested/current session brand."""

    session = ensure_demo_session(storage)
    resolved_brand_id = brand_id or get_selected_brand_id(storage)

    if resolved_brand_id not in session['brands']:
        session['brands'][resolved_brand_id] = build_brand_state(resolved_brand_id)

    return session['brands'][resolved_brand_id]


def reset_brand_state(
    storage: MutableMapping[str, Any],
    brand_id: str | None = None,
) -> dict[str, Any]:
    """Restore one brand to its deterministic baseline without affecting others."""

    session = ensure_demo_session(storage)
    resolved_brand_id = brand_id or get_selected_brand_id(storage)
    session['brands'][resolved_brand_id] = build_brand_state(resolved_brand_id)
    return session['brands'][resolved_brand_id]


def snapshot_brand_state(
    storage: MutableMapping[str, Any],
    brand_id: str | None = None,
) -> dict[str, Any]:
    """Return a detached copy useful for AI/tool consumers and tests."""

    return deepcopy(get_brand_state(storage, brand_id))
