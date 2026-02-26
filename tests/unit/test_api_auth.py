"""Tests for API key authentication."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from signalops.api.app import create_app
from signalops.storage.database import Base, get_engine


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Create a test client with a temp-file SQLite database.

    We patch SIGNALOPS_DB_URL so the app lifespan creates its engine
    against the same DB file where we've already created tables.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_url = f"sqlite:///{db_path}"

    # Pre-create tables in the temp DB
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
        app = create_app()
        with TestClient(app) as c:
            yield c

    # Clean up temp file
    try:
        os.unlink(db_path)
    except OSError:
        pass


class TestApiKeyAuth:
    def test_no_api_key_configured_allows_open_access(self, client: TestClient) -> None:
        """When SIGNALOPS_API_KEY is not set, requests pass without auth."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no SIGNALOPS_API_KEY is set
            os.environ.pop("SIGNALOPS_API_KEY", None)
            resp = client.get("/api/projects")
            assert resp.status_code == 200

    def test_invalid_api_key_returns_401(self, client: TestClient) -> None:
        with patch.dict(os.environ, {"SIGNALOPS_API_KEY": "valid-key"}):
            resp = client.get(
                "/api/projects",
                headers={"X-API-Key": "wrong-key"},
            )
            assert resp.status_code == 401

    def test_valid_api_key_accepted(self, client: TestClient) -> None:
        with patch.dict(os.environ, {"SIGNALOPS_API_KEY": "valid-key"}):
            resp = client.get(
                "/api/projects",
                headers={"X-API-Key": "valid-key"},
            )
            assert resp.status_code == 200

    def test_missing_header_when_key_required_returns_401(self, client: TestClient) -> None:
        """When SIGNALOPS_API_KEY is set but no header sent, returns 401."""
        with patch.dict(os.environ, {"SIGNALOPS_API_KEY": "valid-key"}):
            resp = client.get("/api/projects")
            assert resp.status_code == 401

    def test_empty_env_key_allows_open_access(self, client: TestClient) -> None:
        """Empty SIGNALOPS_API_KEY means open access (self-hosted mode)."""
        with patch.dict(os.environ, {"SIGNALOPS_API_KEY": ""}):
            resp = client.get(
                "/api/projects",
                headers={"X-API-Key": "anything"},
            )
            assert resp.status_code == 200
