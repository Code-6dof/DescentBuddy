"""Descent Buddy network discovery server.

Stores active player endpoints so DescentBuddy clients can find each other
without any NAT traversal — the client just needs a reachable UDP port.

Deploy on your Texas server:
    pip install fastapi uvicorn
    python discovery_server.py

To run as a background service:
    nohup python discovery_server.py &

Entries expire after TTL_SECONDS if no heartbeat is received.
Clients heartbeat every 120 s; the server TTL is 300 s.
"""

import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_TTL_SECONDS = 300
_HOST = "0.0.0.0"
_PORT = 8765

app = FastAPI(title="Descent Discovery", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# uid -> player record
_players: dict[str, dict] = {}


class RegisterRequest(BaseModel):
    uid: str
    username: str
    port: int
    status: str = "online"


def _prune() -> None:
    cutoff = time.time() - _TTL_SECONDS
    stale = [uid for uid, p in _players.items() if p["ts"] <= cutoff]
    for uid in stale:
        del _players[uid]


@app.post("/register")
async def register(body: RegisterRequest, request: Request):
    """Register or heartbeat an endpoint. The server records the caller's public IP."""
    _players[body.uid] = {
        "uid": body.uid,
        "username": body.username,
        "ip": request.client.host,
        "port": body.port,
        "status": body.status,
        "ts": time.time(),
    }
    _prune()
    return {"ok": True}


@app.get("/players")
async def get_players():
    """Return all players with a fresh heartbeat."""
    _prune()
    return list(_players.values())


@app.delete("/unregister/{uid}")
async def unregister(uid: str):
    """Explicitly remove a player (called on clean disconnect)."""
    _players.pop(uid, None)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok", "players": len(_players)}


if __name__ == "__main__":
    uvicorn.run(app, host=_HOST, port=_PORT)
