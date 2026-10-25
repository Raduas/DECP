## this will be the  entry point for the API, 
# where we will define the routes and endpoints self (L2) health check, settings, etc.


from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

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
