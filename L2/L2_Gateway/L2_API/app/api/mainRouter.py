from fastapi import APIRouter

#from app.api.routes import selfroutes
from app.api.routes import devices
#from app.core.config import settings
from app.api.routes import measurements
api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(measurements.router)
#api_router.include_router(selfroutes.router)

