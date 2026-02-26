"""LinkedIn connector — stubbed implementation ready for API integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from signalops.connectors.base import Connector, RawPost

logger = logging.getLogger(__name__)

# LinkedIn-specific engagement metrics mapping
LINKEDIN_METRIC_MAPPING = {
    "numLikes": "likes",
    "numComments": "replies",  # Map to our generic "replies"
    "numShares": "retweets",  # Map to our generic "retweets"
    "numImpressions": "views",
}


@dataclass
class LinkedInPost:
    """LinkedIn-specific post data before normalization to RawPost."""

    urn: str  # LinkedIn URN (e.g., "urn:li:share:123456")
    author_urn: str  # Author URN
    author_name: str
    author_headline: str  # LinkedIn "bio" equivalent
    author_connections: int  # Approximate connection count
    author_is_premium: bool
    text: str
    post_type: str  # "article", "post", "share"
    published_at: str  # ISO datetime
    reactions: int
    comments: int
    shares: int
    impressions: int | None  # Only available for own company posts


class LinkedInConnector(Connector):
    """LinkedIn connector — reads LinkedIn posts and profiles.

    IMPORTANT: This connector is currently STUBBED. All methods raise
    NotImplementedError with guidance on what's needed for full implementation.

    To implement:
    1. Apply for LinkedIn Marketing Developer Platform access
    2. Obtain OAuth 2.0 client credentials
    3. Implement the LinkedIn REST API v2 calls in each method

    LinkedIn API docs: https://learn.microsoft.com/en-us/linkedin/
    """

    def __init__(
        self,
        access_token: str | None = None,
        base_url: str = "https://api.linkedin.com/v2",
    ) -> None:
        self._access_token = access_token
        self._base_url = base_url
        self._is_stubbed = access_token is None

    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """Search LinkedIn posts matching query.

        LinkedIn API equivalent: Content Search API
        Requires: Marketing Developer Platform access, rw_ads scope

        Current status: STUBBED
        """
        if self._is_stubbed:
            logger.warning(
                "LinkedIn connector is stubbed. Returning empty results. "
                "To enable: set LINKEDIN_ACCESS_TOKEN and implement API calls."
            )
            return []

        # TODO: Implement LinkedIn Content Search API
        # POST https://api.linkedin.com/v2/search
        # Headers: Authorization: Bearer {access_token}
        # Body: {"keywords": query, "type": "CONTENT", ...}
        raise NotImplementedError(
            "LinkedIn search is not yet implemented. "
            "See https://learn.microsoft.com/en-us/linkedin/marketing/"
            "community-management/shares"
        )

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch LinkedIn profile by URN.

        LinkedIn API equivalent: GET /v2/people/{id}
        Requires: r_liteprofile scope

        Current status: STUBBED
        """
        if self._is_stubbed:
            return {
                "id": user_id,
                "platform": "linkedin",
                "name": "Unknown",
                "headline": "",
                "connections": 0,
                "is_premium": False,
                "_stubbed": True,
            }

        raise NotImplementedError(
            "LinkedIn user profile fetch is not yet implemented. "
            "See https://learn.microsoft.com/en-us/linkedin/shared/"
            "references/v2/profile"
        )

    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a comment on a LinkedIn post.

        LinkedIn API equivalent: POST /v2/socialActions/{id}/comments
        Requires: w_member_social scope

        Current status: STUBBED (not planned for v0.3 — LinkedIn is read-only)
        """
        raise NotImplementedError(
            "LinkedIn reply/comment is not implemented. "
            "v0.3 LinkedIn support is read-only intelligence only. "
            "Comment posting requires w_member_social scope and explicit user consent."
        )

    def like(self, post_id: str) -> bool:
        """Like a LinkedIn post. Not implemented."""
        raise NotImplementedError(
            "LinkedIn like is not implemented. LinkedIn connector is read-only intelligence only."
        )

    def follow(self, user_id: str) -> bool:
        """Follow a LinkedIn user. Not implemented."""
        raise NotImplementedError(
            "LinkedIn follow is not implemented. LinkedIn connector is read-only intelligence only."
        )

    def health_check(self) -> bool:
        """Verify LinkedIn API connectivity.

        Checks: valid access token, required scopes available
        """
        if self._is_stubbed:
            logger.info("LinkedIn connector health check: STUBBED (no access token)")
            return False

        # TODO: Call GET /v2/me to verify auth
        raise NotImplementedError("LinkedIn health check not yet implemented.")

    def to_raw_post(self, linkedin_post: LinkedInPost) -> RawPost:
        """Convert a LinkedIn-specific post to the generic RawPost format."""
        from datetime import UTC, datetime

        try:
            created_at = datetime.fromisoformat(linkedin_post.published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now(UTC)

        return RawPost(
            platform="linkedin",
            platform_id=linkedin_post.urn,
            author_id=linkedin_post.author_urn,
            author_username=linkedin_post.author_name.lower().replace(" ", "-"),
            author_display_name=linkedin_post.author_name,
            author_followers=linkedin_post.author_connections,
            author_verified=linkedin_post.author_is_premium,
            text=linkedin_post.text,
            created_at=created_at,
            language=None,  # LinkedIn API provides this
            reply_to_id=None,
            conversation_id=None,
            metrics={
                "likes": linkedin_post.reactions,
                "retweets": linkedin_post.shares,  # Mapped
                "replies": linkedin_post.comments,  # Mapped
                "views": linkedin_post.impressions or 0,
            },
            entities={"urls": [], "mentions": [], "hashtags": []},
            raw_json={"_source": "linkedin", "_stubbed": True},
        )
