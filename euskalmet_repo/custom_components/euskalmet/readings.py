from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Mapping


_WIND_MEASURES_IN_METERS_PER_SECOND = {"mean_speed", "max_speed"}
_AGGREGATED_READING_DATE = re.compile(
    r"/at/(\d{4})/(\d{2})/(\d{2})/(\d{2})$"
)
_AGGREGATED_PUBLICATION_DELAY = timedelta(minutes=15)

def _numeric_value(value: object) -> float | int | None:
    """Normalizar un valor numérico publicado por Euskalmet."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (float, int)):
        return value

    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def available_measure_keys(
    document: object,
    measures: Mapping[str, Mapping[str, Any]],
) -> set[str]:
    """Obtener las magnitudes soportadas por un documento de estación."""

    if not isinstance(document, dict):
        return set()

    available = {
        (str(item.get("type", "")), str(item.get("name", "")))
        for item in document.values()
        if isinstance(item, dict)
    }

    return {
        key
        for key, config in measures.items()
        if (
            str(config.get("measure_type", "")),
            str(config.get("measure", "")),
        )
        in available
    }


def parse_public_readings(
    document: object,
    measures: Mapping[str, Mapping[str, Any]],
    document_date: datetime,
) -> dict[str, dict[str, Any]]:
    """Extraer la lectura más reciente de cada magnitud del JSON público."""

    if not isinstance(document, dict):
        return {}

    requested = {
        (
            str(config.get("measure_type", "")),
            str(config.get("measure", "")),
        ): key
        for key, config in measures.items()
    }
    latest: dict[str, tuple[datetime, float | int, str, str]] = {}

    for measure_id, raw_item in document.items():
        if not isinstance(raw_item, dict):
            continue

        spec = (
            str(raw_item.get("type", "")),
            str(raw_item.get("name", "")),
        )
        key = requested.get(spec)
        if key is None:
            continue

        positions = raw_item.get("data")
        if not isinstance(positions, dict):
            continue

        for position_cm, timeline in positions.items():
            if not isinstance(timeline, dict):
                continue

            for raw_time, raw_value in timeline.items():
                try:
                    hour, minute = (
                        int(part)
                        for part in str(raw_time).split(":", 2)[:2]
                    )
                    observed_at = document_date.replace(
                        hour=hour,
                        minute=minute,
                        second=0,
                        microsecond=0,
                    )
                except (TypeError, ValueError):
                    continue

                value = _numeric_value(raw_value)
                if value is None:
                    continue

                if spec[1] in _WIND_MEASURES_IN_METERS_PER_SECOND:
                    value = round(float(value) * 3.6, 1)

                candidate = (
                    observed_at,
                    value,
                    str(measure_id),
                    str(position_cm),
                )
                previous = latest.get(key)
                if previous is None or candidate[0] > previous[0]:
                    latest[key] = candidate

    return {
        key: {
            "value": candidate[1],
            "observed_at": candidate[0],
            "measure_id": candidate[2],
            "sensor_position_cm": candidate[3],
        }
        for key, candidate in latest.items()
    }


def available_aggregated_measure_keys(
    document: object,
    measures: Mapping[str, Mapping[str, Any]],
) -> set[str]:
    """Obtener las magnitudes soportadas por una respuesta agregada."""

    if not isinstance(document, dict):
        return set()
    items = document.get("items")
    if not isinstance(items, list):
        return set()

    available = {
        (str(item.get("measureType", "")), str(item.get("measureId", "")))
        for item in items
        if isinstance(item, dict)
    }
    return {
        key
        for key, config in measures.items()
        if (
            str(config.get("measure_type", "")),
            str(config.get("measure", "")),
        )
        in available
    }


def _aggregated_slot_times(
    reading: Mapping[str, Any],
    slot: object,
) -> tuple[datetime, datetime] | None:
    """Convertir una franja agregada en sus instantes UTC de inicio y fin."""

    if not isinstance(slot, dict):
        return None
    oid = reading.get("oid")
    range_value = slot.get("range")
    if not isinstance(oid, str) or not isinstance(range_value, str):
        return None

    match = _AGGREGATED_READING_DATE.search(oid)
    if match is None:
        return None

    try:
        interval = range_value.split("[", 1)[1].split("]", 1)[0]
        start_raw, end_raw = interval.split("..", 1)

        def build(raw: str) -> datetime:
            parts = raw.split(":")
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(parts[0]),
                int(parts[1]),
                int(parts[2]),
                int(parts[3].ljust(6, "0")) if len(parts) > 3 else 0,
                tzinfo=timezone.utc,
            )

        return build(start_raw), build(end_raw)
    except (IndexError, TypeError, ValueError):
        return None


def parse_aggregated_readings(
    document: object,
    measures: Mapping[str, Mapping[str, Any]],
    now: datetime,
) -> dict[str, dict[str, Any]]:
    """Extraer la última franja terminada de cada magnitud agregada."""

    if not isinstance(document, dict):
        return {}
    items = document.get("items")
    if not isinstance(items, list):
        return {}

    requested = {
        (
            str(config.get("measure_type", "")),
            str(config.get("measure", "")),
        ): key
        for key, config in measures.items()
    }
    now_utc = now.astimezone(timezone.utc)
    candidates: dict[
        str, list[tuple[datetime, float | int, str, str]]
    ] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        spec = (
            str(item.get("measureType", "")),
            str(item.get("measureId", "")),
        )
        key = requested.get(spec)
        if key is None:
            continue
        readings = item.get("readings")
        if not isinstance(readings, list):
            continue

        position = item.get("sensorPosition")
        position_cm = (
            str(position.get("at"))
            if isinstance(position, dict) and position.get("at") is not None
            else ""
        )
        sensor_id = str(item.get("sensorId", ""))

        for reading in readings:
            if not isinstance(reading, dict):
                continue
            slots = reading.get("slots")
            values = reading.get("values")
            if not isinstance(slots, list) or not isinstance(values, list):
                continue

            for index, raw_value in enumerate(values):
                if index >= len(slots):
                    continue
                times = _aggregated_slot_times(reading, slots[index])
                value = _numeric_value(raw_value)
                if times is None or value is None:
                    continue
                observed_at, interval_end = times
                if interval_end + _AGGREGATED_PUBLICATION_DELAY > now_utc:
                    continue
                if spec[1] in _WIND_MEASURES_IN_METERS_PER_SECOND:
                    value = round(float(value) * 3.6, 1)

                candidate = (observed_at, value, sensor_id, position_cm)
                candidates.setdefault(key, []).append(candidate)

    for values in candidates.values():
        values.sort(key=lambda candidate: candidate[0])

    latest = {
        key: values[-1]
        for key, values in candidates.items()
        if values
    }

    # Euskalmet crea las franjas antes de publicar sus observaciones y puede
    # dejarlas temporalmente a cero incluso después de cerrarlas. Si todas las
    # magnitudes coinciden en una misma franja y todas valen cero, se conserva
    # la cohorte anterior. Un cero aislado (lluvia, radiación o viento) sigue
    # siendo una lectura perfectamente válida.
    while len(latest) > 1:
        latest_times = {candidate[0] for candidate in latest.values()}
        if (
            len(latest_times) != 1
            or not all(candidate[1] == 0 for candidate in latest.values())
        ):
            break
        if not all(len(values) > 1 for values in candidates.values()):
            break
        for values in candidates.values():
            values.pop()
        latest = {key: values[-1] for key, values in candidates.items()}

    return {
        key: {
            "value": candidate[1],
            "observed_at": candidate[0],
            "measure_id": candidate[2],
            "sensor_position_cm": candidate[3],
        }
        for key, candidate in latest.items()
    }
