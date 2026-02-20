"""YAML config loader with environment variable resolution."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .defaults import DEFAULT_CREDENTIALS_DIR, DEFAULT_PROJECTS_DIR
from .schema import ProjectConfig

logger = logging.getLogger(__name__)


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


# ── Multi-project helpers ──


def scan_projects(directory: str | Path = DEFAULT_PROJECTS_DIR) -> list[ProjectConfig]:
    """Scan a directory for project YAML configs and load all valid ones.

    Invalid configs are logged as warnings and skipped.
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    configs: list[ProjectConfig] = []
    for yaml_file in sorted(directory.glob("*.yaml")):
        try:
            configs.append(load_project(yaml_file))
        except Exception as e:
            logger.warning("Skipping invalid project config %s: %s", yaml_file.name, e)

    return configs


def get_active_project() -> str | None:
    """Read active project ID from ~/.signalops/active_project.

    Returns None if no active project is set.
    """
    active_file = DEFAULT_CREDENTIALS_DIR / "active_project"
    if active_file.exists():
        name = active_file.read_text().strip()
        return name if name else None
    return None


def set_active_project(project_id: str) -> None:
    """Write active project ID to ~/.signalops/active_project."""
    DEFAULT_CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    active_file = DEFAULT_CREDENTIALS_DIR / "active_project"
    active_file.write_text(project_id)


def resolve_project(
    project_name: str | None = None,
    projects_dir: str | Path = DEFAULT_PROJECTS_DIR,
) -> ProjectConfig:
    """Resolve a project config by name or active project.

    Resolution order:
    1. Explicit project_name if provided
    2. Active project from ~/.signalops/active_project
    3. Raises ValueError if neither is available

    Args:
        project_name: Explicit project name to load.
        projects_dir: Directory containing project YAML files.

    Returns:
        Loaded and validated ProjectConfig.

    Raises:
        ValueError: If no project can be resolved.
        FileNotFoundError: If the resolved config file doesn't exist.
    """
    projects_dir = Path(projects_dir)

    if project_name is None:
        project_name = get_active_project()

    if project_name is None:
        msg = "No project specified and no active project set. Run: signalops project set <name>"
        raise ValueError(msg)

    config_path = projects_dir / f"{project_name}.yaml"
    if not config_path.exists():
        msg = f"Project config not found: {config_path}"
        raise FileNotFoundError(msg)

    return load_project(config_path)
