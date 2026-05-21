"""Unit tests for app.utils.demo_rate_limiter.DemoRateLimiter.

We swap in a MagicMock SupabaseService whose `get_db_session()` yields a
session whose `.execute().fetchall()` returns whatever the test wants.
That lets us cover each of the three branches (allowed, over-hourly,
over-daily) plus the fail-open path without standing up Postgres.
"""

from __future__ import annotations

import pytest

from app.config import DEMO_IP_DAILY_LIMIT, DEMO_IP_HOURLY_LIMIT
from app.utils.demo_rate_limiter import DemoRateLimiter


@pytest.mark.asyncio
async def test_allows_first_session(mock_supabase, rate_limit_rows):
    """Counts of 1 for both windows mean we're well under both caps."""
    rate_limit_rows[:] = [("hour", 1), ("day", 1)]
    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.allowed is True
    assert result.reason is None
    assert result.retry_after is None


@pytest.mark.asyncio
async def test_allows_exactly_at_limit(mock_supabase, rate_limit_rows):
    """The limit is "max allowed", not "first rejected" — equal-to is fine."""
    rate_limit_rows[:] = [
        ("hour", DEMO_IP_HOURLY_LIMIT),
        ("day", DEMO_IP_DAILY_LIMIT - 1),
    ]
    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.allowed is True


@pytest.mark.asyncio
async def test_rejects_when_hourly_count_exceeds_limit(mock_supabase, rate_limit_rows):
    rate_limit_rows[:] = [("hour", DEMO_IP_HOURLY_LIMIT + 1), ("day", 1)]
    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.allowed is False
    assert result.reason == "DEMO_HOURLY_LIMIT_EXCEEDED"
    # Retry-after fires off the next hour boundary; bounds-check rather
    # than wall-clock match to keep the test deterministic.
    assert 1 <= result.retry_after <= 60 * 60


@pytest.mark.asyncio
async def test_rejects_when_daily_count_exceeds_limit(mock_supabase, rate_limit_rows):
    """Daily limit fires only if hourly is fine — otherwise hourly wins."""
    rate_limit_rows[:] = [("hour", 1), ("day", DEMO_IP_DAILY_LIMIT + 1)]
    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.allowed is False
    assert result.reason == "DEMO_DAILY_LIMIT_EXCEEDED"
    assert 1 <= result.retry_after <= 24 * 60 * 60


@pytest.mark.asyncio
async def test_hourly_takes_priority_over_daily(mock_supabase, rate_limit_rows):
    rate_limit_rows[:] = [
        ("hour", DEMO_IP_HOURLY_LIMIT + 1),
        ("day", DEMO_IP_DAILY_LIMIT + 1),
    ]
    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.reason == "DEMO_HOURLY_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_fail_open_on_db_error(mock_supabase):
    """DB hiccup must not 503 the demo — abuse limiter is friction, not core."""
    # Replace the contextmanager with one that raises on `execute`.
    from contextlib import contextmanager
    from unittest.mock import MagicMock

    boom_session = MagicMock()
    boom_session.execute = MagicMock(side_effect=RuntimeError("connection refused"))

    @contextmanager
    def _broken_session():
        yield boom_session

    mock_supabase.get_db_session = _broken_session

    result = await DemoRateLimiter(mock_supabase).check_and_increment("1.2.3.4")
    assert result.allowed is True
    assert result.reason is None
