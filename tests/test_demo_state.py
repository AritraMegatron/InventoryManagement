from __future__ import annotations

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.currency_service import format_money
from app.state.demo_state import (
    build_brand_state,
    ensure_demo_session,
    get_brand_state,
    reset_brand_state,
    select_brand,
)


def test_india_and_canada_profiles_and_networks() -> None:
    india = build_brand_state(INDIA_BRAND_ID)
    canada = build_brand_state(CANADA_BRAND_ID)

    assert india['profile']['currency_code'] == 'INR'
    assert india['profile']['country_code'] == 'IN'
    assert len(india['network']['outlets']) == 63

    assert canada['profile']['currency_code'] == 'CAD'
    assert canada['profile']['country_code'] == 'CA'
    assert len(canada['network']['outlets']) == 24


def test_network_generation_is_deterministic_but_not_shared() -> None:
    first = build_brand_state(CANADA_BRAND_ID)
    second = build_brand_state(CANADA_BRAND_ID)

    assert first == second
    first['network']['outlets'][0]['monthly_revenue'] = -1
    assert second['network']['outlets'][0]['monthly_revenue'] > 0


def test_session_brand_switching_is_isolated() -> None:
    storage: dict = {}
    session = ensure_demo_session(storage)
    assert session['selected_brand_id'] == INDIA_BRAND_ID

    india = get_brand_state(storage)
    india['decisions']['command_center']['demo'] = 'india-only'

    canada = select_brand(storage, CANADA_BRAND_ID)
    canada['decisions']['command_center']['demo'] = 'canada-only'

    assert get_brand_state(storage, INDIA_BRAND_ID)['decisions']['command_center']['demo'] == 'india-only'
    assert get_brand_state(storage, CANADA_BRAND_ID)['decisions']['command_center']['demo'] == 'canada-only'


def test_reset_only_resets_requested_brand() -> None:
    storage: dict = {}
    india = get_brand_state(storage, INDIA_BRAND_ID)
    india['workflows']['demand_inventory']['forecast_run_number'] = 9

    canada = select_brand(storage, CANADA_BRAND_ID)
    canada['workflows']['demand_inventory']['forecast_run_number'] = 4

    reset_brand_state(storage, INDIA_BRAND_ID)

    assert get_brand_state(storage, INDIA_BRAND_ID)['workflows']['demand_inventory']['forecast_run_number'] == 0
    assert get_brand_state(storage, CANADA_BRAND_ID)['workflows']['demand_inventory']['forecast_run_number'] == 4


def test_country_specific_currency_formatting() -> None:
    india = build_brand_state(INDIA_BRAND_ID)
    canada = build_brand_state(CANADA_BRAND_ID)

    assert format_money(12_800_000, india['profile']) == '₹1.3 Cr'
    assert format_money(128_000, india['profile']) == '₹1.3 L'
    assert format_money(2_450_000, canada['profile']) == 'C$2.5M'
    assert format_money(128_000, canada['profile']) == 'C$128.0K'
