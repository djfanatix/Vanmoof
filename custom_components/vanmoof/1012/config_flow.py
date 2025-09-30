
from bleak import BleakClient, BleakError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from .pymoof_wrapper import VanMoofHub

from .retrieve_encryption_key import RetrieveEncryptionKey
from .sx_client import SXClient
from .sx3_client import SX3Client
from .discover_bike import DiscoverBike  # Assuming this class discovers the bike

import voluptuous as vol

import logging
_LOGGER = logging.getLogger(__name__)

class VanMoofConfigFlow(config_entries.ConfigFlow, domain="vanmoof"):
    """Handle a config flow for VanMoof."""

    VERSION = 1

    def __init__(self):
        """Initialize the VanMoof config flow."""
        self.username = None
        self.password = None
        self.encryption_key = None
        self.user_key_id = None
        self.mac_address = None
        self.polling_interval = 60  # Default to 60 seconds
        super().__init__()

    async def async_step_user(self, user_input=None):
        """Handle the user input to authenticate and get the bike details."""

        errors = {}
        if user_input is not None:
            self.username = user_input["username"]
            self.password = user_input["password"]
            self.polling_interval = user_input.get("polling_interval", 60)  # Use the user-provided polling interval

            # Step 1: Retrieve the encryption key and bike details
            try:
                encryption_key, user_key_id, mac_address, vanmoof_type  = await RetrieveEncryptionKey.query(
                    self.username, self.password
                )

                self.encryption_key = encryption_key
                self.user_key_id = user_key_id
                self.mac_address = mac_address
                self.vanmoof_type = vanmoof_type

                _LOGGER.debug("Bike MAC address: %s", self.mac_address)

            # Proceed to Step 2: Discover the nearby bike
                return await self.async_step_discover_bike()

            except Exception as e:
                errors["base"] = f"Error retrieving bike details: {e}"

                # If user input is invalid, show form again
        return self.async_show_form(
            step_id="user", data_schema=self._create_data_schema(), errors=errors
        )

    async def async_step_discover_bike(self, user_input=None):
        """Discover the nearby bike using the MAC address and connect to it."""
        errors = {}

        if self.mac_address:
            _LOGGER.debug("Attempting to connect to the bike with MAC address: %s", self.mac_address)

            try:
                # Step 3: Use the MAC address to discover and connect to the bike
                device, client_type = await DiscoverBike.query(
                    self.mac_address, self.polling_interval, self.encryption_key
                )  # Pass encryption_key here as well

                if not device:
                    errors["base"] = "no_bike_found"
                    _LOGGER.error("No bike found with MAC address: %s", self.mac_address)
                    return self.async_show_form(
                        step_id="discover_bike", errors=errors
                    )

                _LOGGER.debug("Bike discovered successfully: %s", device)

                # Final step: Return to finish the configuration
                return self.async_create_entry(
                    title=f"VanMoof Bike ({self.mac_address})",
                    data={
                        "username": self.username,
                        "password": self.password,
                        "encryption_key": self.encryption_key,
                        "user_key_id": self.user_key_id,
                        "mac_address": self.mac_address,
                        "polling_interval": self.polling_interval,
                        "vanmoof_type": client_type,  # Assuming client_type represents the bike type
                    },
                )

            except Exception as e:
                _LOGGER.error("Error discovering bike: %s", e)
                errors["base"] = "bike_discovery_failed"

        return self.async_show_form(
            step_id="discover_bike", errors=errors
        )


    def _create_data_schema(self):
        """Create the data schema for the form."""
        # This is where you define the form inputs
        return vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Optional("polling_interval", default=60): vol.All(int, vol.Range(min=10, max=3600)),
            }
        )
    # Add this method to indicate successful setup
    async def async_setup_entry(self, hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
        """Set up the VanMoof integration."""
        try:
            # If the entry has been created successfully, return True
            _LOGGER.info("VanMoof setup completed successfully")
            return True
        except Exception as e:
            _LOGGER.error("Error during setup: %s", e)
            return False