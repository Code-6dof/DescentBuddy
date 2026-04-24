"""Firestore notification queries for the rdladder userNotifications collection."""

from datetime import datetime, timezone

import requests

_RDLADDER_KEY = "REDACTED_RDLADDER_KEY"
_RUN_QUERY_URL = (
    "https://firestore.googleapis.com/v1/projects/rdladder"
    "/databases/(default)/documents:runQuery"
)
_DOC_BASE = (
    "https://firestore.googleapis.com/v1/projects/rdladder"
    "/databases/(default)/documents"
)


def fetch_user_notifications(uid: str, id_token: str | None = None) -> list[dict]:
    """Fetch userNotifications for uid, newest first. Returns [] on any error."""
    headers = {"Authorization": f"Bearer {id_token}"} if id_token else {}
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "userNotifications"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "userId"},
                    "op": "EQUAL",
                    "value": {"stringValue": uid},
                }
            },
            "orderBy": [
                {"field": {"fieldPath": "createdAt"}, "direction": "DESCENDING"}
            ],
            "limit": 50,
        }
    }
    try:
        resp = requests.post(
            f"{_RUN_QUERY_URL}?key={_RDLADDER_KEY}",
            headers=headers,
            json=payload,
            timeout=10,
        )
        print(f"[notifications] uid={uid!r} status={resp.status_code}")
        if not resp.ok:
            return []
        items = resp.json()
        results = []
        for item in items:
            doc = item.get("document")
            if not doc:
                continue
            fields = doc.get("fields", {})
            results.append({
                "id": doc["name"].rsplit("/", 1)[-1],
                "title": fields.get("title", {}).get("stringValue", ""),
                "message": fields.get("message", {}).get("stringValue", ""),
                "link": fields.get("link", {}).get("stringValue", ""),
                "type": fields.get("type", {}).get("stringValue", ""),
                "read": fields.get("read", {}).get("booleanValue", False),
                "created_at": fields.get("createdAt", {}).get("timestampValue", ""),
            })
        return results
    except Exception:
        return []


def mark_notification_read(doc_id: str, id_token: str) -> bool:
    """Mark a single notification document as read. Requires an auth token."""
    url = f"{_DOC_BASE}/userNotifications/{doc_id}"
    headers = {"Authorization": f"Bearer {id_token}"}
    body = {"fields": {"read": {"booleanValue": True}}}
    params = {"updateMask.fieldPaths": "read", "key": _RDLADDER_KEY}
    try:
        resp = requests.patch(url, headers=headers, json=body, params=params, timeout=8)
        return resp.ok
    except Exception:
        return False


def mark_all_notifications_read(notifications: list[dict], id_token: str) -> None:
    """Mark all unread notifications as read. Runs each PATCH request in sequence."""
    for n in notifications:
        if not n.get("read"):
            mark_notification_read(n["id"], id_token)


def send_invitation(target_uid: str, sender_name: str, id_token: str) -> bool:
    """Create an invitation notification for target_uid from sender_name."""
    url = f"{_DOC_BASE}/userNotifications"
    headers = {"Authorization": f"Bearer {id_token}"}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body = {
        "fields": {
            "userId": {"stringValue": target_uid},
            "type": {"stringValue": "invitation"},
            "title": {"stringValue": "Game Invitation"},
            "message": {"stringValue": f"{sender_name} invited you to play Descent"},
            "read": {"booleanValue": False},
            "createdAt": {"timestampValue": now},
            "link": {"stringValue": ""},
        }
    }
    try:
        resp = requests.post(
            f"{url}?key={_RDLADDER_KEY}",
            headers=headers,
            json=body,
            timeout=8,
        )
        return resp.ok
    except Exception:
        return False
