import logging
from enum import Enum
import bleak.backends.client
from bleak import BleakScanner, BleakClient
from .bleak_client_utils import read_from_characteristic
from .sx_profile import SXProfile

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
            result = await read_from_characteristic(
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

    async def get_parameters(self) -> dict:
        try:
            result = await self._read(self._bike_profile.Bike.PARAMETERS)

            _LOGGER.debug(f"Parameters data: {result}")
            
            # Extract all parameters from the array
            module_state = int(result[2]) if len(result) > 2 else None
            lock_state = int(result[3]) if len(result) > 3 else None
            battery_level = int(result[5]) if len(result) > 5 else None
            module_level = int(result[6]) if len(result) > 6 else None
            light_mode = int(result[7]) if len(result) > 7 else None
            power_level = int(result[8]) if len(result) > 8 else None
            
            # Distance is 4 bytes at indices 11-14
            if len(result) > 14:
                distance = result[11] + (result[12] << 8) + (result[13] << 16) + (result[14] << 24)
                distance_km = distance / 10
            else:
                distance_km = None
            
            # Error code and charging status at index 15
            error_code = int(result[15]) if len(result) > 15 else None
            
            _LOGGER.debug(f"Battery level: {battery_level}%")
            _LOGGER.debug(f"Module level: {module_level}%")
            _LOGGER.debug(f"Module state: {module_state}")
            _LOGGER.debug(f"Lock state: {lock_state}")
            _LOGGER.debug(f"Light mode: {light_mode}")
            _LOGGER.debug(f"Power level: {power_level}")
            _LOGGER.debug(f"Distance: {distance_km} km")
            
            return {
                "battery_level": battery_level,
                "module_level": module_level,
                "module_state": module_state,
                "lock_state": lock_state,
                "light_mode": light_mode,
                "power_level": power_level,
                "distance": distance_km,
                "error_code": error_code,
            }
        except Exception as e:
            _LOGGER.error(f"Failed to get parameters: {e}")
            raise

    async def get_lock_state(self) -> LockState | None:

        try:
            result = await self._read(self._bike_profile.Defense.LOCK_STATE)
            lock_state = LockState(result[0])
            _LOGGER.info(f"Lock state: {lock_state.name}")
            return lock_state
        except AttributeError as e:
            _LOGGER.debug("Lock state not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get lock state: {e}")
            return None

    async def get_distance_travelled(self) -> float | None:

        try:
            result = await self._read(self._bike_profile.Movement.DISTANCE)
            distance_km = int.from_bytes(result, "little") / 10  # Convert hectometers to kilometers
            _LOGGER.info(f"Distance travelled: {distance_km} km")
            return distance_km
        except AttributeError as e:
            _LOGGER.debug("Distance travelled not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get distance travelled: {e}")
            return None

    async def get_power_level(self) -> int | None:
        """
        **Must be authenticated to call**

        Gets the power level of the bike.
        """
        try:
            result = await self._read(self._bike_profile.Movement.POWER_LEVEL)
            _LOGGER.info(f"Power level: {result}")
            return result
        except AttributeError as e:
            _LOGGER.debug("Power level not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get power level: {e}")
            return None

    async def get_frame_number(self) -> str | None:
        """
        **No authentication needed to call**

        Returns the frame number of the bike.
        """
        try:
            result = await self._read(self._bike_profile.BikeInfo.FRAME_NUMBER, needs_decryption=False)
            frame_number = result.decode("ascii")
            _LOGGER.info(f"Frame number: {frame_number}")
            return frame_number
        except AttributeError as e:
            _LOGGER.debug("Frame number not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get frame number: {e}")
            return None

    async def get_speed(self) -> int | None:
        """
        **Must be authenticated to call**

        Gets the current speed of the bike in kilometers per hour.
        """
        try:
            result = await self._read(self._bike_profile.Movement.SPEED)
            speed = int.from_bytes(result, "little")
            _LOGGER.info(f"Current speed: {speed} km/h")
            return speed
        except AttributeError as e:
            _LOGGER.debug("Speed not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get speed: {e}")
            return None

    async def get_light_mode(self) -> int | None:
        """
        **Must be authenticated to call**

        Gets the light mode.
        """
        try:
            result = await self._read(self._bike_profile.Movement.SPEED)
            _LOGGER.info(f"Light mode: {result}")
            return result
        except AttributeError as e:
            _LOGGER.debug("Light mode not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get light mode: {e}")
            return None

    async def get_module_battery_level(self) -> int | None:
        """
        **Must be authenticated to call**

        Gets the module battery level for SX1/S1 bikes.
        """
        try:
            result = await self._read(self._bike_profile.Bike.PARAMETERS)
            module_level = int(result[6])
            _LOGGER.info(f"Module battery level: {module_level}%")
            return module_level
        except AttributeError as e:
            _LOGGER.debug("Module battery level not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get module battery level: {e}")
            return None

    async def get_error_codes(self) -> int | None:
        """
        **Must be authenticated to call**

        Gets the current error codes for SX1/S1 bikes.
        """
        try:
            # Error codes are typically in a dedicated characteristic or part of parameters
            result = await self._read(self._bike_profile.Bike.PARAMETERS)
            # Error code is at a specific position in the parameters
            error_code = int.from_bytes(result[7:9], "little") if len(result) > 8 else 0
            _LOGGER.info(f"Error codes: {error_code}")
            return error_code
        except AttributeError as e:
            _LOGGER.debug("Error codes not available for this bike model: %s", e)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get error codes: {e}")
            return None
