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


def pollen_device_info(
    station_id: str,
    municipality_id: str,
    municipality_name: str,
) -> DeviceInfo:
    """Build the device representing an official pollen station."""

    return DeviceInfo(
        identifiers={(DOMAIN, f"pollen_{station_id}_{municipality_id}")},
        manufacturer="Gobierno Vasco - Departamento de Salud",
        model="Estación de polen",
        name=f"Polen - {municipality_name}",
        sw_version="Open Data Euskadi API",
        via_device=(DOMAIN, station_id),
    )
