"""Tests for independent data-source polling intervals."""

from datetime import UTC, datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "euskalmet" / "polling.py"
)
SPEC = spec_from_file_location("euskalmet_polling", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

update_due = MODULE.update_due


def test_source_without_previous_attempt_is_due() -> None:
    now = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)

    assert update_due(None, timedelta(hours=1), now)


def test_source_waits_for_its_complete_interval() -> None:
    now = datetime(2026, 7, 31, 10, 59, 59, tzinfo=UTC)
    attempted = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)

    assert not update_due(attempted, timedelta(hours=1), now)


def test_source_is_due_on_interval_boundary() -> None:
    now = datetime(2026, 7, 31, 11, 0, tzinfo=UTC)
    attempted = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)

    assert update_due(attempted, timedelta(hours=1), now)
