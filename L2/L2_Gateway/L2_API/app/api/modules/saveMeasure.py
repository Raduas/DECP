
import json
from time import time
from app.core.dbOperations.measurements_db import insert_measurement, insert_measurements_batch, insert_measurements_batch_session, insert_measurement_session
from app.api.mqtt.publishMQTT import send_response

async def meas_register(data):
    sensorID = data.get("local_channel")
    raw = data.get("temp")
    calc_value = raw * 1.8 + 32  # Example conversion to Fahrenheit
    print(f"measureSensor: {sensorID} - raw: {raw} - calc: {calc_value}")

    # 1. Registrace / Aktualizace zařízení
    status = 1 if raw is None else 0
    timestamp = int(time()*1000)
    await insert_measurement(
        timestamp=timestamp, 
        sensorID=sensorID, 
        raw_value=raw, 
        calc_value=calc_value,
        status=status
    )


async def meas_register_batch(data):
    sensorID = data.get("local_channel")
    measurements = data.get("measurements", [])
    rows = []
    timestamp = int(time() * 1000)

    for i, raw in enumerate(measurements):
        rows.append(
            (
                timestamp + i,
                sensorID,
                raw,
                raw * 1.8 + 32,
                0
            )
        )
    
    if rows:
        await insert_measurements_batch(rows)

async def meas_register_cont_session(data):
    sensorID = data.get("local_channel")
    raw = data.get("temp")
    calc_value = raw * 1.8 + 32  # Example conversion to Fahrenheit
    sessionName = data.get("sessionName")
    print(f"measureSensor: {sensorID} - raw: {raw} - calc: {calc_value} - session: {sessionName}")

    # 1. Registrace / Aktualizace zařízení
    status = 1 if raw is None else 0
    timestamp = int(time()*1000)
    await insert_measurement_session(
        timestamp=timestamp, 
        sensorID=sensorID, 
        sessionName=sessionName,
        raw_value=raw, 
        calc_value=calc_value,
        status=status
    )

async def meas_register_batch_session(data):
    sensorID = data.get("local_channel")
    sessionName = data.get("sessionName")
    measurements = data.get("measurements", [])
    rows = []
    timestamp = int(time() * 1000)
    
    for i, raw in enumerate(measurements):
        rows.append(
            (
                timestamp + i,
                sensorID,
                sessionName,
                raw,
                raw * 1.8 + 32,
                0
            )
        )
    
    if rows:
        await insert_measurements_batch_session(rows)
