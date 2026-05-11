import enum
import math
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
#from cryptography.hazmat.primitives.ciphers.algorithms import AES
#from cryptography.hazmat.primitives.ciphers.modes import ECB
#from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

import logging
_LOGGER = logging.getLogger(__name__)


class SXProfile:
    """
    Represents the profile for the GATT UUIDs for the SX1/SX2 bikes. Contains functionality
    to encrypt and decrypt BLE payloads and handle authentication for SX models.

    :param key: The hexadecimal string of the encrypted key from VanMoof servers.
    :param user_key_id: Integer of the user key id from VanMoof servers.
    """

    def __init__(self, encryption_key: str) -> None:
            """
            Initialize the class with an encryption key and set up AES encryption in ECB mode.

            :param encryption_key: A hex string representing the encryption key.
            """
            # Convert the key from a hex string to bytes
            key_bytes = bytes.fromhex(encryption_key)

            # Adjust the key length to 16 bytes
            if len(key_bytes) == 17:
                key_bytes = key_bytes[1:]
            elif len(key_bytes) < 16:
                key_bytes = key_bytes.rjust(16, b'\0')

            # Separate the passcode (first 6 bytes of the key)
            self._passcode = key_bytes[:6]

            # Set up AES in ECB mode with the adjusted key
            self._cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.ECB(),
                backend=default_backend()
            )



    def decrypt_payload(self, data: bytes) -> bytes:
        """
        Decrypts a Bluetooth payload.

        :param data: A bytes array of data. Must be a multiple of 16 bytes long.
        """
        decryptor = self._cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()

 

    class Bike(enum.Enum):
        SERVICE_UUID = "8e7f1a50-087a-44c9-b292-a2c628fdd9aa"
        CHALLENGE = "8e7f1a51-087a-44c9-b292-a2c628fdd9aa"
        NEW_PRIVATE_KEY = "8e7f1a52-087a-44c9-b292-a2c628fdd9aa"
        FUNCTIONS = "8e7f1a53-087a-44c9-b292-a2c628fdd9aa"
        PARAMETERS = "8e7f1a54-087a-44c9-b292-a2c628fdd9aa"
