# ESP32 Sensor Node

BME280 outdoor node on ESP32 + MicroPython. Reads temperature, humidity
and pressure and exposes them as a BLE peripheral.

WiFi is never started: it shares the antenna and the 2.4 GHz radio with
BLE, and draws far more current.

## Files

| File              | What it is                                      |
| ----------------- | ----------------------------------------------- |
| `main.py`         | Entry point: reads the sensor, updates BLE      |
| `ble_sensor.py`   | BLE peripheral, GATT table, advertising         |
| `bme280_float.py` | Sensor driver (third party)                     |
| `deploy.sh`       | Copies all of the above to the board and resets |

## GATT

Advertised as `esp32-sensor`, standard Environmental Sensing service
`0x181A`:

| Characteristic | UUID     | Wire format     |
| -------------- | -------- | --------------- |
| Temperature    | `0x2A6E` | sint16, 0.01 °C |
| Humidity       | `0x2A6F` | uint16, 0.01 %  |
| Pressure       | `0x2A6D` | uint32, 0.1 Pa  |

Standard SIG characteristics, so any generic BLE app on a phone reads
the node without knowing anything about this project.

Readings are refreshed every 10 s and pushed to connected subscribers
via notify.

## Wiring

BME280 over I2C: `SCL` to GPIO22, `SDA` to GPIO21.

## Deploy

    ./deploy.sh

Finds the board, copies every file, resets. Runs from anywhere.

Files are only ever copied, never removed. A module dropped from this
repo stays in flash until deleted by hand:

    mpremote connect /dev/cu.usbserial-XXX fs ls
    mpremote connect /dev/cu.usbserial-XXX fs rm :stale_module.py

## Common commands

Find the board's port:

    ls /dev/cu.*

Open the REPL to watch the running program:

    mpremote connect /dev/cu.usbserial-XXX repl

Exit with `Ctrl-]`. `Ctrl-C` then `Ctrl-D` restarts `main.py` from the
top, which is the only way to see the MAC address it prints at startup.

Run a file without installing it, leaving the board's own `main.py`
untouched:

    mpremote connect /dev/cu.usbserial-XXX run some_file.py

Erase and reflash MicroPython firmware:

    esptool --port /dev/cu.usbserial-XXX erase-flash
    esptool --port /dev/cu.usbserial-XXX write-flash -z 0x1000 <firmware>.bin

Only one session can hold the serial port. Close the REPL (`Ctrl-]`)
before any `fs` command or `deploy.sh`, or they fail with
`TransportError: could not enter raw repl`.

## Diagnostics

The measurement loop catches read failures instead of dying on them, and
appends each one to `errors.log` in flash, with `time.ticks_ms()` since
boot as the only timestamp available on a board with no clock. A `boot`
line is written at startup, so an unexpected one marks a reset.

Serial output is useless once the node runs on battery, which is why
this goes to a file.

    mpremote connect /dev/cu.usbserial-XXX fs cat :errors.log
    mpremote connect /dev/cu.usbserial-XXX fs rm :errors.log

The file is truncated past 8 KB.
