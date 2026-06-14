from asyncio_mqtt import Client
import asyncio
from app.api.mqtt import routerMQTT

TOPICS = ["l1/test", "l1/registration", "l1/config_ack/+", "l1/measurement/+", "l1/batch/+","l1/measurement/+/+/+"]



async def mqtt_loop():

    async with Client("mqtt5", 1883) as client:
        for t in TOPICS:
            await client.subscribe(t)

        async with client.unfiltered_messages() as messages:
            async for msg in messages:
                await routerMQTT.router(msg.topic, msg.payload.decode())
                

