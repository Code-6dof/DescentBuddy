"""Firebase authentication — rdladder accounts for identity, descent-buddy for presence token."""

import json
import os
import sys
from pathlib import Path

import requests

from core.api_keys import DESCENT_BUDDY_KEY as _DESCENT_BUDDY_KEY
from core.api_keys import RDLADDER_KEY as _RDLADDER_KEY


def _config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    return base / "descentbuddy"


_SESSION_PATH = _config_dir() / "session.json"

_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
_ANON_SIGN_UP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"
_RDLADDER_FIRESTORE = "https://firestore.googleapis.com/v1/projects/rdladder/databases/(default)/documents"

_PROFILE_COLLECTIONS = ["users", "pilots", "players", "members"]
_USERNAME_FIELDS = ["username", "name", "callsign", "pilot_name", "handle", "displayName"]


def fetch_rdladder_username_public(uid: str) -> str | None:
    """Fetch username from rdladder Firestore without an auth token (public read)."""
    try:
        resp = requests.get(
            f"{_RDLADDER_FIRESTORE}/users/{uid}",
            params={"key": _RDLADDER_KEY},
            timeout=8,
        )
        if resp.ok:
            value = (
                resp.json()
                .get("fields", {})
                .get("username", {})
                .get("stringValue", "")
                .strip()
            )
            return value or None
    except Exception:
        pass
    return None

_ERROR_MAP = {
    "INVALID_EMAIL": "Invalid email address.",
    "INVALID_PASSWORD": "Incorrect password.",
    "EMAIL_NOT_FOUND": "No account found with that email.",
    "INVALID_LOGIN_CREDENTIALS": "Email or password is incorrect.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Try again later.",
    "USER_DISABLED": "This account has been disabled.",
}


def sign_in(email: str, password: str) -> dict:
    """Authenticate against rdladder Firebase Auth.

    Returns a session dict: {uid, username, email}.
    Raises RuntimeError with a human-readable message on failure.
    """
    resp = requests.post(
        f"{_SIGN_IN_URL}?key={_RDLADDER_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    if not resp.ok:
        raw = data.get("error", {}).get("message", "Sign-in failed.")
        raise RuntimeError(_friendly_error(raw))

    uid = data["localId"]
    id_token = data.get("idToken", "")

    username = _fetch_rdladder_username(uid, id_token)
    if not username:
        username = data.get("displayName") or email.split("@")[0]

    session = {
        "uid": uid,
        "username": username,
        "email": email,
        "idToken": id_token,
        "refreshToken": data.get("refreshToken", ""),
    }
    _save_session(session)
    return session


def _fetch_rdladder_username(uid: str, id_token: str) -> str | None:
    """Try to read the user's real username from the rdladder Firestore profile."""
    public = fetch_rdladder_username_public(uid)
    if public:
        return public
    headers = {"Authorization": f"Bearer {id_token}"}
    for collection in _PROFILE_COLLECTIONS:
        try:
            resp = requests.get(
                f"{_RDLADDER_FIRESTORE}/{collection}/{uid}",
                headers=headers,
                params={"key": _RDLADDER_KEY},
                timeout=8,
            )
            if not resp.ok:
                continue
            fields = resp.json().get("fields", {})
            for field in _USERNAME_FIELDS:
                value = fields.get(field, {}).get("stringValue", "").strip()
                if value:
                    return value
        except Exception:
            continue
    return None


def get_fresh_id_token(refresh_token: str) -> str | None:
    """Exchange a refreshToken for a new short-lived idToken."""
    try:
        resp = requests.post(
            f"{_REFRESH_URL}?key={_RDLADDER_KEY}",
            json={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=10,
        )
        if resp.ok:
            return resp.json().get("id_token")
    except Exception:
        pass
    return None


def get_db_token() -> str | None:
    """Sign in anonymously to descent-buddy and return a Firestore write token."""
    try:
        resp = requests.post(
            f"{_ANON_SIGN_UP_URL}?key={_DESCENT_BUDDY_KEY}",
            json={"returnSecureToken": True},
            timeout=10,
        )
        if resp.ok:
            return resp.json().get("idToken")
    except Exception:
        pass
    return None


def load_session() -> dict | None:
    """Load the saved session from disk. Returns None if none exists."""
    try:
        if _SESSION_PATH.exists():
            return json.loads(_SESSION_PATH.read_text())
    except Exception:
        pass
    return None


def clear_session() -> None:
    """Delete the saved session file."""
    try:
        if _SESSION_PATH.exists():
            _SESSION_PATH.unlink()
    except Exception:
        pass


def _save_session(session: dict) -> None:
    _SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    to_save = {k: v for k, v in session.items() if k != "idToken"}
    _SESSION_PATH.write_text(json.dumps(to_save))


def _friendly_error(raw: str) -> str:
    for key, friendly in _ERROR_MAP.items():
        if key in raw:
            return friendly
    return raw
