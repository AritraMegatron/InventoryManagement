from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.auth_service import (
    authenticate_demo_account,
    get_authenticated_brand_id,
    get_authenticated_brand_profile,
    is_authenticated,
    logout_demo_account,
)
from app.state.demo_state import get_brand_state


def test_wrong_credentials_do_not_authenticate() -> None:
    storage: dict = {}
    assert not authenticate_demo_account(storage, 'northstar', 'wrong')
    assert not is_authenticated(storage)


def test_india_account_selects_india_workspace() -> None:
    storage: dict = {}
    assert authenticate_demo_account(storage, 'NORTHSTAR', 'vesperindia')
    assert get_authenticated_brand_id(storage) == INDIA_BRAND_ID
    assert get_authenticated_brand_profile(storage)['currency_code'] == 'INR'
    assert get_brand_state(storage)['brand_id'] == INDIA_BRAND_ID


def test_canada_account_selects_canada_workspace() -> None:
    storage: dict = {}
    assert authenticate_demo_account(storage, 'maplemason', 'vespercanada')
    assert get_authenticated_brand_id(storage) == CANADA_BRAND_ID
    assert get_authenticated_brand_profile(storage)['currency_code'] == 'CAD'
    assert get_brand_state(storage)['brand_id'] == CANADA_BRAND_ID


def test_logout_invalidates_authentication() -> None:
    storage: dict = {}
    assert authenticate_demo_account(storage, 'northstar', 'vesperindia')
    logout_demo_account(storage)
    assert not is_authenticated(storage)


def test_brand_states_remain_isolated_after_account_switch() -> None:
    storage: dict = {}
    authenticate_demo_account(storage, 'northstar', 'vesperindia')
    india = get_brand_state(storage)
    india['decisions']['command_center']['test'] = 'india-only'

    logout_demo_account(storage)
    authenticate_demo_account(storage, 'maplemason', 'vespercanada')
    canada = get_brand_state(storage)

    assert canada['decisions']['command_center'].get('test') is None
    assert storage['vesper_demo_session_v1']['brands'][INDIA_BRAND_ID][
        'decisions'
    ]['command_center']['test'] == 'india-only'
