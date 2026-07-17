from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EuskalmetAPI, EuskalmetAPIError
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EuskalmetCoordinator(DataUpdateCoordinator):
    """Coordinar las actualizaciones de todas las plataformas."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        private_key: str,
        login_id: str,
        region: str,
        zone: str,
        location: str,
        station_id: str,
        station_name: str,
        alert_zone: str,
    ) -> None:
        session = async_get_clientsession(hass)

        self.api = EuskalmetAPI(
            session=session,
            email=email,
            private_key=private_key,
            login_id=login_id,
            region=region,
            zone=zone,
            location=location,
            station_id=station_id,
            station_name=station_name,
            alert_zone=alert_zone,
            time_zone=hass.config.time_zone,
        )
        self._failed_endpoints: set[str] = set()
        self.config_entry_id = ""
        self._month_summary: Any = None
        self._month_summary_updated: datetime | None = None
        self._year_months: dict[int, Any] = {}

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
            raise UpdateFailed(
                f"No se pudo obtener la estación: {err}"
            ) from err

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

        month_due = (
            self._month_summary_updated is None
            or datetime.now(timezone.utc) - self._month_summary_updated
            >= timedelta(hours=1)
        )
        month_call = (
            self.api.get_aggregated_month_summary()
            if month_due
            else asyncio.sleep(0, result=self._month_summary)
        )

        results = await asyncio.gather(
            self.api.get_all_measurements(),
            self.api.get_aggregated_day_summary(),
            month_call,
            self.api.get_daily_forecast(),
            self.api.get_hourly_forecast(),
            self.api.get_alerts(),
            self.api.get_radar_report(),
            return_exceptions=True,
        )

        (
            current_result,
            summary_day_result,
            summary_month_result,
            daily_result,
            hourly_result,
            alerts_result,
            radar_result,
        ) = results

        if isinstance(current_result, asyncio.CancelledError):
            raise current_result

        if isinstance(current_result, Exception):
            raise UpdateFailed(
                f"No se pudieron actualizar las observaciones: {current_result}"
            ) from current_result

        daily = self._optional_result(
            "forecast_daily",
            daily_result,
            [],
        )
        hourly = self._optional_result(
            "forecast_hourly",
            hourly_result,
            {},
        )
        alerts = self._optional_result(
            "alerts",
            alerts_result,
            self.api._empty_alerts(),
        )
        radar = self._optional_result(
            "radar",
            radar_result,
            self.api._empty_radar(),
        )
        summary_day = self._optional_result(
            "summary_day", summary_day_result, {}
        )
        summary_month = self._optional_result(
            "summary_month", summary_month_result, self._month_summary or {}
        )
        if not isinstance(summary_month_result, Exception) and month_due:
            self._month_summary = summary_month
            self._month_summary_updated = datetime.now(timezone.utc)
        local_now = datetime.now(self.api.time_zone)
        self._year_months[local_now.month] = summary_month
        missing_months = [
            month
            for month in range(1, local_now.month)
            if month not in self._year_months
        ]
        if missing_months:
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
            "radar": radar,
        }

    async def async_shutdown(self) -> None:
        """Cerrar recursos del cliente."""

        await self.api.close()
