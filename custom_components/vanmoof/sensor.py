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
            VanMoofEstimatedRangeSensor(coordinator, config_entry, mac_address),
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
            model=self._config_entry.data.get("bike_model") or self._config_entry.data.get("vanmoof_type", "Unknown"),
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


class VanMoofEstimatedRangeSensor(VanMoofSensor):
    """VanMoof estimated range sensor."""

    FULL_BATTERY_RANGE_KM = {
        "S1": {
            "EU": {1: 90, 2: 75, 3: 60, 4: 48},
            "US": {1: 80, 2: 65, 3: 53, 4: 43},
        },
        "S2": {
            "EU": {1: 120, 2: 100, 3: 80, 4: 65},
            "US": {1: 100, 2: 90, 3: 78, 4: 65},
        },
        "S3": {
            "EU": {1: 145, 2: 120, 3: 95, 4: 75},
            "US": {1: 120, 2: 100, 3: 85, 4: 70},
        },
    }

    def __init__(self, coordinator: VanMoofDataUpdateCoordinator, config_entry, mac_address: str):
        super().__init__(coordinator, config_entry, mac_address, "VanMoof Bike Estimated Range", f"vanmoof_bike_{mac_address}_estimated_range")

    @property
    def state(self):
        battery_level = self._to_int(self.coordinator.data.get("battery_level"))
        power_level = self._to_int(self.coordinator.data.get("power_level"))
        if battery_level is None or power_level is None:
            return None

        model = self._range_model()
        region = self._range_region()
        power_level = min(max(power_level, 1), 4)
        full_range = self.FULL_BATTERY_RANGE_KM.get(model, {}).get(region, {}).get(power_level)
        if full_range is None:
            return None

        return round(full_range * battery_level / 100)

    @property
    def unit_of_measurement(self):
        return "km"

    def _range_model(self) -> str | None:
        bike_model = str(self._config_entry.data.get("bike_model", "")).upper()
        vanmoof_type = str(self._config_entry.data.get("vanmoof_type", "")).upper()
        bike_name = str(self._config_entry.data.get("bike_name", "")).upper()
        model_value = f"{bike_model} {vanmoof_type} {bike_name}"

        if (
            "S3" in model_value
            or "X3" in model_value
            or "SX3" in model_value
            or "ES-3" in model_value
            or "2020" in model_value
            or "ELECTRIFIED_2020" in model_value
        ):
            return "S3"
        if (
            "S2" in model_value
            or "X2" in model_value
            or "ES-2" in model_value
            or "2018" in model_value
            or "ELECTRIFIED_2018" in model_value
        ):
            return "S2"
        if (
            "S1" in model_value
            or "X1" in model_value
            or "ES-1" in model_value
            or "2016" in model_value
            or "2017" in model_value
            or "SMARTBIKE" in model_value
            or "ELECTRIFIED_2016" in model_value
            or "ELECTRIFIED_2017" in model_value
        ):
            return "S1"
        return "S1"

    def _range_region(self) -> str | None:
        region = self.coordinator.data.get("region")
        if region is None:
            return "EU"

        region = str(region).upper()
        if region in ("EU", "US"):
            return region
        return "EU"

    def _to_int(self, value):
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            return int.from_bytes(value, "little")
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


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
