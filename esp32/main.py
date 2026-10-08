"""ESP32 outdoor sensor node.

Reads a BME280 over I2C and publishes the values over BLE GATT.

WiFi is intentionally never started: WiFi and BLE share one antenna and
one 2.4 GHz radio on the ESP32, and WiFi draws far more current. Both were the
reason for moving this node off WiFi in the first place.
"""

import io
import sys
import time

import bluetooth
from machine import I2C, Pin

import bme280_float as bme280
from ble_sensor import BLESensor

DEVICE_NAME = "esp32-sensor"
READ_INTERVAL_S = 10

ERROR_LOG = "errors.log"
ERROR_LOG_MAX_BYTES = 8192


def log_error(message):
    """Append one line to a log file in flash, so a failure that happens on
    battery can still be read back over USB days later.

    Prints go to the serial console, which nobody is watching when the node is
    deployed. Once the file grows past a few KB, writing stops rather than
    starting over: the first failures are the interesting ones, and a failure
    that repeats every loop would otherwise wipe them within minutes. Delete
    the file over USB to start a fresh log.
    """
    line = "{} {}\n".format(time.ticks_ms(), message)
    print(line, end="")
    try:
        size = 0
        try:
            with open(ERROR_LOG, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
        except OSError:
            pass

        if size > ERROR_LOG_MAX_BYTES:
            return
        with open(ERROR_LOG, "a") as f:
            f.write(line)
    except OSError as exc:
        # Logging must never be the thing that takes the node down.
        print("could not write log:", exc)


def format_exception(exc):
    """Render a full traceback into a string.

    MicroPython has no traceback module; sys.print_exception writes to a
    file-like object instead, so it gets an in-memory buffer.
    """
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    return buf.getvalue().rstrip()


def init_sensor():
    """Start the I2C bus and the BME280 sensor."""
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    return bme280.BME280(i2c=i2c)


def main():
    bme = init_sensor()
    ble = BLESensor(bluetooth.BLE(), name=DEVICE_NAME)
    log_error("boot")

    while True:
        try:
            # read_compensated_data() returns floats: C, Pa, %RH.
            # The .values property returns formatted strings instead.
            temp_c, pressure_pa, humidity_pct = bme.read_compensated_data()
            ble.update(temp_c, pressure_pa, humidity_pct)
            print(
                "temp={:.2f}C  pressure={:.1f}hPa  humidity={:.2f}%".format(
                    temp_c, pressure_pa / 100, humidity_pct
                )
            )
        except Exception as exc:
            # Carry on, whatever failed. An exception anywhere in this loop
            # ends main() for good while the BLE stack keeps serving the last
            # values it had, which looks like a working node for hours.
            #
            # The full traceback says which call failed: one of the several
            # I2C calls inside the sensor read, or the BLE write.
            log_error("loop failed:\n" + format_exception(exc))

        time.sleep(READ_INTERVAL_S)


main()