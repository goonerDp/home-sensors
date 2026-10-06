"""Subscribe to the MQTT state topic and store every reading."""

import asyncio
import json
import logging
import signal
import sqlite3
import os

import aiomqtt

from pi_hub.db import connect, insert_reading
from pi_hub.mqtt import BROKER_HOST, BROKER_PORT, TOPIC_STATE

RECONNECT_DELAY_S = 5

log = logging.getLogger(__name__)


def handle_message(conn: sqlite3.Connection, payload: bytes) -> None:
    """Decode one MQTT payload and store it, skipping anything malformed."""
    try:
        sample = json.loads(payload)
    except json.JSONDecodeError:
        log.warning("Ignoring non-JSON payload: %r", payload[:100])
        return

    try:
        insert_reading(conn, sample)
    except (sqlite3.Error, KeyError):
        # A bad row must not kill the recorder: the publisher may have
        # changed its payload, and we would rather log and keep running.
        log.exception("Failed to store sample")
        return

    log.debug(
        "Stored sample at %s", sample.get("timestamp")
    )


async def listen(conn: sqlite3.Connection, stop: asyncio.Event) -> None:
    """Consume the state topic until the connection drops or we are stopped."""
    async with aiomqtt.Client(
        hostname=BROKER_HOST, port=BROKER_PORT, identifier="pi-hub-recorder"
    ) as client:
        # A retained message arrives immediately on subscribe, so the first
        # row after a restart may duplicate the last one already stored.
        await client.subscribe(TOPIC_STATE, qos=1)
        log.info("Subscribed to %s", TOPIC_STATE)

        async for message in client.messages:
            handle_message(conn, message.payload)
            if stop.is_set():
                return


async def run(stop: asyncio.Event) -> None:
    conn = connect()
    try:
        while not stop.is_set():
            try:
                await listen(conn, stop)
            except aiomqtt.MqttError:
                log.warning("MQTT connection lost, retrying in %ds", RECONNECT_DELAY_S)
                try:
                    await asyncio.wait_for(stop.wait(), RECONNECT_DELAY_S)
                    return
                except TimeoutError:
                    continue
    finally:
        conn.close()


async def amain() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await run(stop)
    log.info("Stopped")


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    asyncio.run(amain())


if __name__ == "__main__":
    main()