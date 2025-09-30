"""VanMoof integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the VanMoof integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VanMoof from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform (use async_forward_entry_setups instead)
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    # Forward the setup to the device_tracker platform (add this line)
    #await hass.config_entries.async_forward_entry_setup(entry, "device_tracker")  
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a VanMoof config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    # Unload the sensor platform
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    return True
