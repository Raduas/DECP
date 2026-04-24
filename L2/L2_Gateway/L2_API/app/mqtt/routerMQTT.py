import json
from app.api.modules.saveMeasure import meas_register
from app.api.modules.deviceRegister import device_register


async def router(topic, payload):

    data = json.loads(payload)
    print(f"Received MQTT message on topic '{topic}': {data}")
    if topic == "l1/registration":
        await device_register(data)
        print(f"Device registration processed for MAC: {data.get('mac_address')}")

    if topic == "l1/test":
        await meas_register(data)
        print(f"Measurement registration processed for device ID: {data.get('device_id')}")