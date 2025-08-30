import asyncio
from .sx3client import SX3Client
from .sxclient import SXClient
from bleak import BleakScanner

class DiscoverBike:
    @staticmethod
    async def query():
        """Discover nearby VanMoof bikes."""
        devices = await BleakScanner.discover(
            service_uuids=[
                "6acc5540-e631-4069-944d-b8ca7598ad50",  # SX3
                "8e7f1a50-087a-44c9-b292-a2c628fdd9aa",  # SX1/SX2
                "6acb5520-e631-4069-944d-b8ca7598ad50",  # Smart SX1
            ]
        )

        # Iterate through discovered devices and match by UUID
        for device in devices:
            # Check for SX3 UUID
            if "6acc5540-e631-4069-944d-b8ca7598ad50" in device.metadata["uuids"]:
                print(f"Found SX3: {device.address}")
                return device, "SX3Client"

            # Check for SX1/SX2 UUID
            if "8e7f1a50-087a-44c9-b292-a2c628fdd9aa" in device.metadata["uuids"]:
                print(f"Found SX1/SX2: {device.address}")
                return device, "SXClient"

            # Check for Smart SX1 UUID (not supported)
            if "6acb5520-e631-4069-944d-b8ca7598ad50" in device.metadata["uuids"]:
                print(f"Found Smart SX1: {device.address} (but it's not supported)")
                raise Exception("Smart SX1 is not supported.")

        # If no bike found, log it and return None
        print("No VanMoof bikes found.")
        return None, None
