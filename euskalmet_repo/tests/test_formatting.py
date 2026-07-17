"""Tests for formatting helpers without importing Home Assistant."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "euskalmet"
    / "formatting.py"
)
SPEC = spec_from_file_location("euskalmet_formatting", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

degrees_to_compass = MODULE.degrees_to_compass
spanish_weather_condition = MODULE.spanish_weather_condition


def test_degrees_to_compass_boundaries() -> None:
    assert degrees_to_compass(0) == "N"
    assert degrees_to_compass(11.24) == "N"
    assert degrees_to_compass(11.25) == "NNE"
    assert degrees_to_compass(90) == "E"
    assert degrees_to_compass(180) == "S"
    assert degrees_to_compass(270) == "O"
    assert degrees_to_compass(360) == "N"
    assert degrees_to_compass(-90) == "O"


def test_degrees_to_compass_invalid_values() -> None:
    assert degrees_to_compass(None) is None
    assert degrees_to_compass(True) is None
    assert degrees_to_compass("invalid") is None


def test_spanish_weather_condition() -> None:
    assert spanish_weather_condition("rainy") == "Lluvia"
    assert spanish_weather_condition("unknown-condition") == "unknown-condition"
    assert spanish_weather_condition(None) is None
