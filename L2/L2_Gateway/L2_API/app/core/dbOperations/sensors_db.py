from app.core import db as db_module

# =========================
# SENSOR OPERACE
# =========================

async def insert_sensor(
    deviceID,
    #local_channel,
    sensorName=None,
    conversion_rule="NONE",
    param_a=0.0,
    param_b=0.0,
    param_c=0.0,
    #sensor_class="ANALOG"
):

    cursor = await db_module.db.execute("""
    INSERT INTO Sensors (
        deviceID,
        local_channel,
        sensorName,
        conversion_rule,
        param_a,
        param_b,
        param_c    
    )
    VALUES (?, 
            (SELECT COALESCE(MAX(local_channel), 0) + 1 FROM Sensors WHERE deviceID = ?),
            ?, ?, ?, ?, ?)
            ON CONFLICT(sensorName, deviceID)
            DO UPDATE SET conversion_rule=excluded.conversion_rule,
                          param_a=excluded.param_a,
                          param_b=excluded.param_b,
                          param_c=excluded.param_c
            RETURNING sensorID, local_channel;
    """,
    (
        deviceID,
        deviceID, # pro poddotaz SELECT COALESCE...
        #local_channel,
        sensorName,
        conversion_rule,
        param_a,
        param_b,
        param_c,
        #sensor_class
    ))

    row = await cursor.fetchone()   # ← POVINNÉ
    await cursor.close()
    await db_module.db.commit()
    return row


# cache (mac, local_channel) -> sensorID; kanál senzoru se po registraci nemění
_sensor_id_cache = {}

async def get_sensor_id(mac_address, local_channel):
    key = (mac_address, int(local_channel))
    if key in _sensor_id_cache:
        return _sensor_id_cache[key]

    cursor = await db_module.db.execute("""
        SELECT Sensors.sensorID
        FROM Sensors
        JOIN DeviceL1 ON DeviceL1.id = Sensors.deviceID
        WHERE DeviceL1.mac_address = ?
          AND Sensors.local_channel = ?
    """, key)
    row = await cursor.fetchone()
    await cursor.close()

    if row is None:
        return None     # neznámé zařízení/kanál -> necachovat, může se ještě zaregistrovat
    _sensor_id_cache[key] = row["sensorID"]
    return row["sensorID"]


async def get_all_sensors():
    cursor= await db_module.db.execute("""
        SELECT sensorName
        FROM Sensors
    """)
    rows = await cursor.fetchall()
    await cursor.close()
    return rows