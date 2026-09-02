from __future__ import annotations

from copy import deepcopy
import random
from typing import Any

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID


FORMATS = [
    'Mall kiosk',
    'High-street café',
    'Compact takeaway',
    'Premium café',
    'Delivery-led store',
]


INDIA_CITY_CLUSTERS = [
    ('Delhi NCR', 'New Delhi', 28.6139, 77.2090, ['Connaught Place', 'Saket', 'Aerocity']),
    ('Delhi NCR', 'Gurugram', 28.4595, 77.0266, ['Cyber Hub', 'Golf Course Road', 'Sector 29']),
    ('Delhi NCR', 'Noida', 28.5355, 77.3910, ['DLF Mall of India', 'Sector 18', 'Sector 62']),
    ('West', 'Mumbai', 19.0760, 72.8777, ['Phoenix Palladium', 'Bandra Linking Road', 'Powai']),
    ('West', 'Pune', 18.5204, 73.8567, ['Phoenix Marketcity', 'Koregaon Park', 'Baner']),
    ('South', 'Bengaluru', 12.9716, 77.5946, ['Indiranagar', 'Koramangala', 'Whitefield']),
    ('South', 'Hyderabad', 17.3850, 78.4867, ['Jubilee Hills', 'Banjara Hills', 'HITEC City']),
    ('South', 'Chennai', 13.0827, 80.2707, ['Phoenix Marketcity', 'T Nagar', 'Anna Nagar']),
    ('East', 'Kolkata', 22.5726, 88.3639, ['Park Street', 'Salt Lake Sector V', 'New Town']),
    ('North', 'Chandigarh', 30.7333, 76.7794, ['Elante Mall', 'Sector 17', 'Madhya Marg']),
    ('North', 'Jaipur', 26.9124, 75.7873, ['C Scheme', 'World Trade Park', 'Vaishali Nagar']),
    ('West', 'Ahmedabad', 23.0225, 72.5714, ['Ahmedabad One', 'SG Highway', 'Prahlad Nagar']),
    ('North', 'Lucknow', 26.8467, 80.9462, ['Hazratganj', 'Gomti Nagar', 'Aliganj']),
    ('South', 'Kochi', 9.9312, 76.2673, ['Lulu Mall', 'Panampilly Nagar', 'Marine Drive']),
    ('Central', 'Indore', 22.7196, 75.8577, ['Vijay Nagar', 'Palasia', 'Treasure Island']),
    ('East', 'Bhubaneswar', 20.2961, 85.8245, ['Saheed Nagar', 'Patia', 'Esplanade Mall']),
    ('East', 'Guwahati', 26.1445, 91.7362, ['GS Road', 'Christian Basti', 'City Center']),
    ('West', 'Surat', 21.1702, 72.8311, ['VR Surat', 'Vesu', 'Adajan']),
    ('Central', 'Nagpur', 21.1458, 79.0882, ['Dharampeth', 'Civil Lines', 'Wardha Road']),
    ('South', 'Coimbatore', 11.0168, 76.9558, ['RS Puram', 'Peelamedu', 'Brookefields']),
    ('East', 'Patna', 25.5941, 85.1376, ['Fraser Road', 'Boring Road', 'Patliputra']),
]


CANADA_CITY_CLUSTERS = [
    ('Ontario', 'Toronto', 43.6532, -79.3832, ['Yorkville', 'Queen Street West']),
    ('Ontario', 'Mississauga', 43.5890, -79.6441, ['Square One', 'Port Credit']),
    ('Ontario', 'Ottawa', 45.4215, -75.6972, ['ByWard Market', 'Lansdowne']),
    ('Ontario', 'Hamilton', 43.2557, -79.8711, ['James Street North', 'Westdale']),
    ('Quebec', 'Montreal', 45.5019, -73.5674, ['Plateau Mont-Royal', 'Old Montreal']),
    ('Quebec', 'Quebec City', 46.8139, -71.2080, ['Old Quebec', 'Sainte-Foy']),
    ('British Columbia', 'Vancouver', 49.2827, -123.1207, ['Yaletown', 'Kitsilano']),
    ('British Columbia', 'Surrey', 49.1913, -122.8490, ['Central City', 'Guildford']),
    ('Alberta', 'Calgary', 51.0447, -114.0719, ['17th Avenue', 'Kensington']),
    ('Alberta', 'Edmonton', 53.5461, -113.4938, ['Whyte Avenue', 'Ice District']),
    ('Manitoba', 'Winnipeg', 49.8951, -97.1384, ['The Forks', 'Osborne Village']),
    ('Nova Scotia', 'Halifax', 44.6488, -63.5752, ['Waterfront', 'Spring Garden Road']),
]


