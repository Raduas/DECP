## this will be the  entry point for the API, 
# for measurements query
from app.core.dbOperations import device_db
from app.api.modules.querryFuncions import from_int_to_datetime
from app.core.dbOperations import measurements_db
from app.core.dbOperations import sensors_db
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


from fastapi import APIRouter


router = APIRouter(prefix="/graphs", tags=["graphs"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def filter_measurements(request: Request, filter: str | None = None, detailID: str | None = None, q: int = 50):    
    filtering = []
    measurements = []
    if filter == "Sensor":
      filtering = await sensors_db.get_all_sensors()
    elif filter == "Session":
      filtering = await measurements_db.get_all_sessions()
    elif filter == "Device":
      filtering = await device_db.get_all_devices()
    if filter and detailID:
        if filter == "Sensor":
          measurements = await measurements_db.get_measurements_by_sensor(detailID, q)
          measurements = [{**dict(m), "timestamp": from_int_to_datetime(m["timestamp"])}
          for m in measurements
            ]
        elif filter == "Session":
          measurements = await measurements_db.get_measurements_by_session(detailID, q)
          measurements = [{**dict(m), "timestamp": from_int_to_datetime(m["timestamp"])}
          for m in measurements
            ]
        elif filter == "Device":
          measurements = await measurements_db.get_measurements_by_device(detailID, q)
          measurements = [{**dict(m), "timestamp": from_int_to_datetime(m["timestamp"])}
          for m in measurements
            ]
    return templates.TemplateResponse("graphs.html", {
            "request": request,
            "filter": filter,
            "measQuery": q,
            "filtering": filtering,
            "detailID": detailID,
            "measurements": measurements
        })
