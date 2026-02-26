"""Onboarding setup endpoints."""

from __future__ import annotations

import logging
import os
from typing import Any

import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from signalops.api.deps import get_db
from signalops.pipeline.sequence_engine import SequenceEngine
from signalops.storage.database import Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/setup", tags=["setup"])
settings_router = APIRouter(prefix="/api", tags=["settings"])


# ── Pydantic request/response models ──


class SetupRequest(BaseModel):
    """Onboarding wizard submission."""

    # Step 1: Company
    project_name: str
    product_url: str
    description: str
    problem_statement: str
    # Step 2: ICP
    role_keywords: list[str]
    tweet_topics: list[str]
    min_followers: int = 200
    languages: list[str] = ["en"]
    # Step 3: Twitter
    twitter_username: str
    twitter_password: str
    x_api_key: str | None = None
    # Step 4: Persona
    persona_name: str
    persona_role: str
    persona_tone: str = "helpful"
    voice_notes: str = ""
    example_reply: str = ""
    llm_provider: str = "ollama"  # ollama or cloud
    llm_api_key: str | None = None
    # Step 5: Sequence
    sequence_template: str = "gentle_touch"  # gentle_touch, direct, full
    max_actions_per_day: int = 20
    require_approval: bool = True


class SetupStatus(BaseModel):
    """Whether setup is complete."""

    is_complete: bool
    project_id: str | None = None
    project_name: str | None = None


class TestConnectionRequest(BaseModel):
    """Request body for testing Twitter credentials."""

    username: str
    password: str


class TestConnectionResult(BaseModel):
    """Result of testing Twitter credentials."""

    success: bool
    message: str
    username: str | None = None


class SettingsUpdateRequest(BaseModel):
    """Partial update for settings (all fields optional)."""

    twitter_username: str | None = None
    twitter_password: str | None = None
    llm_provider: str | None = None
    llm_api_key: str | None = None
    max_actions_per_day: int | None = None
    require_approval: bool | None = None


class SettingsUpdateResponse(BaseModel):
    """Result of a settings update."""

    success: bool
    message: str


# Lazy-loaded TwikitConnector to avoid import errors when twikit is not installed.
# This will be replaced by a real import once Terminal 1 adds twikit_connector.py.
TwikitConnector: Any = None


def _get_twikit_connector_class() -> Any:
    """Lazily import TwikitConnector."""
    global TwikitConnector  # noqa: PLW0603
    if TwikitConnector is None:
        from signalops.connectors.twikit_connector import (
            TwikitConnector as _Cls,
        )

        TwikitConnector = _Cls
    return TwikitConnector


# ── Routes ──


