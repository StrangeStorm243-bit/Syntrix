"""Abstract base class for platform connectors and shared data types."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class Platform(enum.Enum):
    """Supported social media platforms."""

    X = "x"
    LINKEDIN = "linkedin"
    SOCIALDATA = "socialdata"

    @classmethod
    def from_string(cls, value: str) -> Platform:
        """Case-insensitive platform lookup."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"Unknown platform '{value}'. Supported platforms: {valid}") from None


@dataclass
class RawPost:
    """A single post from any social platform, before normalization."""

    platform: str  # "x", "linkedin", etc.
    platform_id: str  # Tweet ID (string, not int)
    author_id: str
    author_username: str
    author_display_name: str
    author_followers: int
    author_verified: bool
    text: str
    created_at: datetime
    language: str | None
    reply_to_id: str | None
    conversation_id: str | None
    metrics: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, Any] = field(default_factory=dict)
    raw_json: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate platform is a known value."""
        Platform.from_string(self.platform)  # Raises if unknown


class Connector(ABC):
    """Abstract base class for social platform connectors."""

    @abstractmethod
    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """Search for posts matching query. Returns newest first."""

    @abstractmethod
    def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch user profile by ID."""

    @abstractmethod
    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply. Returns the new post's platform ID."""

    @abstractmethod
    def like(self, post_id: str) -> bool:
        """Like a post. Returns True if successful."""
        ...

    @abstractmethod
    def follow(self, user_id: str) -> bool:
        """Follow a user. Returns True if successful."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity and auth."""
