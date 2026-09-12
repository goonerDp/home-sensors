# ESP32 Sensor Node

BME280 sensor node on ESP32 + MicroPython. Reads temperature, humidity, and pressure, connects to WiFi.

## Setup

Create `config.py` (not tracked in git) with:

```python
WIFI_SSID = "your_network"
WIFI_PASSWORD = "your_password"
```

## Common commands

Find the board's port:

```bash
ls /dev/cu.*
```

Copy files to the board:

```bash
mpremote connect /dev/cu.usbserial-XXX fs cp main.py :main.py
mpremote connect /dev/cu.usbserial-XXX fs cp config.py :config.py
mpremote connect /dev/cu.usbserial-XXX fs cp bme280_float.py :bme280_float.py
```

List files on the board:

```bash
mpremote connect /dev/cu.usbserial-XXX fs ls
```

Open REPL (interactive console):

```bash
mpremote connect /dev/cu.usbserial-XXX
```

Exit REPL: `Ctrl-]`

Erase and reflash MicroPython firmware:

```bash
esptool --port /dev/cu.usbserial-XXX erase-flash
esptool --port /dev/cu.usbserial-XXX write-flash -z 0x1000 <firmware>.bin
```
