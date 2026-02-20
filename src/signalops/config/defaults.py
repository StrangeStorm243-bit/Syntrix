"""Stub — real implementation on feat/data branch."""
from pathlib import Path

DEFAULT_DB_URL = "sqlite:///signalops.db"
DEFAULT_CREDENTIALS_DIR = Path.home() / ".signalops"
DEFAULT_PROJECTS_DIR = Path("projects")
MAX_TWEET_LENGTH = 280
MAX_REPLY_LENGTH = 240
DEFAULT_SEARCH_MAX_RESULTS = 100
SUPPORTED_PLATFORMS = ["x"]
