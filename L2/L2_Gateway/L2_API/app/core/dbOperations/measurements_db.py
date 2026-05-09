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

    cursor = await db_module.db.execute("""
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

    await db_module.executemany("""
    INSERT INTO Measurements (
        timestamp,
        sensorID,
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """, data)

    await db_module.commit()

async def on_ack_received(mac):
    await db_module.execute(
        "UPDATE configs SET isDirty = 0, lastSync = ? WHERE deviceID = (SELECT id FROM DeviceL1 WHERE mac_address = ?)",
        (int(time()), mac)
    )
    await db_module.commit()
    print(f"Konfigurace pro {mac} byla úspěšně synchronizována.")