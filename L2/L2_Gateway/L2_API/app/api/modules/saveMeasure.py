from time import time

from app.core.dbOperations.measurements_db import (
    insert_measurement,
    insert_measurement_session,
    insert_measurements_batch,
    insert_measurements_batch_session,
)
from app.core.dbOperations.sensors_db import get_sensor_id


def _calc(raw):
    # None = chyba čtení na L1 (např. NaN z odpojeného termočlánku)
    if raw is None:
        return None, 1
    return raw * 1.8 + 32, 0  # Example conversion to Fahrenheit


async def _resolve_sensor(mac, data):
    # local_channel je číslo kanálu v rámci zařízení -> převod na globální sensorID
    local_channel = data.get("local_channel")
    if local_channel is None:
        print(f"Missing local_channel from {mac}: {data}")
        return None
    sensorID = await get_sensor_id(mac, local_channel)
    if sensorID is None:
        print(f"Unknown sensor: mac={mac}, local_channel={local_channel}")
    return sensorID


async def meas_register(mac, data):
    sensorID = await _resolve_sensor(mac, data)
    if sensorID is None:
        return
    raw = data.get("temp")
    calc_value, status = _calc(raw)
    print(f"measureSensor: {sensorID} - raw: {raw} - calc: {calc_value}")

    timestamp = int(time() * 1000)
    await insert_measurement(
        timestamp=timestamp,
        sensorID=sensorID,
        raw_value=raw,
        calc_value=calc_value,
        status=status,
    )


async def meas_register_batch(mac, data):
    sensorID = await _resolve_sensor(mac, data)
    if sensorID is None:
        return
    measurements = data.get("measurements", [])
    rows = []
    timestamp = int(time() * 1000)

    for i, raw in enumerate(measurements):
        calc_value, status = _calc(raw)
        rows.append((timestamp + i, sensorID, raw, calc_value, status))

    if rows:
        await insert_measurements_batch(rows)


async def meas_register_cont_session(mac, data):
    sensorID = await _resolve_sensor(mac, data)
    if sensorID is None:
        return
    raw = data.get("temp")
    calc_value, status = _calc(raw)
    sessionName = data.get("sessionName")
    print(
        f"measureSensor: {sensorID} - raw: {raw} - calc: {calc_value} - session: {sessionName}"
    )

    timestamp = int(time() * 1000)
    await insert_measurement_session(
        timestamp=timestamp,
        sensorID=sensorID,
        sessionName=sessionName,
        raw_value=raw,
        calc_value=calc_value,
        status=status,
    )


async def meas_register_batch_session(mac, data):
    sensorID = await _resolve_sensor(mac, data)
    if sensorID is None:
        return
    sessionName = data.get("sessionName")
    measurements = data.get("measurements", [])
    rows = []
    timestamp = int(time() * 1000)

    for i, raw in enumerate(measurements):
        calc_value, status = _calc(raw)
        rows.append((timestamp + i, sensorID, sessionName, raw, calc_value, status))

    if rows:
        await insert_measurements_batch_session(rows)
