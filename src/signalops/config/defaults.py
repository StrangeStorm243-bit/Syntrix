"""Default values and constants used across the application."""

from pathlib import Path

# Database
DEFAULT_DB_URL = "sqlite:///signalops.db"

# Filesystem paths
DEFAULT_CREDENTIALS_DIR = Path.home() / ".signalops"
DEFAULT_PROJECTS_DIR = Path("projects")

# Tweet constraints
MAX_TWEET_LENGTH = 280
MAX_REPLY_LENGTH = 240

# API defaults
DEFAULT_SEARCH_MAX_RESULTS = 100
DEFAULT_RATE_LIMITS = {
    "max_replies_per_hour": 5,
    "max_replies_per_day": 20,
}

# LLM defaults (Ollama — $0/month)
DEFAULT_JUDGE_MODEL = "ollama/llama3.2:3b"
DEFAULT_DRAFT_MODEL = "ollama/mistral:7b"
DEFAULT_LLM_TEMPERATURE = 0.3
DEFAULT_LLM_MAX_TOKENS = 1024

# Platform support
SUPPORTED_PLATFORMS = ["x"]
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "ja"]
