import logging
from enum import Enum
import bleak.backends.client
from bleak import BleakScanner, BleakClient
from .sx_profile import SXProfile
from pymoof.util import bleak_utils

_LOGGER = logging.getLogger(__name__)

class LockState(Enum):
    UNLOCKED = 0x00
    LOCKED = 0x01
    AWAITING_UNLOCK = 0x02

class SXClient:
    """
    A wrapper around a bleak client that allows bluetooth communication with a Vanmoof S and X.
    """

    def __init__(
        self,
        bleak_client: bleak.backends.client.BaseBleakClient,
        encryption_key: str,
    ) -> None:
        self._gatt_client = bleak_client
        self._bike_profile = SXProfile(encryption_key)

    async def _get_nonce(self) -> bytes:
        return await self._read(
            self._bike_profile.Bike.CHALLENGE,
            needs_decryption=False,
        )

    async def _read(self, characteristic_uuid, needs_decryption: bool = True) -> bytes:
        try:
            result = await bleak_utils.read_from_characteristic(
                self._gatt_client,
                characteristic_uuid,
            )
            if needs_decryption:
                result = self._bike_profile.decrypt_payload(result)
            return result
        except Exception as e:
            _LOGGER.error(f"Failed to read characteristic {characteristic_uuid}: {e}")
            raise
        
# we try to read a parameter to be sure, the connection is ok
    async def get_discovery(self) -> int: 
        try:
            result = await self._read(self._bike_profile.Bike.PARAMETERS)

            _LOGGER.debug(f"Battery data: {result}")
            battery_level = int(result[5])
            
            return battery_level
        except Exception as e:
            _LOGGER.error(f"Failed to get parameters: {e}")
            raise

    async def get_parameters(self) -> int: 
        try:
            result = await self._read(self._bike_profile.Bike.PARAMETERS)

            _LOGGER.debug(f"Battery data: {result}")
            battery_level = int(result[5])
            _LOGGER.debug(f"Battery level: {battery_level}%")
            module_level = int(result[6])
            _LOGGER.debug(f"Module level: {module_level}%")
            
            return {
                "battery_level": battery_level,
                "module_level": module_level
                }
        except Exception as e:
            _LOGGER.error(f"Failed to get parameters: {e}")
            raise

    async def get_lock_state(self) -> LockState:

        try:
            result = await self._read(self._bike_profile.Defense.LOCK_STATE)
            lock_state = LockState(result[0])
            _LOGGER.info(f"Lock state: {lock_state.name}")
            return lock_state
        except Exception as e:
            _LOGGER.error(f"Failed to get lock state: {e}")
            raise

    async def get_distance_travelled(self) -> float:

        try:
            result = await self._read(self._bike_profile.Movement.DISTANCE)
            distance_km = int.from_bytes(result, "little") / 10  # Convert hectometers to kilometers
            _LOGGER.info(f"Distance travelled: {distance_km} km")
            return distance_km
        except Exception as e:
            _LOGGER.error(f"Failed to get distance travelled: {e}")
            raise

    async def get_power_level(self) -> int:
        """
        **Must be authenticated to call**

        Gets the power level of the bike.
        """
        try:
            result = await self._read(self._bike_profile.Movement.POWER_LEVEL)
            _LOGGER.info(f"Power level: {result}")
            return result
        except Exception as e:
            _LOGGER.error(f"Failed to get power level: {e}")
            raise

    async def get_frame_number(self) -> str:
        """
        **No authentication needed to call**

        Returns the frame number of the bike.
        """
        try:
            result = await self._read(self._bike_profile.BikeInfo.FRAME_NUMBER, needs_decryption=False)
            frame_number = result.decode("ascii")
            _LOGGER.info(f"Frame number: {frame_number}")
            return frame_number
        except Exception as e:
            _LOGGER.error(f"Failed to get frame number: {e}")
            raise

    async def get_speed(self) -> int:
        """
        **Must be authenticated to call**

        Gets the current speed of the bike in kilometers per hour.
        """
        try:
            result = await self._read(self._bike_profile.Movement.SPEED)
            speed = int.from_bytes(result, "little")
            _LOGGER.info(f"Current speed: {speed} km/h")
            return speed
        except Exception as e:
            _LOGGER.error(f"Failed to get speed: {e}")
            raise

    async def get_light_mode(self) -> int:
        """
        **Must be authenticated to call**

        Gets the light mode.
        """
        try:
            result = await self._read(self._bike_profile.Movement.SPEED)
            _LOGGER.info(f"Light mode: {result}")
            return result
        except Exception as e:
            _LOGGER.error(f"Failed to get light mode: {e}")
            raise
