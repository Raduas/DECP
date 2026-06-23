## this will be the  entry point for the API, 
# where we will define the routes and endpoints self (L2) health check, settings, etc.
import json


from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.core.dbOperations import deviceconfig_db
from app.core.dbOperations import device_db

from fastapi import APIRouter
from app.api.mqtt.publishMQTT import send_response

router = APIRouter(prefix="/health", tags=["health"])
templates = Jinja2Templates(directory="app/templates")


#@router.get("/health", response_class=HTMLResponse)
#async def health_check(request: Request):# Health check endpoint
#    
#    health = await selfdb.get_self() # declaration to do

#    return templates.TemplateResponse("health.html", { # template to do
#            "request": Request,
#            "health": health
#        })
