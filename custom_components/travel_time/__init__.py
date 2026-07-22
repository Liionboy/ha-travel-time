"""The Travel Time integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import create_provider
from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_DEST_LAT,
    CONF_DEST_LON,
    CONF_MODE,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    CONF_PROVIDER,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import TravelTimeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Travel Time from a config entry."""
    session = async_get_clientsession(hass)

    provider = create_provider(
        provider=entry.data[CONF_PROVIDER],
        session=session,
        origin_lat=entry.data[CONF_ORIGIN_LAT],
        origin_lon=entry.data[CONF_ORIGIN_LON],
        dest_lat=entry.data[CONF_DEST_LAT],
        dest_lon=entry.data[CONF_DEST_LON],
        mode=entry.data.get(CONF_MODE, DEFAULT_MODE),
        api_key=entry.data.get(CONF_API_KEY, ""),
        base_url=entry.data.get(CONF_BASE_URL, ""),
    )

    interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = TravelTimeCoordinator(
        hass,
        provider,
        timedelta(seconds=interval),
        entry.entry_id,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed:
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Travel Time config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    return True
