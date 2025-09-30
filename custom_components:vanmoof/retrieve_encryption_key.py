import base64
import httpx

class RetrieveEncryptionKey:
    @staticmethod
    async def query(username, password):
        """
        This method handles the process of retrieving the encryption key and user key ID 
        for a VanMoof bike using the provided username and password.
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
            # Authenticate and get the token
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_URL}/authenticate", headers=headers)
                response.raise_for_status()  # Raises an exception for HTTP errors
                result = response.json()

                if "error" in result:
                    raise Exception(f"Authentication Error: {result['error']}")

                token = result["token"]

                # Fetch customer data (including bike details)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.get(
                    f"{API_URL}/getCustomerData",
                    headers=headers,
                    params={"includeBikeDetails": "true"},
                )
                response.raise_for_status()
                result = response.json()

                # Extract bike details
                bike_details = result.get("data", {}).get("bikeDetails", [])
                if not bike_details:
                    raise Exception("No bike details found.")

                # Retrieve encryption key and user key ID
                encryption_key = bike_details[0]["key"]["encryptionKey"]
                user_key_id = bike_details[0]["key"]["userKeyId"]

                return encryption_key, user_key_id

        except httpx.RequestError as e:
            # Handle network or HTTP request-related errors
            raise Exception(f"Network error occurred: {e}")
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 404, 500)
            raise Exception(f"HTTP error occurred: {e}")
        except Exception as e:
            # Handle other exceptions
            raise Exception(f"Failed to retrieve the encryption key: {e}")
