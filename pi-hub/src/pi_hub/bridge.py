"""Poll the ESP32 sensor node over BLE and publish readings to MQTT."""

import asyncio
import logging

import aiomqtt

from pi_hub.mqtt import announce_online, make_client, publish_sample
from pi_hub.read_sensor import DEVICE_ADDRESS, read_sample

POLL_INTERVAL_S = 60
RETRY_DELAY_S = 10
RECONNECT_DELAY_S = 5

log = logging.getLogger(__name__)


async def poll_loop(client: aiomqtt.Client, address: str) -> None:
    """Read and publish on a schedule, until the MQTT connection breaks."""
    await announce_online(client)

    while True:
        try:
            sample = await read_sample(address)
        except Exception:
            # A BLE failure is expected now and then; it must not tear down
            # the MQTT session, so it is swallowed here rather than raised.
            log.exception("BLE read failed")
            await asyncio.sleep(RETRY_DELAY_S)
            continue

        if sample is None:
            log.warning("Device %s not in range", address)
            await asyncio.sleep(RETRY_DELAY_S)
            continue

        await publish_sample(client, sample)
        log.info(
            "temp=%.2fC humidity=%.2f%% pressure=%.1fhPa rssi=%ddBm",
            sample["temperature_c"],
            sample["humidity_pct"],
            sample["pressure_hpa"],
            sample["rssi_dbm"],
        )
        await asyncio.sleep(POLL_INTERVAL_S)


async def run(address: str) -> None:
    """Keep an MQTT session open, reconnecting if the broker goes away."""
    while True:
        try:
            async with make_client() as client:
                log.info("Connected to MQTT broker at %s", client._hostname)
                await poll_loop(client, address)
        except aiomqtt.MqttError:
            log.warning("MQTT connection lost, retrying in %ds", RECONNECT_DELAY_S)
            await asyncio.sleep(RECONNECT_DELAY_S)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    try:
        asyncio.run(run(DEVICE_ADDRESS))
    except KeyboardInterrupt:
        log.info("Stopped")


if __name__ == "__main__":
    main()