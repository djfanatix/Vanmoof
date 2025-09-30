import logging
from bleak import BleakScanner, BleakClient
from .sx_client import SXClient
import asyncio

_LOGGER = logging.getLogger(__name__)

class DiscoverBike:
    @staticmethod
    async def query(mac_address: str, polling_interval: int, encryption_key: str):
        """Discover the nearby bike using the MAC address and connect to it."""
        _LOGGER.debug(f"Starting bike discovery process for MAC address {mac_address} with polling interval {polling_interval} seconds...")

        try:
            while True:
                # Discover devices based on known service UUIDs
                devices = await BleakScanner.discover(
                    service_uuids=[
                        "6acc5540-e631-4069-944d-b8ca7598ad50",  # SX3
                        "8e7f1a54-087a-44c9-b292-a2c628fdd9aa",  # SX1/SX2
                        "6acb5520-e631-4069-944d-b8ca7598ad50",  # Smart SX1
                    ]
                )
                _LOGGER.debug(f"Discovered {len(devices)} devices.")
                
                if not devices:
                    _LOGGER.warning("No devices found during discovery.")
                    await asyncio.sleep(polling_interval)  # Wait before retrying
                    continue  # Retry if no devices are found

                # Loop through discovered devices to find one matching the provided MAC address
                for device in devices:
                    _LOGGER.debug(f"Discovered device: {device.name} ({device.address})")

                    if device.address.lower() == mac_address.lower():
                        # Found the device with the MAC address
                        _LOGGER.info(f"Found bike with MAC address: {device.name} ({device.address})")
                        
                        # Initialize the BleakClient with the discovered device
                        bleak_client = BleakClient(device)
                        await bleak_client.connect()
                        _LOGGER.info(f"Successfully connected to {device.name} ({device.address})")

                        # Initialize the SXClient with the BleakClient
                        sx_client = SXClient(bleak_client, encryption_key)

                        # Attempt to authenticate #not needed if we are not writing
                        ## await sx_client.authenticate()

                        # Get the battery level
                        battery_level = await sx_client.get_battery_level()
                        _LOGGER.info(f"Battery level: {battery_level}%")

                        return device, "SXClient", battery_level  # Return the device, client type, and battery level

                # If no matching device is found, retry after waiting for the polling interval
                _LOGGER.warning(f"No bike found with MAC address: {mac_address}")
                await asyncio.sleep(polling_interval)  # Wait before retrying

        except Exception as e:
            _LOGGER.error(f"Error during bike discovery: {e}")
            return None, None, None
