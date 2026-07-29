"""Helpers for the public Open Data Euskadi pollen API."""

from __future__ import annotations

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

    species: dict[str, dict[str, Any]] = {}
    measurements = latest.get("measurements", [])
    if isinstance(measurements, list):
        for measurement in measurements:
            if not isinstance(measurement, dict):
                continue
            specie_id = measurement.get("specieId")
            value = measurement.get("pollenCount")
            if not isinstance(specie_id, str) or not isinstance(value, (int, float)):
                continue
            species[specie_id] = {
                "name": str(measurement.get("specieName") or specie_id),
                "value": float(value),
            }

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
