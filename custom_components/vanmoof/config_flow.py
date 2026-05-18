
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    CONF_POLLING_INTERVAL,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
)
from .retrieve_encryption_key import InvalidAuth, RetrieveEncryptionKey
from .discover_bike import DiscoverBike

import voluptuous as vol
import logging
_LOGGER = logging.getLogger(__name__)

class VanMoofConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VanMoof."""

    VERSION = 1

    def __init__(self):
        """Initialize the VanMoof config flow."""
        self.username = None
        self.password = None
        self.encryption_key = None
        self.user_key_id = None
        self.mac_address = None
        self.bike_name = None
        self.serial_number = None
        self.bike_model = None
        self.vanmoof_type = None
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        super().__init__()

    async def async_step_user(self, user_input=None):
        """Handle the user input to authenticate and get the bike details."""

        errors = {}
        if user_input is not None:
            self.username = user_input[CONF_USERNAME]
            self.password = user_input[CONF_PASSWORD]
            self.polling_interval = user_input.get(
                CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
            )

            # Step 1: Retrieve the encryption key and bike details
            try:
                encryption_key, user_key_id, mac_address, vanmoof_type, bike_name, serial_number, bike_model = await RetrieveEncryptionKey.query(
                    self.username,
                    self.password,
                    get_async_client(self.hass),
                )

                self.encryption_key = encryption_key
                self.user_key_id = user_key_id
                self.mac_address = mac_address
                self.vanmoof_type = vanmoof_type
                self.bike_name = bike_name
                self.serial_number = serial_number
                self.bike_model = bike_model

                _LOGGER.debug("Bike MAC address: %s", self.mac_address)
                _LOGGER.debug("Bike name: %s", self.bike_name)
                _LOGGER.debug("Serial number: %s", self.serial_number)
                _LOGGER.debug("Bike model: %s", self.bike_model)

            # Proceed to Step 2: Discover the nearby bike
                return await self.async_step_discover_bike()

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.error("Error retrieving bike details: %s", e)
                errors["base"] = "auth_error"

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
                    self.mac_address,
                    self.polling_interval,
                    self.encryption_key,
                    self.user_key_id,
                    self.vanmoof_type,
                )  # Pass encryption_key, user_key_id, and bike type

                if not device:
                    errors["base"] = "no_vanmoof_bike_found"
                    _LOGGER.error("No bike found with MAC address: %s", self.mac_address)
                    return self.async_show_form(
                        step_id="discover_bike", errors=errors
                    )

                _LOGGER.debug("Bike discovered successfully: %s", device)

                # Final step: Return to finish the configuration
                return self.async_create_entry(
                    title=self.bike_name,
                    data={
                        "username": self.username,
                        "password": self.password,
                        "encryption_key": self.encryption_key,
                        "user_key_id": self.user_key_id,
                        "mac_address": self.mac_address,
                        CONF_POLLING_INTERVAL: self.polling_interval,
                        "vanmoof_type": self.vanmoof_type,
                        "bike_name": self.bike_name,
                        "bike_model": self.bike_model,
                        "serial_number": self.serial_number,
                        "client_type": client_type,
                    },
                )

            except Exception as e:
                _LOGGER.error("Error discovering bike: %s", e)
                errors["base"] = "bike_discovery_failed"

        return self.async_show_form(
            step_id="discover_bike",
            data_schema=vol.Schema({}),
            errors=errors,
        )


    def _create_data_schema(self):
        """Create the data schema for the form."""
        # This is where you define the form inputs
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL
                ): vol.All(
                    int,
                    vol.Range(
                        min=MIN_POLLING_INTERVAL,
                        max=MAX_POLLING_INTERVAL,
                    ),
                ),
            }
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Create options flow."""
        return VanMoofOptionsFlow(config_entry)


class VanMoofOptionsFlow(config_entries.OptionsFlow):
    """Handle options for VanMoof."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_polling_interval = self._config_entry.options.get(
            CONF_POLLING_INTERVAL,
            self._config_entry.data.get(
                CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLLING_INTERVAL,
                        default=current_polling_interval,
                    ): vol.All(
                        int,
                        vol.Range(
                            min=MIN_POLLING_INTERVAL,
                            max=MAX_POLLING_INTERVAL,
                        ),
                    ),
                }
            ),
        )
