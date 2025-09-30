from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import bleak


class VanMoofBatterySensor(SensorEntity):
    """Representation of the VanMoof Battery sensor."""
    def __init__(self, bike_data):
        self._bike_data = bike_data

    @property
    def name(self):
        return "VanMoof Battery"

    @property
    def state(self):
        return self._bike_data.get("battery_level", "Unknown")

    @property
    def device_class(self):
        return "battery"

class VanMoofDistanceSensor(SensorEntity):
    """Representation of the VanMoof Distance sensor."""
    def __init__(self, bike_data):
        self._bike_data = bike_data

    @property
    def name(self):
        return "VanMoof Distance"

    @property
    def state(self):
        return self._bike_data.get("distance_travelled", "Unknown")

class VanMoofLockStateSensor(SensorEntity):
    """Representation of the VanMoof Lock State sensor."""
    def __init__(self, bike_data):
        self._bike_data = bike_data

    @property
    def name(self):
        return "VanMoof Lock State"

    @property
    def state(self):
        return self._bike_data.get("lock_state", "Unknown")

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the VanMoof sensors."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Retrieve the encryption key
    key, user_key_id = retrieve_encryption_key.query()

    # Discover the nearby bike
    device = await discover_bike.query()

    # Connect to the bike using Bleak
    async with bleak.BleakClient(device) as bleak_client:
        client = SX3Client(bleak_client, key, user_key_id)

        # Authenticate with the bike
        await client.authenticate()

        # Gather data from the bike
        bike_data = {
            "battery_level": await client.get_battery_level(),
            "distance_travelled": await client.get_distance_travelled(),
            "lock_state": await client.get_lock_state(),
        }

        # Add sensors to Home Assistant
        async_add_entities([
            VanMoofBatterySensor(bike_data),
            VanMoofDistanceSensor(bike_data),
            VanMoofLockStateSensor(bike_data),
        ])
