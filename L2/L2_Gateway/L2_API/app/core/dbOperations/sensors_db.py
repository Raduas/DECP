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
