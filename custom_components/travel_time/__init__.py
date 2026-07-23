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
    CONF_AVOID_FERRIES,
    CONF_AVOID_SUBSCRIPTION_ROADS,
    CONF_AVOID_TOLL_ROADS,
    CONF_BASE_COORDS,
    CONF_BASE_URL,
    CONF_DEST_LAT,
    CONF_DEST_LON,
    CONF_MODE,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    CONF_PROVIDER,
    CONF_REGION,
    CONF_TIME_DELTA,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_TYPE,
    DEFAULT_MODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
    PROVIDER_WAZE,
)
from .coordinator import TravelTimeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Travel Time from a config entry."""
    session = async_get_clientsession(hass)

    # Build Waze-specific kwargs if provider is Waze
    waze_kwargs: dict = {}
    if entry.data[CONF_PROVIDER] == PROVIDER_WAZE:
        # Convert base_coords to tuple for pywaze (handles dict from config_flow)
        raw_coords = entry.data.get(CONF_BASE_COORDS)
        base_coords = None
        if isinstance(raw_coords, dict) and raw_coords:
            base_coords = (
                raw_coords.get("latitude", 0),
                raw_coords.get("longitude", 0),
            )
        elif isinstance(raw_coords, str) and "," in raw_coords:
            # Handle legacy string format
            try:
                parts = raw_coords.split(",")
                base_coords = (float(parts[0].strip()), float(parts[1].strip()))
            except (ValueError, IndexError):
                base_coords = None

        waze_kwargs = {
            "region": entry.data.get(CONF_REGION, "EU"),
            "avoid_toll_roads": entry.data.get(CONF_AVOID_TOLL_ROADS, False),
            "avoid_subscription_roads": entry.data.get(
                CONF_AVOID_SUBSCRIPTION_ROADS, False
            ),
            "avoid_ferries": entry.data.get(CONF_AVOID_FERRIES, False),
            "vehicle_type": entry.data.get(CONF_VEHICLE_TYPE, "car"),
            "time_delta": entry.data.get(CONF_TIME_DELTA, 0),
            "base_coords": base_coords,
        }

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
        **waze_kwargs,
    )

    interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = TravelTimeCoordinator(
        hass,
        provider,
        timedelta(seconds=interval),
        entry.entry_id,
        origin_lat=entry.data[CONF_ORIGIN_LAT],
        origin_lon=entry.data[CONF_ORIGIN_LON],
        dest_lat=entry.data[CONF_DEST_LAT],
        dest_lon=entry.data[CONF_DEST_LON],
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
