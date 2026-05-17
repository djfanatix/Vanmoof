from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .vanmoof_coordinator import VanMoofDataUpdateCoordinator

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the VanMoof device tracker platform."""
    coordinator: VanMoofDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    mac_address = config_entry.data["mac_address"]

    async_add_entities([VanMoofDeviceTracker(coordinator, config_entry, mac_address)])


class VanMoofDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Representation of a VanMoof bike device tracker."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._mac_address = mac_address
        self._name = "VanMoof Bike Tracker"
        self._unique_id = f"vanmoof_bike_{mac_address}_tracker"

    @property
    def name(self):
        """Return the name of the device tracker."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the device tracker."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the device tracker (home/not_home)."""
        if self.coordinator.data.get("available"):
            return STATE_HOME
        return STATE_NOT_HOME

    @property
    def source_type(self):
        """Return the source type for the device tracker."""
        return "bluetooth"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac_address)},
            name=self._config_entry.data.get("bike_name", f"VanMoof Bike ({self._mac_address})"),
            manufacturer="VanMoof",
            model=self._config_entry.data.get("vanmoof_type", "Unknown"),
            serial_number=self._config_entry.data.get("serial_number", self._mac_address),
        )

    @property
    def available(self):
        """Return whether the tracker is available."""
        return True