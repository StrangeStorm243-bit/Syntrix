"""Notification system for high-score lead alerts."""

from __future__ import annotations

from signalops.notifications.base import (
    NotificationPayload,
    Notifier,
    get_notifiers,
    notify_high_scores,
)

__all__ = [
    "Notifier",
    "NotificationPayload",
    "get_notifiers",
    "notify_high_scores",
]
