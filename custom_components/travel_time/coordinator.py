"""DataUpdateCoordinator for Travel Time."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    BaseTravelTimeProvider,
    TravelTimeAuthError,
    TravelTimeConnectionError,
    TravelTimeError,
    TravelTimeResult,
    async_reverse_geocode,
)

_LOGGER = logging.getLogger(__name__)


class TravelTimeCoordinator(DataUpdateCoordinator[TravelTimeResult]):
    """Coordinator to fetch travel time data."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: BaseTravelTimeProvider,
        update_interval: timedelta,
        entry_id: str,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="travel_time",
            update_interval=update_interval,
        )
        self.provider = provider
        self._entry_id = entry_id
        self._origin_lat = origin_lat
        self._origin_lon = origin_lon
        self._dest_lat = dest_lat
        self._dest_lon = dest_lon
        self.origin_name: str | None = None
        self.destination_name: str | None = None
        self._geocode_done = False

    async def _async_geocode(self) -> None:
        """Resolve location names from coordinates (once)."""
        if self._geocode_done:
            return
        session = async_get_clientsession(self.hass)
        self.origin_name = await async_reverse_geocode(
            session, self._origin_lat, self._origin_lon
        )
        self.destination_name = await async_reverse_geocode(
            session, self._dest_lat, self._dest_lon
        )
        self._geocode_done = True
        if self.origin_name:
            _LOGGER.info("Origin geocoded: %s", self.origin_name)
        if self.destination_name:
            _LOGGER.info("Destination geocoded: %s", self.destination_name)

    async def _async_update_data(self) -> TravelTimeResult:
        """Fetch data from the provider."""
        # Geocode once on first update
        await self._async_geocode()

        try:
            result = await self.provider.async_get_travel_time()
            # Override origin/destination with geocoded names if available
            if self.origin_name:
                result = TravelTimeResult(
                    duration=result.duration,
                    duration_in_traffic=result.duration_in_traffic,
                    distance=result.distance,
                    origin=self.origin_name,
                    destination=result.destination,
                    route=result.route,
                )
            if self.destination_name:
                result = TravelTimeResult(
                    duration=result.duration,
                    duration_in_traffic=result.duration_in_traffic,
                    distance=result.distance,
                    origin=result.origin,
                    destination=self.destination_name,
                    route=result.route,
                )
            return result
        except TravelTimeAuthError as err:
            from homeassistant.exceptions import ConfigEntryAuthFailed

            raise ConfigEntryAuthFailed(str(err)) from err
        except TravelTimeConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except TravelTimeError as err:
            raise UpdateFailed(str(err)) from err
