## this will be the  entry point for the API, 
# for sensors query


from app.core.dbOperations import sensors_db
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/sensors", tags=["sensors"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_sensors(request: Request):
    
    sensors = await sensors_db.get_all_sensors()

    return templates.TemplateResponse("sensors.html", {
            "request": request,
            "sensors": sensors
        })