
from urllib import request

from app.core import db
from fastapi import FastAPI
from app.api.mqtt import clientMQTT
from fastapi.staticfiles import StaticFiles
import asyncio
from app.api.mainRouter import api_router
from fastapi.templating import Jinja2Templates
from fastapi import Request


app = FastAPI()

app.include_router(api_router)
templates = Jinja2Templates(directory="app/templates")
app.mount("/css", StaticFiles(directory="app/templates/css"), name="css")
app.mount("/js", StaticFiles(directory="app/templates/js"), name="js")


@app.on_event("startup")
async def startup():
    await db.init_db()      # inicializace databáze
    asyncio.create_task(    
        clientMQTT.mqtt_loop()
    )


@app.get("/")
def main_page(request: Request):
    return templates.TemplateResponse("mainPage.html",{"request": request})





@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id*2, "q": q}