@router.get("/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    """Check if initial setup is complete (any project exists)."""
    project = db.query(Project).first()
    if project:
        return SetupStatus(
            is_complete=True,
            project_id=str(project.id),
            project_name=str(project.name),
        )
    return SetupStatus(is_complete=False)


@router.post("/test-connection", response_model=TestConnectionResult)
def test_twitter_connection(
    req: TestConnectionRequest,
) -> TestConnectionResult:
    """Test Twitter credentials via twikit."""
    try:
        cls = _get_twikit_connector_class()
        connector = cls(username=req.username, password=req.password)
        healthy: bool = connector.health_check()
        if healthy:
            return TestConnectionResult(
                success=True,
                message="Connected successfully",
                username=req.username,
            )
        # Try actually logging in
        connector._ensure_client()
        return TestConnectionResult(
            success=True,
            message="Connected successfully",
            username=req.username,
        )
    except Exception as e:
        return TestConnectionResult(
            success=False,
            message=f"Connection failed: {e}",
        )


@router.post("", response_model=SetupStatus)
def complete_setup(
    req: SetupRequest,
    db: Session = Depends(get_db),
) -> SetupStatus:
    """Complete onboarding — creates project config + DB record + default sequences."""
    project_id = req.project_name.lower().replace(" ", "-").replace("_", "-")

    # Generate search queries from topics
    queries: list[dict[str, Any]] = []
    for topic in req.tweet_topics:
        queries.append(
            {
                "text": f"{topic} -is:retweet lang:en",
                "label": topic,
                "platform": "x",
                "max_results_per_run": 100,
                "enabled": True,
            }
        )

    # Build project config YAML
    config: dict[str, Any] = {
        "project_id": project_id,
        "project_name": req.project_name,
        "description": req.description,
        "product_url": req.product_url,
        "platforms": {"x": {"enabled": True, "search_type": "recent"}},
        "queries": queries,
        "icp": {
            "min_followers": req.min_followers,
            "languages": req.languages,
            "prefer_bios_containing": req.role_keywords,
        },
        "relevance": {
            "system_prompt": (
                f"You are a relevance judge for {req.project_name}. "
                f"{req.description}. The product solves: {req.problem_statement}. "
                "Evaluate if this tweet indicates someone who might benefit "
                "from this product."
            ),
            "positive_signals": [f"Expressing frustration related to: {req.problem_statement}"],
            "negative_signals": ["Recruiting posts", "Bot-like behavior"],
        },
        "persona": {
            "name": req.persona_name,
            "role": req.persona_role,
            "tone": req.persona_tone,
            "voice_notes": req.voice_notes,
            "example_reply": req.example_reply,
        },
        "rate_limits": {
            "max_replies_per_hour": max(1, req.max_actions_per_day // 8),
            "max_replies_per_day": req.max_actions_per_day,
        },
        "llm": {
            "judge_model": (
                "ollama/llama3.2:3b" if req.llm_provider == "ollama" else "gpt-4o-mini"
            ),
            "draft_model": ("ollama/mistral:7b" if req.llm_provider == "ollama" else "gpt-4o-mini"),
            "temperature": 0.3,
            "max_tokens": 1024,
        },
    }

    # Write YAML
    projects_dir = "projects"
    os.makedirs(projects_dir, exist_ok=True)
    config_path = f"{projects_dir}/{project_id}.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Store Twitter credentials as env vars (for this process)
    from signalops.utils.credentials import encrypt_credential

    os.environ["TWIKIT_USERNAME"] = req.twitter_username  # username doesn't need encryption
    os.environ["TWIKIT_PASSWORD"] = encrypt_credential(req.twitter_password)
    if req.x_api_key:
        os.environ["X_BEARER_TOKEN"] = req.x_api_key

    # Create DB record
    project = Project(
        id=project_id,
        name=req.project_name,
        config_path=config_path,
        is_active=True,
    )
    # Deactivate other projects
    db.query(Project).update({"is_active": False})
    db.add(project)
    db.flush()

    # Create default sequences (use a no-op connector since we're just seeding templates)
    seq_engine = SequenceEngine(db, None)
    seq_engine.create_default_sequences(project_id)

    db.commit()

    return SetupStatus(
        is_complete=True,
        project_id=project_id,
        project_name=req.project_name,
    )


# ── Settings Routes ──


@settings_router.put("/settings", response_model=SettingsUpdateResponse)
def update_settings(
    req: SettingsUpdateRequest,
    db: Session = Depends(get_db),
) -> SettingsUpdateResponse:
    """Update settings — persists Twitter creds to env vars and config to YAML."""
    # Find active project
    project: Project | None = db.query(Project).filter(Project.is_active.is_(True)).first()
    if project is None:
        return SettingsUpdateResponse(
            success=False,
            message="No active project found. Complete setup first.",
        )

    # Update env vars for Twitter credentials
    from signalops.utils.credentials import encrypt_credential

    if req.twitter_username is not None:
        os.environ["TWIKIT_USERNAME"] = req.twitter_username
    if req.twitter_password is not None:
        os.environ["TWIKIT_PASSWORD"] = encrypt_credential(req.twitter_password)

    # Load, modify, and save the project YAML config
    config_path: str = str(project.config_path)
    if os.path.exists(config_path):
        with open(config_path) as f:
            config: dict[str, Any] = yaml.safe_load(f) or {}
    else:
        config = {}

    changed = False

    if req.llm_provider is not None:
        llm_section = config.setdefault("llm", {})
        if req.llm_provider == "ollama":
            llm_section["judge_model"] = "ollama/llama3.2:3b"
            llm_section["draft_model"] = "ollama/mistral:7b"
        else:
            llm_section["judge_model"] = "gpt-4o-mini"
            llm_section["draft_model"] = "gpt-4o-mini"
        changed = True

    if req.llm_api_key is not None and req.llm_api_key:
        env_key = "OPENAI_API_KEY"
        if req.llm_provider == "anthropic":
            env_key = "ANTHROPIC_API_KEY"
        os.environ[env_key] = req.llm_api_key

    if req.max_actions_per_day is not None:
        rate_section = config.setdefault("rate_limits", {})
        rate_section["max_replies_per_day"] = req.max_actions_per_day
        rate_section["max_replies_per_hour"] = max(1, req.max_actions_per_day // 8)
        changed = True

    if req.require_approval is not None:
        config["require_approval"] = req.require_approval
        changed = True

    if changed:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return SettingsUpdateResponse(
        success=True,
        message="Settings updated successfully.",
    )
