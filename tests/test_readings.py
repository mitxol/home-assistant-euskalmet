"""Tests for Euskalmet provisional summary helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "readings.py"
)
SPEC = spec_from_file_location("euskalmet_readings", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

combine_provisional_summaries = MODULE.combine_provisional_summaries


def _summary(mean: float | None, readings: int) -> dict:
    return {
        "items": [
            {
                "measureType": "measuresForAir",
                "measureId": "temperature",
                "summary": {"mean": mean, "processedReadings": readings},
            }
        ]
    }


def test_combined_mean_is_weighted_by_readings() -> None:
    result = combine_provisional_summaries([_summary(10.0, 6), _summary(20.0, 2)])

    assert result["items"][0]["summary"]["mean"] == 12.5
    assert result["items"][0]["summary"]["processedReadings"] == 8


def test_combined_mean_ignores_parts_without_mean() -> None:
    result = combine_provisional_summaries([_summary(10.0, 6), _summary(None, 6)])

    assert result["items"][0]["summary"]["mean"] == 10.0
