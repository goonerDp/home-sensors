# pi-hub

BLE central running on the Raspberry Pi 5. Polls the ESP32 outdoor node
over GATT and republishes the readings to the local MQTT broker.

## Requirements

System packages, outside of uv:

    sudo apt install -y bluez mosquitto mosquitto-clients

## Setup

    uv sync

## Usage

    uv run python -m pi_hub.scan           # list nearby BLE devices
    uv run python -m pi_hub.read_sensor    # read the node once
    uv run python -m pi_hub.bridge         # poll and publish continuously

## MQTT

| Topic                 | Retained | Payload              |
| --------------------- | -------- | -------------------- |
| `home/outdoor/state`  | yes      | JSON, see below      |
| `home/outdoor/status` | yes      | `online` / `offline` |

`state` is published once per poll interval (60 s):

```json
{
  "temperature_c": 22.98,
  "humidity_pct": 37.7,
  "pressure_hpa": 1012.5,
  "rssi_dbm": -57,
  "timestamp": "2026-10-03T17:47:10+03:00"
}
```

Values are rounded to the BME280's stated accuracy (±0.5 °C, ±3 %RH,
±1 hPa). `rssi_dbm` is measured by the Pi, from the advertisement that
located the node; it varies by 10 dB or more between reads even when
nothing moves, so judge the link by a trend, not a single sample.
`timestamp` is set by the Pi on arrival — the ESP32 has no clock.

`status` is backed by an MQTT last will, so the broker publishes
`offline` by itself if the bridge dies. A clean shutdown publishes it
explicitly. **Treat data as stale whenever `status` is not `online`** —
`state` is retained and will otherwise keep serving the last reading
indefinitely.

Inspect the live stream with:

    mosquitto_sub -h localhost -t 'home/#' -v

## Node

Address `48:9D:31:04:7F:1E`, advertised as `esp32-sensor`. GATT contract
is documented in `../esp32/README.md`.

## Running as a service

    sudo cp systemd/pi-hub-bridge.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now pi-hub-bridge
    journalctl -u pi-hub-bridge -f

Paths and `User=` in the unit assume `gooner_dp` and
`~/projects/home-sensors`. Edit both if either differs.