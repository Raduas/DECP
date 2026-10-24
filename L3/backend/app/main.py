# backend/app/main.py
import asyncio, hashlib, secrets, uuid
from dataclasses import dataclass, field
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

# ---------- auth ----------
async def gw_auth(authorization: str = Header(...)) -> str:
    h = hashlib.sha256(authorization.removeprefix("Bearer ").encode()).hexdigest()
    gw_id = await app.state.pool.fetchval("SELECT id FROM gateways WHERE token_hash=$1", h)
    if not gw_id:
        raise HTTPException(401)
    return gw_id

# ---------- modely ----------
class Hello(BaseModel):
    fw: str
    capabilities: list[str] = []
    devices: list[dict] = []
    sensors: list[dict] = []
    config_version: int = 0

class Sample(BaseModel):
    ts: int                 # epoch ms UTC
    sensor_id: int          # L2 Sensors.sensorID
    status: int = 0
    raw: int | None = None
    value: float | None = None

class Batch(BaseModel):
    session_name: str | None = None
    samples: list[Sample]

# ---------- REST pro L2 ----------
@app.post("/api/v1/gw/hello")
async def hello(h: Hello, gw: str = Depends(gw_auth)):
    # upsert devices/sensors podle (gw, l2_id), uložit capabilities/fw
    cfg = await pending_config(gw, h.config_version)
    return {"server_time": now_ms(), "heartbeat_s": 20, "batch_max": 1000, "config": cfg}

@app.post("/api/v1/gw/measurements")
async def ingest(b: Batch, gw: str = Depends(gw_auth)):
    rows = [(s.ts, gw, s.sensor_id, s.status, s.raw, s.value, b.session_name) for s in b.samples]
    await app.state.pool.executemany(
        """INSERT INTO measurements(time, gateway_id, sensor_id, status, raw, value, session_name)
           VALUES (to_timestamp($1/1000.0), $2, $3, $4, $5, $6, $7)
           ON CONFLICT DO NOTHING""", rows)
    return {"accepted": len(rows)}      # L2 podle toho označí synced=1

# ---------- hub: řídicí kanál ----------
class Hub:
    def __init__(self):
        self.conns: dict[str, WebSocket] = {}
        self.pending: dict[str, asyncio.Future] = {}

    async def send_cmd(self, gw: str, type_: str, payload: dict, timeout: float = 10):
        ws = self.conns.get(gw)
        if not ws:
            raise HTTPException(409, "gateway offline")
        cid = uuid.uuid4().hex
        fut = asyncio.get_running_loop().create_future()
        self.pending[cid] = fut
        await ws.send_json({"v": 1, "type": type_, "id": cid, "payload": payload})
        try:
            return await asyncio.wait_for(fut, timeout)
        finally:
            self.pending.pop(cid, None)

hub = Hub()

@app.websocket("/ws/gw")
async def ws_gw(ws: WebSocket):
    try:
        gw = await gw_auth(ws.headers.get("authorization", ""))
    except HTTPException:
        await ws.close(code=4401); return
    await ws.accept()
    hub.conns[gw] = ws
    try:
        while True:
            m = await ws.receive_json()
            if m["type"] == "heartbeat":
                await touch_gateway(gw, m["payload"])
            elif m.get("corr_id") in hub.pending:
                f = hub.pending[m["corr_id"]]
                if not f.done():
                    f.set_result(m["payload"])
    except WebSocketDisconnect:
        pass
    finally:
        if hub.conns.get(gw) is ws:
            del hub.conns[gw]

# ---------- UI -> příkazy ----------
@app.post("/api/v1/gateways/{gw}/commands")
async def command(gw: str, type: str, payload: dict = {}):
    return await hub.send_cmd(gw, type, payload)

# ---------- live session (relay) ----------
@dataclass
class Session:
    gw: str
    token: str
    peers: dict[str, WebSocket] = field(default_factory=dict)

sessions: dict[str, Session] = {}

@app.post("/api/v1/gateways/{gw}/sessions")
async def open_session(gw: str, kind: str):
    sid, tok = uuid.uuid4().hex, secrets.token_urlsafe(16)
    sessions[sid] = Session(gw, tok)
    await hub.send_cmd(gw, "session.open", {"session_id": sid, "kind": kind, "token": tok})
    return {"session_id": sid}

@app.websocket("/ws/session/{sid}")
async def ws_session(ws: WebSocket, sid: str, role: str, token: str = ""):
    s = sessions.get(sid)
    if not s or (role == "l2" and token != s.token):   # TODO: auth uživatele pro role=ui
        await ws.close(code=4403); return
    await ws.accept()
    s.peers[role] = ws
    other = "ui" if role == "l2" else "l2"
    try:
        while True:
            m = await ws.receive()
            if m["type"] == "websocket.disconnect":
                break
            peer = s.peers.get(other)
            if peer:
                if m.get("bytes") is not None:
                    await peer.send_bytes(m["bytes"])
                elif m.get("text") is not None:
                    await peer.send_text(m["text"])
    finally:
        s.peers.pop(role, None)
        if not s.peers:
            sessions.pop(sid, None)