_TIER_ONE_INDIA = {
    'New Delhi', 'Gurugram', 'Noida', 'Mumbai', 'Pune', 'Bengaluru',
    'Hyderabad', 'Chennai', 'Kolkata',
}

_TIER_ONE_CANADA = {
    'Toronto', 'Mississauga', 'Ottawa', 'Montreal', 'Vancouver',
    'Calgary', 'Edmonton',
}

_FORMAT_MULTIPLIER = {
    'Mall kiosk': 0.96,
    'High-street café': 1.04,
    'Compact takeaway': 0.88,
    'Premium café': 1.18,
    'Delivery-led store': 0.82,
}

_SIZE_RANGES = {
    'Mall kiosk': (260, 430),
    'High-street café': (520, 850),
    'Compact takeaway': (300, 500),
    'Premium café': (700, 1100),
    'Delivery-led store': (260, 450),
}


def _stable_seed(text: str) -> int:
    # Match the deterministic seed used by the current Network Intelligence MVP.
    return sum(
        (index + 1) * ord(character)
        for index, character in enumerate(text)
    )


def _status(age_months: int, margin_pct: float, growth_pct: float) -> str:
    if age_months <= 6:
        return 'Newly opened'
    if margin_pct < 10.5 or growth_pct < -4.5:
        return 'Underperforming'
    if margin_pct > 17.0 and growth_pct > 4.0:
        return 'Above target'
    return 'Needs attention'


def _build_india_rows() -> list[dict[str, Any]]:
    """Reproduce the existing 63-outlet India network in neutral money units."""

    rows: list[dict[str, Any]] = []
    store_number = 0

    for region, city, city_lat, city_lon, outlets in INDIA_CITY_CLUSTERS:
        for local_index, outlet in enumerate(outlets):
            store_number += 1
            store_id = f'{city.lower().replace(" ", "-")}-{local_index + 1}'
            rng = random.Random(_stable_seed(store_id))

            outlet_format = FORMATS[(store_number + local_index) % len(FORMATS)]
            latitude = city_lat + rng.uniform(-0.055, 0.055)
            longitude = city_lon + rng.uniform(-0.055, 0.055)
            city_factor = 1.15 if city in _TIER_ONE_INDIA else 0.92

            revenue_lakh = (
                rng.uniform(15.0, 25.0)
                * city_factor
                * _FORMAT_MULTIPLIER[outlet_format]
            )

            age_months = rng.randint(10, 72)
            if store_number in {13, 28, 41, 54, 61}:
                age_months = rng.randint(2, 6)

            growth_pct = rng.uniform(-7.5, 12.5)
            margin_pct = rng.uniform(8.0, 24.0)
            size_min, size_max = _SIZE_RANGES[outlet_format]
            square_feet = rng.randint(size_min, size_max)

            rent_per_sq_ft = (
                rng.uniform(330, 720)
                if city in _TIER_ONE_INDIA
                else rng.uniform(180, 430)
            )
            monthly_rent = square_feet * rent_per_sq_ft
            monthly_revenue = revenue_lakh * 100_000
            average_ticket = float(rng.randint(245, 335))
            employees = max(6, int(square_feet / rng.uniform(55, 78)))
            monthly_orders = int(monthly_revenue / average_ticket)
            operating_profit = monthly_revenue * margin_pct / 100

            rows.append({
                'store_id': store_id,
                'outlet': outlet,
                'city': city,
                'region': region,
                'lat': round(latitude, 5),
                'lon': round(longitude, 5),
                'format': outlet_format,
                'age_months': age_months,
                'square_feet': square_feet,
                'monthly_revenue': round(monthly_revenue, 2),
                'operating_profit': round(operating_profit, 2),
                'margin_pct': round(margin_pct, 1),
                'growth_pct': round(growth_pct, 1),
                'next_month_revenue': round(
                    monthly_revenue * (1 + growth_pct / 100), 2
                ),
                'employees': employees,
                'monthly_orders': monthly_orders,
                'average_ticket': average_ticket,
                'delivery_share_pct': rng.randint(19, 51),
                'monthly_rent': round(monthly_rent, 2),
                'rent_ratio_pct': round(monthly_rent / monthly_revenue * 100, 1),
                'waste_pct': round(rng.uniform(1.4, 5.8), 1),
                'stockout_pct': round(rng.uniform(1.0, 8.5), 1),
                'rating': round(rng.uniform(3.8, 4.8), 1),
                'status': _status(age_months, margin_pct, growth_pct),
            })

    return rows


