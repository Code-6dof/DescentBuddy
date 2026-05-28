"""Network discovery client — register this client's game endpoint and fetch others.

The discovery server (server/discovery_server.py) is a lightweight FastAPI service
that stores active player endpoints keyed by uid. Any DescentBuddy client running
with "Host" enabled is visible here. Entries expire after 5 minutes without a
heartbeat; clients heartbeat every 2 minutes.

Update _SERVER_URL after deploying the server to your Texas machine.
"""

import requests

_SERVER_URL = "http://dxxtracker.com:8765"
_TIMEOUT = 5
DEFAULT_PORT = 5197  # DXX-Redux default UDP port


def get_public_ip() -> str | None:
    """Return this machine's public IPv4 address via a simple echo service."""
    try:
        return requests.get("https://api4.ipify.org", timeout=_TIMEOUT).text.strip()
    except Exception:
        return None


def register(uid: str, username: str, port: int, status: str = "online") -> bool:
    """Register or heartbeat on the discovery server. Returns True on success."""
    try:
        resp = requests.post(
            f"{_SERVER_URL}/register",
            json={"uid": uid, "username": username, "port": port, "status": status},
            timeout=_TIMEOUT,
        )
        return resp.ok
    except Exception:
        return False


def unregister(uid: str) -> None:
    """Remove this client from the discovery server on clean disconnect."""
    try:
        requests.delete(f"{_SERVER_URL}/unregister/{uid}", timeout=_TIMEOUT)
    except Exception:
        pass


def fetch_players() -> list[dict]:
    """Return all active players from the discovery server."""
    try:
        resp = requests.get(f"{_SERVER_URL}/players", timeout=_TIMEOUT)
        return resp.json() if resp.ok else []
    except Exception:
        return []
