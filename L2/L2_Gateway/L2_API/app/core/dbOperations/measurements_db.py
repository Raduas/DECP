from time import time

from app.core import db as db_module

# =========================
# MEASUREMENT OPERACE
# =========================

async def insert_measurement(
    timestamp,
    sensorID,
    raw_value,
    calc_value=None,
    status=0
):

    await db_module.db.execute("""
    INSERT INTO Measurements (
        timestamp,
        sensorID,
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (
        timestamp,
        sensorID,
        raw_value,
        calc_value,
        status
    ))
    await db_module.db.commit()

# batch insert (doporučeno)

async def insert_measurements_batch(data):

    await db_module.db.executemany("""
    INSERT INTO Measurements (
        timestamp,
        sensorID,
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """, data)

    await db_module.db.commit()


async def insert_measurement_session(
    timestamp,
    sensorID,
    sessionName,
    raw_value,
    calc_value=None,
    status=0
):

    await db_module.db.execute("""
    INSERT INTO Session_Measurements (
        timestamp,
        sensorID,
        SessionName,
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        timestamp,
        sensorID,
        sessionName,
        raw_value,
        calc_value,
        status
    ))
    await db_module.db.commit()


async def insert_measurements_batch_session(data):

    await db_module.db.executemany("""
    INSERT INTO Session_Measurements (
        timestamp,
        sensorID,
        SessionName,                                
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, data)

    await db_module.db.commit()

async def on_ack_received(mac):
    await db_module.db.execute(
        "UPDATE configs SET isDirty = 0, lastSync = ? WHERE deviceID = (SELECT id FROM DeviceL1 WHERE mac_address = ?)",
        (int(time()), mac)
    )
    await db_module.db.commit()
    print(f"Konfigurace pro {mac} byla úspěšně synchronizována.")

async def get_measurements_by_sensor(sensorName, limit=None):
    print(f"SensorName: {sensorName}")
    cursor = await db_module.db.execute("""
    SELECT timestamp, raw_value, calc_value, Null as SessionName, status
    FROM Measurements
    WHERE SensorID = (SELECT sensorID FROM Sensors WHERE sensorName = ?)                                    
        UNION
    SELECT timestamp, raw_value, calc_value, SessionName, status
    FROM Session_Measurements
    WHERE SensorID = (SELECT sensorID FROM Sensors WHERE sensorName = ?)
    ORDER BY timestamp DESC
    LIMIT ?
    """, (sensorName, sensorName, limit))
    rows = await cursor.fetchall()
    await cursor.close()
    return rows

async def get_all_sessions():
    cursor = await db_module.db.execute("""
    SELECT DISTINCT SessionName
    FROM Session_Measurements
                                        
    """)
    rows = await cursor.fetchall()
    await cursor.close()
    return rows


async def get_measurements_by_session(sessionName, limit=None):
    
    print(f"SessionName: {sessionName}")
    cursor = await db_module.db.execute("""
    SELECT timestamp, raw_value, calc_value, SessionName, status
    FROM Session_Measurements
    WHERE SessionName = ?
    ORDER BY timestamp DESC
    LIMIT ?
    """, (sessionName, limit))
    rows = await cursor.fetchall()
    await cursor.close()
    return rows

async def get_measurements_by_device(deviceName, limit=None):
    print(f"DeviceName: {deviceName}")
    cursor = await db_module.db.execute("""
    SELECT timestamp, raw_value, calc_value, Null as SessionName, status
    FROM Measurements
    WHERE SensorID IN
        (SELECT sensorID
        FROM Sensors
        WHERE deviceID IN (SELECT id FROM DeviceL1 WHERE deviceName = ?))
    UNION
    SELECT timestamp, raw_value, calc_value, SessionName, status
    FROM Session_Measurements
    WHERE SensorID IN
        (SELECT sensorID
        FROM Sensors
        WHERE deviceID IN (SELECT id FROM DeviceL1 WHERE deviceName = ?))
    ORDER BY timestamp DESC
    LIMIT ?
    """, (deviceName, deviceName, limit))
    rows = await cursor.fetchall()
    await cursor.close()
    return rows