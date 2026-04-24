"""Firestore presence management — reads and writes to the descent-buddy project."""

from datetime import datetime, timezone

import requests

from core.api_keys import DESCENT_BUDDY_KEY as _API_KEY

_PROJECT = "descent-buddy"
_BASE = f"https://firestore.googleapis.com/v1/projects/{_PROJECT}/databases/(default)/documents"
_RUN_QUERY_URL = f"https://firestore.googleapis.com/v1/projects/{_PROJECT}/databases/(default)/documents:runQuery"

_ONLINE_THRESHOLD_SECONDS = 90
_CHAT_LIMIT = 60


def write_presence(uid: str, username: str, status: str, db_token: str) -> bool:
    """Write or update the presence document for this user. Returns True on success."""
    url = f"{_BASE}/presence/{uid}"
    now = datetime.now(timezone.utc).isoformat()
    body = {
        "fields": {
            "uid": {"stringValue": uid},
            "username": {"stringValue": username},
            "status": {"stringValue": status},
            "last_seen": {"stringValue": now},
        }
    }
    try:
        resp = requests.patch(
            url,
            json=body,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
        return resp.ok
    except Exception:
        return False


def delete_presence(uid: str, db_token: str) -> None:
    """Remove the user's presence document (used for invisible mode and on quit)."""
    url = f"{_BASE}/presence/{uid}"
    try:
        requests.delete(
            url,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
    except Exception:
        pass


def fetch_all_presence() -> list[dict]:
    """Fetch all active presence documents. Filters out stale entries."""
    url = f"{_BASE}/presence"
    try:
        resp = requests.get(url, params={"key": _API_KEY}, timeout=10)
        if not resp.ok:
            return []
        cutoff = datetime.now(timezone.utc).timestamp() - _ONLINE_THRESHOLD_SECONDS
        result = []
        for doc in resp.json().get("documents", []):
            fields = doc.get("fields", {})
            last_seen_str = fields.get("last_seen", {}).get("stringValue", "")
            try:
                if datetime.fromisoformat(last_seen_str).timestamp() < cutoff:
                    continue
            except Exception:
                continue
            result.append({
                "uid": fields.get("uid", {}).get("stringValue", ""),
                "username": fields.get("username", {}).get("stringValue", "?"),
                "status": fields.get("status", {}).get("stringValue", "online"),
            })
        return result
    except Exception:
        return []


def write_member(uid: str, username: str, db_token: str) -> None:
    """Register or update the user in the permanent community members registry."""
    url = f"{_BASE}/members/{uid}"
    now = datetime.now(timezone.utc).isoformat()
    body = {
        "fields": {
            "uid": {"stringValue": uid},
            "username": {"stringValue": username},
            "last_seen": {"stringValue": now},
        }
    }
    try:
        requests.patch(
            url,
            json=body,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
    except Exception:
        pass


def send_chat_message(uid: str, username: str, message: str, db_token: str) -> bool:
    """Post a message to the community chat collection. Returns True on success."""
    url = f"{_BASE}/chat"
    now = datetime.now(timezone.utc).isoformat()
    body = {
        "fields": {
            "uid": {"stringValue": uid},
            "username": {"stringValue": username},
            "message": {"stringValue": message},
            "timestamp": {"stringValue": now},
        }
    }
    try:
        resp = requests.post(
            url,
            json=body,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
        return resp.ok
    except Exception:
        return False


def fetch_recent_chat() -> list[dict]:
    """Fetch the most recent chat messages ordered by timestamp ascending."""
    query = {
        "structuredQuery": {
            "from": [{"collectionId": "chat"}],
            "orderBy": [{"field": {"fieldPath": "timestamp"}, "direction": "ASCENDING"}],
            "limit": _CHAT_LIMIT,
        }
    }
    try:
        resp = requests.post(
            _RUN_QUERY_URL,
            json=query,
            params={"key": _API_KEY},
            timeout=10,
        )
        if not resp.ok:
            return []
        messages = []
        for item in resp.json():
            doc = item.get("document")
            if not doc:
                continue
            fields = doc.get("fields", {})
            messages.append({
                "uid": fields.get("uid", {}).get("stringValue", ""),
                "username": fields.get("username", {}).get("stringValue", "?"),
                "message": fields.get("message", {}).get("stringValue", ""),
                "timestamp": fields.get("timestamp", {}).get("stringValue", ""),
            })
        return messages
    except Exception:
        return []



def write_presence(uid: str, username: str, status: str, db_token: str) -> bool:
    """Write or update the presence document for this user. Returns True on success."""
    url = f"{_BASE}/presence/{uid}"
    now = datetime.now(timezone.utc).isoformat()
    body = {
        "fields": {
            "uid": {"stringValue": uid},
            "username": {"stringValue": username},
            "status": {"stringValue": status},
            "last_seen": {"stringValue": now},
        }
    }
    try:
        resp = requests.patch(
            url,
            json=body,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
        return resp.ok
    except Exception:
        return False


def delete_presence(uid: str, db_token: str) -> None:
    """Remove the user's presence document (used for invisible mode and on quit)."""
    url = f"{_BASE}/presence/{uid}"
    try:
        requests.delete(
            url,
            headers={"Authorization": f"Bearer {db_token}"},
            params={"key": _API_KEY},
            timeout=10,
        )
    except Exception:
        pass


def fetch_all_presence() -> list[dict]:
    """Fetch all active presence documents. Filters out stale entries."""
    url = f"{_BASE}/presence"
    try:
        resp = requests.get(url, params={"key": _API_KEY}, timeout=10)
        if not resp.ok:
            return []
        cutoff = datetime.now(timezone.utc).timestamp() - _ONLINE_THRESHOLD_SECONDS
        result = []
        for doc in resp.json().get("documents", []):
            fields = doc.get("fields", {})
            last_seen_str = fields.get("last_seen", {}).get("stringValue", "")
            try:
                if datetime.fromisoformat(last_seen_str).timestamp() < cutoff:
                    continue
            except Exception:
                continue
            result.append({
                "uid": fields.get("uid", {}).get("stringValue", ""),
                "username": fields.get("username", {}).get("stringValue", "?"),
                "status": fields.get("status", {}).get("stringValue", "online"),
            })
        return result
    except Exception:
        return []
