"""API key authentication for the SignalOps REST API."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


async def require_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str | None:
    """Validate X-API-Key if SIGNALOPS_API_KEY is set. Skip if not configured."""
    expected = os.environ.get("SIGNALOPS_API_KEY", "")
    if not expected:
        return None  # No API key configured — open access (self-hosted mode)
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
