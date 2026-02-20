"""Tests for the exception hierarchy and retry utility."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from signalops.exceptions import (
    APIError,
    AuthenticationError,
    ConfigError,
    RateLimitError,
    SignalOpsError,
    StreamTierError,
    retry_with_backoff,
)

# ── Hierarchy tests ──


class TestExceptionHierarchy:
    def test_api_error_is_signalops_error(self) -> None:
        assert isinstance(APIError("x"), SignalOpsError)

    def test_rate_limit_error_is_api_error(self) -> None:
        assert isinstance(RateLimitError("x"), APIError)

    def test_authentication_error_is_api_error(self) -> None:
        assert isinstance(AuthenticationError(), APIError)

    def test_stream_tier_error_is_api_error(self) -> None:
        assert isinstance(StreamTierError(), APIError)

    def test_config_error_is_signalops_error(self) -> None:
        assert isinstance(ConfigError("bad"), SignalOpsError)


class TestAPIErrorAttributes:
    def test_defaults(self) -> None:
        err = APIError("fail")
        assert err.status_code is None
        assert err.retryable is False

    def test_custom_status_and_retryable(self) -> None:
        err = APIError("server error", status_code=503, retryable=True)
        assert err.status_code == 503
        assert err.retryable is True

    def test_rate_limit_error_attributes(self) -> None:
        err = RateLimitError("slow down", retry_after=30.0)
        assert err.status_code == 429
        assert err.retryable is True
        assert err.retry_after == 30.0

    def test_authentication_error_attributes(self) -> None:
        err = AuthenticationError()
        assert err.status_code == 401
        assert err.retryable is False

    def test_stream_tier_error_attributes(self) -> None:
        err = StreamTierError()
        assert err.status_code == 403
        assert err.retryable is False


# ── Retry tests ──


class TestRetryWithBackoff:
    @patch("signalops.exceptions.time.sleep")
    def test_succeeds_on_first_try(self, mock_sleep: object) -> None:
        result = retry_with_backoff(lambda: 42)
        assert result == 42

    @patch("signalops.exceptions.time.sleep")
    def test_succeeds_after_transient_failure(self, mock_sleep: object) -> None:
        calls = {"count": 0}

        def flaky() -> str:
            calls["count"] += 1
            if calls["count"] < 3:
                raise APIError("boom", status_code=500, retryable=True)
            return "ok"

        result = retry_with_backoff(flaky, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert calls["count"] == 3

    @patch("signalops.exceptions.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep: object) -> None:
        def always_fail() -> str:
            raise APIError("down", status_code=502, retryable=True)

        with pytest.raises(APIError, match="down"):
            retry_with_backoff(always_fail, max_retries=3, base_delay=0.01)

    @patch("signalops.exceptions.time.sleep")
    def test_does_not_retry_non_retryable(self, mock_sleep: object) -> None:
        calls = {"count": 0}

        def bad_request() -> str:
            calls["count"] += 1
            raise APIError("bad", status_code=400, retryable=False)

        with pytest.raises(APIError, match="bad"):
            retry_with_backoff(bad_request, max_retries=3, base_delay=0.01)
        assert calls["count"] == 1  # no retry

    @patch("signalops.exceptions.time.sleep")
    def test_does_not_retry_auth_error(self, mock_sleep: object) -> None:
        calls = {"count": 0}

        def auth_fail() -> str:
            calls["count"] += 1
            raise AuthenticationError("nope")

        with pytest.raises(AuthenticationError):
            retry_with_backoff(auth_fail, max_retries=3, base_delay=0.01)
        assert calls["count"] == 1

    @patch("signalops.exceptions.time.sleep")
    def test_respects_retry_after(self, mock_sleep: object) -> None:
        calls = {"count": 0}

        def rate_limited() -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RateLimitError("wait", retry_after=30.0)
            return "ok"

        result = retry_with_backoff(rate_limited, max_retries=3, base_delay=1.0)
        assert result == "ok"
        # sleep should have been called with at least 30.0
        mock_sleep.assert_called_once()  # type: ignore[union-attr]
        sleep_time: float = mock_sleep.call_args[0][0]  # type: ignore[union-attr]
        assert sleep_time >= 30.0

    @patch("signalops.exceptions.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep: object) -> None:
        calls = {"count": 0}

        def fail_twice() -> str:
            calls["count"] += 1
            if calls["count"] <= 2:
                raise APIError("retry me", status_code=500, retryable=True)
            return "done"

        result = retry_with_backoff(fail_twice, max_retries=3, base_delay=1.0, max_delay=60.0)
        assert result == "done"
        assert mock_sleep.call_count == 2  # type: ignore[union-attr]
        delays = [c[0][0] for c in mock_sleep.call_args_list]  # type: ignore[union-attr]
        # base_delay * 2^0 = 1.0, base_delay * 2^1 = 2.0
        assert delays[0] == pytest.approx(1.0)
        assert delays[1] == pytest.approx(2.0)
