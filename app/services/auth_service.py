from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, MutableMapping

from app.data.brand_catalog import (
    CANADA_BRAND_ID,
    INDIA_BRAND_ID,
    get_brand_profile,
    has_brand,
)
from app.state.demo_state import select_brand


AUTH_SCHEMA_VERSION = 1
AUTH_STORAGE_KEY = 'vesper_demo_auth_v1'


@dataclass(frozen=True)
class DemoAccount:
    login_id: str
    password: str
    brand_id: str


# MVP/demo authentication only. Replace with real authentication before
# production use. Keeping the account mapping in one service prevents page
# code from knowing anything about tenant credentials.
_DEMO_ACCOUNTS: dict[str, DemoAccount] = {
    'northstar': DemoAccount(
        login_id='northstar',
        password='vesperindia',
        brand_id=INDIA_BRAND_ID,
    ),
    'maplemason': DemoAccount(
        login_id='maplemason',
        password='vespercanada',
        brand_id=CANADA_BRAND_ID,
    ),
}


def authenticate_demo_account(
    storage: MutableMapping[str, Any],
    login_id: str,
    password: str,
) -> bool:
    """Authenticate a demo account and select its associated brand.

    This is intentionally a lightweight MVP credential gate, not production
    authentication. The returned session is JSON serializable so it works with
    NiceGUI user storage and can later be replaced by a proper identity layer.
    """

    normalized_login = str(login_id or '').strip().lower()
    supplied_password = str(password or '')
    account = _DEMO_ACCOUNTS.get(normalized_login)

    if account is None:
        return False

    if not secrets.compare_digest(supplied_password, account.password):
        return False

    # Materialize/select the correct isolated brand state before marking the
    # authentication session valid.
    select_brand(storage, account.brand_id)

    storage[AUTH_STORAGE_KEY] = {
        'schema_version': AUTH_SCHEMA_VERSION,
        'authenticated': True,
        'brand_id': account.brand_id,
        'login_id': account.login_id,
    }
    return True


def get_auth_session(storage: MutableMapping[str, Any]) -> dict[str, Any] | None:
    raw = storage.get(AUTH_STORAGE_KEY)
    if not isinstance(raw, dict):
        return None
    if raw.get('schema_version') != AUTH_SCHEMA_VERSION:
        return None
    if raw.get('authenticated') is not True:
        return None

    brand_id = raw.get('brand_id')
    if not isinstance(brand_id, str) or not has_brand(brand_id):
        return None

    return raw


def is_authenticated(storage: MutableMapping[str, Any]) -> bool:
    return get_auth_session(storage) is not None


def get_authenticated_brand_id(
    storage: MutableMapping[str, Any],
) -> str | None:
    session = get_auth_session(storage)
    if session is None:
        return None
    return str(session['brand_id'])


def get_authenticated_brand_profile(
    storage: MutableMapping[str, Any],
) -> dict[str, Any] | None:
    brand_id = get_authenticated_brand_id(storage)
    if brand_id is None:
        return None
    return get_brand_profile(brand_id)


def logout_demo_account(storage: MutableMapping[str, Any]) -> None:
    storage.pop(AUTH_STORAGE_KEY, None)


def demo_account_summary() -> list[dict[str, str]]:
    """Return non-secret account metadata for diagnostics/tests."""

    rows: list[dict[str, str]] = []
    for account in _DEMO_ACCOUNTS.values():
        profile = get_brand_profile(account.brand_id)
        rows.append(
            {
                'login_id': account.login_id,
                'brand_id': account.brand_id,
                'brand_name': profile['display_name'],
                'country': profile['country'],
                'currency_code': profile['currency_code'],
            }
        )
    return rows
