from __future__ import annotations

import math
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Iterable


MAX_STATION_DISTANCE_KM = 120.0
METEOROLOGICAL_STATION_TYPE = "KM"

_BIZKAIA_COAST = {
    "bakio",
    "barrika",
    "bermeo",
    "busturia",
    "ea",
    "elantxobe",
    "getxo",
    "gorliz",
    "ibarrangelu",
    "ispaster",
    "lekeitio",
    "lemoiz",
    "mendexa",
    "mundaka",
    "muskiz",
    "ondarroa",
    "plentzia",
    "santurtzi",
    "sopela",
    "sukarrieta",
    "zierbena",
}

_GIPUZKOA_COAST = {
    "deba",
    "donostia san sebastian",
    "getaria",
    "hondarribia",
    "irun",
    "lezo",
    "mutriku",
    "orio",
    "pasaia",
    "san sebastian",
    "zarautz",
    "zumaia",
}


class LocationDiscoveryError(ValueError):
    """No se pudo asociar la ubicación con los catálogos de Euskalmet."""


def station_from_feature(feature: object) -> dict[str, Any] | None:
    """Normalizar una estación activa del GeoJSON oficial."""

    if not isinstance(feature, dict):
        return None

    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None
    if properties.get("fechabaja"):
        return None

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None

    try:
        station_longitude = float(coordinates[0])
        station_latitude = float(coordinates[1])
    except (TypeError, ValueError):
        return None

    station_id = str(properties.get("codigo") or "").strip()
    if not station_id:
        return None

    return {
        "station_id": station_id,
        "station_name": str(properties.get("nombre") or station_id).strip(),
        "station_type": str(properties.get("tipo") or "").strip(),
        "municipality": str(properties.get("municipio") or "").strip(),
        "province": str(properties.get("provincia") or "").strip(),
        "station_latitude": station_latitude,
        "station_longitude": station_longitude,
    }


def active_meteorological_stations(
    features: Iterable[object],
) -> list[dict[str, Any]]:
    """Listar solo estaciones activas clasificadas como meteorológicas."""

    stations = []
    for feature in features:
        station = station_from_feature(feature)
        if (
            station is not None
            and station["station_type"] == METEOROLOGICAL_STATION_TYPE
        ):
            stations.append(station)

    return sorted(
        stations,
        key=lambda station: normalize_text(station["station_name"]),
    )


def station_by_id(
    stations: Iterable[dict[str, Any]],
    station_id: str,
) -> dict[str, Any]:
    """Encontrar una estación normalizada por su código oficial."""

    for station in stations:
        if station.get("station_id") == station_id:
            return station

    raise LocationDiscoveryError(
        f"La estación {station_id} no está disponible"
    )


def normalize_text(value: object) -> str:
    """Normalizar nombres vascos/castellanos para compararlos."""

    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(
        "".join(char if char.isalnum() else " " for char in text.lower()).split()
    )


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Calcular la distancia ortodrómica entre dos coordenadas."""

    radius = 6371.0088
    lat_a, lat_b = map(math.radians, (latitude_a, latitude_b))
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(longitude_b - longitude_a)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(value))


def nearest_active_station(
    features: Iterable[object],
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Elegir la estación activa más cercana de un GeoJSON oficial."""

    stations = [
        station
        for feature in features
        if (station := station_from_feature(feature)) is not None
    ]
    return nearest_station(stations, latitude, longitude)


def nearest_station(
    stations: Iterable[dict[str, Any]],
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Elegir la estación normalizada más cercana a unas coordenadas."""

    candidates: list[tuple[float, dict[str, Any]]] = []

    for station in stations:
        distance = haversine_km(
            latitude,
            longitude,
            station["station_latitude"],
            station["station_longitude"],
        )
        candidates.append(
            (
                distance,
                {
                    **station,
                    "station_distance_km": round(distance, 1),
                },
            )
        )

    if not candidates:
        raise LocationDiscoveryError("El catálogo no contiene estaciones válidas")

    distance, station = min(candidates, key=lambda candidate: candidate[0])

    if distance > MAX_STATION_DISTANCE_KM:
        raise LocationDiscoveryError(
            "La ubicación de Home Assistant está fuera de la cobertura de Euskalmet"
        )

    return station


def catalog_identifier(item: dict[str, Any], field: str) -> str | None:
    """Extraer un identificador de los distintos esquemas del API."""

    aliases = {
        "region": ("region", "regionId"),
        "zone": ("zone", "zoneId", "regionZoneId"),
        "location": (
            "location",
            "locationId",
            "regionZoneLocationId",
        ),
    }

    for key in (*aliases.get(field, (field, f"{field}Id")), "id", "code"):
        value = item.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, dict):
            nested = catalog_identifier(value, field)
            if nested:
                return nested

    return None


def catalog_names(item: dict[str, Any], identifier: str) -> list[str]:
    """Obtener nombres traducidos y técnicos de un elemento del catálogo."""

    values: list[object] = [identifier, item.get("name")]
    translated = item.get("nameByLang")

    if isinstance(translated, dict):
        values.extend(translated.values())

    names = [normalize_text(value) for value in values]
    return [name for name in names if name]


def name_match_score(target: str, candidates: Iterable[str]) -> float:
    """Puntuar una localidad frente a sus nombres de catálogo."""

    normalized_target = normalize_text(target)
    if not normalized_target:
        return 0.0

    best = 0.0
    for candidate in candidates:
        normalized_candidate = normalize_text(candidate)
        if not normalized_candidate:
            continue
        if (
            normalized_target in normalized_candidate
            or normalized_candidate in normalized_target
        ):
            best = max(best, 0.95)
        best = max(
            best,
            SequenceMatcher(
                None,
                normalized_target,
                normalized_candidate,
            ).ratio(),
        )

    return best


def alert_zone_for(
    province: str,
    municipality: str,
    latitude: float,
) -> str:
    """Resolver una de las siete zonas oficiales de avisos."""

    normalized_province = normalize_text(province)
    normalized_municipality = normalize_text(municipality)

    if "bizkaia" in normalized_province:
        if normalized_municipality in _BIZKAIA_COAST:
            return "BIZKAIA_COAST"
        return "BIZKAIA_INTERIOR"

    if "gipuzkoa" in normalized_province:
        if normalized_municipality in _GIPUZKOA_COAST:
            return "GIPUZKOA_COAST"
        return "GIPUZKOA_INTERIOR"

    if "araba" in normalized_province or "alava" in normalized_province:
        return "CORE" if latitude < 42.65 else "TRANSITION"

    raise LocationDiscoveryError(
        f"Provincia fuera de las zonas de avisos de Euskalmet: {province}"
    )
