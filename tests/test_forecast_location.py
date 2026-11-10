"""Municipal forecast overrides must not move a station or alter existing entries."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components" / "euskalmet" / "forecast_location.py"
)
SPEC = spec_from_file_location("euskalmet_forecast_location", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

forecast_configuration = MODULE.forecast_configuration
forecast_location_key = MODULE.forecast_location_key

STATION = {
    "region": "basque_country",
    "zone": "donostialdea",
    "location": "donostia",
    "station_id": "C017",
    "latitude": 43.29,
    "longitude": -1.98,
    "alert_zone": "GIPUZKOA_COAST",
}


def test_existing_entries_retain_their_forecast_and_station() -> None:
    before = dict(STATION)
    assert forecast_configuration(STATION, {}) == {
        "region": "basque_country", "zone": "donostialdea", "location": "donostia"
    }
    assert before == STATION


def test_only_forecast_identifiers_change_for_another_municipality() -> None:
    before = dict(STATION)
    result = forecast_configuration(
        STATION, {"forecast_location": "basque_country/donostialdea/errenteria"}
    )
    assert result == {
        "region": "basque_country", "zone": "donostialdea", "location": "errenteria"
    }
    assert before == STATION
    assert set(result) == {"region", "zone", "location"}


@pytest.mark.parametrize("selected", ["station", "", "region/zone/", None, {}, 5])
def test_automatic_or_incomplete_options_use_the_existing_location(selected) -> None:
    assert forecast_configuration(STATION, {"forecast_location": selected}) == (
        forecast_configuration(STATION, {})
    )


def test_identical_municipality_ids_in_different_zones_remain_distinct() -> None:
    first = {"region": "region", "zone": "one", "location": "town"}
    second = {**first, "zone": "two"}
    assert forecast_location_key(first) != forecast_location_key(second)


def test_legacy_missing_identifiers_keep_the_original_setup_defaults() -> None:
    assert forecast_configuration({}, {}) == {
        "region": "01", "zone": "01", "location": "VITORIA-GASTEIZ"
    }
