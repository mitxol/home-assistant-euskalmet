"""Helpers for the public Open Data Euskadi pollen API."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from math import asin, cos, radians, sin, sqrt
from typing import Any

POLLEN_STATIONS = {
    "020": {
        "name": "Bilbao",
        "latitude": 43.2630,
        "longitude": -2.9350,
    },
    "059": {
        "name": "Vitoria-Gasteiz",
        "latitude": 42.8467,
        "longitude": -2.6726,
    },
    "069": {
        "name": "Donostia / San Sebastián",
        "latitude": 43.3183,
        "longitude": -1.9812,
    },
}


def nearest_pollen_station(
    latitude: float,
    longitude: float,
) -> tuple[str, str]:
    """Return the closest of the three official pollen stations."""

    def distance(station: dict[str, Any]) -> float:
        lat1 = radians(latitude)
        lat2 = radians(float(station["latitude"]))
        delta_lat = lat2 - lat1
        delta_lon = radians(float(station["longitude"]) - longitude)
        value = (
            sin(delta_lat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        )
        return 2 * asin(sqrt(value))

    municipality_id, station = min(
        POLLEN_STATIONS.items(),
        key=lambda item: distance(item[1]),
    )
    return municipality_id, str(station["name"])


def parse_pollen_measurements(
    document: object,
    municipality_id: str,
    municipality_name: str,
) -> dict[str, Any]:
    """Normalize the newest daily record returned by the pollen API."""

    if not isinstance(document, list):
        raise ValueError("La respuesta de polen no es una lista")

    records = [
        item
        for item in document
        if isinstance(item, dict)
        and item.get("municipalityId") == municipality_id
        and isinstance(item.get("date"), str)
    ]
    if not records:
        return {
            "municipality_id": municipality_id,
            "municipality_name": municipality_name,
            "observed_on": None,
            "total": None,
            "species": {},
        }

    try:
        latest = max(records, key=lambda item: date.fromisoformat(item["date"]))
    except ValueError as err:
        raise ValueError("La API de polen devolvió una fecha no válida") from err

    # The API omits taxa with a zero count from some daily records. Build the
    # entity catalogue from the complete lookback response so entities that
    # were reported on earlier days are still created after a restart.
    species: dict[str, dict[str, Any]] = {}
    for record in records:
        measurements = record.get("measurements", [])
        if not isinstance(measurements, list):
            continue
        for measurement in measurements:
            if not isinstance(measurement, dict):
                continue
            specie_id = measurement.get("specieId")
            if not isinstance(specie_id, str):
                continue
            species[specie_id] = {
                "name": str(measurement.get("specieName") or specie_id),
                "value": 0.0,
            }

    latest_measurements = latest.get("measurements", [])
    if isinstance(latest_measurements, list):
        for measurement in latest_measurements:
            if not isinstance(measurement, dict):
                continue
            specie_id = measurement.get("specieId")
            value = measurement.get("pollenCount")
            if (
                not isinstance(specie_id, str)
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                continue
            species.setdefault(
                specie_id,
                {"name": str(measurement.get("specieName") or specie_id)},
            )["value"] = float(value)

    total = latest.get("measurementsTotalCount")
    return {
        "municipality_id": municipality_id,
        "municipality_name": str(
            latest.get("municipalityName") or municipality_name
        ),
        "observed_on": latest["date"],
        "total": float(total) if isinstance(total, (int, float)) else None,
        "species": species,
    }


def registered_pollen_species(
    entries: Iterable[tuple[str, str | None]],
    station_id: str,
    municipality_id: str,
) -> dict[str, dict[str, Any]]:
    """Recover taxa for this station from existing entity unique IDs."""

    prefix = f"{station_id}_pollen_{municipality_id}_"
    species = {}
    for unique_id, original_name in entries:
        if not unique_id.startswith(prefix):
            continue
        specie_id = unique_id[len(prefix):]
        if not specie_id or specie_id == "total":
            continue
        species[specie_id] = {"name": original_name or specie_id}
    return species


def pollen_species_value(pollen: object, specie_id: str) -> float | None:
    """Return a taxon count, treating omitted taxa as zero in a valid sample."""

    if not isinstance(pollen, dict) or not pollen.get("observed_on"):
        return None

    species = pollen.get("species")
    if not isinstance(species, dict):
        return 0.0

    measurement = species.get(specie_id)
    if not isinstance(measurement, dict):
        return 0.0

    value = measurement.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)
