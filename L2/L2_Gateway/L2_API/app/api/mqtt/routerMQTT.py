import json
import logging

from app.api.modules.deviceRegister import device_register
from app.api.modules.saveMeasure import (
    meas_register,
    meas_register_batch,
    meas_register_batch_session,
    meas_register_cont_session,
)
from app.core.dbOperations.measurements_db import on_ack_received

logger = logging.getLogger(__name__)

async def router(topic, payload):
    # jedna vadná zpráva nesmí shodit celou MQTT smyčku
    try:
        await _dispatch(topic, payload)
    except Exception:
        logger.exception("Error processing MQTT message on %r, payload: %r", topic, payload)


async def _dispatch(topic, payload):

    data = json.loads(payload)
    print(f"Received MQTT message on topic '{topic}': {data}")

    # topicy měření končí MAC adresou: "l1/measurement/cont/stream/C0:49:EF:E6:3C:7C"
    mac = topic.split("/")[-1]

    if topic == "l1/registration":
        await device_register(data)
        print(f"Device registration processed for MAC: {data.get('mac')}")

    elif topic == "l1/test":
        # bez MAC v topicu nelze dohledat sensorID -> neukládá se
        print(f"test: {data}")

    elif topic.startswith("l1/measurement/cont/stream/"):
        await meas_register(mac, data)
        print(f"Measurement {topic} for device ID: {data.get('device_id')}")

    elif topic.startswith("l1/measurement/cont/batch/"):
        await meas_register_batch(mac, data)
        print(f"Batch {topic} for device ID: {data.get('device_id')}")

    elif topic.startswith("l1/measurement/session/stream/"):
        await meas_register_cont_session(mac, data)
        print(f"Session measurement {topic} with session name: {data.get('sessionName')}")

    elif topic.startswith("l1/measurement/session/batch/"):
        await meas_register_batch_session(mac, data)
        print(f"Batch session {topic} for device ID: {data.get('device_id')} with session name: {data.get('sessionName')}")

    elif topic.startswith("l1/config_ack/"):
        # topic vypadá takto: "l1/config_ack/C0:49:EF:E6:3C:7C"
        print(f"Received config ACK for MAC: {mac}")
        await on_ack_received(mac)
