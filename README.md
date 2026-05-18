# VanMoof Home Assistant Custom Integration

<div style="background-color:#F6E30A; border-radius:12px; padding:16px; color:#000; font-weight:600; margin-bottom:16px;">
  <strong>VanMoof</strong> — This integration is designed for VanMoof bikes and supports BLE connectivity via Home Assistant.
</div>

A custom Home Assistant integration to connect to VanMoof e-bikes over Bluetooth Low Energy (BLE).

This integration supports both older VanMoof SX1/S1 bikes and newer S3/X3 bikes. It provides bike telemetry sensors and a Bluetooth-based device tracker.

## Donations
If you appreciate the integration: [Buy me a Beer](https://www.paypal.com/paypalme/pieterverougstraete)

## Features

- **BLE Connectivity** — Works with native Bluetooth and BLE proxies(ESPhome, not Shelly!).
- Bike presence detection
- Battery level sensor
- Module battery sensor
- Lock state sensor
- Distance travelled sensor
- Power level sensor
- Estimated range sensor
- Light mode sensor
- Error code

## Estimated range

The estimated range sensor calculates an approximate remaining range in kilometers based on:

- battery percentage
- current power level
- region mode (`EU` or `US`)
- bike model

The values below are estimates for a full battery. The sensor scales them with the current battery level. For example, an S3 in EU mode on power level 2 uses `120 km` as the full-battery estimate, so at 50% battery the sensor reports about `60 km`.

| Model | Mode | Level 1 | Level 2 | Level 3 | Level 4 |
| --- | --- | ---: | ---: | ---: | ---: |
| S1 | EU | 90 km | 75 km | 60 km | 48 km |
| S1 | US | 80 km | 65 km | 53 km | 43 km |
| S2 | EU | 120 km | 100 km | 80 km | 65 km |
| S2 | US | 100 km | 90 km | 78 km | 65 km |
| S3 | EU | 145 km | 120 km | 95 km | 75 km |
| S3 | US | 120 km | 100 km | 85 km | 70 km |

Ranges depend on riding style, temperature, tire pressure, terrain, bike condition, wind, and rider weight, so this sensor should be treated as an estimate rather than an exact prediction.

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
