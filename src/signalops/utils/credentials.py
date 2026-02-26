"""Credential encryption utilities."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_KEY_DIR = Path.home() / ".signalops"
_KEY_FILE = _KEY_DIR / "fernet.key"


def _get_or_create_key() -> bytes:
    """Load or generate a Fernet encryption key."""
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()
    _KEY_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
    except ImportError:
        key = base64.urlsafe_b64encode(b"0" * 32)  # Fallback, not secure
    _KEY_FILE.write_bytes(key)
    return key


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential string."""
    key = _get_or_create_key()
    try:
        from cryptography.fernet import Fernet

        return Fernet(key).encrypt(plaintext.encode()).decode()
    except ImportError:
        return base64.b64encode(plaintext.encode()).decode()


def decrypt_credential(encrypted: str) -> str:
    """Decrypt a credential string. Returns as-is if not encrypted."""
    key = _get_or_create_key()
    try:
        from cryptography.fernet import Fernet

        return Fernet(key).decrypt(encrypted.encode()).decode()
    except (ImportError, Exception):  # noqa: BLE001
        return encrypted  # Not encrypted or decryption failed — return as-is
