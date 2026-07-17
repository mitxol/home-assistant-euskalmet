"""Utilidades compartidas por las entidades de Euskalmet."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, MANUFACTURER, MODEL


def device_info(station_id: str, station_name: str) -> DeviceInfo:
    """Construir la información común del dispositivo meteorológico."""

    return DeviceInfo(
        identifiers={(DOMAIN, station_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=station_name,
        sw_version="OpenData API",
    )


def summary_device_info(station_id: str, station_name: str) -> DeviceInfo:
    """Construir el dispositivo separado de resúmenes y estadísticas."""

    return DeviceInfo(
        identifiers={(DOMAIN, f"{station_id}_summaries")},
        manufacturer=MANUFACTURER,
        model="Resúmenes meteorológicos",
        name=f"{station_name} - Resúmenes y estadísticas",
        sw_version="OpenData API",
        via_device=(DOMAIN, station_id),
    )
