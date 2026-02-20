"""YAML config loader with environment variable resolution."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import yaml

from .schema import ProjectConfig


def load_project(path: str | Path) -> ProjectConfig:
    """Load and validate a project.yaml file."""
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)

    # Resolve environment variables in string values
    raw = _resolve_env_vars(raw)

    config = ProjectConfig(**raw)
    return config


def _resolve_env_vars(obj: Any) -> Any:
    """Recursively replace ${VAR} with os.environ[VAR]."""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var = obj[2:-1]
            return os.environ.get(var, obj)
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def config_hash(path: str | Path) -> str:
    """SHA-256 of config file for change detection."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
