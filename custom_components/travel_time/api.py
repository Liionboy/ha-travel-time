"""API clients for Travel Time providers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

from .const import (
    GOOGLE_DIRECTIONS_URL,
    MODE_BICYCLING,
    MODE_DRIVING,
    MODE_TRANSIT,
    MODE_WALKING,
    ORS_BASE_URL,
    ORS_DIRECTIONS_PATH,
    OSRM_BASE_URL,
    PROFILE_CYCLING_REGULAR,
    PROFILE_DRIVING_CAR,
    PROFILE_FOOT_WALKING,
    PROFILE_WHEELCHAIR,
)

_LOGGER = logging.getLogger(__name__)


class TravelTimeError(Exception):
    """Base exception for travel time API errors."""


class TravelTimeAuthError(TravelTimeError):
    """Authentication error."""


class TravelTimeConnectionError(TravelTimeError):
    """Connection error."""


@dataclass(slots=True)
class AlternativeRoute:
    """An alternative route with duration and distance."""

    duration: float  # seconds
    distance: float  # meters
    name: str | None
    street_names: list[str]


@dataclass(slots=True)
class TravelTimeResult:
    """Result from a travel time API call."""

    duration: float  # seconds
    duration_in_traffic: float | None  # seconds
    distance: float  # meters
    origin: str
    destination: str
    route: str | None
    street_names: list[str] | None = None
    alternative_routes: list[AlternativeRoute] | None = None


# Map integration modes to ORS profiles
MODE_TO_ORS_PROFILE = {
    MODE_DRIVING: PROFILE_DRIVING_CAR,
    MODE_WALKING: PROFILE_FOOT_WALKING,
    MODE_BICYCLING: PROFILE_CYCLING_REGULAR,
}

# Map integration modes to Google modes
MODE_TO_GOOGLE_MODE = {
    MODE_DRIVING: MODE_DRIVING,
    MODE_WALKING: MODE_WALKING,
    MODE_BICYCLING: MODE_BICYCLING,
    MODE_TRANSIT: MODE_TRANSIT,
}


def _format_coords(lat: float, lon: float) -> str:
    """Format coordinates as a human-readable string."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.5f}°{lat_dir}, {abs(lon):.5f}°{lon_dir}"


NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


async def async_reverse_geocode(
    session: aiohttp.ClientSession, lat: float, lon: float
) -> str | None:
    """Reverse geocode coordinates to a location name using Nominatim."""
    params = {
        "lat": str(lat),
        "lon": str(lon),
        "format": "json",
        "zoom": "14",
        "accept-language": "ro",
    }
    headers = {"User-Agent": "ha-travel-time/1.0"}
    try:
        resp = await session.get(NOMINATIM_URL, params=params, headers=headers)
        if resp.status == 200:
            data = await resp.json()
            display = data.get("display_name", "")
            if display:
                # Simplify: take first 3 parts (city, county, country)
                parts = [p.strip() for p in display.split(",")]
                if len(parts) >= 3:
                    return ", ".join(parts[:3])
                return display
    except Exception:
        pass
    return None


class BaseTravelTimeProvider(ABC):
    """Base class for travel time providers."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str,
    ) -> None:
        self._session = session
        self._origin_lat = origin_lat
        self._origin_lon = origin_lon
        self._dest_lat = dest_lat
        self._dest_lon = dest_lon
        self._mode = mode

    @abstractmethod
    async def async_get_travel_time(self) -> TravelTimeResult:
        """Get travel time between origin and destination."""


class OpenRouteServiceProvider(BaseTravelTimeProvider):
    """OpenRouteService API provider."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str,
        api_key: str,
        base_url: str = ORS_BASE_URL,
    ) -> None:
        super().__init__(session, origin_lat, origin_lon, dest_lat, dest_lon, mode)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _get_profile(self) -> str:
        """Get ORS profile from integration mode."""
        return MODE_TO_ORS_PROFILE.get(self._mode, PROFILE_DRIVING_CAR)

    async def async_get_travel_time(self) -> TravelTimeResult:
        """Get travel time from OpenRouteService."""
        profile = self._get_profile()
        url = f"{self._base_url}{ORS_DIRECTIONS_PATH}/{profile}"

        # ORS expects [lon, lat] format
        body = {
            "coordinates": [
                [self._origin_lon, self._origin_lat],
                [self._dest_lon, self._dest_lat],
            ],
            "instructions": False,
        }

        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = await self._session.post(url, json=body, headers=headers)
        except aiohttp.ClientError as err:
            raise TravelTimeConnectionError(f"Connection error: {err}") from err

        if resp.status == 401 or resp.status == 403:
            raise TravelTimeAuthError(f"Authentication failed: HTTP {resp.status}")

        if resp.status >= 400:
            text = await resp.text()
            raise TravelTimeError(f"ORS API error {resp.status}: {text}")

        data = await resp.json()

        routes = data.get("routes", [])
        if not routes:
            raise TravelTimeError("No routes found")

        route = routes[0]
        summary = route.get("summary", {})

        duration = summary.get("duration", 0)
        distance = summary.get("distance", 0)

        # Extract route name/summary
        segments = route.get("segments", [])
        route_name = None
        if segments:
            steps = segments[0].get("steps", [])
            if steps:
                route_name = " → ".join(
                    s.get("name", "") for s in steps[:3] if s.get("name")
                ) or None

        origin_str = _format_coords(self._origin_lat, self._origin_lon)
        dest_str = _format_coords(self._dest_lat, self._dest_lon)

        return TravelTimeResult(
            duration=duration,
            duration_in_traffic=None,  # ORS doesn't provide traffic data in free tier
            distance=distance,
            origin=origin_str,
            destination=dest_str,
            route=route_name,
        )


