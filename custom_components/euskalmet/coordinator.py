from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EuskalmetAPI, EuskalmetAPIError, EuskalmetNotFoundError
from .const import (
    ALERTS_UPDATE_INTERVAL,
    DAILY_FORECAST_UPDATE_INTERVAL,
    DAY_SUMMARY_UPDATE_INTERVAL,
    HOURLY_FORECAST_UPDATE_INTERVAL,
    MONTH_SUMMARY_UPDATE_INTERVAL,
    OCEAN_FORECAST_UPDATE_INTERVAL,
    POLLEN_UPDATE_INTERVAL,
    TIDES_UPDATE_INTERVAL,
    UPDATE_INTERVAL,
)
from .pollen import nearest_pollen_station
from .polling import update_due

_LOGGER = logging.getLogger(__name__)


class EuskalmetCoordinator(DataUpdateCoordinator):
    """Coordinar las actualizaciones de todas las plataformas."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        private_key: str,
        region: str,
        zone: str,
        location: str,
        station_id: str,
        station_name: str,
        alert_zone: str,
        latitude: float,
        longitude: float,
    ) -> None:
        session = async_get_clientsession(hass)
        pollen_id, pollen_name = nearest_pollen_station(latitude, longitude)

        self.api = EuskalmetAPI(
            session=session,
            email=email,
            private_key=private_key,
            region=region,
            zone=zone,
            location=location,
            station_id=station_id,
            station_name=station_name,
            alert_zone=alert_zone,
            pollen_municipality_id=pollen_id,
            pollen_municipality_name=pollen_name,
            preferred_language=hass.config.language,
            time_zone=hass.config.time_zone,
        )
        self._failed_endpoints: set[str] = set()
        self.config_entry_id = ""
        self._summary_day: Any = None
        self._summary_day_attempted: datetime | None = None
        self._month_summary: Any = None
        self._month_summary_attempted: datetime | None = None
        self._year_months: dict[int, Any] = {}
        self._year_month_attempted: dict[int, datetime] = {}
        self._daily_forecast: list[dict[str, Any]] | None = None
        self._daily_forecast_attempted: datetime | None = None
        self._hourly_forecast: dict[str, Any] | None = None
        self._hourly_forecast_attempted: datetime | None = None
        self._alerts: dict[str, Any] | None = None
        self._alerts_attempted: datetime | None = None
        self._ocean: dict[str, Any] | None = None
        self._ocean_attempted: datetime | None = None
        self._tides: dict[str, Any] | None = None
        self._tides_attempted: datetime | None = None
        self._pollen: dict[str, Any] | None = None
        self._pollen_attempted: datetime | None = None
        self._astro: dict[str, Any] | None = None
        self._astro_attempt_date: date | None = None

        super().__init__(
            hass,
            _LOGGER,
            name="euskalmet",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_setup(self) -> None:
        """Obtener una vez los metadatos estables de la estación."""

        try:
            station = await self.api.get_station()
        except EuskalmetAPIError as err:
            raise UpdateFailed(f"No se pudo obtener la estación: {err}") from err

        names = station.get("name", {})

        if isinstance(names, dict):
            self.api.station_name = names.get(
                "SPANISH",
                self.api.station_name,
            )

        try:
            await self.api.get_station_capabilities()
        except EuskalmetAPIError as err:
            _LOGGER.warning(
                "No se pudieron detectar las magnitudes de %s: %s",
                self.api.station_id,
                err,
            )

    def _optional_result(
        self,
        endpoint: str,
        result: Any,
        default: Any,
    ) -> Any:
        """Conservar el último dato de un endpoint opcional si falla."""

        if isinstance(result, asyncio.CancelledError):
            raise result

        # The daily summary can be absent briefly just after midnight. Do not
        # report an expected 404 or retain yesterday's accumulated values.
        if endpoint == "summary_day" and isinstance(result, EuskalmetNotFoundError):
            self._failed_endpoints.discard(endpoint)
            return default

        if isinstance(result, Exception):
            if endpoint not in self._failed_endpoints:
                _LOGGER.warning(
                    "No se pudo actualizar %s de Euskalmet: %s",
                    endpoint,
                    result,
                )
                self._failed_endpoints.add(endpoint)

            if self.data is not None:
                return self.data.get(endpoint, default)

            return default

        if endpoint in self._failed_endpoints:
            _LOGGER.info(
                "Se ha recuperado la actualización de %s de Euskalmet",
                endpoint,
            )
            self._failed_endpoints.remove(endpoint)

        return result

    async def _async_update_data(self) -> dict[str, Any]:
        """Actualizar todos los datos de Euskalmet."""

        now_utc = datetime.now(UTC)

        summary_day_due = update_due(
            self._summary_day_attempted,
            DAY_SUMMARY_UPDATE_INTERVAL,
            now_utc,
        )
        if summary_day_due:
            self._summary_day_attempted = now_utc
        summary_day_call = (
            self.api.get_aggregated_day_summary()
            if summary_day_due
            else asyncio.sleep(0, result=self._summary_day or {})
        )

        month_due = update_due(
            self._month_summary_attempted,
            MONTH_SUMMARY_UPDATE_INTERVAL,
            now_utc,
        )
        if month_due:
            self._month_summary_attempted = now_utc
        month_call = (
            self.api.get_aggregated_month_summary()
            if month_due
            else asyncio.sleep(0, result=self._month_summary or {})
        )

        daily_due = update_due(
            self._daily_forecast_attempted,
            DAILY_FORECAST_UPDATE_INTERVAL,
            now_utc,
        )
        if daily_due:
            self._daily_forecast_attempted = now_utc
        daily_call = (
            self.api.get_daily_forecast()
            if daily_due
            else asyncio.sleep(0, result=self._daily_forecast or [])
        )

        hourly_due = update_due(
            self._hourly_forecast_attempted,
            HOURLY_FORECAST_UPDATE_INTERVAL,
            now_utc,
        )
        if hourly_due:
            self._hourly_forecast_attempted = now_utc
        hourly_call = (
            self.api.get_hourly_forecast()
            if hourly_due
            else asyncio.sleep(0, result=self._hourly_forecast or {})
        )

        alerts_due = update_due(
            self._alerts_attempted,
            ALERTS_UPDATE_INTERVAL,
            now_utc,
        )
        if alerts_due:
            self._alerts_attempted = now_utc
        alerts_call = (
            self.api.get_alerts()
            if alerts_due
            else asyncio.sleep(
                0,
                result=self._alerts or self.api._empty_alerts(),
            )
        )

        ocean_due = update_due(
            self._ocean_attempted,
            OCEAN_FORECAST_UPDATE_INTERVAL,
            now_utc,
        )
        if ocean_due:
            self._ocean_attempted = now_utc
        ocean_call = (
            self.api.get_ocean_forecast()
            if ocean_due
            else asyncio.sleep(0, result=self._ocean or {})
        )

        tides_due = update_due(
            self._tides_attempted,
            TIDES_UPDATE_INTERVAL,
            now_utc,
        )
        if tides_due:
            self._tides_attempted = now_utc
        tides_call = (
            self.api.get_tides()
            if tides_due
            else asyncio.sleep(0, result=self._tides or {})
        )

        pollen_due = update_due(
            self._pollen_attempted,
            POLLEN_UPDATE_INTERVAL,
            now_utc,
        )
        if pollen_due:
            self._pollen_attempted = now_utc
        pollen_call = (
            self.api.get_pollen_measurements()
            if pollen_due
            else asyncio.sleep(0, result=self._pollen or {})
        )
        local_today = datetime.now(self.api.time_zone).date()
        astro_due = self._astro_attempt_date != local_today
        if astro_due:
            self._astro_attempt_date = local_today
        astro_call = (
            self.api.get_astro_calendar()
            if astro_due
            else asyncio.sleep(0, result=self._astro or {})
        )

        results = await asyncio.gather(
            self.api.get_all_measurements(),
            summary_day_call,
            month_call,
            daily_call,
            hourly_call,
            alerts_call,
            ocean_call,
            tides_call,
            self.api.get_radar_report(),
            pollen_call,
            astro_call,
            return_exceptions=True,
        )

        (
            current_result,
            summary_day_result,
            summary_month_result,
            daily_result,
            hourly_result,
            alerts_result,
            ocean_result,
            tides_result,
            radar_result,
            pollen_result,
            astro_result,
        ) = results

        if isinstance(current_result, asyncio.CancelledError):
            raise current_result

        if isinstance(current_result, Exception):
            raise UpdateFailed(
                f"No se pudieron actualizar las observaciones: {current_result}"
            ) from current_result

        if daily_due:
            daily = self._optional_result(
                "forecast_daily",
                daily_result,
                self._daily_forecast or [],
            )
            if not isinstance(daily_result, Exception):
                self._daily_forecast = daily
        else:
            daily = self._daily_forecast or []

        if hourly_due:
            hourly = self._optional_result(
                "forecast_hourly",
                hourly_result,
                self._hourly_forecast or {},
            )
            if not isinstance(hourly_result, Exception):
                self._hourly_forecast = hourly
        else:
            hourly = self._hourly_forecast or {}

        if alerts_due:
            alerts = self._optional_result(
                "alerts",
                alerts_result,
                self._alerts or self.api._empty_alerts(),
            )
            if not isinstance(alerts_result, Exception):
                self._alerts = alerts
        else:
            alerts = self._alerts or self.api._empty_alerts()

        if ocean_due:
            ocean = self._optional_result(
                "ocean",
                ocean_result,
                self._ocean or {},
            )
            if not isinstance(ocean_result, Exception):
                self._ocean = ocean
        else:
            ocean = self._ocean or {}

        if tides_due:
            tides = self._optional_result(
                "tides",
                tides_result,
                self._tides or {},
            )
            if not isinstance(tides_result, Exception):
                self._tides = tides
        else:
            tides = self._tides or {}

        radar = self._optional_result(
            "radar",
            radar_result,
            self.api._empty_radar(),
        )

        if pollen_due:
            pollen = self._optional_result(
                "pollen",
                pollen_result,
                self._pollen or {},
            )
            if not isinstance(pollen_result, Exception):
                self._pollen = pollen
        else:
            pollen = self._pollen or {}

        if astro_due:
            astro = self._optional_result(
                "astro",
                astro_result,
                self._astro or {},
            )
            if not isinstance(astro_result, Exception):
                self._astro = astro
        else:
            astro = self._astro or {}

        if summary_day_due:
            summary_day = self._optional_result(
                "summary_day",
                summary_day_result,
                self._summary_day or {},
            )
            if isinstance(summary_day_result, EuskalmetNotFoundError):
                self._summary_day = {}
            elif not isinstance(summary_day_result, Exception):
                self._summary_day = summary_day
        else:
            summary_day = self._summary_day or {}

        if month_due:
            summary_month = self._optional_result(
                "summary_month",
                summary_month_result,
                self._month_summary or {},
            )
            if not isinstance(summary_month_result, Exception):
                self._month_summary = summary_month
        else:
            summary_month = self._month_summary or {}
        local_now = datetime.now(self.api.time_zone)
        self._year_months[local_now.month] = summary_month
        missing_months = [
            month
            for month in range(1, local_now.month)
            if month not in self._year_months
            and update_due(
                self._year_month_attempted.get(month),
                MONTH_SUMMARY_UPDATE_INTERVAL,
                now_utc,
            )
        ]
        if missing_months:
            for month in missing_months:
                self._year_month_attempted[month] = now_utc
            loaded = await asyncio.gather(
                *(
                    self.api.get_aggregated_month_summary(
                        local_now.replace(month=month, day=1)
                    )
                    for month in missing_months
                ),
                return_exceptions=True,
            )
            for month, result in zip(missing_months, loaded, strict=True):
                if not isinstance(result, Exception):
                    self._year_months[month] = result

        weather = daily[0] if daily else None

        return {
            "current": current_result,
            "summary_day": summary_day,
            "summary_month": summary_month,
            "summary_year_months": dict(self._year_months),
            "weather": weather,
            "forecast_daily": daily,
            "forecast_hourly": hourly,
            "alerts": alerts,
            "ocean": ocean,
            "tides": tides,
            "radar": radar,
            "pollen": pollen,
            "astro": astro,
        }

    async def async_shutdown(self) -> None:
        """Cerrar recursos del cliente."""

        await self.api.close()
