"""Coordinator for shared VanMoof bike data updates."""
from __future__ import annotations

import logging
import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from bleak import BleakScanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL, DOMAIN
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
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return int.from_bytes(value, "little")
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return int(value)


def _enum_name(value):
    if value is None:
        return None
    return getattr(value, "name", str(value))


def _is_missing_service_error(err: Exception) -> bool:
    message = str(err)
    return "Service" in message and "not found on the BLE client" in message


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
            CONF_POLLING_INTERVAL,
            entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL),
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
                    return await self._async_get_sx3_data(sx_client)

                sx_client = SXClient(client, self._encryption_key)
                try:
                    parameters = await sx_client.get_parameters()
                except Exception as err:
                    if _is_missing_service_error(err):
                        battery_level = await self._async_read_standard_battery(client)
                        return self._s1_data(battery_level)
                    raise
                
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

    async def _async_read_standard_battery(self, client) -> int | None:
        """Read the standard BLE battery characteristic when an older bike exposes it."""
        try:
            data = await client.read_gatt_char("00002a19-0000-1000-8000-00805f9b34fb")
        except Exception as err:
            _LOGGER.debug("S1 standard BLE battery characteristic is not available: %s", err)
            return None

        if not data:
            return None
        return int(data[0])

    def _s1_data(self, battery_level: int | None) -> dict[str, Any]:
        """Build coordinator data for bikes without the SX/S3 encrypted services."""
        return {
            "available": True,
            "battery_level": battery_level,
            "module_level": None,
            "lock_state": None,
            "distance_travelled": None,
            "power_level": None,
            "region": None,
            "light_mode": None,
            "module_state": None,
            "charging": None,
            "errors": None,
            "speed": None,
            "motor_battery_state": None,
            "module_battery_state": None,
        }

    async def _async_read_optional(
        self,
        name: str,
        reader: Callable[[], Awaitable[Any]],
    ) -> Any:
        """Read an optional SX3/X3 characteristic without failing the whole update."""
        try:
            return await reader()
        except Exception as err:
            _LOGGER.debug("Unable to read optional VanMoof S3/X3 value %s: %s", name, err)
            return None

    async def _async_get_sx3_battery_level(self, sx_client: SX3Client) -> int:
        """Read S3/X3 battery level with a retry for occasional false 100% reports."""
        battery_level = await sx_client.get_battery_level()
        if battery_level != 100:
            return battery_level

        for _ in range(2):
            await asyncio.sleep(5)
            battery_level = await sx_client.get_battery_level()
            if battery_level < 100:
                return battery_level
        return battery_level

    async def _async_get_sx3_data(self, sx_client: SX3Client) -> dict[str, Any]:
        """Fetch S3/X3 data, keeping the core pymoof-compatible reads mandatory."""
        battery_level = await self._async_get_sx3_battery_level(sx_client)
        lock_state = await sx_client.get_lock_state()
        distance_travelled = await sx_client.get_distance_travelled()

        return {
            "available": True,
            "battery_level": battery_level,
            "module_level": await self._async_read_optional(
                "module_level", sx_client.get_module_battery_level
            ),
            "lock_state": _enum_name(lock_state),
            "distance_travelled": distance_travelled,
            "power_level": _to_int(
                await self._async_read_optional("power_level", sx_client.get_power_level)
            ),
            "speed": await self._async_read_optional("speed", sx_client.get_speed),
            "region": None,
            "light_mode": await self._async_read_optional(
                "light_mode", sx_client.get_light_mode
            ),
            "module_state": await self._async_read_optional(
                "module_state", sx_client.get_module_state
            ),
            "charging": None,
            "errors": await self._async_read_optional("errors", sx_client.get_errors),
            "motor_battery_state": await self._async_read_optional(
                "motor_battery_state", sx_client.get_motor_battery_state
            ),
            "module_battery_state": await self._async_read_optional(
                "module_battery_state", sx_client.get_module_battery_state
            ),
        }

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
                return await self._async_get_sx3_data(sx_client)

            sx_client = SXClient(client, self._encryption_key)
            try:
                parameters = await sx_client.get_parameters()
            except Exception as err:
                if _is_missing_service_error(err):
                    battery_level = await self._async_read_standard_battery(client)
                    return self._s1_data(battery_level)
                raise
            
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
