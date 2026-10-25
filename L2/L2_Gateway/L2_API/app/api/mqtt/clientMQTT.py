import asyncio
import logging

from app.api.mqtt import routerMQTT
from asyncio_mqtt import Client, MqttError

logger = logging.getLogger(__name__)

TOPICS = [
    "l1/test",
    "l1/registration",
    "l1/config_ack/+",
    "l1/measurement/+",
    "l1/batch/+",
    "l1/measurement/+/+/+",
]
RECONNECT_DELAY_S = 5


async def mqtt_loop():
    # při výpadku brokeru se znovu připojí, jinak by task tiše skončil
    while True:
        try:
            async with Client("mqtt5", 1883) as client:
                for t in TOPICS:
                    await client.subscribe(t)
                print("MQTT connected, subscribed to:", TOPICS)

                async with client.unfiltered_messages() as messages:
                    async for msg in messages:
                        await routerMQTT.router(
                            msg.topic, msg.payload.decode(errors="replace")
                        )
        except MqttError as e:
            print(f"MQTT connection error: {e}; reconnecting in {RECONNECT_DELAY_S}s")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Unexpected MQTT loop error; reconnecting in %ds", RECONNECT_DELAY_S
            )
        await asyncio.sleep(RECONNECT_DELAY_S)