class GoogleMapsProvider(BaseTravelTimeProvider):
    """Google Maps Directions API provider."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str,
        api_key: str,
    ) -> None:
        super().__init__(session, origin_lat, origin_lon, dest_lat, dest_lon, mode)
        self._api_key = api_key

    def _get_google_mode(self) -> str:
        """Get Google Maps mode from integration mode."""
        return MODE_TO_GOOGLE_MODE.get(self._mode, MODE_DRIVING)

    async def async_get_travel_time(self) -> TravelTimeResult:
        """Get travel time from Google Maps Directions API."""
        google_mode = self._get_google_mode()

        origin = f"{self._origin_lat},{self._origin_lon}"
        destination = f"{self._dest_lat},{self._dest_lon}"

        params: dict[str, str] = {
            "origin": origin,
            "destination": destination,
            "mode": google_mode,
            "key": self._api_key,
        }

        try:
            resp = await self._session.get(GOOGLE_DIRECTIONS_URL, params=params)
        except aiohttp.ClientError as err:
            raise TravelTimeConnectionError(f"Connection error: {err}") from err

        if resp.status >= 400:
            text = await resp.text()
            raise TravelTimeError(f"Google API error {resp.status}: {text}")

        data = await resp.json()

        status = data.get("status", "")
        if status == "REQUEST_DENIED":
            raise TravelTimeAuthError(f"Google API denied: {data.get('error_message', 'Invalid API key')}")
        if status != "OK":
            raise TravelTimeError(f"Google API status: {status}")

        routes = data.get("routes", [])
        if not routes:
            raise TravelTimeError("No routes found")

        leg = routes[0]["legs"][0]

        duration = leg.get("duration", {}).get("value", 0)
        duration_in_traffic = leg.get("duration_in_traffic", {}).get("value")
        distance = leg.get("distance", {}).get("value", 0)

        origin_name = leg.get("start_address", _format_coords(self._origin_lat, self._origin_lon))
        dest_name = leg.get("end_address", _format_coords(self._dest_lat, self._dest_lon))

        # Route summary
        route_name = routes[0].get("summary", None)

        return TravelTimeResult(
            duration=duration,
            duration_in_traffic=duration_in_traffic,
            distance=distance,
            origin=origin_name,
            destination=dest_name,
            route=route_name,
        )


class WazeProvider(BaseTravelTimeProvider):
    """Waze routing provider with real-time traffic data."""

    # Map vehicle type strings to pywaze values
    _VEHICLE_TYPE_MAP = {
        "car": None,
        "taxi": "TAXI",
        "motorcycle": "MOTORCYCLE",
    }

    def __init__(
        self,
        session: aiohttp.ClientSession,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str,
        region: str = "EU",
        avoid_toll_roads: bool = False,
        avoid_subscription_roads: bool = False,
        avoid_ferries: bool = False,
        realtime: bool = True,
        vehicle_type: str = "car",
        alternatives: int = 3,
        time_delta: int = 0,
        base_coords: tuple[float, float] | None = None,
    ) -> None:
        super().__init__(session, origin_lat, origin_lon, dest_lat, dest_lon, mode)
        self._region = region
        self._avoid_toll_roads = avoid_toll_roads
        self._avoid_subscription_roads = avoid_subscription_roads
        self._avoid_ferries = avoid_ferries
        self._realtime = realtime
        self._vehicle_type = vehicle_type
        self._alternatives = alternatives
        self._time_delta = time_delta
        self._base_coords = base_coords

    async def async_get_travel_time(self) -> TravelTimeResult:
        """Get travel time from Waze with alternative routes."""
        from pywaze.route_calculator import WazeRouteCalculator, WRCError

        origin = f"{self._origin_lat},{self._origin_lon}"
        destination = f"{self._dest_lat},{self._dest_lon}"

        pywaze_vehicle = self._VEHICLE_TYPE_MAP.get(self._vehicle_type)

        try:
            import httpx
            async with httpx.AsyncClient() as http_client:
                calculator = WazeRouteCalculator(
                    client=http_client,
                    region=self._region,
                )

                routes = await calculator.calc_routes(
                    origin,
                    destination,
                    vehicle_type=pywaze_vehicle,
                    avoid_toll_roads=self._avoid_toll_roads,
                    avoid_subscription_roads=self._avoid_subscription_roads,
                    avoid_ferries=self._avoid_ferries,
                    real_time=self._realtime,
                    alternatives=self._alternatives,
                    time_delta=self._time_delta,
                    base_coords=self._base_coords,
                )

        except WRCError as err:
            raise TravelTimeError(f"Waze error: {err}") from err
        except Exception as err:
            raise TravelTimeConnectionError(f"Waze connection error: {err}") from err

        if not routes:
            raise TravelTimeError("No Waze routes found")

        # Get the best route (first one)
        best = routes[0]
        duration = best.duration * 60  # pywaze returns minutes, convert to seconds
        distance = best.distance * 1000  # pywaze returns km, convert to meters

        origin_str = _format_coords(self._origin_lat, self._origin_lon)
        dest_str = _format_coords(self._dest_lat, self._dest_lon)

        # Build alternative routes list (skip the first/best route)
        alt_routes: list[AlternativeRoute] = []
        for alt in routes[1:]:
            alt_routes.append(
                AlternativeRoute(
                    duration=alt.duration * 60,
                    distance=alt.distance * 1000,
                    name=alt.name,
                    street_names=list(alt.street_names) if alt.street_names else [],
                )
            )

        return TravelTimeResult(
            duration=duration,
            duration_in_traffic=duration if self._realtime else None,
            distance=distance,
            origin=origin_str,
            destination=dest_str,
            route=best.name,
            street_names=list(best.street_names) if best.street_names else [],
            alternative_routes=alt_routes if alt_routes else None,
        )


class OSRMProvider(BaseTravelTimeProvider):
    """OSRM (Open Source Routing Machine) provider - free, no API key."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str,
        base_url: str = OSRM_BASE_URL,
    ) -> None:
        super().__init__(session, origin_lat, origin_lon, dest_lat, dest_lon, mode)
        self._base_url = base_url.rstrip("/")

    def _get_osrm_profile(self) -> str:
        """Get OSRM profile from integration mode."""
        profiles = {
            MODE_DRIVING: "car",
            MODE_WALKING: "foot",
            MODE_BICYCLING: "bike",
        }
        return profiles.get(self._mode, "car")

    async def async_get_travel_time(self) -> TravelTimeResult:
        """Get travel time from OSRM."""
        profile = self._get_osrm_profile()
        # OSRM expects lon,lat format
        coords = f"{self._origin_lon},{self._origin_lat};{self._dest_lon},{self._dest_lat}"
        url = f"{self._base_url}/route/v1/{profile}/{coords}"

        params = {
            "overview": "false",
            "alternatives": "false",
            "steps": "false",
        }

        try:
            resp = await self._session.get(url, params=params)
        except aiohttp.ClientError as err:
            raise TravelTimeConnectionError(f"Connection error: {err}") from err

        if resp.status >= 400:
            text = await resp.text()
            raise TravelTimeError(f"OSRM API error {resp.status}: {text}")

        data = await resp.json()

        if data.get("code") != "Ok":
            raise TravelTimeError(f"OSRM error: {data.get('code', 'unknown')}")

        routes = data.get("routes", [])
        if not routes:
            raise TravelTimeError("No routes found")

        route = routes[0]
        duration = route.get("duration", 0)
        distance = route.get("distance", 0)

        origin_str = _format_coords(self._origin_lat, self._origin_lon)
        dest_str = _format_coords(self._dest_lat, self._dest_lon)

        return TravelTimeResult(
            duration=duration,
            duration_in_traffic=None,
            distance=distance,
            origin=origin_str,
            destination=dest_str,
            route=None,
        )


