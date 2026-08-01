"""Tests for Euskalmet tide normalization."""

from datetime import date, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "tides.py"
)
SPEC = spec_from_file_location("euskalmet_tides", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

next_tide_event = MODULE.next_tide_event
parse_tide_report = MODULE.parse_tide_report

TIME_ZONE = ZoneInfo("Europe/Madrid")


def test_parse_tide_report_accepts_object_events() -> None:
    result = parse_tide_report(
        {
            "date": "2026-07-31",
            "tides": [
                {"type": "HIGH_TIDE", "time": "06:40", "height": 4.07},
                {"type": "LOW_TIDE", "time": "12:40", "height": 1.24},
            ],
        },
        date(2026, 7, 31),
        TIME_ZONE,
    )

    assert len(result["events"]) == 2
    assert result["events"][0]["type"] == "high"
    assert result["events"][0]["time"].isoformat() == (
        "2026-07-31T08:40:00+02:00"
    )
    assert result["events"][0]["height"] == 4.07
    assert result["events"][1]["type"] == "low"


def test_parse_tide_report_accepts_production_phase_and_high_fields() -> None:
    result = parse_tide_report(
        {
            "tides": [
                {"phase": "HIGH_TIDE", "time": "16:47:00", "high": 4.25},
                {"phase": "LOW_TIDE", "time": "22:56:00", "high": 0.86},
            ]
        },
        date(2026, 7, 31),
        TIME_ZONE,
    )

    assert result["events"][0]["type"] == "high"
    assert result["events"][0]["height"] == 4.25
    assert result["events"][1]["type"] == "low"
    assert result["events"][1]["height"] == 0.86


def test_parse_tide_report_accepts_string_events() -> None:
    result = parse_tide_report(
        {
            "tides": [
                "Pleamar 18:53 / 4,36 m",
                "Bajamar 01:03 / 1,09 m",
            ]
        },
        date(2026, 7, 31),
        TIME_ZONE,
    )

    assert result["events"][0]["type"] == "low"
    assert result["events"][0]["height"] == 1.09
    assert result["events"][1]["type"] == "high"
    assert result["events"][1]["height"] == 4.36


def test_next_tide_event_selects_future_event() -> None:
    report = parse_tide_report(
        {
            "tides": [
                {"type": "HIGH_TIDE", "time": "06:40", "height": 4.07},
                {"type": "HIGH_TIDE", "time": "18:53", "height": 4.36},
            ]
        },
        date(2026, 7, 31),
        TIME_ZONE,
    )

    event = next_tide_event(
        report["events"],
        "high",
        datetime(2026, 7, 31, 10, 0, tzinfo=TIME_ZONE),
    )

    assert event is not None
    assert event["time"].hour == 20
    assert event["height"] == 4.36


def test_production_tide_times_are_converted_from_utc() -> None:
    report = parse_tide_report(
        {
            "tides": [
                {"phase": "LOW_TIDE", "time": "10:34:00", "high": 1.01},
                {"phase": "HIGH_TIDE", "time": "16:47:00", "high": 4.25},
            ]
        },
        date(2026, 7, 31),
        TIME_ZONE,
    )

    low, high = report["events"]
    assert low["time"].isoformat() == "2026-07-31T12:34:00+02:00"
    assert high["time"].isoformat() == "2026-07-31T18:47:00+02:00"


def test_undocumented_values_are_preserved() -> None:
    raw = ["future API format"]
    result = parse_tide_report(
        {"tides": raw},
        date(2026, 7, 31),
        TIME_ZONE,
    )

    assert result["events"] == []
    assert result["raw_tides"] == raw
