"""Coordinator for shared VanMoof bike data updates."""
from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakClient, BleakScanner
try:
    from homeassistant.components.bluetooth import (
        async_ble_device_from_address,
        async_connect_ble_device,
    )
except ImportError:  # pragma: no cover
    async_ble_device_from_address = None
    async_connect_ble_device = None
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
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

        update_interval = timedelta(seconds=entry.data["polling_interval"])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from the bike via BLE (native or proxy)."""
        try:
            if async_ble_device_from_address is None:
                _LOGGER.warning(
                    "Home Assistant Bluetooth proxy helpers are unavailable; falling back to direct Bleak scanning."
                )
                return await self._async_update_direct()

            ble_device = await async_ble_device_from_address(
                self.hass, self._mac_address, connectable=True
            )

            if not ble_device:
                _LOGGER.warning("VanMoof bike with MAC %s not found in Bluetooth discovery.", self._mac_address)
                raise UpdateFailed(f"VanMoof bike with MAC {self._mac_address} not found.")

            if async_connect_ble_device is None:
                raise UpdateFailed(
                    "Home Assistant Bluetooth proxy support is not available in this version; "
                    "please upgrade Home Assistant or use a native Bluetooth adapter."
                )

            async with async_connect_ble_device(self.hass, ble_device) as client:
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
                return {
                    "available": True,
                    "battery_level": parameters.get("battery_level"),
                    "module_level": parameters.get("module_level"),
                    "lock_state": (await sx_client.get_lock_state()).name,
                    "distance_travelled": await sx_client.get_distance_travelled(),
                    "power_level": _to_int(await sx_client.get_power_level()),
                    "speed": await sx_client.get_speed(),
                    "light_mode": await sx_client.get_light_mode(),
                    "module_state": None,
                    "errors": await sx_client.get_error_codes(),
                    "motor_battery_state": None,
                    "module_battery_state": None,
                    "motor_battery_level": None,
                    "module_battery_level": None,
                }
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

        async with BleakClient(bike_device) as client:
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
            return {
                "available": True,
                "battery_level": parameters.get("battery_level"),
                "module_level": parameters.get("module_level"),
                "lock_state": (await sx_client.get_lock_state()).name,
                "distance_travelled": await sx_client.get_distance_travelled(),
                "power_level": _to_int(await sx_client.get_power_level()),
                "speed": await sx_client.get_speed(),
                "light_mode": await sx_client.get_light_mode(),
                "module_state": None,
                "errors": await sx_client.get_error_codes(),
                "motor_battery_state": None,
                "module_battery_state": None,
                "motor_battery_level": None,
                "module_battery_level": None,
            }
