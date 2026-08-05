"""Normalization helpers for Euskalmet astronomical calendar data."""

from __future__ import annotations

import re
import unicodedata
from contextlib import suppress
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

MOON_PHASE_ALIASES = {
    "new_moon": "new_moon",
    "moon_new": "new_moon",
    "new": "new_moon",
    "luna_nueva": "new_moon",
    "nueva": "new_moon",
    "ilberria": "new_moon",
    "waxing_crescent": "waxing_crescent",
    "increase_to_quarter": "waxing_crescent",
    "new_to_quarter": "waxing_crescent",
    "luna_creciente": "waxing_crescent",
    "creciente": "waxing_crescent",
    "ilgora": "waxing_crescent",
    "first_quarter": "first_quarter",
    "increase_quarter": "first_quarter",
    "cuarto_creciente": "first_quarter",
    "lehen_laurdena": "first_quarter",
    "waxing_gibbous": "waxing_gibbous",
    "increase_to_full": "waxing_gibbous",
    "quarter_to_full": "waxing_gibbous",
    "gibosa_creciente": "waxing_gibbous",
    "full_moon": "full_moon",
    "full": "full_moon",
    "luna_llena": "full_moon",
    "llena": "full_moon",
    "ilbetea": "full_moon",
    "waning_gibbous": "waning_gibbous",
    "decrease_to_quarter": "waning_gibbous",
    "full_to_quarter": "waning_gibbous",
    "gibosa_menguante": "waning_gibbous",
    "last_quarter": "last_quarter",
    "third_quarter": "last_quarter",
    "decrease_quarter": "last_quarter",
    "cuarto_menguante": "last_quarter",
    "azken_laurdena": "last_quarter",
    "waning_crescent": "waning_crescent",
    "decrease_to_new": "waning_crescent",
    "quarter_to_new": "waning_crescent",
    "luna_menguante": "waning_crescent",
    "menguante": "waning_crescent",
    "ilbehera": "waning_crescent",
}


def _slug(value: object) -> str:
    """Return a comparable identifier for a translated API value."""

    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def normalize_moon_phase(value: object) -> str | None:
    """Normalize a known lunar phase to Home Assistant friendly states."""

    if value is None:
        return None
    return MOON_PHASE_ALIASES.get(_slug(value))


def parse_astro_date(
    value: object,
    requested_date: date,
    time_zone: ZoneInfo,
) -> date:
    """Convert the API calendar instant to its local civil date."""

    if not isinstance(value, str) or not value.strip():
        return requested_date

    cleaned = value.strip()
    if len(cleaned) == 10:
        with suppress(ValueError):
            return date.fromisoformat(cleaned)

    with suppress(ValueError):
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=time_zone)
        return parsed.astimezone(time_zone).date()

    return requested_date


def parse_astro_time(
    value: object,
    calendar_date: date,
    time_zone: ZoneInfo,
) -> datetime | None:
    """Parse an ISO datetime or a UTC clock time from the Astro API."""

    if not isinstance(value, str) or not value.strip():
        return None

    cleaned = value.strip()
    iso_value = cleaned.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_value)
    except ValueError:
        parsed = None

    if parsed is not None:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=time_zone)
        return parsed

    for pattern in ("%H:%M:%S", "%H:%M"):
        try:
            clock = datetime.strptime(cleaned, pattern).time()
        except ValueError:
            continue
        return datetime.combine(
            calendar_date,
            clock,
            tzinfo=UTC,
        ).astimezone(time_zone)

    return None


def parse_astro_calendar(
    document: object,
    requested_date: date,
    time_zone: ZoneInfo,
) -> dict[str, Any]:
    """Normalize the useful sun and moon fields from an Astro response."""

    if not isinstance(document, dict):
        return {}

    document_date = parse_astro_date(
        document.get("date"),
        requested_date,
        time_zone,
    )

    moon = document.get("moon")
    sun = document.get("sun")
    moon_data = moon if isinstance(moon, dict) else {}
    sun_data = sun if isinstance(sun, dict) else {}
    raw_phase = moon_data.get("phase")

    return {
        "date": document_date.isoformat(),
        "moonrise": parse_astro_time(
            moon_data.get("riseTime"), document_date, time_zone
        ),
        "moonset": parse_astro_time(
            moon_data.get("setTime"), document_date, time_zone
        ),
        "moon_phase": normalize_moon_phase(raw_phase),
        "moon_phase_raw": raw_phase,
        "sunrise": parse_astro_time(
            sun_data.get("riseTime"), document_date, time_zone
        ),
        "sunset": parse_astro_time(
            sun_data.get("downTime"), document_date, time_zone
        ),
        "source": "euskalmet_astro_calendar",
    }
