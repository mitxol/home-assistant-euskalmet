"""Tests for pollen helpers without importing Home Assistant."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "pollen.py"
)
SPEC = spec_from_file_location("euskalmet_pollen", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

nearest_pollen_station = MODULE.nearest_pollen_station
parse_pollen_measurements = MODULE.parse_pollen_measurements
pollen_species_value = MODULE.pollen_species_value


def test_nearest_pollen_station() -> None:
    assert nearest_pollen_station(43.263, -2.935)[0] == "020"
    assert nearest_pollen_station(42.847, -2.673)[0] == "059"
    assert nearest_pollen_station(43.318, -1.981)[0] == "069"


def test_parse_pollen_measurements_selects_newest_record() -> None:
    result = parse_pollen_measurements(
        [
            {
                "date": "2026-07-04",
                "municipalityId": "020",
                "municipalityName": "BILBAO",
                "measurementsTotalCount": 3,
                "measurements": [],
            },
            {
                "date": "2026-07-05",
                "municipalityId": "020",
                "municipalityName": "BILBAO",
                "measurementsTotalCount": 16,
                "measurements": [
                    {
                        "specieId": "poaceae",
                        "specieName": "Poaceae",
                        "pollenCount": 16,
                    }
                ],
            },
        ],
        "020",
        "Bilbao",
    )

    assert result["observed_on"] == "2026-07-05"
    assert result["total"] == 16.0
    assert result["species"]["poaceae"]["value"] == 16.0


def test_species_from_older_record_is_created_with_zero() -> None:
    result = parse_pollen_measurements(
        [
            {
                "date": "2026-08-02",
                "municipalityId": "059",
                "measurementsTotalCount": 2,
                "measurements": [
                    {
                        "specieId": "eucalyptus",
                        "specieName": "Eucalyptus",
                        "pollenCount": 2,
                    }
                ],
            },
            {
                "date": "2026-08-09",
                "municipalityId": "059",
                "measurementsTotalCount": 34,
                "measurements": [
                    {
                        "specieId": "poaceae",
                        "specieName": "Poaceae",
                        "pollenCount": 34,
                    }
                ],
            },
        ],
        "059",
        "Vitoria-Gasteiz",
    )

    assert result["observed_on"] == "2026-08-09"
    assert result["species"]["poaceae"]["value"] == 34.0
    assert result["species"]["eucalyptus"] == {
        "name": "Eucalyptus",
        "value": 0.0,
    }


def test_parse_pollen_measurements_handles_no_data() -> None:
    result = parse_pollen_measurements([], "069", "Donostia / San Sebastián")
    assert result["observed_on"] is None
    assert result["total"] is None
    assert result["species"] == {}


def test_missing_species_is_zero_when_daily_sample_exists() -> None:
    pollen = {
        "observed_on": "2026-08-12",
        "species": {
            "poaceae": {"name": "Poaceae", "value": 11.0},
        },
    }

    assert pollen_species_value(pollen, "poaceae") == 11.0
    assert pollen_species_value(pollen, "alternaria") == 0.0


def test_species_is_unavailable_without_a_valid_daily_sample() -> None:
    assert pollen_species_value({}, "alternaria") is None
    assert pollen_species_value({"observed_on": None}, "alternaria") is None


def test_invalid_species_value_is_zero_in_a_valid_daily_sample() -> None:
    pollen = {
        "observed_on": "2026-08-12",
        "species": {"alternaria": {"name": "Alternaria", "value": None}},
    }

    assert pollen_species_value(pollen, "alternaria") == 0.0
