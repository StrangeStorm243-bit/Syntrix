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

# Platform support
SUPPORTED_PLATFORMS = ["x"]
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "ja"]
