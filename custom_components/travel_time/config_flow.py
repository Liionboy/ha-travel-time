"""Config flow for Travel Time integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
)

from .api import (
    TravelTimeAuthError,
    TravelTimeConnectionError,
    TravelTimeError,
    create_provider,
)
from .const import (
    CONF_API_KEY,
    CONF_ARRIVAL_TIME,
    CONF_BASE_URL,
    CONF_DEPARTURE_TIME,
    CONF_DESTINATION,
    CONF_DEST_LAT,
    CONF_DEST_LON,
    CONF_MODE,
    CONF_NAME,
    CONF_ORIGIN,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    CONF_PROVIDER,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODE,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MODE_BICYCLING,
    MODE_DRIVING,
    MODE_TRANSIT,
    MODE_WALKING,
    PROVIDER_GOOGLE,
    PROVIDER_ORS,
    PROVIDER_ORS_SELFHOST,
)

_LOGGER = logging.getLogger(__name__)

PROVIDERS = {
    PROVIDER_ORS: "OpenRouteService (free)",
    PROVIDER_GOOGLE: "Google Maps",
    PROVIDER_ORS_SELFHOST: "OpenRouteService (self-hosted)",
}

MODES_ORS = {
    MODE_DRIVING: "Driving",
    MODE_WALKING: "Walking",
    MODE_BICYCLING: "Cycling",
}

MODES_GOOGLE = {
    MODE_DRIVING: "Driving",
    MODE_WALKING: "Walking",
    MODE_BICYCLING: "Cycling",
    MODE_TRANSIT: "Transit",
}


def _parse_location(value: str) -> tuple[float, float] | None:
    """Parse a location string like '44.4268, 26.1025' into (lat, lon)."""
    value = value.strip()
    for sep in [",", ";", " "]:
        parts = value.split(sep)
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                continue
    return None


class TravelTimeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Travel Time."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Select provider and name."""
        if user_input is not None:
            self._data.update(user_input)
            provider = user_input[CONF_PROVIDER]

            if provider == PROVIDER_ORS:
                return await self.async_step_ors_api_key()
            if provider == PROVIDER_GOOGLE:
                return await self.async_step_google_api_key()
            if provider == PROVIDER_ORS_SELFHOST:
                return await self.async_step_ors_selfhost()

            return await self.async_step_origin()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_PROVIDER, default=PROVIDER_ORS): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in PROVIDERS.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_ors_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for OpenRouteService API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_API_KEY] = user_input[CONF_API_KEY]

            # Validate the API key with a test request
            session = async_get_clientsession(self.hass)
            provider = create_provider(
                PROVIDER_ORS,
                session,
                44.4268,
                26.1025,
                44.4397,
                26.0956,
                MODE_DRIVING,
                api_key=user_input[CONF_API_KEY],
            )
            try:
                await provider.async_get_travel_time()
            except TravelTimeAuthError:
                errors["base"] = "invalid_auth"
            except (TravelTimeConnectionError, TravelTimeError):
                errors["base"] = "cannot_connect"

            if not errors:
                return await self.async_step_origin()

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="ors_api_key", data_schema=schema, errors=errors
        )

    async def async_step_google_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for Google Maps API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_API_KEY] = user_input[CONF_API_KEY]

            # Validate the API key
            session = async_get_clientsession(self.hass)
            provider = create_provider(
                PROVIDER_GOOGLE,
                session,
                44.4268,
                26.1025,
                44.4397,
                26.0956,
                MODE_DRIVING,
                api_key=user_input[CONF_API_KEY],
            )
            try:
                await provider.async_get_travel_time()
            except TravelTimeAuthError:
                errors["base"] = "invalid_auth"
            except (TravelTimeConnectionError, TravelTimeError):
                errors["base"] = "cannot_connect"

            if not errors:
                return await self.async_step_origin()

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="google_api_key", data_schema=schema, errors=errors
        )

    async def async_step_ors_selfhost(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for self-hosted OpenRouteService."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_BASE_URL] = user_input[CONF_BASE_URL]
            self._data[CONF_API_KEY] = user_input.get(CONF_API_KEY, "")

            # Validate connection
            session = async_get_clientsession(self.hass)
            provider = create_provider(
                PROVIDER_ORS_SELFHOST,
                session,
                44.4268,
                26.1025,
                44.4397,
                26.0956,
                MODE_DRIVING,
                api_key=self._data[CONF_API_KEY],
                base_url=self._data[CONF_BASE_URL],
            )
            try:
                await provider.async_get_travel_time()
            except TravelTimeAuthError:
                errors["base"] = "invalid_auth"
            except (TravelTimeConnectionError, TravelTimeError):
                errors["base"] = "cannot_connect"

            if not errors:
                return await self.async_step_origin()

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
                vol.Optional(CONF_API_KEY, default=""): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="ors_selfhost", data_schema=schema, errors=errors
        )

    async def async_step_origin(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for origin location."""
        errors: dict[str, str] = {}

        if user_input is not None:
            origin = user_input[CONF_ORIGIN].strip()
            coords = _parse_location(origin)
            if coords:
                self._data[CONF_ORIGIN_LAT] = coords[0]
                self._data[CONF_ORIGIN_LON] = coords[1]
                self._data[CONF_ORIGIN] = origin
                return await self.async_step_destination()
            errors["base"] = "invalid_location"

        schema = vol.Schema(
            {
                vol.Required(CONF_ORIGIN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(
            step_id="origin",
            data_schema=schema,
            errors=errors,
            description_placeholders={"format": "latitude, longitude (e.g. 44.4268, 26.1025)"},
        )

    async def async_step_destination(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for destination location."""
        errors: dict[str, str] = {}

        if user_input is not None:
            destination = user_input[CONF_DESTINATION].strip()
            coords = _parse_location(destination)
            if coords:
                self._data[CONF_DEST_LAT] = coords[0]
                self._data[CONF_DEST_LON] = coords[1]
                self._data[CONF_DESTINATION] = destination
                return await self.async_step_options()
            errors["base"] = "invalid_location"

        schema = vol.Schema(
            {
                vol.Required(CONF_DESTINATION): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(
            step_id="destination",
            data_schema=schema,
            errors=errors,
            description_placeholders={"format": "latitude, longitude (e.g. 44.4397, 26.0956)"},
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step for travel mode and options."""
        if user_input is not None:
            self._data.update(user_input)

            # Validate with test request
            session = async_get_clientsession(self.hass)
            provider = create_provider(
                self._data[CONF_PROVIDER],
                session,
                self._data[CONF_ORIGIN_LAT],
                self._data[CONF_ORIGIN_LON],
                self._data[CONF_DEST_LAT],
                self._data[CONF_DEST_LON],
                user_input.get(CONF_MODE, DEFAULT_MODE),
                api_key=self._data.get(CONF_API_KEY, ""),
                base_url=self._data.get(CONF_BASE_URL, ""),
            )
            try:
                result = await provider.async_get_travel_time()
                _LOGGER.info(
                    "Travel time validation: %s → %s = %.0f seconds, %.0f meters",
                    result.origin,
                    result.destination,
                    result.duration,
                    result.distance,
                )
            except TravelTimeAuthError:
                return self.async_abort(reason="invalid_auth")
            except (TravelTimeConnectionError, TravelTimeError) as err:
                _LOGGER.error("Travel time validation failed: %s", err)
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title=self._data.get(CONF_NAME, DEFAULT_NAME),
                data=self._data,
            )

        provider = self._data.get(CONF_PROVIDER, PROVIDER_ORS)
        if provider in (PROVIDER_ORS, PROVIDER_ORS_SELFHOST):
            modes = MODES_ORS
        else:
            modes = MODES_GOOGLE

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=DEFAULT_MODE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in modes.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_ARRIVAL_TIME): TimeSelector(),
                vol.Optional(CONF_DEPARTURE_TIME): TimeSelector(),
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(int, vol.Range(min=60, max=3600)),
            }
        )
        return self.async_show_form(step_id="options", data_schema=schema)

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reauth flow (API key update)."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:
            return self.async_abort(reason="reauth_unsuccessful")

        if user_input is not None:
            new_data = {**entry.data, CONF_API_KEY: user_input[CONF_API_KEY]}
            self.hass.config_entries.async_update_entry(entry, data=new_data)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(step_id="reauth", data_schema=schema)
