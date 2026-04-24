
from .core import db
from fastapi import FastAPI
from .mqtt import clientMQTT
import asyncio


app = FastAPI()



@app.on_event("startup")
async def startup():

    # inicializace databáze
    await db.init_db()

    # spuštění MQTT loopu na pozadí
    asyncio.create_task(
        clientMQTT.mqtt_loop()
    )

"""
@app.on_event("shutdown")
async def shutdown():

    # zastavení MQTT tasku
    if hasattr(app.state, "mqtt_task"):
        app.state.mqtt_task.cancel()

        try:
            await app.state.mqtt_task
        except asyncio.CancelledError:
            pass

    # zavření databáze
    await db.close_db()
"""

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}