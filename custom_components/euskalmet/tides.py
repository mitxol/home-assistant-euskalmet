"""Normalization helpers for Euskalmet astronomical tides."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo


def _slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def _number(value: object) -> float | None:
    if isinstance(value, dict):
        value = value.get("value", value.get("height"))
    if isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _tide_type(value: object) -> str | None:
    slug = _slug(value)
    if any(word in slug for word in ("high", "pleamar", "itsasgora")):
        return "high"
    if any(word in slug for word in ("low", "bajamar", "itsasbehera")):
        return "low"
    return None


def _event_time(
    value: object,
    report_date: date,
    time_zone: ZoneInfo,
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip()
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is not None:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(time_zone)
    match = re.search(r"\b([01]\d|2[0-3]):([0-5]\d)\b", cleaned)
    if match:
        return datetime(
            report_date.year,
            report_date.month,
            report_date.day,
            int(match.group(1)),
            int(match.group(2)),
            tzinfo=UTC,
        ).astimezone(time_zone)
    return None


def _event_from_item(
    item: object,
    report_date: date,
    time_zone: ZoneInfo,
) -> dict[str, Any] | None:
    raw = item
    if isinstance(item, str):
        cleaned = item.strip()
        try:
            decoded = json.loads(cleaned)
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, dict):
            item = decoded

    if isinstance(item, dict):
        tide_type = _tide_type(
            item.get("type")
            or item.get("tideType")
            or item.get("phase")
            or item.get("phenomenon")
            or item.get("name")
            or item.get("id")
        )
        event_time = _event_time(
            item.get("dateTime")
            or item.get("datetime")
            or item.get("time")
            or item.get("at")
            or item.get("hour"),
            report_date,
            time_zone,
        )
        height = _number(
            item.get("height")
            or item.get("high")
            or item.get("meters")
            or item.get("level")
            or item.get("value")
        )
    else:
        text = str(item)
        tide_type = _tide_type(text)
        event_time = _event_time(text, report_date, time_zone)
        height_match = re.search(r"(-?\d+(?:[.,]\d+)?)\s*m(?:\b|$)", text.lower())
        height = _number(height_match.group(1)) if height_match else None

    if tide_type is None or event_time is None:
        return None
    return {
        "type": tide_type,
        "time": event_time,
        "height": height,
        "raw": raw,
    }


def parse_tide_report(
    document: object,
    requested_date: date,
    time_zone: ZoneInfo,
) -> dict[str, Any]:
    """Normalize one day of tides while preserving undocumented raw values."""

    if not isinstance(document, dict):
        return {"date": requested_date.isoformat(), "events": [], "raw_tides": []}

    report_date = requested_date
    raw_date = document.get("date")
    if isinstance(raw_date, str):
        try:
            parsed_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except ValueError:
            parsed_date = None
        if parsed_date is not None:
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=time_zone)
            report_date = parsed_date.astimezone(time_zone).date()
        elif len(raw_date) >= 10:
            try:
                report_date = date.fromisoformat(raw_date[:10])
            except ValueError:
                pass

    raw_tides = document.get("tides")
    items = raw_tides if isinstance(raw_tides, list) else []
    events = [
        event
        for item in items
        if (event := _event_from_item(item, report_date, time_zone)) is not None
    ]
    events.sort(key=lambda event: event["time"])
    return {
        "date": report_date.isoformat(),
        "events": events,
        "raw_tides": items,
    }


def next_tide_event(
    events: list[dict[str, Any]],
    tide_type: str,
    now: datetime,
) -> dict[str, Any] | None:
    """Return the next future event of one tide type."""

    candidates = [
        event
        for event in events
        if event.get("type") == tide_type
        and isinstance(event.get("time"), datetime)
        and event["time"] >= now
    ]
    return min(candidates, key=lambda event: event["time"], default=None)
