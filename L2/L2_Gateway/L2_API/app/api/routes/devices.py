from urllib.request import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.core import db
from fastapi import APIRouter


router = APIRouter(prefix="/devices", tags=["devices"])
templates = Jinja2Templates(directory="app/templates")

class ConfigUpdate(BaseModel):
    deviceID: str
    typeMeasurement: str | None = None
    measIntervalHz: int | None = None


@router.get("/devices", response_class=HTMLResponse)
async def list_devices(request: Request):
    
    devices = await db.get_all_devices()

    return templates.TemplateResponse("devices.html", {
            "request": request,
            "devices": devices
        })

# Zobrazení stránky s configem
@router.get("/config/{deviceID}", response_class=HTMLResponse)
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
@router.post("/config/update")
async def update_config_api(cfg: ConfigUpdate):

    result = await db.update_config(
        deviceID=cfg.deviceID,
        typeMeasurement=cfg.typeMeasurement,
        measIntervalHz=cfg.measIntervalHz
    )

    return dict(result)
