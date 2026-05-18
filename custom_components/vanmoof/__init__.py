"""VanMoof integration."""
from __future__ import annotations

import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .vanmoof_coordinator import VanMoofDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "device_tracker"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the VanMoof integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VanMoof from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create device in device registry
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["mac_address"])},
        name=entry.data.get("bike_name", f"VanMoof Bike ({entry.data['mac_address']})"),
        manufacturer="VanMoof",
        model=entry.data.get("bike_model") or entry.data.get("vanmoof_type", "Unknown"),
        serial_number=entry.data.get("serial_number", entry.data["mac_address"]),
        sw_version=None,
    )

    coordinator = VanMoofDataUpdateCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        _LOGGER.warning("Initial VanMoof bike update failed: %s", err)

    # Listen for options update
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Listen for option updates."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a VanMoof config entry."""
    unload_results = await asyncio.gather(
        *(
            hass.config_entries.async_forward_entry_unload(entry, platform)
            for platform in PLATFORMS
        )
    )
    unload_ok = all(unload_results)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
