"""Stub — real implementation on feat/data branch."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawPost:
    platform: str
    platform_id: str
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
    @abstractmethod
    def search(self, query, since_id=None, max_results=100): ...
    @abstractmethod
    def get_user(self, user_id): ...
    @abstractmethod
    def post_reply(self, in_reply_to_id, text): ...
    @abstractmethod
    def health_check(self): ...