def create_provider(
    provider: str,
    session: aiohttp.ClientSession,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    mode: str,
    api_key: str = "",
    base_url: str = "",
    # Waze-specific kwargs
    region: str = "EU",
    avoid_toll_roads: bool = False,
    avoid_subscription_roads: bool = False,
    avoid_ferries: bool = False,
    vehicle_type: str = "car",
    alternatives: int = 3,
    time_delta: int = 0,
    base_coords: tuple[float, float] | None = None,
) -> BaseTravelTimeProvider:
    """Create a travel time provider instance."""
    if provider == "openrouteservice" or provider == "openrouteservice_selfhost":
        url = base_url if base_url else ORS_BASE_URL
        return OpenRouteServiceProvider(
            session, origin_lat, origin_lon, dest_lat, dest_lon, mode, api_key, url
        )
    if provider == "google":
        return GoogleMapsProvider(
            session, origin_lat, origin_lon, dest_lat, dest_lon, mode, api_key
        )
    if provider == "osrm":
        url = base_url if base_url else OSRM_BASE_URL
        return OSRMProvider(
            session, origin_lat, origin_lon, dest_lat, dest_lon, mode, url
        )
    if provider == "waze":
        return WazeProvider(
            session,
            origin_lat,
            origin_lon,
            dest_lat,
            dest_lon,
            mode,
            region=region,
            avoid_toll_roads=avoid_toll_roads,
            avoid_subscription_roads=avoid_subscription_roads,
            avoid_ferries=avoid_ferries,
            vehicle_type=vehicle_type,
            alternatives=alternatives,
            time_delta=time_delta,
            base_coords=base_coords,
        )
    raise TravelTimeError(f"Unknown provider: {provider}")
