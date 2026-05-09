from app.core import db as db_module
# =========================
# CONFIG OPERACE    
# =========================

async def insert_config(
    deviceID,
    typeMeasurement="CONTINUAL",
    measIntervalHz=0.2):    
    cursor = await db_module.db.execute("""
    INSERT INTO configs (
        deviceID,
        typeMeasurement,
        measIntervalHz
    )
    VALUES (?, ?, ?)
    ON CONFLICT(deviceID) DO NOTHING
    RETURNING typeMeasurement, measIntervalHz;
    """,
    (
        deviceID,
        typeMeasurement,
        measIntervalHz
    ))
    row = await cursor.fetchone()
    await cursor.close()

    # pokud se nevložilo → načti existující config
    if row is None:
        cursor = await db_module.db.execute("""
        SELECT typeMeasurement, measIntervalHz
        FROM configs
        WHERE deviceID = ?
        """, (deviceID,))
        
        row = await cursor.fetchone()
        await cursor.close()

    await db_module.db.commit()
    return row


async def update_config(
    deviceID,
    typeMeasurement="CONTINUAL",
    measIntervalHz=0.2,
    isDirty=1
):
    cursor = await db_module.db.execute("""
    UPDATE configs
    SET typeMeasurement = COALESCE(?, typeMeasurement),
        measIntervalHz = COALESCE(?, measIntervalHz),
        isDirty = ?
    WHERE deviceID = ?
    RETURNING typeMeasurement, measIntervalHz;
    """,
    (
        typeMeasurement,
        measIntervalHz,
        isDirty,
        deviceID
    ))
    row = await cursor.fetchone()
    await cursor.close()
    await db_module.db.commit()
    return row

async def get_config(deviceID):

    cursor = await db_module.db.execute("""
    SELECT *
    FROM configs
    WHERE deviceID = ?
    """,
    (deviceID,))
    return await cursor.fetchone()