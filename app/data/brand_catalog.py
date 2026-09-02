from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class BrandProfile:
    brand_id: str
    display_name: str
    short_name: str
    country: str
    country_code: str
    currency_code: str
    currency_symbol: str
    timezone: str
    locale: str
    map_center_lat: float
    map_center_lon: float
    map_zoom: int
    business_description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


INDIA_BRAND_ID = 'northstar_india'
CANADA_BRAND_ID = 'maple_mason_canada'
DEFAULT_BRAND_ID = INDIA_BRAND_ID


_BRAND_PROFILES: dict[str, BrandProfile] = {
    INDIA_BRAND_ID: BrandProfile(
        brand_id=INDIA_BRAND_ID,
        display_name='Northstar Shakes — India',
        short_name='Northstar Shakes',
        country='India',
        country_code='IN',
        currency_code='INR',
        currency_symbol='₹',
        timezone='Asia/Kolkata',
        locale='en-IN',
        map_center_lat=22.8,
        map_center_lon=79.0,
        map_zoom=5,
        business_description=(
            'Multi-location dessert and beverage chain operating across India.'
        ),
    ),
    CANADA_BRAND_ID: BrandProfile(
        brand_id=CANADA_BRAND_ID,
        display_name='Maple & Mason Café — Canada',
        short_name='Maple & Mason Café',
        country='Canada',
        country_code='CA',
        currency_code='CAD',
        currency_symbol='C$',
        timezone='America/Toronto',
        locale='en-CA',
        map_center_lat=56.1304,
        map_center_lon=-106.3468,
        map_zoom=3,
        business_description=(
            'Multi-location café and beverage chain operating across Canada.'
        ),
    ),
}


def list_brand_profiles() -> list[dict[str, Any]]:
    """Return safe copies of every demo brand profile."""

    return [
        profile.to_dict()
        for profile in _BRAND_PROFILES.values()
    ]


def get_brand_profile(brand_id: str) -> dict[str, Any]:
    """Return a copy of one demo brand profile."""

    try:
        profile = _BRAND_PROFILES[brand_id]
    except KeyError as exc:
        raise KeyError(f'Unknown Vesper demo brand: {brand_id}') from exc

    return deepcopy(profile.to_dict())


def has_brand(brand_id: str) -> bool:
    return brand_id in _BRAND_PROFILES
