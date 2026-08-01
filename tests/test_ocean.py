"""Tests for Ocean Forecast normalization."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "ocean.py"
)
SPEC = spec_from_file_location("euskalmet_ocean", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

parse_ocean_forecast = MODULE.parse_ocean_forecast


def test_parse_complete_ocean_forecast() -> None:
    result = parse_ocean_forecast(
        {
            "at": "2026-07-31T00:00:00+02:00",
            "for": "2026-07-31T00:00:00+02:00",
            "forecastTextByLang": {
                "SPANISH": "Marejada.",
                "BASQUE": "Itsaskia.",
            },
            "forecastDescriptionByLang": {
                "SPANISH": "Mar de fondo del noroeste.",
                "BASQUE": "Ipar-mendebaldeko hondoko itsasoa.",
            },
            "waterTemperature": {"value": 22, "unit": "Celsius"},
            "visibility": {
                "min": 4,
                "max": 10,
                "type": "GOOD",
                "id": "visibility-good",
                "unit": "km",
            },
            "waveHeight": 1.5,
        },
        ZoneInfo("Europe/Madrid"),
    )

    assert result["valid_for_date"].isoformat() == "2026-07-31"
    assert result["wave_height"] == 1.5
    assert result["wave_height_unit"] == "m"
    assert result["water_temperature"] == 22.0
    assert result["water_temperature_unit"] == "°C"
    assert result["visibility_min"] == 4.0
    assert result["visibility_max"] == 10.0
    assert result["visibility_unit"] == "km"
    assert result["forecast_texts"]["eu"] == "Itsaskia."
    assert result["forecast_descriptions"]["es"] == "Mar de fondo del noroeste."


def test_parse_ocean_forecast_handles_missing_fields() -> None:
    result = parse_ocean_forecast(
        {"for": "not-a-date"},
        ZoneInfo("Europe/Madrid"),
    )

    assert result["valid_for_date"] is None
    assert result["wave_height"] is None
    assert result["water_temperature"] is None
    assert result["visibility_min"] is None
    assert result["forecast_texts"] == {}


def test_parse_ocean_forecast_rejects_invalid_numbers() -> None:
    result = parse_ocean_forecast(
        {
            "waveHeight": "NaN",
            "waterTemperature": {"value": True},
            "visibility": {"min": "invalid", "max": "Infinity"},
        },
        ZoneInfo("Europe/Madrid"),
    )

    assert result["wave_height"] is None
    assert result["water_temperature"] is None
    assert result["visibility_min"] is None
    assert result["visibility_max"] is None


def test_ocean_utc_midnight_is_converted_to_local_date() -> None:
    result = parse_ocean_forecast(
        {"for": "2026-07-30T22:00:00.000+0000"},
        ZoneInfo("Europe/Madrid"),
    )

    assert result["valid_for_date"].isoformat() == "2026-07-31"


def test_visibility_uses_documented_kilometres_despite_api_label() -> None:
    result = parse_ocean_forecast(
        {"visibility": {"min": 4, "max": 10, "unit": "m"}},
        ZoneInfo("Europe/Madrid"),
    )

    assert result["visibility_min"] == 4.0
    assert result["visibility_max"] == 10.0
    assert result["visibility_unit"] == "km"
    assert result["visibility_raw_unit"] == "m"
