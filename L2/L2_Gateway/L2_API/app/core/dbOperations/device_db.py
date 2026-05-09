from app.core import db as db_module
# =========================
# DEVICE OPERACE
# =========================

async def insert_device(
    id,
    mac_address,
    deviceName,
    short_id=None,
    location=None,
    status=0,
    type=None
):
    print(f"Inserting/updating device: id={id}, mac={mac_address}, name={deviceName}")
    cursor = await db_module.db.execute("""
    INSERT INTO DeviceL1 (
        id,
        mac_address,
        short_id,
        deviceName,
        location,
        status,
        type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(mac_address)
    DO UPDATE SET deviceName=excluded.deviceName
    RETURNING id, short_id, mac_address;
    """,
    (
        id,
        mac_address,
        short_id,
        deviceName,
        location,
        status,
        type
    ))
    row = await cursor.fetchone()   # ← POVINNÉ
    await cursor.close()
    await db_module.db.commit()
    return row



async def get_device_by_mac(mac):

    cursor = await db_module.db.execute("""
    SELECT *
    FROM DeviceL1
    WHERE mac_address = ?
    """,
    (mac,))

    return await cursor.fetchone()

async def get_mac_by_id(device_id):

    cursor = await db_module.db.execute("""
    SELECT mac_address
    FROM DeviceL1
    WHERE id = ?
    """,
    (device_id,))

    return await cursor.fetchone()

async def get_all_devices():

    cursor = await db_module.db.execute("""
    SELECT id,
           mac_address,
           deviceName,
           short_id,
           status
    FROM DeviceL1
    ORDER BY deviceName;
    """)

    rows = await cursor.fetchall()
    await cursor.close()

    return rows