# pi-hub

BLE central running on the Raspberry Pi 5. Reads BME280 values from the
ESP32 outdoor node over GATT.

## Setup

    uv sync

## Usage

    uv run python -m pi_hub.scan           # list nearby BLE devices
    uv run python -m pi_hub.read_sensor    # read the node once
    uv run python -m pi_hub.bridge         # poll the node continuously

## Node

Address `48:9D:31:04:7F:1E`, advertised as `esp32-sensor`, exposing the
standard Environmental Sensing service (0x181A).

## Running as a service

    sudo cp systemd/pi-hub-bridge.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now pi-hub-bridge

Paths and `User=` in the unit assume `gooner_dp` and
`~/projects/home-sensors`. Edit both if either differs.

    journalctl -u pi-hub-bridge -f