from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import EuskalmetCoordinator
from .entity import device_info
from .formatting import spanish_weather_condition

PARALLEL_UPDATES = 0


WEATHER_MAP = {
    "00": "sunny",
    "01": "partlycloudy",
    "02": "partlycloudy",
    "03": "cloudy",
    "04": "cloudy",
    "05": "fog",
    "06": "fog",
    "07": "fog",
    "08": "rainy",
    "09": "rainy",
    "10": "rainy",
    "11": "pouring",
    "12": "rainy",
    "13": "pouring",
    "14": "snowy-rainy",
    "15": "lightning-rainy",
    "16": "lightning",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar la entidad meteorológica."""

    coordinator = entry.runtime_data

    async_add_entities(
        [EuskalmetWeather(coordinator)]
    )


class EuskalmetWeather(
    CoordinatorEntity,
    WeatherEntity,
):
    """Entidad meteorológica de Euskalmet."""

    _attr_has_entity_name = True
    _attr_translation_key = "weather"

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
        | WeatherEntityFeature.FORECAST_HOURLY
    )

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: EuskalmetCoordinator) -> None:
        """Inicializar la entidad."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.api.station_id}_weather"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Actualizar el estado y publicar las previsiones renovadas."""

        super()._handle_coordinator_update()
        self.hass.async_create_task(self.async_update_listeners(None))

    @property
    def device_info(self) -> DeviceInfo:
        """Información del dispositivo."""

        return device_info(
            self.coordinator.api.station_id,
            self.coordinator.api.station_name,
        )

    def _current(self, key: str) -> dict[str, Any] | None:
        """Obtener una medición actual."""

        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get(
            "current",
            {},
        )

        measurement = current.get(key)

        if measurement and measurement.get("stale") is True:
            return None

        return measurement

    def _map_condition(
        self,
        code: str | None,
        forecast_datetime: datetime | None = None,
    ) -> str | None:
        """Convertir un código Euskalmet a una condición de HA."""

        if code is None:
            return None

        condition = WEATHER_MAP.get(
            str(code).zfill(2),
            "cloudy",
        )

        if condition != "sunny":
            return condition

        # Para el estado actual usamos sun.sun.
        if forecast_datetime is None:
            sun = self.hass.states.get("sun.sun")

            if (
                sun is not None
                and sun.state == "below_horizon"
            ):
                return "clear-night"

        return condition

    def _hourly_data(self) -> dict:
        """Obtener el documento completo de previsión horaria."""

        if not self.coordinator.data:
            return {}

        hourly = self.coordinator.data.get(
            "forecast_hourly",
            {},
        )

        return hourly if isinstance(hourly, dict) else {}

    def _hourly_items(self) -> list[dict]:
        """Obtener los bloques horarios."""

        return (
            self._hourly_data()
            .get("trends", {})
            .get("set", [])
        )

    @staticmethod
    def _extract_hour(item: dict) -> int | None:
        """Extraer la hora inicial del campo range."""

        value = item.get("range")

        if not isinstance(value, str):
            return None

        try:
            start = value.split("[", 1)[1].split("..", 1)[0]
            return int(start.split(":", 1)[0])

        except (IndexError, TypeError, ValueError):
            return None

    def _hourly_base_datetime(self) -> datetime:
        """Obtener la fecha UTC de validez del pronóstico."""

        raw_datetime = self._hourly_data().get("for")

        if isinstance(raw_datetime, str):
            parsed = dt_util.parse_datetime(raw_datetime)

            if parsed is not None:
                return dt_util.as_utc(parsed)

        return datetime.now(UTC)

    def _build_hour_datetime(
        self,
        item: dict,
    ) -> datetime | None:
        """Construir el datetime UTC de un bloque horario."""

        hour = self._extract_hour(item)

        if hour is None:
            return None

        base = self._hourly_base_datetime()
        forecast_date = item.get("_forecast_date")
        if isinstance(forecast_date, str):
            try:
                parsed_date = datetime.fromisoformat(forecast_date)
            except ValueError:
                pass
            else:
                base = base.replace(
                    year=parsed_date.year,
                    month=parsed_date.month,
                    day=parsed_date.day,
                )

        try:
            return base.replace(
                hour=hour,
                minute=0,
                second=0,
                microsecond=0,
            )

        except ValueError:
            return None

    def _nearest_hourly_condition_code(self) -> str | None:
        """Obtener el código del próximo bloque horario."""

        now = dt_util.now()
        candidates: list[tuple[datetime, dict]] = []

        for item in self._hourly_items():
            forecast_datetime = self._build_hour_datetime(item)

            if (
                forecast_datetime is None
                or forecast_datetime <= now
            ):
                continue

            candidates.append(
                (forecast_datetime, item)
            )

        if not candidates:
            return None

        _, nearest = min(
            candidates,
            key=lambda candidate: candidate[0],
        )

        return (
            nearest.get("symbolSet", {})
            .get("weather", {})
            .get("id")
        )

    @property
    def condition(self) -> str | None:
        """Condición meteorológica actual."""

        # La siguiente previsión horaria suele representar mejor
        # la condición actual que una predicción diaria.
        hourly_code = self._nearest_hourly_condition_code()

        if hourly_code is not None:
            return self._map_condition(hourly_code)

        if not self.coordinator.data:
            return None

        weather = self.coordinator.data.get("weather")

        if not isinstance(weather, dict):
            return None

        code = (
            weather.get("weather", {})
            .get("id")
        )

        return self._map_condition(code)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Añadir descripción y metadatos de la edición de la previsión."""

        hourly = self._hourly_data()

        return {
            "condicion": spanish_weather_condition(self.condition),
            "prevision_emitida": hourly.get("at"),
            "prevision_valida": hourly.get("for"),
            "localidad_prevision": self.coordinator.api.location,
            "region_prevision": self.coordinator.api.region,
            "zona_prevision": self.coordinator.api.zone,
        }

    @property
    def native_temperature(self) -> Any:
        """Temperatura actual."""

        value = self._current("temperature")

        return value.get("value") if value else None

    @property
    def humidity(self) -> Any:
        """Humedad actual."""

        value = self._current("humidity")

        return value.get("value") if value else None

    @property
    def native_pressure(self) -> Any:
        """Presión atmosférica actual."""

        value = self._current("pressure")

        return value.get("value") if value else None

    @property
    def native_wind_speed(self) -> Any:
        """Velocidad actual del viento."""

        value = self._current("wind_speed")

        return value.get("value") if value else None

    @property
    def wind_bearing(self) -> Any:
        """Dirección actual del viento."""

        value = self._current("wind_direction")

        return value.get("value") if value else None

    @property
    def native_precipitation(self) -> Any:
        """Precipitación actual."""

        value = self._current("precipitation")

        return value.get("value") if value else None

    async def async_forecast_daily(
        self,
    ) -> list[Forecast]:
        """Devolver la previsión diaria."""

        forecast: list[Forecast] = []

        if not self.coordinator.data:
            return forecast

        daily = sorted(
            self.coordinator.data.get(
                "forecast_daily",
                [],
            ),
            key=lambda day: day.get("date", ""),
        )

        for day in daily:
            forecast_datetime = day.get("date")

            if not forecast_datetime:
                continue

            weather = day.get("weather", {})
            temperatures = day.get(
                "temperatureRange",
                {},
            )

            forecast.append(
                Forecast(
                    datetime=forecast_datetime,
                    condition=self._map_condition(
                        weather.get("id")
                    ),
                    native_temperature=temperatures.get(
                        "max"
                    ),
                    native_templow=temperatures.get(
                        "min"
                    ),
                )
            )

        return forecast

    async def async_forecast_hourly(
        self,
    ) -> list[Forecast]:
        """Devolver la previsión horaria futura."""

        forecast: list[Forecast] = []
        now = dt_util.now()

        prepared_items: list[
            tuple[datetime, dict]
        ] = []

        for item in self._hourly_items():
            forecast_datetime = self._build_hour_datetime(
                item
            )

            if forecast_datetime is None:
                continue

            # Se descartan las horas ya iniciadas o finalizadas.
            # A las 09:35, la primera previsión será la de las 10:00.
            if forecast_datetime <= now:
                continue

            prepared_items.append(
                (forecast_datetime, item)
            )

        prepared_items.sort(
            key=lambda prepared: prepared[0]
        )

        for forecast_datetime, item in prepared_items:
            weather = (
                item.get("symbolSet", {})
                .get("weather", {})
            )

            wind_speed = (
                item.get("windspeed", {})
                .get("value")
            )

            if wind_speed is not None:
                try:
                    wind_speed = round(
                        float(wind_speed) * 3.6,
                        1,
                    )
                except (TypeError, ValueError):
                    wind_speed = None

            forecast.append(
                Forecast(
                    datetime=forecast_datetime.isoformat(),
                    condition=self._map_condition(
                        weather.get("id"),
                        forecast_datetime,
                    ),
                    native_temperature=(
                        item.get("temperature", {})
                        .get("value")
                    ),
                    native_precipitation=(
                        item.get("precipitation", {})
                        .get("value")
                    ),
                    native_wind_speed=wind_speed,
                    wind_bearing=(
                        item.get("winddirection", {})
                        .get("value")
                    ),
                )
            )

        return forecast
