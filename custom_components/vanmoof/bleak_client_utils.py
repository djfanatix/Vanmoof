import logging
import bleak.backends.client
from bleak import BleakClient
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _uuid_value(characteristic_uuid: Any) -> str:
    if hasattr(characteristic_uuid, "value"):
        return characteristic_uuid.value
    return str(characteristic_uuid)


async def _get_services(gatt_client: bleak.backends.client.BaseBleakClient):
    if hasattr(gatt_client, "get_services"):
        return await gatt_client.get_services()

    services = getattr(gatt_client, "services", None)
    if services is not None:
        return services

    raise AttributeError("BLE client does not expose get_services() or services")


async def _resolve_characteristic(gatt_client: bleak.backends.client.BaseBleakClient, characteristic_uuid: Any):
    uuid = _uuid_value(characteristic_uuid)
    service_uuid = getattr(getattr(characteristic_uuid, "SERVICE_UUID", None), "value", None)

    if service_uuid is None:
        return uuid

    services = await _get_services(gatt_client)
    service = services.get_service(service_uuid)
    if service is None:
        raise ValueError(f"Service {service_uuid} not found on the BLE client.")

    return service.get_characteristic(uuid)


async def connect_bleak_client(device, timeout: float = 20.0) -> BleakClient:
    """Connect to a BLE device with a fallback from device object to address."""
    client = BleakClient(device)
    try:
        await client.connect(timeout=timeout)
        return client
    except Exception as first_exc:
        _LOGGER.debug("BleakClient(device) connection failed: %s", first_exc)
        try:
            await client.disconnect()
        except Exception:
            pass

    fallback_target = getattr(device, "address", device)
    client = BleakClient(fallback_target)
    await client.connect(timeout=timeout)
    return client


async def read_from_characteristic(
    gatt_client: bleak.backends.client.BaseBleakClient,
    characteristic_uuid: Any,
) -> bytes:
    uuid = _uuid_value(characteristic_uuid)

    try:
        return await gatt_client.read_gatt_char(uuid)
    except Exception as exc:
        _LOGGER.debug("Direct read_gatt_char(%s) failed: %s", uuid, exc)
        characteristic = await _resolve_characteristic(gatt_client, characteristic_uuid)
        return await gatt_client.read_gatt_char(characteristic)


async def write_to_characteristic(
    gatt_client: bleak.backends.client.BaseBleakClient,
    characteristic_uuid: Any,
    data: bytes,
) -> None:
    uuid = _uuid_value(characteristic_uuid)
    payload = bytes(data)

    try:
        return await gatt_client.write_gatt_char(uuid, payload, response=True)
    except Exception as exc:
        _LOGGER.debug("Direct write_gatt_char(%s) failed: %s", uuid, exc)
        characteristic = await _resolve_characteristic(gatt_client, characteristic_uuid)
        return await gatt_client.write_gatt_char(characteristic, payload, response=True)
