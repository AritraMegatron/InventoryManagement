"""Compatibility entry point for Canada-only callers."""
from app.data.brand_catalog import CANADA_BRAND_ID
from app.services.brand_network_sync_service import sync_brand_network


def sync_canada_network(brand_state):
    if brand_state['brand_id'] == CANADA_BRAND_ID:
        sync_brand_network(brand_state)
