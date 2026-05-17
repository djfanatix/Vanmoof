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
            VanMoofMotorBatteryLevelSensor(coordinator, config_entry, mac_address),
            VanMoofModuleBatteryLevelSensor(coordinator, config_entry, mac_address),
            VanMoofLockStateSensor(coordinator, config_entry, mac_address),
            VanMoofDistanceSensor(coordinator, config_entry, mac_address),
            VanMoofPowerLevelSensor(coordinator, config_entry, mac_address),
            VanMoofSpeedSensor(coordinator, config_entry, mac_address),
            VanMoofLightModeSensor(coordinator, config_entry, mac_address),
            VanMoofModuleStateSensor(coordinator, config_entry, mac_address),
            VanMoofErrorCodeSensor(coordinator, config_entry, mac_address),
            VanMoofMotorBatteryStateSensor(coordinator, config_entry, mac_address),
            VanMoofModuleBatteryStateSensor(coordinator, config_entry, mac_address),
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
        return self.coordinator.last_update_success and bool(self.coordinator.data.get("available"))

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


class VanMoofMotorBatteryLevelSensor(VanMoofSensor):
    """VanMoof motor battery level sensor (S3/X3)."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Motor Battery Level", f"vanmoof_bike_{mac_address}_motor_battery_level")

    @property
    def state(self):
        return self.coordinator.data.get("motor_battery_level")

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def unit_of_measurement(self):
        return "%"


class VanMoofModuleBatteryLevelSensor(VanMoofSensor):
    """VanMoof module battery level sensor (S3/X3)."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Module Battery Level", f"vanmoof_bike_{mac_address}_module_battery_level")

    @property
    def state(self):
        return self.coordinator.data.get("module_battery_level")

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


class VanMoofSpeedSensor(VanMoofSensor):
    """VanMoof speed sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Speed", f"vanmoof_bike_{mac_address}_speed")

    @property
    def state(self):
        return self.coordinator.data.get("speed")

    @property
    def unit_of_measurement(self):
        return "km/h"


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


class VanMoofMotorBatteryStateSensor(VanMoofSensor):
    """VanMoof motor battery state sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Motor Battery State", f"vanmoof_bike_{mac_address}_motor_battery_state")

    @property
    def state(self):
        return self.coordinator.data.get("motor_battery_state")


class VanMoofModuleBatteryStateSensor(VanMoofSensor):
    """VanMoof module battery state sensor."""

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Module Battery State", f"vanmoof_bike_{mac_address}_module_battery_state")

    @property
    def state(self):
        return self.coordinator.data.get("module_battery_state")
