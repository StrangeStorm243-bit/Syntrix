"""Connector factory — creates platform connectors from config."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from signalops.connectors.base import Connector, Platform

if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig

logger = logging.getLogger(__name__)


class ConnectorFactory:
    """Creates and caches connector instances based on platform config.

    WARNING: _instances is a class-level mutable dict shared across all tests.
    Every test that uses ConnectorFactory MUST call ConnectorFactory.clear_cache()
    in setup (see test_connector_factory.py setup_method for the pattern).
    """

    _instances: dict[str, Connector] = {}

    @classmethod
    def create(
        cls,
        platform: Platform | str,
        config: ProjectConfig | None = None,
        **kwargs: Any,
    ) -> Connector:
        """Create a connector for the given platform.

        Args:
            platform: Platform enum or string identifier
            config: Project config (optional, used for platform-specific settings)
            **kwargs: Additional kwargs passed to connector constructor

        Returns:
            Connector instance

        Raises:
            ValueError: If platform is unknown
            NotImplementedError: If platform connector is not yet implemented
        """
        if isinstance(platform, str):
            platform = Platform.from_string(platform)

        cache_key = f"{platform.value}:{id(config)}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        connector = cls._build_connector(platform, config, **kwargs)
        cls._instances[cache_key] = connector
        return connector

    @classmethod
    def create_all(cls, config: ProjectConfig) -> dict[Platform, Connector]:
        """Create connectors for all enabled platforms in config."""
        connectors: dict[Platform, Connector] = {}
        platforms_config = getattr(config, "platforms", None)

        if not platforms_config:
            # Default: X only
            connectors[Platform.X] = cls.create(Platform.X, config)
            return connectors

        for platform_name, platform_cfg in _iter_platform_configs(platforms_config):
            if not platform_cfg.enabled:
                continue
            try:
                platform = Platform.from_string(platform_name)
                connectors[platform] = cls.create(platform, config)
            except (ValueError, NotImplementedError) as e:
                logger.warning("Skipping platform '%s': %s", platform_name, e)

        return connectors

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached connector instances."""
        cls._instances.clear()

    @classmethod
    def _build_connector(
        cls,
        platform: Platform,
        config: ProjectConfig | None,
        **kwargs: Any,
    ) -> Connector:
        """Build a connector instance for the given platform."""
        if platform == Platform.X:
            return cls._build_x_connector(config, **kwargs)
        if platform == Platform.LINKEDIN:
            return cls._build_linkedin_connector(config, **kwargs)
        if platform == Platform.SOCIALDATA:
            return cls._build_socialdata_connector(config, **kwargs)

        raise ValueError(f"No connector implementation for platform: {platform.value}")

    @classmethod
    def _build_x_connector(cls, config: ProjectConfig | None, **kwargs: Any) -> Connector:
        """Build X/Twitter connector."""
        from signalops.connectors.x_api import XConnector

        bearer_token = kwargs.get("bearer_token") or os.environ.get("X_BEARER_TOKEN", "")
        if not bearer_token:
            raise ValueError(
                "X_BEARER_TOKEN environment variable is required for X connector. "
                "Set it in your .env file."
            )
        return XConnector(bearer_token=bearer_token)

    @classmethod
    def _build_linkedin_connector(cls, config: ProjectConfig | None, **kwargs: Any) -> Connector:
        """Build LinkedIn connector (stubbed)."""
        from signalops.connectors.linkedin import LinkedInConnector

        return LinkedInConnector()

    @classmethod
    def _build_socialdata_connector(cls, config: ProjectConfig | None, **kwargs: Any) -> Connector:
        """Build SocialData connector."""
        raise NotImplementedError(
            "SocialData connector is not yet implemented. "
            "Set platform to 'x' in your project config."
        )


def _iter_platform_configs(
    platforms_config: Any,
) -> list[tuple[str, Any]]:
    """Iterate over platform configs, yielding (name, config) pairs."""
    from signalops.config.schema import PlatformsConfig

    if isinstance(platforms_config, PlatformsConfig):
        result: list[tuple[str, Any]] = []
        for field_name in PlatformsConfig.model_fields:
            cfg = getattr(platforms_config, field_name)
            result.append((field_name, cfg))
        return result
    return []
