from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

import httpx
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / '.env', override=False)

MAPPLS_AUTOSUGGEST_URL = (
    'https://search.mappls.com/search/places/autosuggest/json'
)
MAPPLS_GEOCODE_URL = 'https://search.mappls.com/search/address/geocode'
MAPPLS_PLACE_DETAILS_URL = (
    'https://place.mappls.com/O2O/entity/place-details/{eloc}'
)


class LocationServiceError(RuntimeError):
    """Raised when a configured address provider cannot complete a request."""


@dataclass(frozen=True, slots=True)
class LocationSuggestion:
    provider_id: str
    display_name: str
    formatted_address: str
    city: str = ''
    state: str = ''
    postal_code: str = ''
    latitude: float | None = None
    longitude: float | None = None
    provider: str = 'demo'
    result_type: str = ''

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def searchable_text(self) -> str:
        return ' '.join(
            part
            for part in (
                self.display_name,
                self.formatted_address,
                self.city,
                self.state,
                self.postal_code,
            )
            if part
        ).lower()


class LocationService(Protocol):
    @property
    def provider_label(self) -> str:
        ...

    @property
    def is_live(self) -> bool:
        ...

    async def suggest(
        self,
        query: str,
        *,
        proximity: tuple[float, float] | None = None,
        limit: int = 6,
    ) -> list[LocationSuggestion]:
        ...

    async def resolve(
        self,
        suggestion: LocationSuggestion,
    ) -> LocationSuggestion:
        ...

    async def geocode(self, address: str) -> LocationSuggestion | None:
        ...


def _clean_text(value: Any) -> str:
    return str(value or '').strip()


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ''):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return None


