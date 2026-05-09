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
