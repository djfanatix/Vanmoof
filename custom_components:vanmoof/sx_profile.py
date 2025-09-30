import enum
import math
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes


class SXClient:
    """
    Represents the profile for the GATT UUIDs for the SX1/SX2 bikes. Contains functionality
    to encrypt and decrypt BLE payloads and handle authentication for SX models.

    :param key: The hexadecimal string of the encrypted key from VanMoof servers.
    :param user_key_id: Integer of the user key id from VanMoof servers.
    """

    def __init__(self, key: str, user_key_id: int) -> None:
        self._cipher = Cipher(algorithms.AES(bytes.fromhex(key)), modes.ECB())
        self._user_key_id = user_key_id

    def build_authentication_payload(self, challenge: bytes) -> bytes:
        """
        Builds the authentication payload given a challenge.

        :param challenge: A bytes array that represents the challenge from the bike.
        """
        encryptor = self._cipher.encryptor()

        # Create the 16-byte payload using the challenge
        data = bytearray(16)
        data[0:len(challenge)] = challenge

        # Encrypt the challenge
        encrypted_data = bytearray(encryptor.update(data) + encryptor.finalize())

        # Append the user key ID as a 4-byte integer
        encrypted_data.extend(self._user_key_id.to_bytes(4, byteorder="big"))

        return bytes(encrypted_data)

    def decrypt_payload(self, data: bytes) -> bytes:
        """
        Decrypts a Bluetooth payload.

        :param data: A bytes array of data. Must be a multiple of 16 bytes long.
        """
        decryptor = self._cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()

    def build_encrypted_payload(self, challenge: bytes, data: bytes) -> bytes:
        """
        Encrypts data signed with a challenge. This will build a payload and pad with
        zeroes to the nearest multiple of 16 bytes.

        :param challenge: A bytes array that represents the challenge from the bike.
        :param data: A bytes array of data.
        """
        encryptor = self._cipher.encryptor()

        # Start with a 16-byte block and insert the challenge and data
        payload = bytearray(16)
        payload[0:len(challenge)] = challenge
        payload[len(challenge):] = data

        # Pad to the nearest cipher block size (16 bytes)
        padding_length = (16 - len(payload) % 16) % 16
        payload.extend(b'\x00' * padding_length)

        return bytes(encryptor.update(payload) + encryptor.finalize())

    class Security(enum.Enum):
        SERVICE_UUID = "8e7f1500-087a-44c9-b292-a2c628fdd9aa"
        CHALLENGE = "8e7f1501-087a-44c9-b292-a2c628fdd9aa"
        KEY_INDEX = "8e7f1502-087a-44c9-b292-a2c628fdd9aa"

    class Defense(enum.Enum):
        SERVICE_UUID = "8e7f1520-087a-44c9-b292-a2c628fdd9aa"
        LOCK_STATE = "8e7f1521-087a-44c9-b292-a2c628fdd9aa"
        UNLOCK_REQUEST = "8e7f1522-087a-44c9-b292-a2c628fdd9aa"
        ALARM_STATE = "8e7f1523-087a-44c9-b292-a2c628fdd9aa"

    class BikeInfo(enum.Enum):
        SERVICE_UUID = "8e7f1540-087a-44c9-b292-a2c628fdd9aa"
        BATTERY_LEVEL = "8e7f1541-087a-44c9-b292-a2c628fdd9aa"
        FIRMWARE_VERSION = "8e7f1542-087a-44c9-b292-a2c628fdd9aa"
        FRAME_NUMBER = "8e7f1543-087a-44c9-b292-a2c628fdd9aa"