def _address_tokens(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get('addressTokens')
    return value if isinstance(value, dict) else {}


class MapplsLocationService:
    """Mappls autosuggest and place-resolution client.

    Mappls autosuggest returns an eLoc identifier. Latitude and longitude are
    then requested from Place Details. Coordinate fields depend on the Mappls
    products enabled for the configured key, so the caller must retain the
    manual-coordinate fallback in the UI.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 8.0,
    ) -> None:
        api_key = api_key.strip()
        if not api_key:
            raise ValueError('Mappls API key must not be blank.')
        self._api_key = api_key
        self._timeout = httpx.Timeout(timeout_seconds)

    @property
    def provider_label(self) -> str:
        return 'Mappls India address search'

    @property
    def is_live(self) -> bool:
        return True

    async def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        # Mappls uses a valueless ``tokenizeAddress`` parameter. Keep empty
        # strings in the query while still excluding parameters that are truly
        # absent.
        safe_params = {
            key: value
            for key, value in params.items()
            if value is not None
        }
        safe_params['access_token'] = self._api_key

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=safe_params)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LocationServiceError(
                'Mappls did not respond before the address-search timeout.'
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in {401, 403}:
                message = (
                    'Mappls rejected the configured key or the required API '
                    'product is not enabled.'
                )
            elif status == 429:
                message = 'Mappls address-search rate limit was reached.'
            else:
                message = f'Mappls returned HTTP {status}.'
            raise LocationServiceError(message) from exc
        except httpx.HTTPError as exc:
            raise LocationServiceError(
                'The Mappls address service could not be reached.'
            ) from exc

        if response.status_code == 204 or not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise LocationServiceError(
                'Mappls returned an invalid JSON response.'
            ) from exc

        if not isinstance(payload, dict):
            raise LocationServiceError(
                'Mappls returned an unexpected response structure.'
            )
        return payload

    @staticmethod
    def _from_mappls_item(item: dict[str, Any]) -> LocationSuggestion:
        tokens = _address_tokens(item)
        place_name = _clean_text(
            item.get('placeName')
            or item.get('name')
            or item.get('poi')
        )
        place_address = _clean_text(
            item.get('placeAddress')
            or item.get('formattedAddress')
            or item.get('address')
        )
        city = _clean_text(item.get('city') or tokens.get('city'))
        state = _clean_text(item.get('state') or tokens.get('state'))
        postal_code = _clean_text(
            item.get('pincode')
            or item.get('postalCode')
            or tokens.get('pincode')
        )
        provider_id = _clean_text(
            item.get('eLoc')
            or item.get('eloc')
            or item.get('placeId')
        )
        display_name = place_name or place_address or provider_id

        return LocationSuggestion(
            provider_id=provider_id,
            display_name=display_name,
            formatted_address=place_address or display_name,
            city=city,
            state=state,
            postal_code=postal_code,
            latitude=_safe_float(
                item.get('latitude')
                or item.get('lat')
                or item.get('entry_lat')
                or item.get('entryLatitude')
            ),
            longitude=_safe_float(
                item.get('longitude')
                or item.get('lng')
                or item.get('lon')
                or item.get('entry_lon')
                or item.get('entryLongitude')
            ),
            provider='mappls',
            result_type=_clean_text(item.get('type')),
        )

    async def suggest(
        self,
        query: str,
        *,
        proximity: tuple[float, float] | None = None,
        limit: int = 6,
    ) -> list[LocationSuggestion]:
        query = ' '.join(query.split())[:45]
        if len(query) < 3:
            return []

        params: dict[str, Any] = {
            'query': query,
            'region': 'IND',
            # An empty tokenizeAddress parameter requests structured tokens
            # when the configured Mappls plan makes them available.
            'tokenizeAddress': '',
        }
        if proximity is not None:
            params['location'] = f'{proximity[0]},{proximity[1]}'

        payload = await self._get_json(
            MAPPLS_AUTOSUGGEST_URL,
            params=params,
        )

        raw_items: list[dict[str, Any]] = []
        for key in ('suggestedLocations', 'userAddedLocations'):
            value = payload.get(key, [])
            if isinstance(value, list):
                raw_items.extend(
                    item for item in value if isinstance(item, dict)
                )

        results: list[LocationSuggestion] = []
        seen: set[tuple[str, str]] = set()
        for item in raw_items:
            suggestion = self._from_mappls_item(item)
            if not suggestion.display_name:
                continue
            identity = (
                suggestion.provider_id,
                suggestion.formatted_address.lower(),
            )
            if identity in seen:
                continue
            seen.add(identity)
            results.append(suggestion)
            if len(results) >= max(1, limit):
                break
        return results

    async def _place_details(self, eloc: str) -> LocationSuggestion | None:
        eloc = eloc.strip()
        if not eloc:
            return None
        payload = await self._get_json(
            MAPPLS_PLACE_DETAILS_URL.format(eloc=eloc),
            params={},
        )
        if not payload:
            return None
        return self._from_mappls_item(payload)

    async def resolve(
        self,
        suggestion: LocationSuggestion,
    ) -> LocationSuggestion:
        if suggestion.has_coordinates:
            return suggestion

        details = await self._place_details(suggestion.provider_id)
        if details is None:
            return suggestion

        return LocationSuggestion(
            provider_id=(
                details.provider_id or suggestion.provider_id
            ),
            display_name=(
                details.display_name or suggestion.display_name
            ),
            formatted_address=(
                details.formatted_address
                or suggestion.formatted_address
            ),
            city=details.city or suggestion.city,
            state=details.state or suggestion.state,
            postal_code=(
                details.postal_code or suggestion.postal_code
            ),
            latitude=details.latitude,
            longitude=details.longitude,
            provider='mappls',
            result_type=(
                details.result_type or suggestion.result_type
            ),
        )

    async def geocode(self, address: str) -> LocationSuggestion | None:
        address = ' '.join(address.split())
        if len(address) < 3:
            return None

        payload = await self._get_json(
            MAPPLS_GEOCODE_URL,
            params={
                'address': address,
                'itemCount': 1,
                'region': 'IND',
            },
        )
        item = _first_mapping(payload.get('copResults'))
        if item is None:
            return None
        result = self._from_mappls_item(item)
        return await self.resolve(result)


INDIA_DEMO_LOCATIONS: tuple[LocationSuggestion, ...] = (
    LocationSuggestion(
        'DEMO-NOIDA-62', 'Sector 62, Noida',
        'Electronic City Metro corridor, Sector 62, Noida, Uttar Pradesh 201309',
        'Noida', 'Uttar Pradesh', '201309', 28.6280, 77.3649,
    ),
    LocationSuggestion(
        'DEMO-GGM-54', 'Golf Course Road, Sector 54',
        'Golf Course Road commercial belt, Sector 54, Gurugram, Haryana 122011',
        'Gurugram', 'Haryana', '122011', 28.4446, 77.0996,
    ),
    LocationSuggestion(
        'DEMO-KOL-SV', 'Sector V, Salt Lake',
        'College More commercial cluster, Sector V, Salt Lake, Kolkata, West Bengal 700091',
        'Kolkata', 'West Bengal', '700091', 22.5726, 88.4331,
    ),
    LocationSuggestion(
        'DEMO-BLR-100FT', 'Indiranagar 100 Feet Road',
        '100 Feet Road retail corridor, Indiranagar, Bengaluru, Karnataka 560038',
        'Bengaluru', 'Karnataka', '560038', 12.9719, 77.6412,
    ),
    LocationSuggestion(
        'DEMO-DEL-CP', 'Connaught Place',
        'Inner Circle, Connaught Place, New Delhi, Delhi 110001',
        'New Delhi', 'Delhi', '110001', 28.6315, 77.2167,
    ),
    LocationSuggestion(
        'DEMO-MUM-BKC', 'Bandra Kurla Complex',
        'Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra 400051',
        'Mumbai', 'Maharashtra', '400051', 19.0676, 72.8697,
    ),
    LocationSuggestion(
        'DEMO-MUM-POWAI', 'Hiranandani Gardens, Powai',
        'Hiranandani Gardens, Powai, Mumbai, Maharashtra 400076',
        'Mumbai', 'Maharashtra', '400076', 19.1187, 72.9073,
    ),
    LocationSuggestion(
        'DEMO-PUN-KP', 'Koregaon Park',
        'Koregaon Park, Pune, Maharashtra 411001',
        'Pune', 'Maharashtra', '411001', 18.5362, 73.8940,
    ),
    LocationSuggestion(
        'DEMO-HYD-HITEC', 'HITEC City',
        'HITEC City, Madhapur, Hyderabad, Telangana 500081',
        'Hyderabad', 'Telangana', '500081', 17.4435, 78.3772,
    ),
    LocationSuggestion(
        'DEMO-CHE-OMR', 'OMR, Perungudi',
        'Old Mahabalipuram Road, Perungudi, Chennai, Tamil Nadu 600096',
        'Chennai', 'Tamil Nadu', '600096', 12.9610, 80.2412,
    ),
    LocationSuggestion(
        'DEMO-AHM-SG', 'S G Highway',
        'Sarkhej Gandhinagar Highway, Ahmedabad, Gujarat 380054',
        'Ahmedabad', 'Gujarat', '380054', 23.0750, 72.5254,
    ),
    LocationSuggestion(
        'DEMO-JAI-C', 'C-Scheme',
        'C-Scheme, Jaipur, Rajasthan 302001',
        'Jaipur', 'Rajasthan', '302001', 26.9079, 75.7949,
    ),
)


CANADA_DEMO_LOCATIONS: tuple[LocationSuggestion, ...] = (
    LocationSuggestion(
        'DEMO-CA-TOR-EATON', 'Yonge & Dundas, Toronto',
        '220 Yonge Street, Toronto, Ontario M5B 2H1, Canada',
        'Toronto', 'Ontario', 'M5B 2H1', 43.6544, -79.3807,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-VAN-PACIFIC', 'Pacific Centre, Vancouver',
        '701 West Georgia Street, Vancouver, British Columbia V7Y 1G5, Canada',
        'Vancouver', 'British Columbia', 'V7Y 1G5', 49.2832, -123.1171,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-MTL-EATON', 'Sainte-Catherine, Montréal',
        '705 Rue Sainte-Catherine Ouest, Montréal, Québec H3B 4G5, Canada',
        'Montréal', 'Québec', 'H3B 4G5', 45.5037, -73.5710,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-CGY-CHINOOK', 'Chinook Centre, Calgary',
        '6455 Macleod Trail SW, Calgary, Alberta T2H 0K8, Canada',
        'Calgary', 'Alberta', 'T2H 0K8', 50.9985, -114.0744,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-OTT-RIDEAU', 'Rideau Centre, Ottawa',
        '50 Rideau Street, Ottawa, Ontario K1N 9J7, Canada',
        'Ottawa', 'Ontario', 'K1N 9J7', 45.4251, -75.6900,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-MIS-SQ1', 'Square One, Mississauga',
        '100 City Centre Drive, Mississauga, Ontario L5B 2C9, Canada',
        'Mississauga', 'Ontario', 'L5B 2C9', 43.5930, -79.6425,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-EDM-WEM', 'West Edmonton Mall',
        '8882 170 Street NW, Edmonton, Alberta T5T 4J2, Canada',
        'Edmonton', 'Alberta', 'T5T 4J2', 53.5225, -113.6242,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-HFX-SHOPPING', 'Halifax Shopping Centre',
        '7001 Mumford Road, Halifax, Nova Scotia B3L 4N9, Canada',
        'Halifax', 'Nova Scotia', 'B3L 4N9', 44.6494, -63.6189,
        provider='demo-ca',
    ),
    LocationSuggestion(
        'DEMO-CA-TOR-THE-WELL',
        'The Well, Toronto',
        '486 Front Street West, Toronto, Ontario M5V 0V2, Canada',
        'Toronto',
        'Ontario',
        'M5V 0V2',
        43.6427,
        -79.3948,
        provider='demo-ca',
    ),
)


class DemoCanadianLocationService:
    """Offline Canadian address catalog for deterministic client demos."""

    @property
    def provider_label(self) -> str:
        return 'Built-in Canadian demo addresses'

    @property
    def is_live(self) -> bool:
        return False

    async def suggest(
        self,
        query: str,
        *,
        proximity: tuple[float, float] | None = None,
        limit: int = 6,
    ) -> list[LocationSuggestion]:
        del proximity
        words = [word for word in query.lower().split() if word]
        if len(''.join(words)) < 3:
            return []

        ranked: list[tuple[int, LocationSuggestion]] = []
        for suggestion in CANADA_DEMO_LOCATIONS:
            text = suggestion.searchable_text
            matches = sum(word in text for word in words)
            if matches:
                exact_bonus = 5 if query.lower() in text else 0
                ranked.append((matches * 10 + exact_bonus, suggestion))
        ranked.sort(key=lambda item: (-item[0], item[1].display_name))
        return [item[1] for item in ranked[:max(1, limit)]]

    async def resolve(
        self,
        suggestion: LocationSuggestion,
    ) -> LocationSuggestion:
        return suggestion

    async def geocode(self, address: str) -> LocationSuggestion | None:
        query = address.lower().strip()
        if not query:
            return None
        best: tuple[int, LocationSuggestion] | None = None
        words = [word for word in query.split() if len(word) >= 3]
        for suggestion in CANADA_DEMO_LOCATIONS:
            text = suggestion.searchable_text
            score = sum(word in text for word in words)
            if query in text:
                score += 10
            if best is None or score > best[0]:
                best = (score, suggestion)
        return best[1] if best and best[0] >= 2 else None


class DemoIndianLocationService:
    """Offline fallback so the demo remains usable without an API key."""

    @property
    def provider_label(self) -> str:
        return 'Built-in Indian demo addresses'

    @property
    def is_live(self) -> bool:
        return False

    async def suggest(
        self,
        query: str,
        *,
        proximity: tuple[float, float] | None = None,
        limit: int = 6,
    ) -> list[LocationSuggestion]:
        del proximity
        words = [word for word in query.lower().split() if word]
        if len(''.join(words)) < 3:
            return []

        ranked: list[tuple[int, LocationSuggestion]] = []
        for suggestion in INDIA_DEMO_LOCATIONS:
            text = suggestion.searchable_text
            matches = sum(word in text for word in words)
            if matches:
                exact_bonus = 5 if query.lower() in text else 0
                ranked.append((matches * 10 + exact_bonus, suggestion))
        ranked.sort(key=lambda item: (-item[0], item[1].display_name))
        return [item[1] for item in ranked[:max(1, limit)]]

    async def resolve(
        self,
        suggestion: LocationSuggestion,
    ) -> LocationSuggestion:
        return suggestion

    async def geocode(self, address: str) -> LocationSuggestion | None:
        query = address.lower().strip()
        if not query:
            return None
        best: tuple[int, LocationSuggestion] | None = None
        words = [word for word in query.split() if len(word) >= 3]
        for suggestion in INDIA_DEMO_LOCATIONS:
            text = suggestion.searchable_text
            score = sum(word in text for word in words)
            if query in text:
                score += 10
            if best is None or score > best[0]:
                best = (score, suggestion)
        return best[1] if best and best[0] >= 2 else None


class HybridLocationService:
    """Use Mappls when configured and transparently retain demo fallback."""

    def __init__(
        self,
        live_service: MapplsLocationService | None,
        demo_service: LocationService,
    ) -> None:
        self._live = live_service
        self._demo = demo_service
        self.last_warning = ''

    @property
    def provider_label(self) -> str:
        if self._live is not None:
            return self._live.provider_label
        return self._demo.provider_label

    @property
    def is_live(self) -> bool:
        return self._live is not None

    async def suggest(
        self,
        query: str,
        *,
        proximity: tuple[float, float] | None = None,
        limit: int = 6,
    ) -> list[LocationSuggestion]:
        self.last_warning = ''
        live_results: list[LocationSuggestion] = []
        if self._live is not None:
            try:
                live_results = await self._live.suggest(
                    query,
                    proximity=proximity,
                    limit=limit,
                )
            except LocationServiceError as exc:
                self.last_warning = str(exc)

        demo_results = await self._demo.suggest(
            query,
            proximity=proximity,
            limit=limit,
        )
        combined: list[LocationSuggestion] = []
        seen: set[str] = set()
        for item in [*live_results, *demo_results]:
            identity = (
                item.formatted_address or item.display_name
            ).lower()
            if identity in seen:
                continue
            seen.add(identity)
            combined.append(item)
            if len(combined) >= max(1, limit):
                break
        return combined

    async def resolve(
        self,
        suggestion: LocationSuggestion,
    ) -> LocationSuggestion:
        self.last_warning = ''
        if suggestion.provider == 'mappls' and self._live is not None:
            try:
                resolved = await self._live.resolve(suggestion)
                if resolved.has_coordinates:
                    return resolved
                # A Mappls plan may return address details without coordinate
                # subtemplate access. Try matching the address to the offline
                # catalog before asking for manual latitude/longitude.
                demo_match = await self._demo.geocode(
                    resolved.formatted_address
                )
                if demo_match is not None:
                    return replace(
                        resolved,
                        latitude=demo_match.latitude,
                        longitude=demo_match.longitude,
                    )
                return resolved
            except LocationServiceError as exc:
                self.last_warning = str(exc)
        return await self._demo.resolve(suggestion)

    async def geocode(self, address: str) -> LocationSuggestion | None:
        self.last_warning = ''
        if self._live is not None:
            try:
                result = await self._live.geocode(address)
                if result is not None and result.has_coordinates:
                    return result
                if result is not None:
                    demo_match = await self._demo.geocode(
                        result.formatted_address
                    )
                    if demo_match is not None:
                        return replace(
                            result,
                            latitude=demo_match.latitude,
                            longitude=demo_match.longitude,
                        )
                    return result
            except LocationServiceError as exc:
                self.last_warning = str(exc)
        return await self._demo.geocode(address)


def create_location_service(
    profile: dict[str, Any] | None = None,
) -> HybridLocationService:
    """Create a country-appropriate address service for the active brand.

    Mappls is intentionally used only for the India workspace. The Canadian
    MVP uses a deterministic offline catalog until a Canada-capable production
    provider (for example Google Places) is configured later.
    """

    country_code = str((profile or {}).get('country_code') or 'IN').upper()
    if country_code == 'CA':
        return HybridLocationService(None, DemoCanadianLocationService())

    key = (
        os.getenv('MAPPLS_REST_KEY')
        or os.getenv('MAPPLS_ACCESS_TOKEN')
        or os.getenv('MAPPLS_API_KEY')
        or ''
    ).strip()
    live = MapplsLocationService(key) if key else None
    return HybridLocationService(live, DemoIndianLocationService())
