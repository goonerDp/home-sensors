"""Publish sensor samples to the local MQTT broker."""

import json
import logging
from datetime import datetime, timezone

import aiomqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883

TOPIC_STATE = "home/outdoor/state"
TOPIC_STATUS = "home/outdoor/status"

STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"

log = logging.getLogger(__name__)

# The broker publishes this on our behalf if the connection drops without a
# clean disconnect, so subscribers can tell stale data from live data.
WILL = aiomqtt.Will(
    topic=TOPIC_STATUS,
    payload=STATUS_OFFLINE,
    qos=1,
    retain=True,
)


def make_client() -> aiomqtt.Client:
    """Build a client. The connection itself is opened by 'async with'."""
    return aiomqtt.Client(
        hostname=BROKER_HOST,
        port=BROKER_PORT,
        identifier="pi-hub-bridge",
        will=WILL,
    )


async def announce_online(client: aiomqtt.Client) -> None:
    """Overwrite whatever the will left behind on the previous run."""
    await client.publish(TOPIC_STATUS, STATUS_ONLINE, qos=1, retain=True)

async def announce_offline(client: aiomqtt.Client) -> None:
    """Publish the same payload the will would have, on a clean shutdown."""
    await client.publish(TOPIC_STATUS, STATUS_OFFLINE, qos=1, retain=True)

async def publish_sample(client: aiomqtt.Client, sample: dict) -> None:
    # Copy before adding the timestamp: the caller's dict stays untouched.
    payload = dict(sample)
    payload["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # retain=True so a subscriber that connects later gets the last reading
    # immediately instead of waiting a full poll interval for the next one.
    await client.publish(TOPIC_STATE, json.dumps(payload), qos=1, retain=True)