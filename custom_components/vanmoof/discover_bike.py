import logging
from bleak import BleakScanner
from .bleak_client_utils import connect_bleak_client
from .sx_client import SXClient
from .sx3_client import SX3Client

_LOGGER = logging.getLogger(__name__)

def _is_sx3_bike(vanmoof_type: str | None) -> bool:
    if not vanmoof_type:
        return False
    value = vanmoof_type.upper()
    return any(token in value for token in ("SX3", "S3", "X3"))


def _is_s1_bike(vanmoof_type: str | None, user_key_id: int | None = None) -> bool:
    if user_key_id is None:
        return True
    if not vanmoof_type:
        return False
    value = vanmoof_type.upper()
    return (
        "S1" in value
        or "X1" in value
        or "SMARTBIKE" in value
        or "SMART_S" in value
        or "ELECTRIFIED" in value
    )


class DiscoverBike:
    @staticmethod
    async def query(
        mac_address: str,
        polling_interval: int,
        encryption_key: str,
        user_key_id: int | None = None,
        vanmoof_type: str | None = None,
    ):
        """Discover the nearby bike using the MAC address and connect to it."""
        _LOGGER.debug(f"Starting bike discovery process for MAC address {mac_address} with polling interval {polling_interval} seconds...")

        try:
            devices = await BleakScanner.discover(timeout=10.0)
            _LOGGER.debug(f"Discovered {len(devices)} devices.")

            if not devices:
                _LOGGER.warning("No devices found during discovery.")
                return None, None

            ## Loop through discovered devices to find one matching the provided MAC address
            for device in devices:
                _LOGGER.debug(f"Discovered device: {device.name} ({device.address})")

                if device.address.lower() == mac_address.lower():
                    # Found the device with the MAC address
                    _LOGGER.info(f"Found bike with MAC address: {device.name} ({device.address})")

                    bleak_client = await connect_bleak_client(device)
                    _LOGGER.info(f"Successfully connected to {device.name} ({device.address})")

                    try:
                        if _is_s1_bike(vanmoof_type, user_key_id):
                            _LOGGER.info("Detected S1/SmartBike profile; skipping SX encrypted parameter read.")
                            return device, "S1Client"

                        if _is_sx3_bike(vanmoof_type):
                            sx_client = SX3Client(bleak_client, encryption_key, user_key_id)
                            await sx_client.authenticate()
                            battery_level = await sx_client.get_battery_level()
                            _LOGGER.info(f"SX3 bike battery level: {battery_level}%")
                            return device, "SX3Client"

                        sx_client = SXClient(bleak_client, encryption_key)
                        battery_level = await sx_client.get_discovery()
                        _LOGGER.info(f"SX bike battery level: {battery_level}%")
                        return device, "SXClient"
                    finally:
                        try:
                            await bleak_client.disconnect()
                        except Exception:
                            pass

            _LOGGER.warning(f"No bike found with MAC address: {mac_address}")
            return None, None

        except Exception as e:
            _LOGGER.error(f"Error during bike discovery: {e}")
            return None, None
