"""One paper per explicit nightly window; freshness is not a due decision."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo


WINDOW_TIMEZONE = "America/New_York"
WINDOW_START_HOUR = 1
RECOVERY_DEADLINE_HOURS = 6


def generation_window(generated_at: dt.datetime, now: dt.datetime) -> dict:
    if generated_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("generation window requires timezone-aware timestamps")
    utc = dt.timezone.utc
    generated_at, now = generated_at.astimezone(utc), now.astimezone(utc)
    if generated_at > now:
        raise ValueError("latest generation timestamp is in the future")
    zone = ZoneInfo(WINDOW_TIMEZONE)
    local = now.astimezone(zone)
    date = local.date()
    start = dt.datetime.combine(date, dt.time(WINDOW_START_HOUR), zone)
    if now < start.astimezone(utc):
        date -= dt.timedelta(days=1)
        start = dt.datetime.combine(date, dt.time(WINDOW_START_HOUR), zone)
    end = dt.datetime.combine(date + dt.timedelta(days=1), dt.time(WINDOW_START_HOUR), zone)
    start_utc, end_utc = start.astimezone(utc), end.astimezone(utc)
    due = generated_at < start_utc
    deadline = start_utc + dt.timedelta(hours=RECOVERY_DEADLINE_HOURS)
    return {
        "standard": "VRS-NIGHTLY-WINDOW-1",
        "timezone": WINDOW_TIMEZONE,
        "window_id": date.isoformat(),
        "starts_at_utc": start_utc.isoformat(),
        "ends_at_utc": end_utc.isoformat(),
        "recovery_deadline_utc": deadline.isoformat(),
        "satisfied": not due,
        "generation_due": due,
        "overdue": due and now >= deadline,
        "rule": "one sealed paper in [window start, next window start); never use the 36-hour freshness SLO to skip a due window",
    }
