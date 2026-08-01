"""Small helpers for scheduling independent Euskalmet data sources."""

from __future__ import annotations

from datetime import datetime, timedelta


def update_due(
    last_attempt: datetime | None,
    interval: timedelta,
    now: datetime,
) -> bool:
    """Return whether a source should be requested again."""

    return last_attempt is None or now - last_attempt >= interval
