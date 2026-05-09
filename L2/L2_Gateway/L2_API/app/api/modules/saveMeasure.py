
import json
from time import time
from app.core.dbOperations.measurements_db import insert_measurement
from app.api.mqtt.publishMQTT import send_response

async def meas_register(data):
    sensorID = data.get("local_channel")
    raw = data.get("temp")
    calc_value = raw * 1.8 + 32  # Example conversion to Fahrenheit
    print(f"measureSensor: {sensorID} - raw: {raw} - calc: {calc_value}")

    # 1. Registrace / Aktualizace zařízení
    #meas = await db_insert_measurement(sensorID, status=0, raw_value=raw, calc_value=calc_value)
    status = 1 if raw is None else 0
    timestamp = int(time()*1000)
    await insert_measurement(
        timestamp=timestamp, 
        sensorID=sensorID, 
        raw_value=raw, 
        calc_value=calc_value,
        status=status
    )


async def db_insert_measurement(sensorID, status=0, raw_value=None, calc_value=None):
    timestamp = {int(time()*1000)}
    if raw_value is None:
        status = 1  # Chyba: chybí raw_value
    query = """
    INSERT INTO Measurements (timestamp, sensorID, status, raw_value, calc_value)
    VALUES (?, ?, ?, ?, ?)
    """
    return await db.fetch_one(query, (timestamp, sensorID, status,raw_value , calc_value))
