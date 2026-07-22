"""DataUpdateCoordinator for Travel Time."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BaseTravelTimeProvider, TravelTimeAuthError, TravelTimeConnectionError, TravelTimeError, TravelTimeResult

_LOGGER = logging.getLogger(__name__)


class TravelTimeCoordinator(DataUpdateCoordinator[TravelTimeResult]):
    """Coordinator to fetch travel time data."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: BaseTravelTimeProvider,
        update_interval: timedelta,
        entry_id: str,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="travel_time",
            update_interval=update_interval,
        )
        self.provider = provider
        self._entry_id = entry_id

    async def _async_update_data(self) -> TravelTimeResult:
        """Fetch data from the provider."""
        try:
            return await self.provider.async_get_travel_time()
        except TravelTimeAuthError as err:
            from homeassistant.exceptions import ConfigEntryAuthFailed

            raise ConfigEntryAuthFailed(str(err)) from err
        except TravelTimeConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except TravelTimeError as err:
            raise UpdateFailed(str(err)) from err
