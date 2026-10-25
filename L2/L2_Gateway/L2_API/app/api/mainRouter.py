from app.api.routes import devices, graphs, measurements
from fastapi import APIRouter

#from app.api.routes import selfroutes, settings
 
api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(measurements.router)
#api_router.include_router(selfroutes.router)
api_router.include_router(graphs.router)
