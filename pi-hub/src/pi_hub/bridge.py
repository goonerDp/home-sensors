"""Poll the ESP32 sensor node over BLE at a fixed interval."""

import asyncio
import logging

from pi_hub.read_sensor import DEVICE_ADDRESS, read_sample

POLL_INTERVAL_S = 60
RETRY_DELAY_S = 10

log = logging.getLogger(__name__)


async def poll_forever(address: str) -> None:
    """Read the sensor on a schedule, surviving transient BLE failures."""
    while True:
        try:
            sample = await read_sample(address)
        except Exception:
            # exception() logs the full traceback, so a failure mode that
            # repeats can be identified from the log alone.
            log.exception("Read failed")
            await asyncio.sleep(RETRY_DELAY_S)
            continue

        if sample is None:
            log.warning("Device %s not in range", address)
            await asyncio.sleep(RETRY_DELAY_S)
            continue

        log.info(
            "temp=%.2fC humidity=%.2f%% pressure=%.1fhPa rssi=%ddBm",
            sample["temperature_c"],
            sample["humidity_pct"],
            sample["pressure_hpa"],
            sample["rssi_dbm"],
        )
        await asyncio.sleep(POLL_INTERVAL_S)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    try:
        asyncio.run(poll_forever(DEVICE_ADDRESS))
    except KeyboardInterrupt:
        log.info("Stopped")


if __name__ == "__main__":
    main()