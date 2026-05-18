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
    def _parse_bike_detail(bike_detail):
        """Parse a VanMoof API bike detail object into integration data."""
        mac_address = bike_detail.get("macAddress")
        if not mac_address:
            raise Exception("No 'macAddress' found in bike details.")

        vanmoof_type = bike_detail.get("bleProfile")
        if not vanmoof_type:
            raise Exception("No 'bleProfile' found in bike details.")

        model_details = bike_detail.get("modelDetails") or {}
        bike_model_parts = [
            bike_detail.get("model"),
            bike_detail.get("modelName"),
            bike_detail.get("modelCode"),
            bike_detail.get("series"),
            bike_detail.get("bikeType"),
            bike_detail.get("controller"),
            bike_detail.get("frameShape"),
            model_details.get("Edition"),
            vanmoof_type,
        ]
        bike_model = " ".join(str(part) for part in bike_model_parts if part)

        bike_name = bike_detail.get("name", "VanMoof Bike")
        serial_number = bike_detail.get("frameNumber", mac_address)

        bike_keys = bike_detail.get("key", {})
        encryption_key = bike_keys.get("encryptionKey")
        user_key_id = bike_keys.get("userKeyId") if "userKeyId" in bike_keys else None
        if user_key_id is not None:
            user_key_id = int(user_key_id)

        if not encryption_key:
            raise Exception("Missing 'encryptionKey' in bike keys.")

        return {
            "encryption_key": encryption_key,
            "user_key_id": user_key_id,
            "mac_address": mac_address,
            "vanmoof_type": vanmoof_type,
            "bike_name": bike_name,
            "serial_number": serial_number,
            "bike_model": bike_model,
        }

    @staticmethod
    async def query_bikes(username, password, client=None):
        """
        Retrieve all bike details from a VanMoof account using the provided
        username and password.
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

                bike_details = result.get("data", {}).get("bikeDetails", [])
                if not bike_details:
                    raise Exception("No bike details found.")
                
                _LOGGER.debug("Bike details found: %s", bike_details)

                bikes = []
                for index, bike_detail in enumerate(bike_details):
                    try:
                        bikes.append(RetrieveEncryptionKey._parse_bike_detail(bike_detail))
                    except Exception as err:
                        _LOGGER.warning(
                            "Skipping VanMoof bike detail at index %s because it is incomplete: %s",
                            index,
                            err,
                        )

                if not bikes:
                    raise NoBikeDetails("No usable bike details found.")

                for bike in bikes:
                    _LOGGER.debug(
                        "Parsed bike: name=%s mac=%s model=%s bleProfile=%s userKeyId=%s",
                        bike["bike_name"],
                        bike["mac_address"],
                        bike["bike_model"],
                        bike["vanmoof_type"],
                        bike["user_key_id"],
                    )
                    if bike["user_key_id"] is None:
                        _LOGGER.warning(
                            "No 'userKeyId' found for %s. This may be an older bike model.",
                            bike["bike_name"],
                        )

                return bikes

            # Fallback for non-Home Assistant callers. Home Assistant passes its shared
            # httpx client so SSL setup is not performed inside the event loop here.
            async with httpx.AsyncClient() as fallback_client:
                return await RetrieveEncryptionKey.query_bikes(
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

    @staticmethod
    async def query(username, password, client=None):
        """
        Retrieve the first bike on an account.

        Kept for older callers; config flow uses query_bikes so users can
        select the correct bike when multiple bikes are on the account.
        """
        bikes = await RetrieveEncryptionKey.query_bikes(username, password, client)
        bike = bikes[0]
        return (
            bike["encryption_key"],
            bike["user_key_id"],
            bike["mac_address"],
            bike["vanmoof_type"],
            bike["bike_name"],
            bike["serial_number"],
            bike["bike_model"],
        )
