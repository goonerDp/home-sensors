# home-sensors

Home environment monitoring.

    BME280 --I2C--> ESP32 --BLE--> Raspberry Pi 5 --MQTT--> subscribers

## Components

| Directory | Runs on                 | What it is                          |
| --------- | ----------------------- | ----------------------------------- |
| `esp32/`  | ESP32, MicroPython      | Outdoor node: BME280 over BLE GATT  |
| `pi-hub/` | Raspberry Pi 5, CPython | BLE central, publishes to MQTT      |

Each has its own README. The two sides share no code — they talk over
standard Bluetooth SIG characteristics — and are deployed separately.
