"""ESP32 outdoor sensor node.

Reads a BME280 over I2C and publishes the values over BLE GATT.

WiFi is intentionally never started here: WiFi and BLE share one antenna and
one 2.4 GHz radio on the ESP32, and WiFi draws far more current. Both were the
reason for moving this node off WiFi in the first place.
"""

import time

import bluetooth
from machine import Pin, I2C

import bme280_float as bme280
from ble_sensor import BLESensor

DEVICE_NAME = "esp32-sensor"
READ_INTERVAL_S = 10


def init_sensor():
    """Start the I2C bus and the BME280 sensor."""
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    return bme280.BME280(i2c=i2c)


def main():
    bme = init_sensor()
    ble = BLESensor(bluetooth.BLE(), name=DEVICE_NAME)

    while True:
        # read_compensated_data() returns floats: C, Pa, %RH.
        # The .values property returns formatted strings instead - not usable here.
        temp_c, pressure_pa, humidity_pct = bme.read_compensated_data()

        ble.update(temp_c, pressure_pa, humidity_pct)

        print(
            "temp={:.2f}C  pressure={:.1f}hPa  humidity={:.2f}%".format(
                temp_c, pressure_pa / 100, humidity_pct
            )
        )
        time.sleep(READ_INTERVAL_S)


main()