def _build_canada_rows() -> list[dict[str, Any]]:
    """Build a deterministic 24-outlet synthetic Canadian café network."""

    rows: list[dict[str, Any]] = []
    store_number = 0

    for region, city, city_lat, city_lon, outlets in CANADA_CITY_CLUSTERS:
        for local_index, outlet in enumerate(outlets):
            store_number += 1
            seed_key = f'canada:{city}:{outlet}:{local_index}'
            store_id = f'ca-{city.lower().replace(" ", "-")}-{local_index + 1}'
            rng = random.Random(_stable_seed(seed_key))

            outlet_format = FORMATS[(store_number + local_index + 1) % len(FORMATS)]
            latitude = city_lat + rng.uniform(-0.045, 0.045)
            longitude = city_lon + rng.uniform(-0.045, 0.045)
            city_factor = 1.12 if city in _TIER_ONE_CANADA else 0.94

            monthly_revenue = (
                rng.uniform(78_000, 132_000)
                * city_factor
                * _FORMAT_MULTIPLIER[outlet_format]
            )

            age_months = rng.randint(9, 68)
            if store_number in {4, 11, 19, 23}:
                age_months = rng.randint(2, 6)

            growth_pct = rng.uniform(-6.8, 11.5)
            margin_pct = rng.uniform(8.5, 22.5)
            size_min, size_max = _SIZE_RANGES[outlet_format]
            square_feet = rng.randint(size_min, size_max)

            # Synthetic commercial rents in CAD/month.
            if city in {'Toronto', 'Vancouver', 'Montreal'}:
                monthly_rent = rng.uniform(13_500, 25_000)
            elif city in _TIER_ONE_CANADA:
                monthly_rent = rng.uniform(10_000, 19_000)
            else:
                monthly_rent = rng.uniform(7_500, 14_500)

            average_ticket = round(rng.uniform(12.25, 18.75), 2)
            employees = max(6, int(square_feet / rng.uniform(58, 82)))
            monthly_orders = int(monthly_revenue / average_ticket)
            operating_profit = monthly_revenue * margin_pct / 100

            rows.append({
                'store_id': store_id,
                'outlet': outlet,
                'city': city,
                'region': region,
                'lat': round(latitude, 5),
                'lon': round(longitude, 5),
                'format': outlet_format,
                'age_months': age_months,
                'square_feet': square_feet,
                'monthly_revenue': round(monthly_revenue, 2),
                'operating_profit': round(operating_profit, 2),
                'margin_pct': round(margin_pct, 1),
                'growth_pct': round(growth_pct, 1),
                'next_month_revenue': round(
                    monthly_revenue * (1 + growth_pct / 100), 2
                ),
                'employees': employees,
                'monthly_orders': monthly_orders,
                'average_ticket': average_ticket,
                'delivery_share_pct': rng.randint(18, 46),
                'monthly_rent': round(monthly_rent, 2),
                'rent_ratio_pct': round(monthly_rent / monthly_revenue * 100, 1),
                'waste_pct': round(rng.uniform(1.2, 5.2), 1),
                'stockout_pct': round(rng.uniform(0.8, 7.5), 1),
                'rating': round(rng.uniform(3.9, 4.8), 1),
                'status': _status(age_months, margin_pct, growth_pct),
            })

    return rows


def build_network_rows(brand_id: str) -> list[dict[str, Any]]:
    """Return a fresh deterministic outlet network for one demo brand."""

    if brand_id == INDIA_BRAND_ID:
        return deepcopy(_build_india_rows())
    if brand_id == CANADA_BRAND_ID:
        return deepcopy(_build_canada_rows())
    raise KeyError(f'Unknown Vesper demo brand: {brand_id}')
