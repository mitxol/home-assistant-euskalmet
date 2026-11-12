"""Tests for Euskalmet station catalogue filtering."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "geography.py"
)
SPEC = spec_from_file_location("euskalmet_geography", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

active_meteorological_stations = MODULE.active_meteorological_stations


def _feature(code: str, name: str, station_type: str, **extra) -> dict:
    """Build a station feature shaped like the official GeoJSON catalogue."""

    properties = {
        "codigo": code,
        "nombre": name,
        "tipo": station_type,
        "municipio": extra.pop("municipio", "Laudio/Llodio"),
        "provincia": extra.pop("provincia", "Araba/Álava"),
        **extra,
    }
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-2.9666, 43.1390]},
        "properties": properties,
    }


def test_includes_complete_and_collaborative_stations() -> None:
    """KM (complete) and KC (collaborative) stations are both selectable."""

    features = [
        _feature("C016", "Arkauti", "KM"),
        _feature("C067", "Gardea", "KC"),
    ]

    station_ids = [
        item["station_id"] for item in active_meteorological_stations(features)
    ]

    assert station_ids == ["C016", "C067"]


def test_excludes_non_meteorological_station_types() -> None:
    """Buoys (B) and other catalogue types are still ignored."""

    features = [
        _feature("B090", "Puerto de Bilbao", "B"),
        _feature("C0AA", "Etura", "KA"),
        _feature("C067", "Gardea", "KC"),
    ]

    station_ids = [
        item["station_id"] for item in active_meteorological_stations(features)
    ]

    assert station_ids == ["C067"]


def test_excludes_closed_stations() -> None:
    """Stations closed in the catalogue are filtered out even if KC."""

    features = [
        _feature("C067", "Gardea", "KC", fechabaja="2020-01-01"),
        _feature("C035", "Altube", "KM"),
    ]

    station_ids = [
        item["station_id"] for item in active_meteorological_stations(features)
    ]

    assert station_ids == ["C035"]


def test_stations_are_sorted_by_name() -> None:
    """The selection list stays alphabetically ordered."""

    features = [
        _feature("C067", "Gardea", "KC"),
        _feature("C061", "Arboleda", "KM"),
    ]

    names = [item["station_name"] for item in active_meteorological_stations(features)]

    assert names == ["Arboleda", "Gardea"]
