from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EuskalmetCoordinator
from .entity import device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar los sensores binarios de Euskalmet."""

    coordinator = entry.runtime_data

    async_add_entities(
        [
            EuskalmetAlertBinarySensor(coordinator),
        ]
    )


class EuskalmetAlertBinarySensor(
    CoordinatorEntity,
    BinarySensorEntity,
):
    """Indica si existe algún aviso meteorológico activo."""

    _attr_has_entity_name = True
    _attr_name = "Aviso meteorológico"

    def __init__(self, coordinator: EuskalmetCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.api.station_id}_weather_alert"
        )

    @property
    def device_info(self) -> DeviceInfo:
        return device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False

        alerts = self.coordinator.data.get("alerts", {})

        return bool(alerts.get("active", False))

    @property
    def icon(self) -> str:
        if self.coordinator.data is None:
            return "mdi:check-circle-outline"

        severity = (
            self.coordinator.data
            .get("alerts", {})
            .get("severity", "NONE")
            .upper()
        )

        return {
            "YELLOW": "mdi:alert",
            "ORANGE": "mdi:alert-octagon",
            "RED": "mdi:alert-decagram",
        }.get(severity, "mdi:check-circle-outline")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}

        alerts = self.coordinator.data.get("alerts", {})

        descriptions = alerts.get("descriptions", [])

        return {
            "severity": alerts.get("severity", "NONE").lower(),
            "alert_count": alerts.get("count", 0),
            "causes": alerts.get("causes", []),
            "description": (
                descriptions[0]
                if descriptions
                else None
            ),
            "descriptions": descriptions,
            "alerts": alerts.get("alerts", []),
        }
