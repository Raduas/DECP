
from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


DATABASE_URL = "sqlite+aiosqlite:////app/database/L2.db" # #"sqlite+aiosqlite:///./L2_data/L2.db"
engine = create_async_engine(DATABASE_URL)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    # engine.begin() automaticky otevře spojení a začne transakci
    async with engine.begin() as conn:
        # run_sync spustí synchronní Base.metadata.create_all 
        # v asynchronním kontextu
        await conn.run_sync(Base.metadata.create_all)

Base = declarative_base()

class Device(Base):
    __tablename__ = 'DeviceL1'

    id = Column(String, primary_key=True)
    mac_address = Column(String, unique=True, nullable=False)
    short_id = Column(Integer) # Inkrementaci vyřešíme v logice
    deviceName = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    status = Column(Integer, default=0)
    type = Column(String(50), nullable=True)

    # Vztah k senzorům (usnadňuje vytahování dat z DB)
    sensors = relationship("Sensor", back_populates="device", cascade="all, delete-orphan")

class Sensor(Base):
    __tablename__ = 'Sensors'

    sensorID = Column(Integer, primary_key=True, autoincrement=True)
    deviceID = Column(String, ForeignKey('DeviceL1.id'), nullable=False)
    local_channel = Column(Integer, nullable=False)
    sensorName = Column(String(30))
    conversion_rule = Column(String, default="NONE")
    param_a = Column(Float, default=0.0)
    param_b = Column(Float, default=0.0)
    param_c = Column(Float, default=0.0)
    
    # Nový sloupec z předchozí debaty pro rozpoznání kamery
    sensor_class = Column(String, default="ANALOG")

    # Vztah zpět k zařízení
    device = relationship("Device", back_populates="sensors")

    # Constraint přímo v modelu
    __table_args__ = (
        CheckConstraint(
            "conversion_rule IN ('NONE', 'LINEAR', 'POLYNOMIAL', 'QUADRATIC')", 
            name="check_conversion_rule"
        ),
        CheckConstraint(
            "sensor_class IN ('ANALOG', 'DIGITAL', 'IMAGE', 'STREAM')", 
            name="check_sensor_class"
        ),
    )


'''
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
        mac_address VARCHAR(17) UNIQUE,
        short_id TINYINT,
        deviceName VARCHAR(50) NOT NULL,
        location VARCHAR(100),
        status TINYINT DEFAULT 0,
        type VARCHAR(50)
    );
    """)


    # ---------- Sensors ----------
    await db.execute("""
    CREATE TABLE IF NOT EXISTS Sensors (
        sensorID INTEGER PRIMARY KEY AUTOINCREMENT,
        deviceID TEXT,
        local_channel TINYINT,
        sensorName VARCHAR(30),

        conversion_rule TEXT CHECK(
            conversion_rule IN (
                'NONE',
                'LINEAR',
                'POLYNOMIAL',
                'QUADRATIC'
            )
        ),

        param_a REAL,
        param_b REAL,
        param_c REAL,

        FOREIGN KEY (deviceID)
            REFERENCES DeviceL1(id)
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


    await db.commit()
'''