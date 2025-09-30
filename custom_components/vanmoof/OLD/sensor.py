from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .sx_client import SXClient
from .discover_bike import DiscoverBike
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the VanMoof battery level sensor."""
    username = config_entry.data["username"]
    password = config_entry.data["password"]
    encryption_key = config_entry.data["encryption_key"]
    mac_address = config_entry.data["mac_address"]
    polling_interval = config_entry.data["polling_interval"]

    # Create an instance of the sensor and add it
    bike_sensor = VanMoofBatterySensor(username, password, encryption_key, mac_address, polling_interval)
    async_add_entities([bike_sensor], update_before_add=True)

class VanMoofBatterySensor(SensorEntity):
    """Representation of a VanMoof Battery Level Sensor."""

    def __init__(self, username, password, encryption_key, mac_address, polling_interval):
        """Initialize the sensor."""
        self._username = username
        self._password = password
        self._encryption_key = encryption_key
        self._mac_address = mac_address
        self._polling_interval = polling_interval
        self._state = None
        self._name = "VanMoof Bike Battery Level"
        self._unique_id = f"vanmoof_bike_{mac_address}_battery"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the current battery level."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            # Discover and connect to the bike
            device, client_type, battery_level = await DiscoverBike.query(
                self._mac_address, self._polling_interval, self._encryption_key
            )
            if battery_level is not None:
                self._state = battery_level
                _LOGGER.debug(f"Updated battery level: {battery_level}%")
            else:
                _LOGGER.warning("Battery level could not be retrieved.")

        except Exception as e:
            _LOGGER.error(f"Error updating battery level sensor: {e}")
