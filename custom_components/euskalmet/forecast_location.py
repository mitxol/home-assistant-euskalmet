"""Selección de previsión independiente de las observaciones de la estación."""

from collections.abc import Mapping
from typing import Any

CONF_FORECAST_LOCATION = "forecast_location"
STATION_FORECAST = "station"
FORECAST_FIELDS = ("region", "zone", "location")
_DEFAULTS = ("01", "01", "VITORIA-GASTEIZ")


def forecast_location_key(location: Mapping[str, str]) -> str:
    """Identificar un municipio sin confundir localidades de distintas zonas."""
    return "/".join(location[field] for field in FORECAST_FIELDS)


def forecast_configuration(
    data: Mapping[str, Any], options: Mapping[str, Any]
) -> dict[str, str]:
    """Aplicar solo la ubicación de previsión; conservar la estación y sus avisos."""
    selected = options.get(CONF_FORECAST_LOCATION)
    if isinstance(selected, str):
        parts = selected.split("/")
        if len(parts) == len(FORECAST_FIELDS) and all(parts):
            return dict(zip(FORECAST_FIELDS, parts, strict=True))

    # Sin opciones, con selección automática o con opciones incompletas,
    # mantener exactamente la ubicación de las entradas existentes.
    return {
        field: data.get(field, default)
        for field, default in zip(FORECAST_FIELDS, _DEFAULTS, strict=True)
    }
