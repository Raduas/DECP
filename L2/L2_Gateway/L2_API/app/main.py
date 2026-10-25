import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.mainRouter import api_router
from app.api.mqtt import clientMQTT
from app.core import db

app = FastAPI()

app.include_router(api_router)
templates = Jinja2Templates(directory="app/templates")
app.mount("/css", StaticFiles(directory="app/templates/css"), name="css")
app.mount("/js", StaticFiles(directory="app/templates/js"), name="js")


@app.on_event("startup")
async def startup():
    await db.init_db()  # inicializace databáze
    asyncio.create_task(clientMQTT.mqtt_loop())
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


@app.get("/")
def main_page(request: Request):
    return templates.TemplateResponse("mainPage.html", {"request": request})


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id * 2, "q": q}
