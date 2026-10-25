from app.core import db as db_module

# =========================
# CONFIG OPERACE    
# =========================

async def insert_config(
    deviceID,
    typeMeasurement="CONTINUAL",
    measIntervalHz=0.2,
    measContinuity="STREAM",
    is_active=0
):    
    cursor = await db_module.db.execute("""
    INSERT INTO configs (
        deviceID,
        typeMeasurement,
        measIntervalHz,
        measContinuity,
        is_active
    )
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(deviceID) DO NOTHING
    RETURNING typeMeasurement, measIntervalHz, measContinuity, is_active;
    """,
    (
        deviceID,
        typeMeasurement,
        measIntervalHz,
        measContinuity,
        is_active
    ))
    row = await cursor.fetchone()
    await cursor.close()

    # pokud se nevložilo → načti existující config
    if row is None:
        cursor = await db_module.db.execute("""
        SELECT typeMeasurement, measIntervalHz, measContinuity, is_active
        FROM configs
        WHERE deviceID = ?
        """, (deviceID,))
        
        row = await cursor.fetchone()
        await cursor.close()

    await db_module.db.commit()
    return row


async def update_config(
    deviceID,
    typeMeasurement=None,   # None = ponechat stávající hodnotu (COALESCE)
    measIntervalHz=None,
    measContinuity=None,
    is_active=None,
    isDirty=1
):
    cursor = await db_module.db.execute("""
    UPDATE configs
    SET typeMeasurement = COALESCE(?, typeMeasurement),
        measIntervalHz = COALESCE(?, measIntervalHz),
        measContinuity = COALESCE(?, measContinuity),
        is_active = COALESCE(?, is_active),
        isDirty = ?
    WHERE deviceID = ?
    RETURNING typeMeasurement, measIntervalHz, measContinuity, is_active;
    """,
    (
        typeMeasurement,
        measIntervalHz,
        measContinuity,
        is_active,
        isDirty,
        deviceID
    ))
    row = await cursor.fetchone()
    await cursor.close()
    await db_module.db.commit()
    return row

async def set_active(deviceID, is_active):
    cursor = await db_module.db.execute("""
    UPDATE configs
    SET is_active = ?
    WHERE deviceID = ?
    """,
    (
        is_active,
        deviceID
    ))
    await cursor.close()
    await db_module.db.commit()

async def get_config(deviceID):

    cursor = await db_module.db.execute("""
    SELECT *
    FROM configs
    WHERE deviceID = ?
    """,
    (deviceID,))
    return await cursor.fetchone()