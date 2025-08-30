import logging
from bleak import BleakClient, BleakError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .pymoof_wrapper import VanMoofHub
from .sx_client import SXClient
from .sx3_client import SX3Client
from .discover_bike import DiscoverBike  # Assuming this class discovers the bike

_LOGGER = logging.getLogger(__name__)

class VanMoofConfigFlow(config_entries.ConfigFlow, domain="vanmoof"):
    """Handle a VanMoof bike configuration flow."""
    
    def __init__(self) -> None:
        """Initialize the VanMoofConfigFlow."""
        self._username = None
        self._password = None
        self._hub = VanMoofHub()

    async def async_step_user(self, user_input=None):
        """Handle the user input step."""
        errors = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            # Step 1: Authenticate with VanMoof API
            _LOGGER.debug("Start Vanmoof API")
            authenticated = await self._hub.authenticate(self._username, self._password)

            if not authenticated:
                errors["base"] = "authentication_failed"
                return self.async_show_form(
                    step_id="user", data_schema=self._create_data_schema(), errors=errors
                )

            # Step 2: Discover the nearby bike and get details
            _LOGGER.debug("Start discover bike")
            device, client_type = await DiscoverBike.query()
            
            if not device:
                errors["base"] = "no_bike_found"
                return self.async_show_form(
                    step_id="user", data_schema=self._create_data_schema(), errors=errors
                )
            
            # Step 3: Connect to the bike via Bluetooth
            try:
                async with BleakClient(device.address) as bleak_client:
                    if client_type == "SX3Client":
                        _LOGGER.debug("Start connect bike S3")
                        # Newer bike (e.g., S3) requires both auth_key and user_key_id
                        client = SX3Client(bleak_client, self._hub.auth_key, self._hub.user_key_id)
                    elif client_type == "SXClient":
                        _LOGGER.debug("Start connect bike S")
                        # Older bike (e.g., S1, S2) only requires auth_key
                        client = SXClient(bleak_client, self._hub.auth_key, None)
                    else:
                        raise Exception("Unsupported client type.")
                    
                    # Authenticate with the bike
                    await client.authenticate()

                    _LOGGER.info(f"Successfully connected to {device.name} ({client_type})")

                # Step 4: Create the configuration entry
                return self.async_create_entry(
                    title=f"VanMoof Bike ({device.name})",
                    data={
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        "device_address": device.address,
                        "device_name": device.name,
                        "client_type": client_type,
                    },
                )
            except BleakError as e:
                _LOGGER.error("Bluetooth error occurred: %s", e)
                errors["base"] = "bluetooth_error"
            except Exception as e:
                _LOGGER.error("Failed to authenticate or connect to bike: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=self._create_data_schema(), errors=errors
        )

    def _create_data_schema(self):
        """Create the data schema for the form."""
        from homeassistant.helpers import config_validation as cv
        from homeassistant.components import frontend

        return vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
