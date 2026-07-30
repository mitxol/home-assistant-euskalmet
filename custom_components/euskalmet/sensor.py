from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MEASURES
from .coordinator import EuskalmetCoordinator
from .entity import device_info, pollen_device_info, summary_device_info
from .formatting import degrees_to_compass

PARALLEL_UPDATES = 0

SUMMARY_SENSOR_SPECS = (
    (
        "precipitation",
        "Precipitación",
        "precipitation",
        (("total", ""),),
        "mm",
        "mdi:weather-rainy",
    ),
    (
        "temperature",
        "Temperatura",
        "temperature",
        (("min", "mínima"), ("mean", "media"), ("max", "máxima")),
        "°C",
        "mdi:thermometer",
    ),
    (
        "wind_gust",
        "Racha",
        "max_speed",
        (("max", "máxima"),),
        "km/h",
        "mdi:weather-windy",
    ),
    (
        "humidity",
        "Humedad",
        "humidity",
        (("min", "mínima"), ("mean", "media"), ("max", "máxima")),
        "%",
        "mdi:water-percent",
    ),
    (
        "pressure",
        "Presión",
        "pressure",
        (("min", "mínima"), ("mean", "media"), ("max", "máxima")),
        "hPa",
        "mdi:gauge",
    ),
    (
        "irradiance",
        "Radiación solar",
        "irradiance",
        (("mean", "media"), ("max", "máxima")),
        "W/m²",
        "mdi:white-balance-sunny",
    ),
    (
        "wind_speed",
        "Velocidad del viento",
        "mean_speed",
        (("mean", "media"),),
        "km/h",
        "mdi:weather-windy",
    ),
)

SUMMARY_SENSORS = tuple(
    (
        f"{prefix}_{field}_{suffix}" if label else f"{prefix}_{suffix}",
        " ".join(part for part in (name, label, period_label) if part),
        section,
        measure,
        field,
        unit,
        icon,
    )
    for prefix, name, measure, fields, unit, icon in SUMMARY_SENSOR_SPECS
    for field, label in fields
    for section, suffix, period_label in (
        ("summary_day", "today", "hoy"),
        (
            "summary_month",
            "month",
            "este mes" if prefix == "precipitation" else "del mes",
        ),
    )
)

SUMMARY_MEASURE_TYPES = {
    "precipitation": "measuresForWater",
    "temperature": "measuresForAir",
    "humidity": "measuresForAir",
    "pressure": "measuresForAtmosphere",
    "irradiance": "measuresForSun",
    "mean_speed": "measuresForWind",
    "max_speed": "measuresForWind",
}

SUMMARY_REQUIRED_KEYS = {
    "precipitation": "precipitation",
    "temperature": "temperature",
    "humidity": "humidity",
    "pressure": "pressure",
    "irradiance": "irradiance",
    "mean_speed": "wind_speed",
    "max_speed": "wind_gust",
}

ANNUAL_SUMMARY_SENSORS = tuple(
    (
        key.replace("_today", "_year").replace("_month", "_year"),
        name.replace(" hoy", " este año")
        .replace(" del mes", " del año")
        .replace(" este mes", " este año"),
        "summary_year",
        measure,
        field,
        unit,
        icon,
    )
    for key, name, section, measure, field, unit, icon in SUMMARY_SENSORS
    if section == "summary_month"
)

