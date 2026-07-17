from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import (
    EuskalmetAPI,
    EuskalmetAPIError,
    EuskalmetAuthenticationError,
    EuskalmetConnectionError,
)
from .const import DOMAIN, MEASURES
from .geography import LocationDiscoveryError


class EuskalmetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configurar credenciales y una estación meteorológica elegida."""

    VERSION = 2

    def __init__(self) -> None:
        """Inicializar el flujo de dos pasos."""

        self._credentials: dict[str, Any] = {}
        self._api: EuskalmetAPI | None = None
        self._stations: list[dict[str, Any]] = []
        self._selected_station: dict[str, Any] | None = None

    @staticmethod
    def _measure_names(keys: list[str]) -> str:
        """Mostrar nombres legibles de una lista de magnitudes."""

        return ", ".join(str(MEASURES[key]["name"]) for key in keys)

    @classmethod
    def _station_status(cls, station: dict[str, Any]) -> str:
        """Resumir capacidades sin hacer excesivamente largo el selector."""

        available = station["available_measures"]
        missing = station["missing_measures"]
        count = f"{len(available)}/{len(MEASURES)}"

        if not missing:
            return f"{count} completa"
        if len(available) <= 3:
            return f"{count} · solo {cls._measure_names(available)}"
        return f"{count} · sin {cls._measure_names(missing)}"

    async def _async_create_selected_entry(self) -> ConfigFlowResult:
        """Resolver los catálogos y crear la entrada seleccionada."""

        if self._api is None or self._selected_station is None:
            return await self.async_step_user()

        station = self._selected_station
        station_id = station["station_id"]
        detected = await self._api.discover_configuration_for_station(
            station_id
        )

        if any(
            entry.data.get("station_id") == station_id
            for entry in self._async_current_entries()
        ):
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(station_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Euskalmet - {station['station_name']}",
            data={
                **self._credentials,
                **detected,
                "latitude": station["station_latitude"],
                "longitude": station["station_longitude"],
                "available_measures": station["available_measures"],
            },
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Validar las credenciales y preparar la lista de estaciones."""

        errors: dict[str, str] = {}

        if user_input is not None:
            api = EuskalmetAPI(
                session=async_get_clientsession(self.hass),
                email=user_input["email"],
                private_key=user_input["private_key"],
                login_id=user_input.get("login_id", ""),
                time_zone=self.hass.config.time_zone,
            )

            try:
                await api.get_regions()
                stations = await api.list_compatible_stations()
            except EuskalmetAuthenticationError:
                errors["base"] = "invalid_auth"
            except (EuskalmetConnectionError, EuskalmetAPIError):
                errors["base"] = "cannot_connect"
            except LocationDiscoveryError:
                errors["base"] = "cannot_load_stations"
            else:
                if not stations:
                    errors["base"] = "no_compatible_stations"
                else:
                    self._credentials = dict(user_input)
                    self._api = api
                    self._stations = stations
                    return await self.async_step_station()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("private_key"): str,
                    vol.Optional("login_id", default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_station(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Elegir una estación compatible y crear una entrada independiente."""

        if self._api is None or not self._stations:
            return await self.async_step_user()

        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input["station_id"]
            station = next(
                (
                    item
                    for item in self._stations
                    if item["station_id"] == station_id
                ),
                None,
            )

            if station is None:
                errors["base"] = "station_not_available"
            else:
                self._selected_station = station

                if station["missing_measures"]:
                    return await self.async_step_confirm()

                try:
                    return await self._async_create_selected_entry()
                except EuskalmetAuthenticationError:
                    errors["base"] = "invalid_auth"
                except (EuskalmetConnectionError, EuskalmetAPIError):
                    errors["base"] = "cannot_connect"
                except (LocationDiscoveryError, TypeError, ValueError):
                    errors["base"] = "cannot_determine_location"

        options = [
            SelectOptionDict(
                value=station["station_id"],
                label=(
                    f"{station['station_name']} — "
                    f"{station['municipality']} — "
                    f"{self._station_status(station)}"
                ),
            )
            for station in self._stations
        ]

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required("station_id"): SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
            errors=errors,
            description_placeholders={
                "station_count": str(len(options)),
            },
        )

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirmar conscientemente una estación con datos incompletos."""

        if self._selected_station is None:
            return await self.async_step_station()

        errors: dict[str, str] = {}
        station = self._selected_station

        if user_input is not None:
            try:
                return await self._async_create_selected_entry()
            except EuskalmetAuthenticationError:
                errors["base"] = "invalid_auth"
            except (EuskalmetConnectionError, EuskalmetAPIError):
                errors["base"] = "cannot_connect"
            except (LocationDiscoveryError, TypeError, ValueError):
                errors["base"] = "cannot_determine_location"

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "station": station["station_name"],
                "available": self._measure_names(
                    station["available_measures"]
                ),
                "missing": self._measure_names(
                    station["missing_measures"]
                ),
            },
        )
