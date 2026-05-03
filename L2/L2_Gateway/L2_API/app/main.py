
from app.core import db
from fastapi import FastAPI
from app.api.mqtt import clientMQTT
import asyncio
from app.api.mainRouter import api_router

app = FastAPI()

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    await db.init_db()      # inicializace databáze
    asyncio.create_task(    # spuštění MQTT loopu na pozadí
        clientMQTT.mqtt_loop()
    )


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


