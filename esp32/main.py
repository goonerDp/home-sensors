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
import machine
from machine import I2C, Pin

import bme280_float as bme280
from ble_sensor import BLESensor

DEVICE_NAME = "esp32-sensor"
READ_INTERVAL_S = 10

ERROR_LOG = "errors.log"
ERROR_LOG_MAX_BYTES = 8192

# machine.reset_cause() returns a bare int; these are the names it can match.
RESET_CAUSES = (
    "PWRON_RESET",
    "HARD_RESET",
    "WDT_RESET",
    "DEEPSLEEP_RESET",
    "SOFT_RESET",
)


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


def reset_cause_name():
    """Why this boot happened, as a name rather than a bare number.

    Tells a restart nobody asked for (watchdog, crash) apart from someone
    plugging the board in.
    """
    cause = machine.reset_cause()
    for name in RESET_CAUSES:
        if getattr(machine, name, None) == cause:
            return name
    return str(cause)


def main():
    # Logged before anything else, so a boot that dies during setup still
    # leaves a line behind.
    log_error("boot " + reset_cause_name())
    bme = init_sensor()
    ble = BLESensor(bluetooth.BLE(), name=DEVICE_NAME)

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