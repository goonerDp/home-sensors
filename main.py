import time
import network
import socket
from machine import Pin, I2C
import bme280_float as bme280
from config import WIFI_SSID, WIFI_PASSWORD, MAC_IP, MAC_PORT

# This function sends sensor data to the Mac.
# It sends the data as part of the URL (a GET request).
def send_data(mac_ip, mac_port, temp, pressure, humidity, wifi_rssi):
    try:
        path = "/data?temp={}&pressure={}&humidity={}&wifi_rssi={}".format(temp, pressure, humidity, wifi_rssi)
        addr = socket.getaddrinfo(mac_ip, mac_port)[0][-1]
        s = socket.socket()
        s.connect(addr)
        request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(path, mac_ip)
        s.send(request.encode())
        s.close()
        print("Data sent.")
    except Exception as e:
        print("Send failed:", e)

def get_wifi_rssi():
    wlan = network.WLAN(network.STA_IF)
    
    if wlan.isconnected():
        return wlan.status('rssi')  # value in dBm, -45
    return None

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
        wifi_rssi = get_wifi_rssi()
        print("Temp:", temp, "Pressure:", pressure, "Humidity:", humidity, "Wifi rssi:", wifi_rssi)
        send_data(MAC_IP, MAC_PORT, temp, pressure, humidity, wifi_rssi)
        time.sleep(10)

main()
