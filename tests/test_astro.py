"""Tests for astronomical calendar normalization."""

from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "astro.py"
)
SPEC = spec_from_file_location("euskalmet_astro", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

normalize_moon_phase = MODULE.normalize_moon_phase
parse_astro_calendar = MODULE.parse_astro_calendar


def test_parse_astro_calendar_converts_utc_clock_times() -> None:
    result = parse_astro_calendar(
        {
            "date": "2026-07-30",
            "moon": {
                "riseTime": "21:42",
                "setTime": "06:15:00",
                "phase": "Luna llena",
            },
            "sun": {
                "riseTime": "06:58",
                "downTime": "21:34",
            },
        },
        date(2026, 7, 30),
        ZoneInfo("Europe/Madrid"),
    )

    assert result["date"] == "2026-07-30"
    assert result["moonrise"].isoformat() == "2026-07-30T23:42:00+02:00"
    assert result["moonset"].isoformat() == "2026-07-30T08:15:00+02:00"
    assert result["sunrise"].isoformat() == "2026-07-30T08:58:00+02:00"
    assert result["sunset"].isoformat() == "2026-07-30T23:34:00+02:00"
    assert result["moon_phase"] == "full_moon"
    assert result["moon_phase_raw"] == "Luna llena"


def test_parse_astro_calendar_accepts_iso_datetimes() -> None:
    result = parse_astro_calendar(
        {
            "date": "2026-12-15",
            "moon": {
                "riseTime": "2026-12-15T04:20:00Z",
                "setTime": None,
                "phase": "waning crescent",
            },
            "sun": {},
        },
        date(2026, 12, 15),
        ZoneInfo("Europe/Madrid"),
    )

    assert result["moonrise"].isoformat() == "2026-12-15T04:20:00+00:00"
    assert result["moonset"] is None
    assert result["moon_phase"] == "waning_crescent"


def test_calendar_utc_midnight_is_converted_to_local_date() -> None:
    result = parse_astro_calendar(
        {
            "date": "2026-07-30T22:00:00.000+0000",
            "moon": {"phase": "DECREASE_TO_QUARTER"},
            "sun": {},
        },
        date(2026, 7, 31),
        ZoneInfo("Europe/Madrid"),
    )

    assert result["date"] == "2026-07-31"
    assert result["moon_phase"] == "waning_gibbous"


def test_euskalmet_phase_codes_cover_the_lunar_cycle() -> None:
    assert normalize_moon_phase("NEW_MOON") == "new_moon"
    assert normalize_moon_phase("INCREASE_TO_QUARTER") == "waxing_crescent"
    assert normalize_moon_phase("FIRST_QUARTER") == "first_quarter"
    assert normalize_moon_phase("INCREASE_TO_FULL") == "waxing_gibbous"
    assert normalize_moon_phase("FULL_MOON") == "full_moon"
    assert normalize_moon_phase("DECREASE_TO_QUARTER") == "waning_gibbous"
    assert normalize_moon_phase("LAST_QUARTER") == "last_quarter"
    assert normalize_moon_phase("THIRD_QUARTER") == "last_quarter"
    assert normalize_moon_phase("DECREASE_TO_NEW") == "waning_crescent"


def test_unknown_phase_is_preserved_as_raw_attribute() -> None:
    result = parse_astro_calendar(
        {"moon": {"phase": "Fase futura"}, "sun": {}},
        date(2026, 7, 30),
        ZoneInfo("Europe/Madrid"),
    )

    assert result["moon_phase"] is None
    assert result["moon_phase_raw"] == "Fase futura"
    assert normalize_moon_phase("Ilbetea") == "full_moon"
