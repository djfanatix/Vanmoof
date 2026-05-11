# VanMoof Home Assistant Custom Integration

A custom Home Assistant integration to connect to VanMoof e-bikes over Bluetooth Low Energy (BLE).

This integration supports both older VanMoof SX1/S1 bikes and newer S3/X3 bikes. It provides bike telemetry sensors and a Bluetooth-based device tracker.

## Features

- **BLE Connectivity** — Works with native Bluetooth and BLE proxies (ESPHome, Shelly, etc.)
- Bike presence detection
- Battery level sensor
- Module battery sensor (S3/X3)
- Lock state sensor
- Distance travelled sensor
- Power level sensor
- Speed sensor
- Light mode sensor
- Module state, error code, motor battery state, and module battery state for S3/X3

## Installation

1. Copy the `custom_components/vanmoof` folder into your Home Assistant configuration directory under `custom_components/vanmoof`.
2. Ensure the following dependencies are available in your Home Assistant environment:
   - `bleak`
   - `pymoof`

   If you are running Home Assistant Core manually, install them with:

   ```bash
   pip install bleak pymoof
   ```

3. Restart Home Assistant.
4. Add the integration through the Home Assistant UI using the "Add Integration" flow, or configure it manually with a config entry.

## Configuration

This custom integration requires the bike MAC address and an encryption key to connect to the bike.

- `mac_address`: The BLE address of your VanMoof bike.
- `encryption_key`: The encrypted key retrieved from the VanMoof API.
- `user_key_id`: Required for S3/X3 authentication.
- `vanmoof_type`: Bike type string used to distinguish SX1/S1 vs S3/X3.

## Notes

- The integration uses BLE to connect to the bike via Home Assistant's Bluetooth integration.
- **Proxy Support** — Works with native Bluetooth adapters and BLE proxies:
  - ESPHome BLE proxy devices
  - Shelly devices with BLE support
  - Any Home Assistant BLE proxy
- When the bike is out of Bluetooth range or in sleep mode, sensors will be marked unavailable and the tracker will report `away`.
- SX3/X3 support is optional and detected based on the configured bike type.

## Troubleshooting

- If the integration fails to connect, confirm that Bluetooth is available on the host and the bike is powered on.
- Check Home Assistant logs for BLE discovery and authentication errors.

## HACS Support

This repository includes HACS metadata in `hacs.json` at the repository root, and the integration content lives under `custom_components/vanmoof`.

- `hacs.json`: HACS repository manifest
- `README.md`: documentation for users
- `logo.svg`: repository logo asset

## Logo

The repository includes a simple logo asset in `logo.svg`.
