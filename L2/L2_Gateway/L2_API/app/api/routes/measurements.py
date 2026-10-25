## this will be the  entry point for the API, 
# for measurements query

from app.api.modules.querryFuncions import from_int_to_datetime
from app.core.dbOperations import device_db, measurements_db, sensors_db
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/measurements", tags=["measurements"])
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
    return templates.TemplateResponse("measurements.html", {
            "request": request,
            "filter": filter,
            "measQuery": q,
            "filtering": filtering,
            "detailID": detailID,
            "measurements": measurements
        })
