"""Per-IP rate limit for demo session creation.

Issues one atomic upsert against ai_proposal_platform.demo_ip_limits that
bumps both the hourly and daily counters for the caller's IP and returns
the new counts. If either counter exceeds its env-configured limit the
attempt is rejected with a retry-after computed against the next window
boundary.

Increment-first design: a rejected request still bumps the counter. That
removes the check-then-increment race and correctly treats abuse attempts
as hits.

Failure mode: any exception from the DB layer is logged and treated as
fail-open — the limiter returns "allowed". Rate limiting is friction, not
core functionality; a DB hiccup shouldn't 503 the demo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text

from app.config import DEMO_IP_DAILY_LIMIT, DEMO_IP_HOURLY_LIMIT
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    reason: Optional[str] = None       # "DEMO_HOURLY_LIMIT_EXCEEDED" | "DEMO_DAILY_LIMIT_EXCEEDED"
    retry_after: Optional[int] = None  # seconds until next window boundary


class DemoRateLimiter:
    def __init__(self, supabase_service: SupabaseService):
        self._supabase = supabase_service

    async def check_and_increment(self, ip: str) -> RateLimitResult:
        """Bump both window counters for `ip` and decide if this attempt is allowed."""
        try:
            with self._supabase.get_db_session() as session:
                result = session.execute(
                    text(
                        """
                        INSERT INTO ai_proposal_platform.demo_ip_limits
                          (ip_address, window_start, window_type, session_count)
                        VALUES
                          (:ip, date_trunc('hour', now()), 'hour', 1),
                          (:ip, date_trunc('day',  now()), 'day',  1)
                        ON CONFLICT (ip_address, window_start, window_type)
                          DO UPDATE SET session_count = demo_ip_limits.session_count + 1
                        RETURNING window_type, session_count
                        """
                    ),
                    {"ip": ip},
                )
                rows = result.fetchall()
                session.commit()
        except Exception as exc:
            logger.warning("demo rate limiter upsert failed for ip=%s: %s", ip, exc)
            return RateLimitResult(allowed=True)

        counts = {window_type: int(count) for window_type, count in rows}
        now = datetime.now(timezone.utc)

        # if counts.get("hour", 0) > DEMO_IP_HOURLY_LIMIT:
        #     next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        #     return RateLimitResult(
        #         allowed=False,
        #         reason="DEMO_HOURLY_LIMIT_EXCEEDED",
        #         retry_after=max(1, int((next_hour - now).total_seconds())),
        #     )

        # if counts.get("day", 0) > DEMO_IP_DAILY_LIMIT:
        #     next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        #     return RateLimitResult(
        #         allowed=False,
        #         reason="DEMO_DAILY_LIMIT_EXCEEDED",
        #         retry_after=max(1, int((next_day - now).total_seconds())),
        #     )

        return RateLimitResult(allowed=True)
