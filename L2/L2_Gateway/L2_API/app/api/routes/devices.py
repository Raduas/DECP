import json

from app.api.mqtt.publishMQTT import send_response
from app.core.dbOperations import device_db, deviceconfig_db
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter(prefix="/devices", tags=["devices"])
templates = Jinja2Templates(directory="app/templates")

class ConfigUpdate(BaseModel):
    deviceID: str
    typeMeasurement: str | None = None
    measIntervalHz: float | None = None
    measContinuity: str | None = None
    sessionName: str | None = None



@router.get("/", response_class=HTMLResponse)
async def list_devices(request: Request):
    
    devices = await device_db.get_all_devices()

    return templates.TemplateResponse("devices.html", {
            "request": request,
            "devices": devices
        })

# Zobrazení stránky s configem
@router.get("/config/{deviceID}", response_class=HTMLResponse)
async def config_page(request: Request, deviceID: str):

    config = await deviceconfig_db.get_config(deviceID)

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "deviceID": deviceID,
            "config": dict(config)
        }
    )

# Aktualizace configu
@router.post("/config/update")
async def update_config_api(cfg: ConfigUpdate):

    mac = await device_db.get_mac_by_id(cfg.deviceID)
    if mac is None:
        raise HTTPException(status_code=404, detail="Device not found")

    result = await deviceconfig_db.update_config(
        deviceID=cfg.deviceID,
        typeMeasurement=cfg.typeMeasurement,
        measIntervalHz = cfg.measIntervalHz,
        measContinuity=cfg.measContinuity,
        isDirty = 1
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Config not found")

    # posílá se kompletní config z DB (nezměněná pole doplněná přes COALESCE), ne null hodnoty z requestu
    payload = {
        "typeMeasurement": result["typeMeasurement"],
        "measIntervalHz": result["measIntervalHz"],
        "measContinuity": result["measContinuity"]
    }
    if cfg.sessionName is not None:
        payload["sessionName"] = cfg.sessionName
    await send_response(topic=f"l2/config/{mac['mac_address']}",payload=json.dumps(payload))

    return {"status": "sent"}



class SessionStart(BaseModel):
    deviceID: str
    start: bool

@router.post("/config/start-session")
async def start_session_api(start: SessionStart):
    await deviceconfig_db.set_active(
        deviceID=start.deviceID,
        is_active=start.start
    )
    payload = {
        "is_active": start.start
    }
    mac = await device_db.get_mac_by_id(start.deviceID)
    if mac is None:
        raise HTTPException(status_code=404, detail="Device not found")
    await send_response(topic=f"l1/start/{mac['mac_address']}",payload=json.dumps(payload))
    return {"status": "sent"}