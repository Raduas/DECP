## this will be the  entry point for the API, 
# for measurements query
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
async def filter_measurements(request: Request):
    
    #measurements = await sensors_db.get_all_sensors()

    return templates.TemplateResponse("measurements.html", {
            "request": request,
          #  "measurements": measurements
        })