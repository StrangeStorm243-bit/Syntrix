"""API key authentication for the SignalOps REST API."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Validate the X-API-Key header against SIGNALOPS_API_KEY env var."""
    expected = os.environ.get("SIGNALOPS_API_KEY", "")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
