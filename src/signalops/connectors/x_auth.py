"""OAuth 2.0 PKCE flow for X API authentication."""

import base64
import hashlib
import json
import secrets
import time
from pathlib import Path

import httpx

from signalops.config.defaults import DEFAULT_CREDENTIALS_DIR

CREDENTIALS_FILE = "credentials.json"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code_verifier and code_challenge pair."""
    code_verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def build_auth_url(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    scopes: list[str] | None = None,
    state: str | None = None,
) -> str:
    """Build the OAuth 2.0 authorization URL for X."""
    if scopes is None:
        scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]

    if state is None:
        state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTHORIZE_URL}?{query}"


def exchange_code(
    client_id: str,
    client_secret: str | None,
    code: str,
    code_verifier: str,
    redirect_uri: str,
) -> dict:
    """Exchange authorization code for tokens."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    auth = None
    if client_secret:
        auth = (client_id, client_secret)
    else:
        data["client_id"] = client_id

    with httpx.Client() as client:
        response = client.post(TOKEN_URL, data=data, auth=auth)
        response.raise_for_status()
        tokens = response.json()

    tokens["expires_at"] = time.time() + tokens.get("expires_in", 7200)
    return tokens


def refresh_token(
    client_id: str,
    client_secret: str | None,
    refresh_tok: str,
) -> dict:
    """Refresh an expired access token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
    }

    auth = None
    if client_secret:
        auth = (client_id, client_secret)
    else:
        data["client_id"] = client_id

    with httpx.Client() as client:
        response = client.post(TOKEN_URL, data=data, auth=auth)
        response.raise_for_status()
        tokens = response.json()

    tokens["expires_at"] = time.time() + tokens.get("expires_in", 7200)
    return tokens


def store_credentials(
    credentials: dict,
    path: Path | None = None,
) -> None:
    """Store credentials as JSON file."""
    if path is None:
        path = DEFAULT_CREDENTIALS_DIR / CREDENTIALS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(credentials, f, indent=2)


def load_credentials(path: Path | None = None) -> dict | None:
    """Load credentials from JSON file. Returns None if not found."""
    if path is None:
        path = DEFAULT_CREDENTIALS_DIR / CREDENTIALS_FILE
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def is_token_expired(credentials: dict) -> bool:
    """Check if the access token has expired (with 5-minute buffer)."""
    expires_at = credentials.get("expires_at", 0)
    return time.time() > (expires_at - 300)
