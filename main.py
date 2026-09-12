import time
import network
from machine import Pin, I2C
import bme280_float as bme280
from config import WIFI_SSID, WIFI_PASSWORD

# This function connects the board to WiFi.
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        # Wait up to 30 seconds for the connection.
        timeout = 30
        while not wlan.isconnected() and timeout > 0:
            print("Status:", wlan.status())
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
    else:
        print("WiFi connection failed. Final status:", wlan.status())
    return wlan.isconnected()

# This function starts the I2C bus and the BME280 sensor.
def init_sensor():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    return bme280.BME280(i2c=i2c)

# This is the main program.
def main():
    connect_wifi()
    bme = init_sensor()

    # Read the sensor every 10 seconds. Do this forever.
    while True:
        temp, pressure, humidity = bme.values
        print("Temp:", temp, "Pressure:", pressure, "Humidity:", humidity)
        time.sleep(10)

main()
