from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID, get_brand_profile
from app.data.network_demo_data import build_network_rows
from app.services.network_service import (
    build_command_center_snapshot,
    build_network_view_rows,
    build_region_centers,
    build_table_columns,
    summarize_network,
)


def test_network_summary_matches_each_brand_baseline():
    india = summarize_network(build_network_rows(INDIA_BRAND_ID))
    canada = summarize_network(build_network_rows(CANADA_BRAND_ID))

    assert india['outlet_count'] == 63
    assert canada['outlet_count'] == 24
    assert india['underperforming_count'] == 19
    assert canada['underperforming_count'] == 7
    assert india['monthly_revenue'] != canada['monthly_revenue']


def test_canada_network_view_uses_cad_thousands_and_canadian_regions():
    profile = get_brand_profile(CANADA_BRAND_ID)
    outlets = build_network_rows(CANADA_BRAND_ID)
    rows = build_network_view_rows(outlets, profile)
    columns = build_table_columns(profile)
    centers = build_region_centers(outlets, profile)

    assert len(rows) == 24
    assert any(column['label'] == 'Revenue C$K' for column in columns)
    assert 'Ontario' in centers
    assert 'Delhi NCR' not in centers
    assert centers['All regions'] == (
        profile['map_center_lat'],
        profile['map_center_lon'],
        profile['map_zoom'],
    )


def test_india_network_view_preserves_inr_lakh_table_unit():
    profile = get_brand_profile(INDIA_BRAND_ID)
    outlets = build_network_rows(INDIA_BRAND_ID)
    columns = build_table_columns(profile)

    assert any(column['label'] == 'Revenue ₹L' for column in columns)


def test_command_center_actions_are_brand_specific_and_native_currency():
    india_profile = get_brand_profile(INDIA_BRAND_ID)
    canada_profile = get_brand_profile(CANADA_BRAND_ID)

    india = build_command_center_snapshot(
        build_network_rows(INDIA_BRAND_ID), india_profile
    )
    canada = build_command_center_snapshot(
        build_network_rows(CANADA_BRAND_ID), canada_profile
    )

    assert india['summary']['outlet_count'] == 63
    assert canada['summary']['outlet_count'] == 24
    assert india['actions'][2]['title'] == 'High-Protein Chocolate Shake'
    assert canada['actions'][2]['title'] == 'Maple Protein Cold Brew'
    assert '₹' in india['actions'][0]['impact']
    assert 'C$' in canada['actions'][0]['impact']


def test_network_forecast_refresh_is_deterministic_and_brand_local():
    from copy import deepcopy
    from app.services.network_service import refresh_network_forecast

    canada_a = build_network_rows(CANADA_BRAND_ID)
    canada_b = deepcopy(canada_a)
    india = build_network_rows(INDIA_BRAND_ID)
    india_before = deepcopy(india)

    refresh_network_forecast(canada_a, 1)
    refresh_network_forecast(canada_b, 1)

    assert canada_a == canada_b
    assert canada_a[0]['next_month_revenue'] != build_network_rows(CANADA_BRAND_ID)[0]['next_month_revenue']
    assert india == india_before
