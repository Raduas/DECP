## this will be the  entry point for the API, 
# for sensors query


from app.core.dbOperations import sensors_db
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.core.dbOperations import deviceconfig_db
from app.core.dbOperations import device_db

from fastapi import APIRouter
from app.api.mqtt.publishMQTT import send_response

router = APIRouter(prefix="/sensors", tags=["sensors"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_sensors(request: Request):
    
    sensors = await sensors_db.get_all_sensors()

    return templates.TemplateResponse("sensors.html", {
            "request": request,
            "sensors": sensors
        })