## this will be the  entry point for the API, 
# for measurements query
import datetime

from app.api.modules.querryFuncions import from_int_to_datetime
from app.core.dbOperations import measurements_db
from app.core.dbOperations import sensors_db
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


from fastapi import APIRouter
from app.api.mqtt.publishMQTT import send_response

router = APIRouter(prefix="/measurements", tags=["measurements"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def filter_measurements(request: Request, filter: str | None = None, sensorName: str | None = None, q: int = 10):    
    filtering = []
    measurements = []
    if filter == "Sensor":
      filtering = await sensors_db.get_all_sensors()

      if sensorName:
        measurements = await measurements_db.get_measurements_by_sensor(sensorName)
        measurements = [{**dict(m), "timestamp": from_int_to_datetime(m["timestamp"])}
        for m in measurements
          ]


    return templates.TemplateResponse("measurements.html", {
            "request": request,
            "filter": filter,
            "measQuery": q,
            "filtering": filtering,
            "sensorName": sensorName,
            "measurements": measurements
        })
