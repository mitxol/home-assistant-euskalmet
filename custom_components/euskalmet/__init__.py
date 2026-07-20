from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import EuskalmetAPI, EuskalmetAPIError
from .const import DOMAIN
from .coordinator import EuskalmetCoordinator
from .history_websocket import async_register_history_websocket
from .radar_websocket import async_register_websocket_commands

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
    Platform.SENSOR,
    Platform.WEATHER,
]

FRONTEND_URL = "/euskalmet_static"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Publicar los recursos frontend opcionales sin cargarlos globalmente."""

    domain_data = hass.data.setdefault(DOMAIN, {})

    if domain_data.get("frontend_registered"):
        return

    frontend_path = Path(__file__).parent / "frontend"

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL,
                str(frontend_path),
                True,
            )
        ]
    )
    async_register_websocket_commands(hass)
    async_register_history_websocket(hass)

    domain_data["frontend_registered"] = True


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Inicializar los recursos globales de la integración."""

    await _async_register_frontend(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Configurar Euskalmet desde una entrada de configuración."""

    await _async_register_frontend(hass)
    coordinator = EuskalmetCoordinator(
        hass=hass,
        email=entry.data["email"],
        private_key=entry.data["private_key"],
        region=entry.data.get("region", "01"),
        zone=entry.data.get("zone", "01"),
        location=entry.data.get("location", "VITORIA-GASTEIZ"),
        station_id=entry.data.get("station_id", "C016"),
        station_name=entry.data.get("station_name", "Arkauti"),
        alert_zone=entry.data.get("alert_zone", "TRANSITION"),
    )
    coordinator.config_entry_id = entry.entry_id

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN].setdefault("coordinators", {})[entry.entry_id] = coordinator

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Autodetectar la ubicación de entradas creadas antes de 2.5.0."""

    if entry.version >= 2:
        return True

    api = EuskalmetAPI(
        session=async_get_clientsession(hass),
        email=entry.data["email"],
        private_key=entry.data["private_key"],
    )

    try:
        detected = await api.discover_configuration(
            float(hass.config.latitude),
            float(hass.config.longitude),
        )
    except (EuskalmetAPIError, TypeError, ValueError) as err:
        _LOGGER.error(
            "No se pudo migrar la ubicación de Euskalmet: %s",
            err,
        )
        return False

    hass.config_entries.async_update_entry(
        entry,
        data={
            **entry.data,
            **detected,
            "latitude": hass.config.latitude,
            "longitude": hass.config.longitude,
        },
        title=f"Euskalmet - {detected['municipality']}",
        version=2,
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Descargar las plataformas y liberar los recursos."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].get("coordinators", {}).pop(
            entry.entry_id,
            None,
        )
        await entry.runtime_data.async_shutdown()

    return unload_ok