EU_POLLEN_NAMES = {
    "no_identificados": "Identifikatu gabeak",
    "compositae_otras_": "Beste konposatu batzuk",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar los sensores de Euskalmet."""

    coordinator = entry.runtime_data
    configured_measures = entry.data.get("available_measures")
    supported = coordinator.api.supported_measurements

    if not supported and isinstance(configured_measures, list):
        supported = {key for key in configured_measures if key in MEASURES}
    if not supported:
        supported = set(MEASURES)

    entities = [
        EuskalmetSensor(coordinator, key) for key in MEASURES if key in supported
    ]

    # Eliminar del registro sensores que versiones anteriores crearon para
    # magnitudes que esta estación no publica.
    registry = er.async_get(hass)
    for key in MEASURES.keys() - supported:
        entity_id = registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            f"{coordinator.api.station_id}_{key}",
        )
        if entity_id is not None:
            registry.async_remove(entity_id)

    entities.append(EuskalmetAlertLevelSensor(coordinator))
    entities.extend(
        EuskalmetSummarySensor(coordinator, config)
        for config in SUMMARY_SENSORS
        if SUMMARY_REQUIRED_KEYS[config[3]] in supported
    )
    entities.extend(
        EuskalmetSummarySensor(coordinator, config)
        for config in ANNUAL_SUMMARY_SENSORS
        if SUMMARY_REQUIRED_KEYS[config[3]] in supported
    )

    pollen_species: set[str] = set()
    pollen_total_added = False

    def add_pollen_entities() -> None:
        nonlocal pollen_total_added
        pollen = (coordinator.data or {}).get("pollen", {})
        species = pollen.get("species", {}) if isinstance(pollen, dict) else {}
        if not isinstance(species, dict):
            return

        new_species = set(species) - pollen_species
        pollen_entities: list[SensorEntity] = []
        if not pollen_total_added:
            pollen_entities.append(EuskalmetPollenTotalSensor(coordinator))
            pollen_total_added = True
        pollen_entities.extend(
            EuskalmetPollenSpeciesSensor(
                coordinator,
                specie_id,
                (
                    EU_POLLEN_NAMES.get(
                        specie_id,
                        str(species[specie_id].get("name") or specie_id),
                    )
                    if str(hass.config.language).lower().startswith("eu")
                    else str(species[specie_id].get("name") or specie_id)
                ),
            )
            for specie_id in sorted(new_species)
            if isinstance(species[specie_id], dict)
        )
        pollen_species.update(new_species)
        if pollen_entities:
            async_add_entities(pollen_entities)

    async_add_entities(entities)
    add_pollen_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_pollen_entities))


class EuskalmetPollenSensor(CoordinatorEntity, SensorEntity):
    """Base for measurements from an Open Data Euskadi pollen station."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "grains/m³"
    _attr_state_class = "measurement"
    _attr_icon = "mdi:flower-pollen"

    @property
    def device_info(self) -> DeviceInfo:
        return pollen_device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.pollen_municipality_id,
            self.coordinator.api.pollen_municipality_name,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        pollen = (self.coordinator.data or {}).get("pollen", {})
        return {
            "observed_on": pollen.get("observed_on"),
            "municipality_id": pollen.get("municipality_id"),
            "municipality_name": pollen.get("municipality_name"),
            "source": "opendata_euskadi_pollen_api",
        }


class EuskalmetPollenTotalSensor(EuskalmetPollenSensor):
    """Total pollen/spore count in the newest published sample."""

    _attr_translation_key = "pollen_total"

    def __init__(self, coordinator: EuskalmetCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.api.station_id}_pollen_"
            f"{coordinator.api.pollen_municipality_id}_total"
        )

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("pollen", {}).get("total")


