#!/usr/bin/env python3
"""List every BLE device the Pi can hear."""

import asyncio

from bleak import BleakScanner

SCAN_SECONDS = 10.0


async def main() -> None:
    print(f"Scanning for {SCAN_SECONDS:.0f} seconds...")

    # return_adv=True gives a dict: address -> (BLEDevice, AdvertisementData).
    # BLEDevice identifies the peer; AdvertisementData holds what the last
    # packet actually carried - RSSI, local name, advertised service UUIDs.
    found = await BleakScanner.discover(timeout=SCAN_SECONDS, return_adv=True)

    if not found:
        print("Nothing found.")
        return

    # RSSI is negative dBm; closer to zero means a stronger signal.
    ordered = sorted(found.values(), key=lambda pair: pair[1].rssi, reverse=True)

    print(f"\nFound {len(ordered)} device(s):\n")
    for device, adv in ordered:
        name = adv.local_name or "<no name>"
        print(f"{device.address}  {adv.rssi:>4} dBm  {name}")
        for uuid in adv.service_uuids:
            print(f"    service: {uuid}")


if __name__ == "__main__":
    asyncio.run(main())