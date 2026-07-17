from __future__ import annotations

from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import RADAR_BOUNDS, RADAR_CENTER, RADAR_RANGE_KM
from .coordinator import EuskalmetCoordinator
from .entity import device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar la cámara de radar de Euskalmet."""

    coordinator = entry.runtime_data

    async_add_entities(
        [
            EuskalmetRadarCamera(coordinator),
        ]
    )


class EuskalmetRadarCamera(
    CoordinatorEntity,
    Camera,
):
    """Cámara con la última imagen del radar de precipitación."""

    _attr_has_entity_name = True
    _attr_name = "Radar de precipitación"
    _attr_content_type = "image/png"

    def __init__(self, coordinator: EuskalmetCoordinator) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)

        self._attr_unique_id = (
            f"{coordinator.api.station_id}_precipitation_radar"
        )

    @property
    def device_info(self) -> DeviceInfo:
        return device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    @property
    def available(self) -> bool:
        if not super().available:
            return False

        if self.coordinator.data is None:
            return False

        radar = self.coordinator.data.get(
            "radar",
            {},
        )

        return bool(
            radar.get("available")
            and radar.get("image")
        )

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Devolver la última imagen del radar."""

        if self.coordinator.data is None:
            return None

        radar = self.coordinator.data.get(
            "radar",
            {},
        )

        return radar.get("image")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}

        radar = self.coordinator.data.get(
            "radar",
            {},
        )

        return {
            "available": radar.get(
                "available",
                False,
            ),
            "range": radar.get("range"),
            "timestamp": radar.get("timestamp"),
            "date": radar.get("date"),
            "report_type": radar.get("report_type"),
            "report": radar.get("report"),
            "frame_count": radar.get(
                "frame_count",
                0,
            ),
            "bounds": RADAR_BOUNDS,
            "center": RADAR_CENTER,
            "range_km": RADAR_RANGE_KM,
            "config_entry_id": self.coordinator.config_entry_id,
        }
