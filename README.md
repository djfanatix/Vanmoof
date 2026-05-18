# VanMoof Home Assistant Custom Integration

<div style="background-color:#F6E30A; border-radius:12px; padding:16px; color:#000; font-weight:600; margin-bottom:16px;">
  <strong>VanMoof</strong> — This integration is designed for VanMoof bikes and supports BLE connectivity via Home Assistant.
</div>

A custom Home Assistant integration to connect to VanMoof e-bikes over Bluetooth Low Energy (BLE).

This integration supports both older VanMoof SX1/S1 bikes and newer S3/X3 bikes. It provides bike telemetry sensors and a Bluetooth-based device tracker.

## Donations
If you appreciate the integration: [Buy me a Beer](https://www.paypal.com/paypalme/pieterverougstraete)

## Features

- **BLE Connectivity** — Works with native Bluetooth and BLE proxies (ESPHome, Shelly, etc.)
- Bike presence detection
- Battery level sensor
- Module battery sensor
- Lock state sensor
- Distance travelled sensor
- Power level sensor
- Light mode sensor
- Module state, error code, motor battery state, and module battery state for S3/X3

## Installation

1. Add the repo: https://github.com/djfanatix/Vanmoof to HACS and add the integration.
2. Restart Home Assistant.
3. Add the integration through the Home Assistant UI using the "Add Integration" flow. 
   You need to provide your Vanmoof login and password to retrieve bike details and user key.
4. The bike needs to be in ble reach of HA or ESP Proxy to do initial connection.

## Notes

- The integration uses BLE to connect to the bike via Home Assistant's Bluetooth infrastructure.
- **Bluetooth Support** — Requires direct BLE/GATT access on the Home Assistant host.
- The integration works if the bike is exposed as a real BLE/GATT peripheral on the host.
- Shelly BLE proxies are not supported because they do not provide the full GATT connection required by VanMoof.
- ESP32 proxy setups can work only if the proxy presents the bike as a full GATT peripheral to the host.
- When the bike is out of Bluetooth range or in sleep mode, sensors will be marked unavailable and the tracker will report `away`.
- SX3/X3 support is optional and detected based on the configured bike type.

## Troubleshooting

- If the integration fails to connect, confirm that Bluetooth is available on the host and the bike is powered on.
- Check Home Assistant logs for BLE discovery and authentication errors.

## Bugs
- I have no idea how the integration handles accounts with multiple bikes




Once merged, HACS will display your logo automatically.

## Logo

The repository includes a simple logo asset in `logo.svg`.
