import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .vanmoof_coordinator import VanMoofDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the VanMoof bike sensors."""
    coordinator: VanMoofDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    mac_address = config_entry.data["mac_address"]

    async_add_entities(
        [
            VanMoofBatterySensor(coordinator, config_entry, mac_address),
            VanMoofModuleLevelSensor(coordinator, config_entry, mac_address),
            VanMoofChargingSensor(coordinator, config_entry, mac_address),
            VanMoofLockStateSensor(coordinator, config_entry, mac_address),
            VanMoofDistanceSensor(coordinator, config_entry, mac_address),
            VanMoofPowerLevelSensor(coordinator, config_entry, mac_address),
            VanMoofRegionSensor(coordinator, config_entry, mac_address),
            VanMoofLightModeSensor(coordinator, config_entry, mac_address),
            VanMoofModuleStateSensor(coordinator, config_entry, mac_address),
            VanMoofErrorCodeSensor(coordinator, config_entry, mac_address),
        ]
    )


class VanMoofSensor(CoordinatorEntity, SensorEntity):
    """Base VanMoof sensor entity."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str, name: str, unique_id: str):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._name = name
        self._unique_id = unique_id
        self._mac_address = mac_address

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def available(self):
        return self.coordinator.data is not None

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


class VanMoofBatterySensor(VanMoofSensor):
    """VanMoof battery level sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Battery Level", f"vanmoof_bike_{mac_address}_battery")

    @property
    def state(self):
        return self.coordinator.data.get("battery_level")

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def unit_of_measurement(self):
        return "%"


class VanMoofModuleLevelSensor(VanMoofSensor):
    """VanMoof module level sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Module Level", f"vanmoof_bike_{mac_address}_module_level")

    @property
    def state(self):
        return self.coordinator.data.get("module_level")

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def unit_of_measurement(self):
        return "%"


class VanMoofLockStateSensor(VanMoofSensor):

    """VanMoof lock state sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Lock State", f"vanmoof_bike_{mac_address}_lock_state")

    @property
    def state(self):
        return self.coordinator.data.get("lock_state")


class VanMoofDistanceSensor(VanMoofSensor):
    """VanMoof distance travelled sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Distance", f"vanmoof_bike_{mac_address}_distance")

    @property
    def state(self):
        return self.coordinator.data.get("distance_travelled")

    @property
    def unit_of_measurement(self):
        return "km"


class VanMoofPowerLevelSensor(VanMoofSensor):
    """VanMoof power level sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Power Level", f"vanmoof_bike_{mac_address}_power_level")

    @property
    def state(self):
        return self.coordinator.data.get("power_level")


class VanMoofRegionSensor(VanMoofSensor):
    """VanMoof bike region sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Region", f"vanmoof_bike_{mac_address}_region")

    @property
    def state(self):
        return self.coordinator.data.get("region")


class VanMoofLightModeSensor(VanMoofSensor):
    """VanMoof light mode sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Light Mode", f"vanmoof_bike_{mac_address}_light_mode")

    @property
    def state(self):
        return self.coordinator.data.get("light_mode")


class VanMoofModuleStateSensor(VanMoofSensor):
    """VanMoof module state sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Module State", f"vanmoof_bike_{mac_address}_module_state")

    @property
    def state(self):
        return self.coordinator.data.get("module_state")


class VanMoofChargingSensor(VanMoofSensor):
    """VanMoof charging state sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Charging", f"vanmoof_bike_{mac_address}_charging")

    @property
    def state(self):
        return self.coordinator.data.get("charging")


class VanMoofErrorCodeSensor(VanMoofSensor):
    """VanMoof error code sensor."""

    ERROR_MESSAGES = {
        0: "No Error",
        1: "Motor Stalled",
        2: "Over Voltage",
        3: "Under Voltage",
        5: "Motor Fast",
        6: "Over Current",
        7: "Torque Abnormal",
        8: "Torque Initial Abnormal",
        9: "Over Temperature",
        16: "Hall Arrangement Mismatch",
        25: "I2C Bus Error",
        26: "GSM UART Timeout",
        27: "Controller UART Timeout",
        28: "GSM Registration Failure",
        29: "No Battery Output",
    }

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Error Code", f"vanmoof_bike_{mac_address}_error_code")

    @property
    def state(self):
        errors = self.coordinator.data.get("errors")
        if isinstance(errors, int):
            message = self.ERROR_MESSAGES.get(errors, "Unknown Error")
            return f"{message} ({errors})"
        return errors or "Unknown Error"

