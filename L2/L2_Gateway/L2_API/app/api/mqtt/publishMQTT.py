
from asyncio_mqtt import Client


async def send_response(topic, payload):
    async with Client("mqtt5", 1883) as client:
        await client.publish(topic, payload) # Zkuste QoS 1
        print(f"Published to {topic} --:-- {payload}")