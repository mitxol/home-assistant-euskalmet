"""Normalization helpers for Euskalmet ocean forecast data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo


def _number(value: object) -> float | None:
    """Return a finite numeric API value."""

    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _unit(value: object) -> str | None:
    """Normalize common units returned by the ocean API."""

    if value is None:
        return None
    text = str(value).strip()
    aliases = {
        "c": "°C",
        "ºc": "°C",
        "°c": "°C",
        "celsius": "°C",
        "m": "m",
        "meter": "m",
        "meters": "m",
        "metre": "m",
        "metres": "m",
        "km": "km",
        "kilometer": "km",
        "kilometers": "km",
        "kilometre": "km",
        "kilometres": "km",
    }
    return aliases.get(text.lower(), text)


def _texts(value: object) -> dict[str, str]:
    """Extract Spanish and Basque variants from an API language map."""

    if not isinstance(value, dict):
        return {}
    result = {}
    for api_key, language in (("SPANISH", "es"), ("BASQUE", "eu")):
        text = value.get(api_key)
        if text:
            result[language] = str(text).strip()
    return result


def _forecast_date(value: object, time_zone: ZoneInfo) -> date | None:
    """Extract a civil date from an API date or datetime."""

    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip()
    if len(cleaned) == 10:
        try:
            return date.fromisoformat(cleaned)
        except ValueError:
            return None
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=time_zone)
    return parsed.astimezone(time_zone).date()


def parse_ocean_forecast(
    document: object,
    time_zone: ZoneInfo,
) -> dict[str, Any]:
    """Normalize the useful fields from an Ocean Forecast response."""

    if not isinstance(document, dict):
        return {}

    temperature = document.get("waterTemperature")
    visibility = document.get("visibility")
    temperature_data = temperature if isinstance(temperature, dict) else {}
    visibility_data = visibility if isinstance(visibility, dict) else {}

    return {
        "issued_at": document.get("at"),
        "valid_for": document.get("for"),
        "valid_for_date": _forecast_date(document.get("for"), time_zone),
        "forecast_texts": _texts(document.get("forecastTextByLang")),
        "forecast_descriptions": _texts(
            document.get("forecastDescriptionByLang")
        ),
        "wave_height": _number(document.get("waveHeight")),
        "wave_height_unit": "m",
        "water_temperature": _number(temperature_data.get("value")),
        "water_temperature_unit": _unit(temperature_data.get("unit")) or "°C",
        "visibility_min": _number(visibility_data.get("min")),
        "visibility_max": _number(visibility_data.get("max")),
        # Production currently labels the 4–10 km range as metres. Euskalmet's
        # own maritime page confirms these values are kilometres.
        "visibility_unit": "km",
        "visibility_raw_unit": _unit(visibility_data.get("unit")),
        "visibility_type": visibility_data.get("type"),
        "visibility_id": visibility_data.get("id"),
        "source": "euskalmet_ocean_forecast",
    }
