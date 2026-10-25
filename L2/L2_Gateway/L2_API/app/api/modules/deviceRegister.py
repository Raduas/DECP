
import json
from time import time

from app.api.mqtt.publishMQTT import send_response
from app.core.dbOperations import device_db, deviceconfig_db, sensors_db


async def device_register(data):
    device_name = data.get("name", "Unknown_Device")
    device_mac = data.get("mac")

    if not device_mac:
        print("Missing MAC")
        return
    print("DATA:", data)
    print("MAC:", data.get("mac") if data else None)
    new_text_id = f"DEV_{int(time()*1000)}" # Vygenerujeme provizorní ID pro př ípad, že je to nové zařízení
    small_id = 1
 
    result_device = await device_db.insert_device(new_text_id, device_mac, device_name, small_id) # 1. Registrace / Aktualizace zařízení
    if not result_device:
        print("Chyba DB: Zařízení se nepodařilo uložit.")
        return

    actual_device_id = result_device["id"]    
   


       
    config = await deviceconfig_db.insert_config(actual_device_id) # 1.1 Vytvoření výchozí konfigurace pro nové zařízení
    print(f"Config for device {actual_device_id}: {config}")
    senzor_name = data.get("sensorType", "Unknown_Sensor")
        
    result_sensor = await sensors_db.insert_sensor(actual_device_id, senzor_name)# 2. Vložení senzoru s reálným device_id
    if not result_sensor:
        print("Chyba DB: Senzor se nepodařilo uložit.")
        return
        
    response_payload = {
        **dict(result_device),
        **dict(result_sensor),
        **dict(config)
    }# Převedeme je na standardní dict a spojíme je.
    print(f"Registered device: {response_payload}")
    print(len(json.dumps(response_payload)))
    # 3. Odeslání MQTT odpovědi
    topic = f"l1/registration/response/{result_device['mac_address']}"
    await send_response(topic, json.dumps(response_payload))
    