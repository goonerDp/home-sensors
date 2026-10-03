"""Connect to the ESP32 node and read one BME280 sample over BLE GATT."""

import asyncio
import struct
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.uuids import normalize_uuid_16

DEVICE_ADDRESS = "48:9D:31:04:7F:1E"
SCAN_TIMEOUT = 10.0

# Standard SIG characteristics, matching what the ESP32 registers.
TEMP_UUID = normalize_uuid_16(0x2A6E)   # sint16, 0.01 C
HUMID_UUID = normalize_uuid_16(0x2A6F)  # uint16, 0.01 %
PRESS_UUID = normalize_uuid_16(0x2A6D)  # uint32, 0.1 Pa


async def find_device(
    address: str, timeout: float = SCAN_TIMEOUT
) -> tuple[BLEDevice, AdvertisementData] | None:
    """Scan until the given address is seen, then stop.

    Returns the advertisement alongside the device because RSSI belongs to
    a single received packet, not to the device itself.
    """
    loop = asyncio.get_running_loop()
    found = loop.create_future()
    wanted = address.upper()

    def on_detect(device: BLEDevice, adv: AdvertisementData) -> None:
        # Fires for every advertising packet the adapter receives.
        if device.address.upper() == wanted and not found.done():
            found.set_result((device, adv))

    async with BleakScanner(detection_callback=on_detect):
        try:
            return await asyncio.wait_for(found, timeout)
        except TimeoutError:
            return None


async def read_sample(address: str) -> dict | None:
    """Find the device, connect, read all three values, disconnect."""
    result = await find_device(address)
    if result is None:
        return None

    device, adv = result

    async with BleakClient(device) as client:
        raw_temp = await client.read_gatt_char(TEMP_UUID)
        raw_humid = await client.read_gatt_char(HUMID_UUID)
        raw_press = await client.read_gatt_char(PRESS_UUID)

    # "<h" signed 16-bit, "<H" unsigned 16-bit, "<I" unsigned 32-bit,
    # all little-endian - the wire format each SIG characteristic defines.
    return {
        "temperature_c": struct.unpack("<h", raw_temp)[0] / 100,
        "humidity_pct": struct.unpack("<H", raw_humid)[0] / 100,
        "pressure_hpa": struct.unpack("<I", raw_press)[0] / 1000,
        "rssi_dbm": adv.rssi,
    }


async def main() -> None:
    sample = await read_sample(DEVICE_ADDRESS)
    if sample is None:
        print(f"Device {DEVICE_ADDRESS} not found.")
        return

    # The Pi has a real clock; the ESP32 does not. Timestamp on arrival.
    print(
        "{}  temp={:.2f}C  humidity={:.2f}%  pressure={:.1f}hPa  rssi={}dBm".format(
            datetime.now().isoformat(timespec="seconds"),
            sample["temperature_c"],
            sample["humidity_pct"],
            sample["pressure_hpa"],
            sample["rssi_dbm"],
        )
    )


if __name__ == "__main__":
    asyncio.run(main())