import logging
import asyncio
from bleak import BleakClient, BleakScanner
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .sx_client import SXClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the VanMoof bike sensors for battery and module levels."""
    username = config_entry.data["username"]
    password = config_entry.data["password"]
    encryption_key = config_entry.data["encryption_key"]
    mac_address = config_entry.data["mac_address"]
    polling_interval = config_entry.data["polling_interval"]

    # Create instances of both battery and module level sensors
    bike_battery_sensor = VanMoofBatterySensor(username, password, encryption_key, mac_address, polling_interval)
    bike_module_sensor = VanMoofModuleLevelSensor(username, password, encryption_key, mac_address, polling_interval)
    
    # Add the sensors to Home Assistant
    async_add_entities([bike_battery_sensor, bike_module_sensor], update_before_add=True)

class VanMoofBatterySensor(SensorEntity):
    """Representation of the VanMoof Bike Battery Level Sensor."""

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
        """Fetch new state data for the battery sensor asynchronously."""
        try:
            # Fetch device information and parameters
            _, _, parameters = await query(self._mac_address, self._polling_interval, self._encryption_key)
            if parameters:
                # Extract battery level from the parameters
                battery_level = parameters.get("battery_level", None)
                if battery_level is not None:
                    self._state = battery_level
                    _LOGGER.info(f"Updated bike battery level: {battery_level}%")
                else:
                    _LOGGER.error("Battery level not available.")
            else:
                _LOGGER.error("Failed to fetch battery level.")
        except Exception as e:
            _LOGGER.error(f"Error updating bike battery level: {e}")

class VanMoofModuleLevelSensor(SensorEntity):
    """Representation of the VanMoof Bike Module Level Sensor."""

    def __init__(self, username, password, encryption_key, mac_address, polling_interval):
        """Initialize the sensor."""
        self._username = username
        self._password = password
        self._encryption_key = encryption_key
        self._mac_address = mac_address
        self._polling_interval = polling_interval
        self._state = None
        self._name = "VanMoof Bike Module Level"
        self._unique_id = f"vanmoof_bike_{mac_address}_module_level"

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
        """Return the current module level."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"

    async def async_update(self):
        """Fetch new state data for the module level sensor asynchronously."""
        try:
            # Fetch device information and parameters
            _, _, parameters = await query(self._mac_address, self._polling_interval, self._encryption_key)
            if parameters:
                # Extract module level from the parameters
                module_level = parameters.get("module_level", None)
                if module_level is not None:
                    self._state = module_level
                    _LOGGER.info(f"Updated bike module level: {module_level}%")
                else:
                    _LOGGER.error("Module level not available.")
            else:
                _LOGGER.error("Failed to fetch module level.")
        except Exception as e:
            _LOGGER.error(f"Error updating bike module level: {e}")

async def query(mac_address: str, polling_interval: int, encryption_key: str):
    """Query the bike's battery and module level using Bleak."""
    try:
        while True:
            # Discover nearby Bluetooth devices
            devices = await BleakScanner.discover()
            _LOGGER.debug(f"Discovered {len(devices)} devices.")
            
            if not devices:
                _LOGGER.warning("No devices found during discovery.")
                await asyncio.sleep(polling_interval)
                continue  # Retry if no devices are found

            # Loop through devices and find the one with the matching MAC address
            for device in devices:
                _LOGGER.debug(f"Discovered device: {device.name} ({device.address})")

                if device.address.lower() == mac_address.lower():
                    # Found the device, connect to it
                    async with BleakClient(device) as client:
                        if client.is_connected:
                            # Initialize SXClient for communication
                            sx_client = SXClient(client, encryption_key)
                            # Fetch parameters, which include the battery and module levels
                            parameters = await sx_client.get_parameters()
                            return device, sx_client, parameters  # Return the device, client, and parameters (as a dictionary)

            _LOGGER.warning(f"No bike found with MAC address: {mac_address}")
            await asyncio.sleep(polling_interval)

    except Exception as e:
        _LOGGER.error(f"Error during bike discovery: {e}")
        return None, None, None
