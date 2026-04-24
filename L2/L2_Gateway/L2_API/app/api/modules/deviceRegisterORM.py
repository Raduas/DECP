import json
from time import time
from app.core import db
from app.mqtt.publishMQTT import send_response
from sqlalchemy import select
from app.core.db import AsyncSessionLocal #SessionLocal
from app.core.db import Device, Sensor

''''''

async def device_register(data):
    try:
        print("Received device registration:", data)
        device_name = data.get("name", "Unknown_Device")
        device_mac = data.get("mac")

        if not device_mac:
            print("Missing MAC")
            return
        
        db_response = await register_device_in_db(data)
        
        # 2. Sestavíme zprávu pro L1
        response_payload = {
            "mac": device_mac,
            "assigned_id": db_response["device_id"],
            "registration_status": db_response["status"]
        }
        
        # 3. Pošleme odpověď zpět specifickému zařízení
        print(f"Handshake s {device_mac} dokončen se statusem: {db_response['status']}")
        topic = f"l1/registration/response/{device_mac}"
        await send_response(topic, json.dumps(response_payload).encode('utf-8'))

    except Exception as e:
        print("Error in device_register:", e)

async def register_device_in_db(payload_data: dict) -> dict:
    mac = payload_data.get("mac")
    
    async with AsyncSessionLocal() as session:
        # 1. Krok: Podíváme se, jestli už MAC adresa v DB existuje
        result = await session.execute(select(Device).where(Device.mac_address == mac))
        existing_device = result.scalar_one_or_none()

        if existing_device:
            # Existuje -> nebudeme nic zapisovat, jen vrátíme info
            return {
                "status": "EXISTS",
                "device_id": existing_device.id,
                "message": "Device is already registered."
            }

        # 2. Krok: Neexistuje -> Vytvoříme nové zařízení (Tabulka DeviceL1)
        new_device_id =f"DEV_{int(time.time()*1000)}" # Vygenerujeme provizorní ID pro případ, že je to nové zařízení

        new_device = Device(
            id=new_device_id,
            mac_address=mac,
            deviceName=payload_data.get("device_name", "Unknown Device"),
            status=1 # Označíme jako aktivní
        )

        # 3. Krok: Připojíme k němu senzory (Tabulka Sensors)
        sensors_data = payload_data.get("sensors", [])
        for s_data in sensors_data:
            new_sensor = Sensor(
                local_channel=s_data.get("local_channel"),
                sensorName=s_data.get("name"),
                sensor_class=s_data.get("class", "ANALOG")
                # deviceID (Foreign Key) se sem doplní automaticky přes relationship!
            )
            # ORM Kouzlo: Pouze přidáme objekt do listu
            new_device.sensors.append(new_sensor)

        # 4. Krok: Uložíme do DB
        session.add(new_device)
        await session.commit() # Tady se reálně provedou INSERTy do obou tabulek

        return {
            "status": "CREATED",
            "device_id": new_device.id,
            "message": "Device and sensors successfully registered."
        }

