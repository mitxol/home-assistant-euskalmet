from __future__ import annotations

from typing import Final


WEATHER_CONDITION_ES: Final[dict[str, str]] = {
    "clear-night": "Despejado",
    "cloudy": "Nublado",
    "exceptional": "Excepcional",
    "fog": "Niebla",
    "hail": "Granizo",
    "lightning": "Tormenta",
    "lightning-rainy": "Tormenta con lluvia",
    "partlycloudy": "Parcialmente nublado",
    "pouring": "Lluvia intensa",
    "rainy": "Lluvia",
    "snowy": "Nieve",
    "snowy-rainy": "Aguanieve",
    "sunny": "Soleado",
    "windy": "Viento",
    "windy-variant": "Viento con nubes",
}

_COMPASS_POINTS: Final[tuple[str, ...]] = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSO",
    "SO",
    "OSO",
    "O",
    "ONO",
    "NO",
    "NNO",
)


def degrees_to_compass(value: object) -> str | None:
    """Convertir grados meteorológicos a uno de 16 puntos cardinales."""

    if isinstance(value, bool) or value is None:
        return None

    try:
        degrees = float(str(value).replace(",", ".")) % 360
    except (TypeError, ValueError):
        return None

    return _COMPASS_POINTS[int((degrees + 11.25) // 22.5) % 16]


def spanish_weather_condition(condition: str | None) -> str | None:
    """Traducir una condición meteorológica canónica de Home Assistant."""

    if condition is None:
        return None
    return WEATHER_CONDITION_ES.get(condition, condition)
