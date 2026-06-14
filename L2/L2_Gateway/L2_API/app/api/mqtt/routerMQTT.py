import json
from app.core.dbOperations.measurements_db import on_ack_received
from app.api.modules.saveMeasure import meas_register_batch, meas_register, meas_register_batch_session, meas_register_cont_session
from app.api.modules.deviceRegister import device_register


async def router(topic, payload):

    data = json.loads(payload)
    print(f"Received MQTT message on topic '{topic}': {data}")


    if topic == "l1/registration":
        await device_register(data)
        print(f"Device registration processed for MAC: {data.get('mac_address')}")

    if topic == "l1/test":
        await meas_register(data)
        print(f"test: {data.get('device_id')}")


    if topic.startswith("l1/measurement/cont/stream/"):
        await meas_register(data)
        print(f"Measurement {topic} for device ID: {data.get('device_id')}")

    if topic.startswith("l1/measurement/cont/batch/"):
        await meas_register_batch(data)
        print(f"Batch {topic} for device ID: {data.get('device_id')}")   

    if topic.startswith("l1/measurement/session/stream/"):
        await meas_register_cont_session(data)
        print(f"bude")

    if topic.startswith("l1/measurement/session/batch/"):
        await meas_register_batch_session(data)
        print(f"Batch session {topic} for device ID: {data.get('device_id')} with session name: {data.get('sessionName')}")




    if topic.startswith("l1/config_ack/"):
        # topic vypadá takto: "l1/config_ack/C0:49:EF:E6:3C:7C"
        mac = topic.split("/")[-1] # Vytáhne MAC adresu z konce stringu
        print(f"Received config ACK for MAC: {mac}")
        await on_ack_received(mac)