class EuskalmetPollenSpeciesSensor(EuskalmetPollenSensor):
    """Pollen/spore count for one taxon."""

    def __init__(
        self,
        coordinator: EuskalmetCoordinator,
        specie_id: str,
        specie_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.specie_id = specie_id
        self._attr_name = specie_name
        self._attr_unique_id = (
            f"{coordinator.api.station_id}_pollen_"
            f"{coordinator.api.pollen_municipality_id}_{specie_id}"
        )

    @property
    def native_value(self) -> float | None:
        pollen = (self.coordinator.data or {}).get("pollen", {})
        if not pollen.get("observed_on"):
            return None
        measurement = pollen.get("species", {}).get(self.specie_id)
        if not isinstance(measurement, dict):
            return 0.0
        return measurement.get("value")


class EuskalmetSummarySensor(CoordinatorEntity, SensorEntity):
    """Sensor de resumen diario o mensual calculado por Euskalmet."""

    _attr_has_entity_name = True
    _attr_state_class = "measurement"

    def __init__(self, coordinator: EuskalmetCoordinator, config: tuple) -> None:
        super().__init__(coordinator)
        (
            self.key,
            _default_name,
            self.section,
            self.measure,
            self.field,
            self._attr_native_unit_of_measurement,
            self._attr_icon,
        ) = config
        self._attr_translation_key = f"summary_{self.key}"
        self._attr_unique_id = f"{coordinator.api.station_id}_{self.key}"
        if self.measure == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif self.measure in {"mean_speed", "max_speed"}:
            self._attr_device_class = SensorDeviceClass.WIND_SPEED
        elif self.measure == "precipitation":
            self._attr_device_class = SensorDeviceClass.PRECIPITATION
            self._attr_suggested_display_precision = 1
        elif self.measure == "humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
        elif self.measure == "pressure":
            self._attr_device_class = SensorDeviceClass.ATMOSPHERIC_PRESSURE
        elif self.measure == "irradiance":
            self._attr_device_class = SensorDeviceClass.IRRADIANCE

    @property
    def device_info(self) -> DeviceInfo:
        return summary_device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    def _summary(self) -> dict[str, Any]:
        if self.section == "summary_year":
            return self._annual_summary()
        document = (self.coordinator.data or {}).get(self.section, {})
        items = document.get("items", []) if isinstance(document, dict) else []
        measure_type = SUMMARY_MEASURE_TYPES[self.measure]
        for item in items:
            if (
                isinstance(item, dict)
                and item.get("measureType") == measure_type
                and item.get("measureId") == self.measure
            ):
                summary = item.get("summary")
                return summary if isinstance(summary, dict) else {}
        return {}

    def _annual_summary(self) -> dict[str, Any]:
        """Combinar resúmenes mensuales conservando pesos y extremos."""

        documents = (self.coordinator.data or {}).get("summary_year_months", {})
        summaries: list[tuple[int, dict[str, Any]]] = []
        for month, document in documents.items():
            items = document.get("items", []) if isinstance(document, dict) else []
            for item in items:
                if (
                    isinstance(item, dict)
                    and item.get("measureType") == SUMMARY_MEASURE_TYPES[self.measure]
                    and item.get("measureId") == self.measure
                    and isinstance(item.get("summary"), dict)
                ):
                    summaries.append((int(month), item["summary"]))
                    break
        if not summaries:
            return {}
        if self.field == "total":
            totals = [
                summary["total"]
                for _, summary in summaries
                if isinstance(summary.get("total"), (int, float))
                and not isinstance(summary.get("total"), bool)
            ]
            return {"total": sum(totals)}
        if self.field == "mean":
            weighted = [
                (float(s["mean"]), int(s.get("processedReadings", 0)))
                for _, s in summaries
                if isinstance(s.get("mean"), (int, float))
                and int(s.get("processedReadings", 0)) > 0
            ]
            count = sum(weight for _, weight in weighted)
            return {
                "mean": (
                    sum(value * weight for value, weight in weighted) / count
                    if count
                    else None
                )
            }
        extremes = [
            (month, s[self.field])
            for month, s in summaries
            if isinstance(s.get(self.field), dict)
            and isinstance(s[self.field].get("value"), (int, float))
        ]
        if not extremes:
            return {}
        month, extreme = (
            min(extremes, key=lambda item: item[1]["value"])
            if self.field == "min"
            else max(extremes, key=lambda item: item[1]["value"])
        )
        return {self.field: {**extreme, "atMonth": month}}

    @property
    def native_value(self) -> Any:
        value = self._summary().get(self.field)
        if isinstance(value, dict):
            value = value.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if self.measure in {"mean_speed", "max_speed"}:
            return round(float(value) * 3.6, 1)
        if self.measure == "precipitation":
            return value
        return round(float(value), 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = self._summary()
        extreme = summary.get(self.field)
        document = (self.coordinator.data or {}).get(self.section, {})
        provisional = isinstance(document, dict) and document.get("provisional") is True
        public_fallback = (
            isinstance(document, dict) and document.get("public_fallback") is True
        )
        attributes = {
            "station": self.coordinator.api.station_id,
            "period": self.section.removeprefix("summary_"),
            "measure": self.measure,
            "source": (
                "euskalmet_public_daily_provisional"
                if public_fallback
                else "euskalmet_api_aggregated_by_day_provisional"
                if provisional
                else "euskalmet_api_aggregated_summary"
            ),
        }
        if isinstance(extreme, dict):
            attributes.update(
                {key: value for key, value in extreme.items() if key != "value"}
            )
        return attributes


class EuskalmetSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Sensor de una medida de Euskalmet."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EuskalmetCoordinator,
        key: str,
    ) -> None:
        super().__init__(coordinator)

        self.key = key
        self.cfg = MEASURES[key]

        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.api.station_id}_{key}"

        self._attr_icon = self.cfg["icon"]

        if "device_class" in self.cfg:
            self._attr_device_class = self.cfg["device_class"]

        if "state_class" in self.cfg:
            self._attr_state_class = self.cfg["state_class"]

        self._attr_native_unit_of_measurement = self.cfg["unit"]

    @property
    def device_info(self) -> DeviceInfo:
        return device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None

        current = self.coordinator.data.get(
            "current",
            {},
        )

        data = current.get(self.key)

        if data is None or data.get("stale") is True:
            return None

        value = data.get("value")

        if self.key == "wind_direction":
            return degrees_to_compass(value)

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}

        current = self.coordinator.data.get(
            "current",
            {},
        )

        data = current.get(self.key)

        if data is None:
            return {}

        attributes = {
            "sensor": data.get(
                "measure_id",
                self.cfg["sensor"],
            ),
            "station": self.coordinator.api.station_id,
            "station_name": self.coordinator.api.station_name,
            "sensor_position_cm": data.get("sensor_position_cm"),
            "measure": self.cfg["measure"],
            "measure_type": self.cfg["measure_type"],
            "source": data.get("source", "euskalmet_api"),
            "slot": data.get("slot"),
            "observed_at": data.get("observed_at"),
            "age_seconds": data.get("age_seconds"),
            "stale": data.get("stale"),
            "from_cache": data.get("from_cache", False),
        }

        if self.key == "wind_direction":
            attributes["degrees"] = data.get("value")

        return attributes


class EuskalmetAlertLevelSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Nivel máximo de aviso meteorológico."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["none", "yellow", "orange", "red"]
    _attr_translation_key = "alert_level"

    def __init__(self, coordinator: EuskalmetCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.api.station_id}_alert_level"

    @property
    def device_info(self) -> DeviceInfo:
        return device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    @property
    def native_value(self) -> str:
        if self.coordinator.data is None:
            return "none"

        severity = self.coordinator.data.get("alerts", {}).get("severity", "NONE")

        return str(severity).lower()

    @property
    def icon(self) -> str:
        severity = self.native_value

        return {
            "yellow": "mdi:alert",
            "orange": "mdi:alert-octagon",
            "red": "mdi:alert-decagram",
        }.get(
            severity,
            "mdi:check-circle-outline",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}

        alerts = self.coordinator.data.get(
            "alerts",
            {},
        )

        descriptions = alerts.get(
            "descriptions",
            [],
        )

        return {
            "active": alerts.get(
                "active",
                False,
            ),
            "alert_count": alerts.get(
                "count",
                0,
            ),
            "causes": alerts.get(
                "causes",
                [],
            ),
            "description": (descriptions[0] if descriptions else None),
            "descriptions": descriptions,
            "alerts": alerts.get(
                "alerts",
                [],
            ),
        }
