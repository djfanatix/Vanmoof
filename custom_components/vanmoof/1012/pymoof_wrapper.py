import logging
from .retrieve_encryption_key import RetrieveEncryptionKey

_LOGGER = logging.getLogger(__name__)

class VanMoofHub:
    """VanMoof Hub that interacts with the API."""

    def __init__(self) -> None:
        """Initialize the VanMoof Hub."""
        self.auth_key = None
        self.user_key_id = None
        self.bike_name = "VanMoof Bike"

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the VanMoof API."""
        try:
            _LOGGER.debug("Retrieving encryption key from VanMoof servers")
            self.auth_key, self.user_key_id = await RetrieveEncryptionKey.query(
                username, password
            )

            if not self.auth_key:
                _LOGGER.warning("Failed to retrieve the encryption key.")
                return False

            # If user_key_id is None, log a warning and continue with just the encryption key
            if not self.user_key_id:
                _LOGGER.warning("No 'userKeyId' found. This may be an older bike model.")
                # You can choose to proceed without userKeyId for older bikes, if that's supported
                self.user_key_id = None  # Explicitly set it to None

            _LOGGER.info("Successfully authenticated with the VanMoof API")
            return True
        except Exception as err:
            _LOGGER.error("Error during authentication: %s", err)
            return False
