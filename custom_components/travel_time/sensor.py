"""Sensor platform for Travel Time."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import TravelTimeResult
from .const import (
    ATTR_ARRIVAL_TIME,
    ATTR_DEPARTURE_TIME,
    ATTR_DESTINATION,
    ATTR_DESTINATION_NAME,
    ATTR_DISTANCE,
    ATTR_DURATION,
    ATTR_DURATION_IN_TRAFFIC,
    ATTR_ORIGIN,
    ATTR_ORIGIN_NAME,
    ATTR_ROUTE,
    CONF_ARRIVAL_TIME,
    CONF_DEPARTURE_TIME,
    CONF_DESTINATION,
    CONF_NAME,
    CONF_ORIGIN,
    CONF_UNITS,
    DEFAULT_NAME,
    DOMAIN,
    UNITS_IMPERIAL,
)
from .coordinator import TravelTimeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Travel Time sensors from a config entry."""
    coordinator: TravelTimeCoordinator = hass.data[DOMAIN][entry.entry_id]

    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    entities: list[SensorEntity] = [
        TravelTimeDurationSensor(coordinator, entry, name),
        TravelTimeDistanceSensor(coordinator, entry, name),
        TravelTimeDurationInTrafficSensor(coordinator, entry, name),
        TravelTimeOriginSensor(coordinator, entry, name),
        TravelTimeDestinationSensor(coordinator, entry, name),
        TravelTimeArrivalSensor(coordinator, entry, name),
        TravelTimeDepartureSensor(coordinator, entry, name),
    ]

    async_add_entities(entities)


class TravelTimeBaseSensor(CoordinatorEntity[TravelTimeCoordinator], SensorEntity):
    """Base class for Travel Time sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TravelTimeCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._name = name

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Travel Time: {self._name}",
            "manufacturer": "Travel Time",
        }


class TravelTimeDurationSensor(TravelTimeBaseSensor):
    """Sensor for travel duration."""

    _attr_name = "Duration"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_translation_key = "duration"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_duration"

    @property
    def native_value(self) -> float | None:
        """Return the duration in seconds."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.duration

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data
        attrs: dict[str, Any] = {
            ATTR_ORIGIN: data.origin,
            ATTR_DESTINATION: data.destination,
        }
        if data.duration_in_traffic is not None:
            attrs[ATTR_DURATION_IN_TRAFFIC] = data.duration_in_traffic
        if data.route:
            attrs[ATTR_ROUTE] = data.route
        return attrs


class TravelTimeDistanceSensor(TravelTimeBaseSensor):
    """Sensor for travel distance."""

    _attr_name = "Distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_translation_key = "distance"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_distance"

    @property
    def native_value(self) -> float | None:
        """Return the distance in meters."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.distance


class TravelTimeDurationInTrafficSensor(TravelTimeBaseSensor):
    """Sensor for travel duration with traffic."""

    _attr_name = "Duration in traffic"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_translation_key = "duration_in_traffic"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_duration_in_traffic"

    @property
    def native_value(self) -> float | None:
        """Return the duration in traffic, falling back to normal duration."""
        if self.coordinator.data is None:
            return None
        if self.coordinator.data.duration_in_traffic is not None:
            return self.coordinator.data.duration_in_traffic
        return self.coordinator.data.duration

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data
        return {
            ATTR_ORIGIN: data.origin,
            ATTR_DESTINATION: data.destination,
        }


class TravelTimeOriginSensor(TravelTimeBaseSensor):
    """Sensor for origin location name."""

    _attr_name = "Origin"
    _attr_translation_key = "origin"
    _attr_icon = "mdi:map-marker"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_origin"

    @property
    def native_value(self) -> str | None:
        """Return the origin name."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.origin


class TravelTimeDestinationSensor(TravelTimeBaseSensor):
    """Sensor for destination location name."""

    _attr_name = "Destination"
    _attr_translation_key = "destination"
    _attr_icon = "mdi:map-marker-check"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_destination"

    @property
    def native_value(self) -> str | None:
        """Return the destination name."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.destination


class TravelTimeArrivalSensor(TravelTimeBaseSensor):
    """Sensor for estimated arrival time."""

    _attr_name = "Arrival Time"
    _attr_translation_key = "arrival_time"
    _attr_icon = "mdi:clock-check-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_arrival"

    def _get_arrival_time(self) -> str | None:
        """Get arrival time from data or options."""
        val = self._entry.data.get(CONF_ARRIVAL_TIME)
        if not val:
            val = self._entry.options.get(CONF_ARRIVAL_TIME)
        return val if val else None

    def _get_target_time(self) -> datetime | None:
        """Parse the configured arrival time."""
        arrival_time_str = self._get_arrival_time()
        if not arrival_time_str:
            return None
        try:
            parts = str(arrival_time_str).split(":")
            target_hour = int(parts[0])
            target_minute = int(parts[1]) if len(parts) > 1 else 0
            now = datetime.now()
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target
        except (ValueError, IndexError, AttributeError):
            return None

    @property
    def native_value(self) -> str | None:
        """Return the arrival time as a readable string."""
        if self.coordinator.data is None:
            return None
        target = self._get_target_time()
        if target is None:
            return None
        return target.strftime("%H:%M")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return None
        duration = self.coordinator.data.duration
        if self.coordinator.data.duration_in_traffic is not None:
            duration = self.coordinator.data.duration_in_traffic
        target = self._get_target_time()
        departure = None
        if target:
            departure = (target - timedelta(seconds=duration)).strftime("%H:%M")
        return {
            ATTR_ARRIVAL_TIME: self._get_arrival_time(),
            ATTR_DURATION: duration,
            "required_departure": departure,
        }


class TravelTimeDepartureSensor(TravelTimeBaseSensor):
    """Sensor for required departure time."""

    _attr_name = "Departure Time"
    _attr_translation_key = "departure_time"
    _attr_icon = "mdi:clock-start"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_departure"

    def _get_arrival_time(self) -> str | None:
        """Get arrival time from data or options."""
        val = self._entry.data.get(CONF_ARRIVAL_TIME)
        if not val:
            val = self._entry.options.get(CONF_ARRIVAL_TIME)
        return val if val else None

    def _get_target_time(self) -> datetime | None:
        """Parse the configured arrival time."""
        arrival_time_str = self._get_arrival_time()
        if not arrival_time_str:
            return None
        try:
            parts = str(arrival_time_str).split(":")
            target_hour = int(parts[0])
            target_minute = int(parts[1]) if len(parts) > 1 else 0
            now = datetime.now()
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target
        except (ValueError, IndexError, AttributeError):
            return None

    @property
    def native_value(self) -> str | None:
        """Return the required departure time as a readable string."""
        if self.coordinator.data is None:
            return None
        target = self._get_target_time()
        if target is None:
            return None
        duration = self.coordinator.data.duration
        if self.coordinator.data.duration_in_traffic is not None:
            duration = self.coordinator.data.duration_in_traffic
        departure = target - timedelta(seconds=duration)
        return departure.strftime("%H:%M")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return None
        return {
            ATTR_DESTINATION: self.coordinator.data.destination,
            ATTR_DESTINATION_NAME: self._entry.data.get(CONF_DESTINATION),
            ATTR_ARRIVAL_TIME: self._get_arrival_time(),
        }
