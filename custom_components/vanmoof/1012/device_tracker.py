from homeassistant.components.device_tracker.config_entry import (
    TrackerEntity,
)
from bleak import BleakClient
import logging

_LOGGER = logging.getLogger(__name__)

class VanMoofDeviceTracker(TrackerEntity):
    """Representation of a VanMoof bike device tracker."""

    def __init__(self, mac_address: str, encryption_key: str):
        """Initialize the device tracker."""
        self._mac_address = mac_address
        self._encryption_key = encryption_key
        self._state = None
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
        """Return the state of the device tracker (home/away)."""
        return self._state

    async def async_update(self):
        """Check if the bike is nearby."""
        try:
            async with BleakClient(self._mac_address) as client:
                # Try to connect and check if successful
                if client.is_connected:
                    self._state = "home"  # Bike is nearby
                    _LOGGER.info(f"VanMoof bike {self._mac_address} is nearby.")
                else:
                    self._state = "away"  # Bike is not nearby
                    _LOGGER.info(f"VanMoof bike {self._mac_address} is not nearby.")
        except Exception as e:
            _LOGGER.error(f"Error updating device tracker: {e}")
            self._state = "away"  # If there's an error, consider the bike away
