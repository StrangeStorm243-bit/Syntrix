"""Abstract base class for platform connectors and shared data types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


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
    metrics: dict = field(default_factory=dict)
    entities: dict = field(default_factory=dict)
    raw_json: dict = field(default_factory=dict)


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
    def get_user(self, user_id: str) -> dict:
        """Fetch user profile by ID."""

    @abstractmethod
    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply. Returns the new post's platform ID."""

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity and auth."""
