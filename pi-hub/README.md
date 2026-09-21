# pi-hub

BLE central running on the Raspberry Pi 5. Connects to the ESP32
outdoor node, reads BME280 values over GATT, and (later) republishes
them to MQTT.

## Setup

    uv sync

## Usage

    uv run python -m pi_hub.scan    # list nearby BLE devices