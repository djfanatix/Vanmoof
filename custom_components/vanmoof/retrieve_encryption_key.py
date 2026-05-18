import base64
import httpx
import logging

_LOGGER = logging.getLogger(__name__)

class InvalidAuth(Exception):
    pass

class NoBikeDetails(Exception):
    pass

class RetrieveEncryptionKey:
    @staticmethod
    async def query(username, password, client=None):
        """
        This method handles the process of retrieving the encryption key, user key ID, 
        and the MAC address for a VanMoof bike using the provided username and password.
        """

        # API endpoint and API key (shared universally across users)
        API_URL = "https://my.vanmoof.com/api/v8"
        API_KEY = "fcb38d47-f14b-30cf-843b-26283f6a5819"

        # Prepare headers for authentication
        headers = {
            "Api-Key": API_KEY,
            "Authorization": "Basic "
            + base64.b64encode(f"{username}:{password}".encode()).decode("ascii"),
        }

        try:
            if client is not None:
                response = await client.post(f"{API_URL}/authenticate", headers=headers)
                response.raise_for_status()  # Raises an exception for HTTP errors
                result = response.json()

                if "error" in result:
                    raise Exception(f"Authentication Error: {result['error']}")

                token = result["token"]
                _LOGGER.debug("Authentication successful. Token received: %s", token)

                # Fetch customer data (including bike details)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.get(
                    f"{API_URL}/getCustomerData",
                    headers=headers,
                    params={"includeBikeDetails": "true"},
                )
                response.raise_for_status()
                result = response.json()

                _LOGGER.debug("Customer data received: %s", result)

                # Extract bike details
                bike_details = result.get("data", {}).get("bikeDetails", [])
                if not bike_details:
                    raise Exception("No bike details found.")
                
                _LOGGER.debug("Bike details found: %s", bike_details)

                # Extract the MAC address (needed to connect to the bike via Bluetooth)
                mac_address = bike_details[0].get("macAddress")
                if not mac_address:
                    raise Exception("No 'macAddress' found in bike details.")
                
                _LOGGER.debug("Bike MAC address: %s", mac_address)

                # Extract Bike Type
                vanmoof_type = bike_details[0].get("bleProfile")
                if not vanmoof_type:
                    raise Exception("No 'bleProfile' found in bike details.")
                
                _LOGGER.debug("bleProfile: %s", vanmoof_type)

                # Extract model information when available. The API has used
                # different field names over time, so keep a combined string
                # with all useful model hints.
                model_details = bike_details[0].get("modelDetails") or {}
                bike_model_parts = [
                    bike_details[0].get("model"),
                    bike_details[0].get("modelName"),
                    bike_details[0].get("modelCode"),
                    bike_details[0].get("series"),
                    bike_details[0].get("bikeType"),
                    bike_details[0].get("controller"),
                    bike_details[0].get("frameShape"),
                    model_details.get("Edition"),
                    vanmoof_type,
                ]
                bike_model = " ".join(str(part) for part in bike_model_parts if part)
                _LOGGER.debug("Bike model: %s", bike_model)
                
                # Extract bike name
                bike_name = bike_details[0].get("name", "VanMoof Bike")
                _LOGGER.debug("Bike name: %s", bike_name)
                
                # Extract serial number (frame number)
                serial_number = bike_details[0].get("frameNumber", mac_address)
                _LOGGER.debug("Serial number: %s", serial_number)

                # Extract the key object from the first bike detail
                bike_keys = bike_details[0].get("key", {})
                _LOGGER.debug("Bike keys: %s", bike_keys)

                # Get the encryptionKey
                encryption_key = bike_keys.get("encryptionKey")

                # Handle the case for old bikes (S1, etc.) that may not have a userKeyId
                user_key_id = bike_keys.get("userKeyId") if "userKeyId" in bike_keys else None
                if user_key_id is not None:
                    user_key_id = int(user_key_id)

                # Log the encryption key and user key ID for debugging purposes
                _LOGGER.debug("Encryption Key: %s", encryption_key)
                _LOGGER.debug("User Key ID: %s", user_key_id)

                # If encryptionKey is missing, raise an error
                if not encryption_key:
                    raise Exception("Missing 'encryptionKey' in bike keys.")

                # Handle missing userKeyId for older bikes
                if user_key_id is None:
                    _LOGGER.warning("No 'userKeyId' found. This may be an older bike model (S1, etc.).")
                    # Consider returning only encryption_key or making it optional for older bikes
                    return encryption_key, None, mac_address, vanmoof_type, bike_name, serial_number, bike_model

                # Return encryption key, user key id, mac address, type, name, and serial
                return encryption_key, user_key_id, mac_address, vanmoof_type, bike_name, serial_number, bike_model

            # Fallback for non-Home Assistant callers. Home Assistant passes its shared
            # httpx client so SSL setup is not performed inside the event loop here.
            async with httpx.AsyncClient() as fallback_client:
                return await RetrieveEncryptionKey.query(
                    username,
                    password,
                    fallback_client,
                )

        except httpx.RequestError as e:
            # Handle network or HTTP request-related errors
            _LOGGER.error(f"Network error occurred: {e}")
            raise Exception(f"Network error occurred: {e}")
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 404, 500)
            _LOGGER.error(f"HTTP error occurred: {e}")
            if e.response is not None and e.response.status_code == 401:
                raise InvalidAuth("Wrong username or password.")
            raise Exception(f"HTTP error occurred: {e}")
        except Exception as e:
            # Handle other exceptions
            _LOGGER.error(f"Failed to retrieve the encryption key: {e}")
            raise Exception(f"Failed to retrieve the encryption key: {e}")
