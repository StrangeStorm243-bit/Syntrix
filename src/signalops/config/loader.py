"""Stub — real implementation on feat/data branch."""
import hashlib
import os
from pathlib import Path

import yaml

from .schema import ProjectConfig


def load_project(path):
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)
    raw = _resolve_env_vars(raw)
    return ProjectConfig(**raw)


def _resolve_env_vars(obj):
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            return os.environ.get(obj[2:-1], obj)
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def config_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
