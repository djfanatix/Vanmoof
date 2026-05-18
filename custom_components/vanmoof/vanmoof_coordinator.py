"""Coordinator for shared VanMoof bike data updates."""
from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakScanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .bleak_client_utils import connect_bleak_client
from .sx_client import SXClient
from .sx3_client import SX3Client

_LOGGER = logging.getLogger(__name__)


def _is_sx3_bike(vanmoof_type: str | None) -> bool:
    if not vanmoof_type:
        return False
    value = vanmoof_type.upper()
    return any(token in value for token in ("SX3", "S3", "X3"))


def _to_int(value):
    if isinstance(value, (bytes, bytearray)):
        return int.from_bytes(value, "little")
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return int(value)


class VanMoofDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage VanMoof bike data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._mac_address = entry.data["mac_address"]
        self._encryption_key = entry.data["encryption_key"]
        self._user_key_id = entry.data.get("user_key_id")
        self._vanmoof_type = entry.data.get("vanmoof_type")
        self._entry = entry

        # Get polling interval from options if available, otherwise from data
        polling_interval_seconds = entry.options.get(
            "polling_interval", 
            entry.data.get("polling_interval", 300)
        )
        update_interval = timedelta(seconds=polling_interval_seconds)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from the bike via BLE."""
        try:
            devices = await BleakScanner.discover(timeout=8.0)
            _LOGGER.debug("Discovered %s BLE devices while searching for VanMoof bike.", len(devices))

            if not devices:
                raise UpdateFailed("No Bluetooth devices discovered.")

            bike_device = next(
                (device for device in devices if device.address.lower() == self._mac_address.lower()),
                None,
            )

            if not bike_device:
                raise UpdateFailed(f"VanMoof bike with MAC {self._mac_address} not found.")

            client = await connect_bleak_client(bike_device)
            try:
                if not client.is_connected:
                    raise UpdateFailed(f"Unable to connect to VanMoof bike {self._mac_address}.")

                if _is_sx3_bike(self._vanmoof_type):
                    sx_client = SX3Client(client, self._encryption_key, self._user_key_id)
                    await sx_client.authenticate()
                    return {
                        "available": True,
                        "battery_level": await sx_client.get_motor_battery_level(),
                        "module_level": await sx_client.get_module_battery_level(),
                        "lock_state": (await sx_client.get_lock_state()).name,
                        "distance_travelled": await sx_client.get_distance_travelled(),
                        "power_level": _to_int(await sx_client.get_power_level()),
                        "speed": await sx_client.get_speed(),
                        "light_mode": await sx_client.get_light_mode(),
                        "module_state": await sx_client.get_module_state(),
                        "errors": await sx_client.get_errors(),
                        "motor_battery_state": await sx_client.get_motor_battery_state(),
                        "module_battery_state": await sx_client.get_module_battery_state(),
                    }

                sx_client = SXClient(client, self._encryption_key)
                parameters = await sx_client.get_parameters()
                
                # Convert lock_state enum
                lock_state_map = {0: "UNLOCKED", 1: "LOCKED", 2: "AWAITING_UNLOCK"}
                lock_state = lock_state_map.get(parameters.get("lock_state"), "UNKNOWN")
                
                # Convert module_state enum
                module_state_map = {
                    0: "ON", 1: "OFF", 2: "SHIPPING", 3: "STANDBY",
                    4: "ALARM_ONE", 5: "ALARM_TWO", 6: "ALARM_THREE", 7: "SLEEPING", 8: "TRACKING"
                }
                module_state = module_state_map.get(parameters.get("module_state"), "UNKNOWN")
                
                light_mode_map = {0: "AUTO", 1: "ON", 2: "OFF", 3: "REAR_FLASH", 4: "REAR_FLASH_OFF"}
                light_mode = light_mode_map.get(parameters.get("light_mode"), "UNKNOWN")
                
                return {
                    "available": True,
                    "battery_level": parameters.get("battery_level"),
                    "module_level": parameters.get("module_level"),
                    "lock_state": lock_state,
                    "distance_travelled": parameters.get("distance"),
                    "power_level": parameters.get("power_level"),
                    "region": parameters.get("region"),
                    "light_mode": light_mode,
                    "module_state": module_state,
                    "charging": parameters.get("charging"),
                    "errors": parameters.get("error_code"),
                }
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass
        except Exception as e:
            _LOGGER.error(f"Error during bike data update: {e}")
            raise UpdateFailed(f"Error updating bike data: {e}")

    async def _async_update_direct(self):
        """Fetch data directly from the bike via Bleak when proxy helpers are unavailable."""
        devices = await BleakScanner.discover(timeout=8.0)
        _LOGGER.debug("Discovered %s BLE devices while searching for VanMoof bike.", len(devices))

        if not devices:
            raise UpdateFailed("No Bluetooth devices discovered.")

        bike_device = next(
            (device for device in devices if device.address.lower() == self._mac_address.lower()),
            None,
        )

        if not bike_device:
            raise UpdateFailed(f"VanMoof bike with MAC {self._mac_address} not found.")

        client = await connect_bleak_client(bike_device)
        try:
            if not client.is_connected:
                raise UpdateFailed(f"Unable to connect to VanMoof bike {self._mac_address}.")

            if _is_sx3_bike(self._vanmoof_type):
                sx_client = SX3Client(client, self._encryption_key, self._user_key_id)
                await sx_client.authenticate()
                return {
                    "available": True,
                    "battery_level": await sx_client.get_motor_battery_level(),
                    "module_level": await sx_client.get_module_battery_level(),
                    "lock_state": (await sx_client.get_lock_state()).name,
                    "distance_travelled": await sx_client.get_distance_travelled(),
                    "power_level": _to_int(await sx_client.get_power_level()),
                    "speed": await sx_client.get_speed(),
                    "light_mode": await sx_client.get_light_mode(),
                    "module_state": await sx_client.get_module_state(),
                    "errors": await sx_client.get_errors(),
                    "motor_battery_state": await sx_client.get_motor_battery_state(),
                    "module_battery_state": await sx_client.get_module_battery_state(),
                }

            sx_client = SXClient(client, self._encryption_key)
            parameters = await sx_client.get_parameters()
            
            lock_state_map = {0: "UNLOCKED", 1: "LOCKED", 2: "AWAITING_UNLOCK"}
            lock_state = lock_state_map.get(parameters.get("lock_state"), "UNKNOWN")

            module_state_map = {
                0: "ON", 1: "OFF", 2: "SHIPPING", 3: "STANDBY",
                4: "ALARM_ONE", 5: "ALARM_TWO", 6: "ALARM_THREE", 7: "SLEEPING", 8: "TRACKING"
            }
            module_state = module_state_map.get(parameters.get("module_state"), "UNKNOWN")

            light_mode_map = {0: "AUTO", 1: "ON", 2: "OFF", 3: "REAR_FLASH", 4: "REAR_FLASH_OFF"}
            light_mode = light_mode_map.get(parameters.get("light_mode"), "UNKNOWN")

            return {
                "available": True,
                "battery_level": parameters.get("battery_level"),
                "module_level": parameters.get("module_level"),
                "lock_state": lock_state,
                "distance_travelled": parameters.get("distance"),
                "power_level": parameters.get("power_level"),
                "region": parameters.get("region"),
                "light_mode": light_mode,
                "module_state": module_state,
                "charging": parameters.get("charging"),
                "errors": parameters.get("error_code"),
            }
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
