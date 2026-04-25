


from pathlib import Path

from fastapi import APIRouter, Request
from .core import db
from fastapi import FastAPI
from .mqtt import clientMQTT
import asyncio
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()


class ConfigUpdate(BaseModel):
    deviceID: str
    typeMeasurement: str | None = None
    measIntervalHz: int | None = None


templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():

    # inicializace databáze
    await db.init_db()

    # spuštění MQTT loopu na pozadí
    asyncio.create_task(
        clientMQTT.mqtt_loop()
    )

@app.get("/devices", response_class=HTMLResponse)
async def list_devices(request: Request):
    
    devices = await db.get_all_devices()

    return templates.TemplateResponse("devices.html", {
            "request": request,
            "devices": devices
        })

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


# Zobrazení stránky s configem
@app.get("/config/{deviceID}", response_class=HTMLResponse)
async def config_page(request: Request, deviceID: str):

    config = await db.get_config(deviceID)

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "deviceID": deviceID,
            "config": dict(config)
        }
    )


# Aktualizace configu
@app.post("/config/update")
async def update_config_api(cfg: ConfigUpdate):

    result = await db.update_config(
        deviceID=cfg.deviceID,
        typeMeasurement=cfg.typeMeasurement,
        measIntervalHz=cfg.measIntervalHz
    )

    return dict(result)

"""
@app.get("/config/{device_id}")
async def get_device_config(device_id: str):
    config = await db.get_config(device_id)
    if config:
        return {
            "deviceID": config["deviceID"],
            "typeMeasurement": config["typeMeasurement"],
            "measIntervalHz": config["measIntervalHz"]
        }
    else:
        return {"error": "Device not found"}"""