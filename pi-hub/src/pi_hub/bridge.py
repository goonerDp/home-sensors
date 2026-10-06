"""Poll the ESP32 sensor node over BLE and publish readings to MQTT."""

import asyncio
import logging
import signal
import os

import aiomqtt

from pi_hub.mqtt import (
    BROKER_HOST,
    announce_offline,
    announce_online,
    make_client,
    publish_sample,
)
from pi_hub.read_sensor import DEVICE_ADDRESS, read_sample

POLL_INTERVAL_S = 60
RETRY_DELAY_S = 10
RECONNECT_DELAY_S = 5

log = logging.getLogger(__name__)


async def wait_or_stop(stop: asyncio.Event, delay: float) -> bool:
    """Sleep for 'delay', or return early if a shutdown was requested.

    Returns True when the wait was cut short by the stop signal, so callers
    can react immediately instead of finishing a full poll interval first.
    """
    try:
        await asyncio.wait_for(stop.wait(), timeout=delay)
        return True
    except TimeoutError:
        return False


async def poll_loop(client: aiomqtt.Client, address: str, stop: asyncio.Event) -> None:
    """Read and publish on a schedule, until stopped or MQTT breaks."""
    await announce_online(client)

    while not stop.is_set():
        try:
            sample = await read_sample(address)
        except Exception:
            # A BLE failure is expected now and then; it must not tear down
            # the MQTT session, so it is swallowed here rather than raised.
            log.exception("BLE read failed")
            if await wait_or_stop(stop, RETRY_DELAY_S):
                return
            continue

        if sample is None:
            log.warning("Device %s not in range", address)
            if await wait_or_stop(stop, RETRY_DELAY_S):
                return
            continue

        await publish_sample(client, sample)
        log.debug(
            "temp=%.2fC humidity=%.1f%% pressure=%.1fhPa rssi=%ddBm",
            sample["temperature_c"],
            sample["humidity_pct"],
            sample["pressure_hpa"],
            sample["rssi_dbm"],
        )
        if await wait_or_stop(stop, POLL_INTERVAL_S):
            return


async def run(address: str, stop: asyncio.Event) -> None:
    """Keep an MQTT session open, reconnecting if the broker goes away."""
    while not stop.is_set():
        try:
            async with make_client() as client:
                log.info("Connected to MQTT broker at %s", BROKER_HOST)
                await poll_loop(client, address, stop)
                # Only reached on a clean shutdown: overwrite the retained
                # status so subscribers are not left thinking we are alive.
                await announce_offline(client)
        except aiomqtt.MqttError:
            log.warning("MQTT connection lost, retrying in %ds", RECONNECT_DELAY_S)
            if await wait_or_stop(stop, RECONNECT_DELAY_S):
                return


async def amain() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    # Ctrl+C sends SIGINT, 'systemctl stop' sends SIGTERM. Both should end
    # the same way, so neither is left to the default handler.
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await run(DEVICE_ADDRESS, stop)
    log.info("Stopped")


def main() -> None:
    logging.basicConfig(
        # LOG_LEVEL=DEBUG turns on per-sample logging without a code change.
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    asyncio.run(amain())


if __name__ == "__main__":
    main()