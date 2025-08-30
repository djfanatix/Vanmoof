"""VanMoof integration."""

from homeassistant import config_entries
from homeassistant.helpers import discovery
import logging

from .sx3_client import SX3Client
from .sx_client import SXClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: config_entries.ConfigEntry):
    """Set up VanMoof from a config entry."""
    _LOGGER.info("Setting up VanMoof integration")
    return True