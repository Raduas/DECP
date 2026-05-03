from time import time

import aiosqlite

DB_PATH = "/app/database/L2.db"
db = None




async def init_db():
    global db
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
        # zapnout foreign keys (SQLite je má defaultně vypnuté)
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("PRAGMA journal_mode=WAL;")

    # ---------- DeviceL1 ----------
    await db.execute("""
    CREATE TABLE IF NOT EXISTS DeviceL1 (
        id TEXT PRIMARY KEY,
        mac_address VARCHAR(17) UNIQUE NOT NULL,
        short_id TINYINT,
        deviceName VARCHAR(50) NOT NULL,
        location VARCHAR(100),
        status TINYINT DEFAULT 0,
        type VARCHAR(50)
    );
    """)

    # ---------- config ----------
    await db.execute("""
    CREATE TABLE IF NOT EXISTS configs (
        deviceID TEXT PRIMARY KEY,
        typeMeasurement TEXT CHECK(typeMeasurement IN ('SESSION', 'CONTINUAL')) default 'CONTINUAL',
        measIntervalHz REAL default 0.2,
        isDirty BOOLEAN DEFAULT 0,
        lastSync TIMESTAMP,
                     
        FOREIGN KEY (deviceID)
            REFERENCES DeviceL1(id)
    );
    """)
    # ---------- Sensors ----------
    await db.execute("""
    CREATE TABLE IF NOT EXISTS Sensors (
        sensorID INTEGER PRIMARY KEY AUTOINCREMENT,
        deviceID TEXT,
        local_channel TINYINT,
        sensorName VARCHAR(30) NOT NULL,
        conversion_rule TEXT CHECK(
            conversion_rule IN (
                'NONE',
                'LINEAR',
                'POLYNOMIAL',
                'QUADRATIC'
            )
        ),
                     
        param_a REAL DEFAULT 0.0,
        param_b REAL DEFAULT 0.0,
        param_c REAL DEFAULT 0.0,

        FOREIGN KEY (deviceID)
            REFERENCES DeviceL1(id)
                     
        -- jeden název senzoru jen jednou na device     
        UNIQUE(deviceID, sensorName),

        -- jeden kanál jen jednou na device
        UNIQUE(deviceID, local_channel)
    );
    """)


    # ---------- Measurements ----------
    await db.execute("""
    CREATE TABLE IF NOT EXISTS Measurements (
        timestamp BIGINT NOT NULL,
        sensorID INT NOT NULL,

        status TINYINT DEFAULT 0,
        raw_value INTEGER,
        calc_value REAL,

        PRIMARY KEY (timestamp, sensorID),

        FOREIGN KEY (sensorID)
            REFERENCES Sensors(sensorID)
    );
    """)


    # index pro výkon (velmi důležité)
    await db.execute("""
    CREATE INDEX IF NOT EXISTS idx_measurements_sensor
    ON Measurements(sensorID);
    """)

    await db.execute("""
    CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
    ON Measurements(timestamp);
    """)


    await db.commit()

# =========================
# CLOSE DB
# =========================

async def close_db():
    global db

    if db:
        await db.close()


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
    cursor = await db.execute("""
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
    await db.commit()
    return row



async def get_device_by_mac(mac):

    cursor = await db.execute("""
    SELECT *
    FROM DeviceL1
    WHERE mac_address = ?
    """,
    (mac,))

    return await cursor.fetchone()

async def get_mac_by_id(device_id):

    cursor = await db.execute("""
    SELECT mac_address
    FROM DeviceL1
    WHERE id = ?
    """,
    (device_id,))

    return await cursor.fetchone()

async def get_all_devices():

    cursor = await db.execute("""
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

    cursor = await db.execute("""
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
    await db.commit()
    return row

# =========================
# CONFIG OPERACE    
# =========================

async def insert_config(
    deviceID,
    typeMeasurement="CONTINUAL",
    measIntervalHz=0.2):    
    cursor = await db.execute("""
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
        cursor = await db.execute("""
        SELECT typeMeasurement, measIntervalHz
        FROM configs
        WHERE deviceID = ?
        """, (deviceID,))
        
        row = await cursor.fetchone()
        await cursor.close()

    await db.commit()
    return row


async def update_config(
    deviceID,
    typeMeasurement="CONTINUAL",
    measIntervalHz=0.2,
    isDirty=1
):
    cursor = await db.execute("""
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
    await db.commit()
    return row

async def get_config(deviceID):

    cursor = await db.execute("""
    SELECT *
    FROM configs
    WHERE deviceID = ?
    """,
    (deviceID,))
    return await cursor.fetchone()


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

    cursor = await db.execute("""
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
    await db.commit()

# batch insert (doporučeno)

async def insert_measurements_batch(data):

    await db.executemany("""
    INSERT INTO Measurements (
        timestamp,
        sensorID,
        raw_value,
        calc_value,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """, data)

    await db.commit()

async def on_ack_received(mac):
    await db.execute(
        "UPDATE configs SET isDirty = 0, lastSync = ? WHERE deviceID = (SELECT id FROM DeviceL1 WHERE mac_address = ?)",
        (int(time()), mac)
    )
    await db.commit()
    print(f"Konfigurace pro {mac} byla úspěšně synchronizována.")