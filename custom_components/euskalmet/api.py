from __future__ import annotations

import asyncio
import base64
import logging
import time
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
import jwt

from .const import (
    API_BASE,
    DEFAULT_STATION,
    MEASURES,
    PUBLIC_READINGS_URL,
    STATIONS_GEOJSON_URL,
)
from .geography import (
    LocationDiscoveryError,
    active_meteorological_stations,
    alert_zone_for,
    catalog_identifier,
    catalog_names,
    name_match_score,
    nearest_station,
    station_by_id,
)
from .readings import (
    available_aggregated_measure_keys,
    available_measure_keys,
    parse_aggregated_readings,
    parse_public_readings,
)

_LOGGER = logging.getLogger(__name__)

MAX_MEASUREMENT_AGE = timedelta(minutes=45)
FUTURE_TOLERANCE = timedelta(minutes=5)
REQUEST_TIMEOUT = 30
MAX_CONCURRENT_REQUESTS = 4
TOKEN_LIFETIME = 3600
TOKEN_REFRESH_MARGIN = 60


class EuskalmetAPIError(Exception):
    """Error de comunicación o respuesta de la API de Euskalmet."""


class EuskalmetAuthenticationError(EuskalmetAPIError):
    """La API rechazó las credenciales configuradas."""


class EuskalmetConnectionError(EuskalmetAPIError):
    """No se pudo establecer o completar la conexión con la API."""


def _slot_start(
    slot: object,
    request_hour: datetime,
) -> datetime | None:
    """Obtener el inicio UTC de un slot real de lecturas de Euskalmet."""

    if not isinstance(slot, dict):
        return None

    range_value = slot.get("range")
    if not isinstance(range_value, str):
        return None

    try:
        start = range_value.split("[", 1)[1].split("..", 1)[0]
        parts = start.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2])
        microsecond = int(parts[3].ljust(6, "0")) if len(parts) > 3 else 0

        # Aunque la API denomina este campo ``LocalTime``, las lecturas
        # de estaciones y la hora del endpoint avanzan en UTC.
        observed_datetime = request_hour.astimezone(UTC).replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
        )
        return observed_datetime

    except (IndexError, TypeError, ValueError):
        return None


def _add_freshness(
    result: dict[str, Any],
    observed_at: datetime | None,
    now: datetime,
    *,
    from_cache: bool,
) -> dict[str, Any]:
    """Añadir timestamp y edad sin alterar el valor de la lectura."""

    if observed_at is None:
        return {
            **result,
            "observed_at": None,
            "age_seconds": None,
            "stale": True,
            "from_cache": from_cache,
        }

    observed_utc = observed_at.astimezone(UTC)
    now_utc = now.astimezone(UTC)
    age = now_utc - observed_utc

    return {
        **result,
        "observed_at": observed_utc.isoformat(),
        "age_seconds": max(0, int(age.total_seconds())),
        "stale": (age > MAX_MEASUREMENT_AGE or age < -FUTURE_TOLERANCE),
        "from_cache": from_cache,
    }


class EuskalmetAPI:
    """Cliente para la API de Euskalmet."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        private_key: str,
        region: str = "01",
        zone: str = "01",
        location: str = "VITORIA-GASTEIZ",
        station_id: str = DEFAULT_STATION,
        station_name: str = "Arkauti",
        alert_zone: str = "TRANSITION",
        time_zone: str = "Europe/Madrid",
    ) -> None:
        self.session = session

        self.email = email
        self.private_key = private_key

        self.region = region
        self.zone = zone
        self.location = location

        self.alert_zone = alert_zone

        try:
            self.time_zone = ZoneInfo(time_zone)
        except ZoneInfoNotFoundError:
            self.time_zone = UTC

        self.station_id = station_id
        self.station_name = station_name
        self.supported_measurements: set[str] | None = None

        self._last_values: dict[str, dict[str, Any]] = {}
        self._request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._token_lock = asyncio.Lock()
        self._token: str | None = None
        self._token_expires_at = 0

    def _jwt(self) -> tuple[str, int]:
        """Generar el token JWT para la API."""

        now = int(time.time())
        expires_at = now + TOKEN_LIFETIME

        payload = {
            "aud": "met01.apikey",
            "iss": "homeassistant",
            "iat": now,
            "exp": expires_at,
            "version": "1.0.0",
        }

        payload["email"] = self.email

        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
        )

        return token, expires_at

    async def _async_jwt(self) -> str:
        """Obtener un JWT válido sin ejecutar RS256 en el event loop."""

        now = int(time.time())

        if (
            self._token is not None
            and now < self._token_expires_at - TOKEN_REFRESH_MARGIN
        ):
            return self._token

        async with self._token_lock:
            now = int(time.time())

            if (
                self._token is not None
                and now < self._token_expires_at - TOKEN_REFRESH_MARGIN
            ):
                return self._token

            try:
                token, expires_at = await asyncio.to_thread(self._jwt)
            except Exception as err:
                raise EuskalmetAuthenticationError(
                    "No se pudo generar el JWT RS256"
                ) from err
            self._token = token
            self._token_expires_at = expires_at

            return token

    def _invalidate_token(self) -> None:
        """Invalidar el JWT almacenado después de un rechazo de la API."""

        self._token = None
        self._token_expires_at = 0

    @staticmethod
    def _utcnow() -> datetime:
        """Devolver la hora UTC actual; aislado para pruebas."""

        return datetime.now(UTC)

    async def _request(self, url: str) -> Any:
        """Realizar una petición autenticada."""

        token = await self._async_jwt()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            async with self._request_semaphore:
                async with asyncio.timeout(REQUEST_TIMEOUT):
                    async with self.session.get(
                        url,
                        headers=headers,
                    ) as response:
                        if response.status in {401, 403}:
                            self._invalidate_token()
                            raise EuskalmetAuthenticationError(
                                f"Autenticación rechazada ({response.status})"
                            )

                        if response.status != 200:
                            body = (await response.text())[:500]
                            raise EuskalmetAPIError(f"HTTP {response.status}: {body}")

                        return await response.json(
                            content_type=None,
                        )

        except TimeoutError as err:
            raise EuskalmetConnectionError(
                f"Tiempo de espera agotado al consultar {url}"
            ) from err
        except aiohttp.ClientError as err:
            raise EuskalmetConnectionError(
                f"Error de conexión con Euskalmet: {err}"
            ) from err

    async def _request_public(self, url: str) -> Any:
        """Consultar un recurso público oficial sin autenticación."""

        try:
            async with self._request_semaphore:
                async with asyncio.timeout(REQUEST_TIMEOUT):
                    async with self.session.get(
                        url,
                        headers={"Accept": "application/geo+json, application/json"},
                    ) as response:
                        if response.status != 200:
                            raise EuskalmetAPIError(
                                f"HTTP {response.status} al consultar {url}"
                            )
                        return await response.json(content_type=None)
        except TimeoutError as err:
            raise EuskalmetConnectionError(
                f"Tiempo de espera agotado al consultar {url}"
            ) from err
        except aiohttp.ClientError as err:
            raise EuskalmetConnectionError(
                f"Error de conexión al consultar {url}: {err}"
            ) from err

    async def get_public_measurements(
        self,
    ) -> dict[str, dict[str, Any] | None]:
        """Obtener todas las lecturas actuales de la estación detectada."""

        now = datetime.now(self.time_zone)
        errors: list[EuskalmetAPIError] = []

        for days_back in range(2):
            document_date = now - timedelta(days=days_back)

            try:
                document = await self._public_readings_document(
                    self.station_id,
                    document_date,
                )
            except EuskalmetAPIError as err:
                errors.append(err)
                continue

            document_measures = available_measure_keys(document, MEASURES)
            if self.supported_measurements is None:
                self.supported_measurements = set()
            self.supported_measurements.update(document_measures)

            parsed = parse_public_readings(
                document,
                MEASURES,
                document_date,
            )
            if not parsed:
                continue

            results: dict[str, dict[str, Any] | None] = {}

            for key in MEASURES:
                reading = parsed.get(key)
                if reading is None:
                    results[key] = None
                    continue

                observed_at = reading["observed_at"]
                result = _add_freshness(
                    {
                        "value": reading["value"],
                        "slot": {
                            "time": observed_at.strftime("%H:%M"),
                            "sensor_position_cm": reading["sensor_position_cm"],
                        },
                        "measure_id": reading["measure_id"],
                        "sensor_position_cm": reading["sensor_position_cm"],
                        "source": "euskalmet_public_station_readings",
                    },
                    observed_at,
                    now,
                    from_cache=False,
                )
                self._last_values[key] = result
                results[key] = result

            return results

        if errors:
            raise errors[-1]

        raise EuskalmetAPIError(
            f"No hay lecturas públicas para la estación {self.station_id}"
        )

    async def get_aggregated_measurements(
        self,
    ) -> dict[str, dict[str, Any] | None]:
        """Obtener todas las lecturas mediante la API diaria agregada."""

        now = datetime.now(self.time_zone)
        errors: list[EuskalmetAPIError] = []
        latest_readings: dict[str, dict[str, Any]] = {}

        for days_back in range(2):
            document_date = now - timedelta(days=days_back)
            try:
                document = await self.get_aggregated_day(document_date)
            except EuskalmetAPIError as err:
                errors.append(err)
                continue

            available = available_aggregated_measure_keys(document, MEASURES)
            if self.supported_measurements is None:
                self.supported_measurements = set()
            self.supported_measurements.update(available)

            parsed = parse_aggregated_readings(document, MEASURES, now)
            for key, reading in parsed.items():
                previous = latest_readings.get(key)
                if previous is None or reading["observed_at"] > previous["observed_at"]:
                    latest_readings[key] = reading

            # En condiciones normales hoy contiene ya todas las magnitudes.
            # Ayer solo es necesario durante el cambio de día, antes de que
            # termine la primera franja, o si el recurso de hoy falla.
            if latest_readings:
                break

        if not latest_readings:
            if errors:
                raise errors[-1]
            raise EuskalmetAPIError(
                "La respuesta agregada no contiene lecturas terminadas para "
                f"la estación {self.station_id}"
            )

        results: dict[str, dict[str, Any] | None] = {}
        for key in MEASURES:
            reading = latest_readings.get(key)
            if reading is None:
                results[key] = None
                continue

            observed_at = reading["observed_at"]
            result = _add_freshness(
                {
                    "value": reading["value"],
                    "slot": {
                        "time": observed_at.strftime("%H:%M"),
                        "sensor_position_cm": reading["sensor_position_cm"],
                    },
                    "measure_id": reading["measure_id"],
                    "sensor_position_cm": reading["sensor_position_cm"],
                    "source": "euskalmet_api_aggregated_by_day",
                },
                observed_at,
                now,
                from_cache=False,
            )
            self._last_values[key] = result
            results[key] = result

        return results

    async def _public_readings_document(
        self,
        station_id: str,
        document_date: datetime,
    ) -> Any:
        """Descargar el documento diario de lecturas de una estación."""

        url = (
            f"{PUBLIC_READINGS_URL}/{quote(station_id, safe='')}/"
            f"{document_date:%Y/%m/%d}/"
            "webmet00-readingsData.json"
        )
        return await self._request_public(url)

    async def _station_catalog_features(self) -> list[object]:
        """Descargar y validar las features del catálogo oficial."""

        station_catalog = await self._request_public(STATIONS_GEOJSON_URL)
        if not isinstance(station_catalog, dict):
            raise LocationDiscoveryError(
                "El catálogo de estaciones no es un GeoJSON válido"
            )

        features = station_catalog.get("features")
        if not isinstance(features, list):
            raise LocationDiscoveryError(
                "El catálogo de estaciones no contiene features"
            )
        return features

    async def get_station_capabilities(self) -> set[str]:
        """Detectar las magnitudes publicadas hoy o el día anterior."""

        now = datetime.now(self.time_zone)
        available: set[str] = set()
        errors: list[EuskalmetAPIError] = []

        for days_back in range(2):
            try:
                document = await self._public_readings_document(
                    self.station_id,
                    now - timedelta(days=days_back),
                )
            except EuskalmetAPIError as err:
                errors.append(err)
                continue
            available.update(available_measure_keys(document, MEASURES))

        if available:
            self.supported_measurements = available
            return available
        if errors:
            raise errors[-1]
        return set()

    async def list_compatible_stations(self) -> list[dict[str, Any]]:
        """Listar estaciones meteorológicas con magnitudes básicas reales."""

        stations = active_meteorological_stations(
            await self._station_catalog_features()
        )
        now = datetime.now(self.time_zone)

        async def with_capabilities(
            station: dict[str, Any],
        ) -> dict[str, Any] | None:
            available: set[str] = set()
            for days_back in range(2):
                try:
                    document = await self._public_readings_document(
                        station["station_id"],
                        now - timedelta(days=days_back),
                    )
                except EuskalmetAPIError:
                    continue
                available.update(available_measure_keys(document, MEASURES))

            if not available:
                return None

            available_ordered = [key for key in MEASURES if key in available]
            missing_ordered = [key for key in MEASURES if key not in available]
            return {
                **station,
                "available_measures": available_ordered,
                "missing_measures": missing_ordered,
            }

        stations_with_capabilities = await asyncio.gather(
            *(with_capabilities(station) for station in stations)
        )
        return [
            station for station in stations_with_capabilities if station is not None
        ]

    @staticmethod
    def _catalog_items(data: Any, collection: str) -> list[dict[str, Any]]:
        """Normalizar las variantes de respuesta de los catálogos."""

        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        if not isinstance(data, dict):
            return []

        for key in (collection, "items", "set"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        return []

    async def get_regions(self) -> list[dict[str, Any]]:
        """Obtener las regiones disponibles para previsión."""

        return self._catalog_items(
            await self._request(f"{API_BASE}/geo/regions"),
            "regions",
        )

    async def get_zones(self, region: str) -> list[dict[str, Any]]:
        """Obtener las zonas de una región."""

        region_path = quote(region, safe="")
        return self._catalog_items(
            await self._request(f"{API_BASE}/geo/regions/{region_path}/zones"),
            "zones",
        )

    async def get_locations(
        self,
        region: str,
        zone: str,
    ) -> list[dict[str, Any]]:
        """Obtener las localidades de una zona de previsión."""

        region_path = quote(region, safe="")
        zone_path = quote(zone, safe="")
        return self._catalog_items(
            await self._request(
                f"{API_BASE}/geo/regions/{region_path}/zones/{zone_path}/locations"
            ),
            "locations",
        )

    async def discover_configuration(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """Autodetectar catálogos, estación y zona de avisos."""

        features = await self._station_catalog_features()
        station = nearest_station(
            active_meteorological_stations(features),
            latitude,
            longitude,
        )
        return await self._discover_configuration_for_station(station)

    async def discover_configuration_for_station(
        self,
        station_id: str,
    ) -> dict[str, Any]:
        """Resolver previsión y avisos para una estación elegida."""

        stations = active_meteorological_stations(
            await self._station_catalog_features()
        )
        station = station_by_id(stations, station_id)
        return await self._discover_configuration_for_station(station)

    async def _discover_configuration_for_station(
        self,
        station: dict[str, Any],
    ) -> dict[str, Any]:
        """Asociar una estación normalizada con los catálogos de previsión."""

        municipality = station["municipality"]
        best: tuple[float, str, str, str] | None = None

        for region_item in await self.get_regions():
            region_id = catalog_identifier(region_item, "region")
            if not region_id:
                continue

            for zone_item in await self.get_zones(region_id):
                zone_id = catalog_identifier(zone_item, "zone")
                if not zone_id:
                    continue

                for location_item in await self.get_locations(
                    region_id,
                    zone_id,
                ):
                    location_id = catalog_identifier(
                        location_item,
                        "location",
                    )
                    if not location_id:
                        continue

                    score = name_match_score(
                        municipality,
                        catalog_names(location_item, location_id),
                    )
                    candidate = (score, region_id, zone_id, location_id)
                    if best is None or candidate[0] > best[0]:
                        best = candidate

        if best is None or best[0] < 0.45:
            raise LocationDiscoveryError(
                f"No se encontró la localidad {municipality} en Euskalmet"
            )

        _, region_id, zone_id, location_id = best
        alert_zone = alert_zone_for(
            station["province"],
            municipality,
            station["station_latitude"],
        )

        return {
            **station,
            "region": region_id,
            "zone": zone_id,
            "location": location_id,
            "alert_zone": alert_zone,
        }

    async def get_measure(self, key: str) -> dict[str, Any] | None:
        """Obtener la última lectura válida de una medida."""

        cfg = MEASURES[key]
        now = self._utcnow()
        for hours_back in range(3):
            date = now - timedelta(hours=hours_back)

            url = (
                f"{API_BASE}/readings/"
                f"forStation/{self.station_id}/"
                f"{cfg['sensor']}/"
                f"measures/{cfg['measure_type']}/"
                f"{cfg['measure']}/"
                f"at/{date:%Y/%m/%d/%H}"
            )

            try:
                data = await self._request(url)

            except EuskalmetAuthenticationError:
                raise
            except EuskalmetConnectionError as err:
                _LOGGER.debug(
                    "Error de conexión obteniendo %s: %s",
                    key,
                    err,
                )
                break
            except EuskalmetAPIError as err:
                _LOGGER.debug(
                    "Error obteniendo %s (%s hora(s) atrás): %s",
                    key,
                    hours_back,
                    err,
                )
                continue

            if not isinstance(data, dict):
                _LOGGER.debug(
                    "Respuesta de lectura no válida para %s",
                    key,
                )
                continue

            values = data.get("values") or []
            slots = data.get("slots") or []

            if not isinstance(values, list) or not isinstance(slots, list):
                _LOGGER.debug(
                    "Valores o slots no válidos para %s",
                    key,
                )
                continue

            candidates = []

            for index, value in enumerate(values):
                if value is None or index >= len(slots):
                    continue

                slot = slots[index]
                observed_at = _slot_start(slot, date)

                if observed_at is not None:
                    candidates.append((observed_at, value, slot))

            if candidates:
                observed_at, value, slot = max(
                    candidates,
                    key=lambda candidate: candidate[0],
                )
                result = _add_freshness(
                    {
                        "value": value,
                        "slot": slot,
                    },
                    observed_at,
                    now,
                    from_cache=False,
                )

                self._last_values[key] = result
                return result

        cached = self._last_values.get(key)

        if cached is None:
            return None

        observed_at = None
        raw_observed_at = cached.get("observed_at")

        if isinstance(raw_observed_at, str):
            with suppress(ValueError):
                observed_at = datetime.fromisoformat(raw_observed_at)

        return _add_freshness(
            cached,
            observed_at,
            now,
            from_cache=True,
        )

    async def get_all_measurements(
        self,
    ) -> dict[str, dict[str, Any] | None]:
        """Obtener todas las medidas actuales."""

        try:
            return await self.get_aggregated_measurements()
        except EuskalmetAuthenticationError:
            raise
        except EuskalmetAPIError as err:
            _LOGGER.warning(
                "No se pudieron obtener las lecturas agregadas de %s; "
                "se usará el documento público como respaldo: %s",
                self.station_id,
                err,
            )

        try:
            return await self.get_public_measurements()
        except EuskalmetAPIError as err:
            _LOGGER.warning(
                "No se pudieron obtener las lecturas públicas de %s; "
                "se usará la API autenticada como respaldo: %s",
                self.station_id,
                err,
            )

        keys = tuple(MEASURES)
        values = await asyncio.gather(*(self.get_measure(key) for key in keys))

        return dict(zip(keys, values, strict=True))

    async def get_station(self) -> dict[str, Any]:
        """Obtener información de la estación."""

        url = f"{API_BASE}/stations/{self.station_id}/current"

        data = await self._request(url)

        if not isinstance(data, dict):
            raise EuskalmetAPIError("La respuesta de la estación no es un objeto JSON")

        return data

    async def get_aggregated_day(self, date: datetime) -> Any:
        """Obtener todas las lecturas diarias agregadas de la estación."""

        url = (
            f"{API_BASE}/readings/aggregated/byDay/"
            f"forStation/{self.station_id}/at/{date:%Y/%m/%d}"
        )
        return await self._request(url)

    async def get_aggregated_day_summary(self, date: datetime | None = None) -> Any:
        """Obtener el resumen agregado de un día."""

        date = date or datetime.now(self.time_zone)
        return await self._request(
            f"{API_BASE}/readings/aggregated/summarized/byDay/"
            f"forStation/{self.station_id}/at/{date:%Y/%m/%d}"
        )

    async def get_aggregated_month_summary(self, date: datetime | None = None) -> Any:
        """Obtener el resumen agregado de un mes."""

        date = date or datetime.now(self.time_zone)
        return await self._request(
            f"{API_BASE}/readings/aggregated/summarized/byMonth/"
            f"forStation/{self.station_id}/at/{date:%Y/%m}"
        )

    async def get_daily_forecast(self) -> list[dict[str, Any]]:
        """Obtener la previsión diaria."""

        today = datetime.now().astimezone()
        region = quote(self.region, safe="")
        zone = quote(self.zone, safe="")
        location = quote(self.location, safe="")

        url = (
            f"{API_BASE}/weather/"
            f"regions/{region}/"
            f"zones/{zone}/"
            f"locations/{location}/"
            f"forecast/trends/"
            f"at/{today:%Y/%m/%d}/"
            f"for/{today:%Y%m%d}"
        )

        data = await self._request(url)

        if not isinstance(data, dict):
            raise EuskalmetAPIError("La previsión diaria no es un objeto JSON")

        trends = data.get("trendsByDate") or {}

        if not isinstance(trends, dict):
            raise EuskalmetAPIError(
                "La previsión diaria no contiene trendsByDate válidos"
            )

        forecast = trends.get("set") or []

        if not isinstance(forecast, list):
            raise EuskalmetAPIError(
                "La previsión diaria no contiene una lista set válida"
            )

        return forecast

    async def get_hourly_forecast(self) -> dict[str, Any]:
        """Obtener la previsión horaria completa."""

        today = datetime.now().astimezone()
        region = quote(self.region, safe="")
        zone = quote(self.zone, safe="")
        location = quote(self.location, safe="")

        url = (
            f"{API_BASE}/weather/"
            f"regions/{region}/"
            f"zones/{zone}/"
            f"locations/{location}/"
            f"forecast/trends/measures/"
            f"at/{today:%Y/%m/%d}/"
            f"for/{today:%Y%m%d}"
        )

        # Se devuelve el JSON completo para conservar:
        # - "for": fecha de validez
        # - "at": fecha de emisión
        # - "trends.set": bloques horarios
        data = await self._request(url)

        if not isinstance(data, dict):
            raise EuskalmetAPIError("La previsión horaria no es un objeto JSON")

        return data

    @staticmethod
    def _empty_alerts() -> dict[str, Any]:
        """Devolver una estructura vacía de avisos."""

        return {
            "active": False,
            "severity": "NONE",
            "count": 0,
            "causes": [],
            "descriptions": [],
            "alerts": [],
        }

    def _alert_url_from_key(self, key: object) -> str:
        """Convertir la clave del aviso en una URL completa."""

        key = str(key).strip().lstrip("/")

        if key.startswith("euskalmet/"):
            api_root = API_BASE.rstrip("/")

            if api_root.endswith("/euskalmet"):
                api_root = api_root[: -len("/euskalmet")]

            return f"{api_root}/{key}"

        return f"{API_BASE.rstrip('/')}/{key}"

    @staticmethod
    def _alert_description(item: dict[str, Any]) -> str:
        """Obtener la descripción del aviso."""

        descriptions = item.get("descriptionByLang") or {}

        if not isinstance(descriptions, dict):
            return ""

        description = (
            descriptions.get("SPANISH")
            or descriptions.get("BASQUE")
            or next(iter(descriptions.values()), "")
        )

        return str(description).strip()

    async def get_alerts(self) -> dict[str, Any]:
        """Obtener avisos meteorológicos."""

        today = datetime.now().astimezone()

        index_url = (
            f"{API_BASE}/alerts/zones/{self.alert_zone}/forecast/at/{today:%Y/%m/%d}"
        )

        index = await self._request(index_url)

        if not isinstance(index, list):
            return self._empty_alerts()

        severity_order = {
            "NONE": 0,
            "YELLOW": 1,
            "ORANGE": 2,
            "RED": 3,
        }

        highest = "NONE"

        alerts = []
        causes = []
        descriptions = []

        keys = [
            entry.get("key")
            for entry in index
            if isinstance(entry, dict) and entry.get("key")
        ]
        responses = await asyncio.gather(
            *(self._request(self._alert_url_from_key(key)) for key in keys),
            return_exceptions=True,
        )

        if keys and all(isinstance(response, Exception) for response in responses):
            raise EuskalmetAPIError("No se pudo descargar ningún aviso meteorológico")

        for key, alert in zip(keys, responses, strict=True):
            if isinstance(alert, asyncio.CancelledError):
                raise alert

            if isinstance(alert, Exception):
                _LOGGER.debug(
                    "Error descargando aviso %s: %s",
                    key,
                    alert,
                )
                continue

            if not isinstance(alert, dict):
                continue

            severity = str(alert.get("severity", "NONE")).upper()

            if severity_order.get(
                severity,
                0,
            ) > severity_order.get(
                highest,
                0,
            ):
                highest = severity

            items = alert.get("items") or []

            for item in items:
                if not isinstance(item, dict):
                    continue

                cause = item.get("cause")
                description = self._alert_description(item)

                alerts.append(
                    {
                        "severity": severity,
                        "cause": cause,
                        "description": description,
                        "zone": alert.get("zoneId"),
                        "issued": alert.get("at"),
                        "valid_for": alert.get("for"),
                        "key": key,
                    }
                )

                if cause and cause not in causes:
                    causes.append(cause)

                if description and description not in descriptions:
                    descriptions.append(description)

        return {
            "active": highest
            in {
                "YELLOW",
                "ORANGE",
                "RED",
            },
            "severity": highest,
            "count": len(alerts),
            "causes": causes,
            "descriptions": descriptions,
            "alerts": alerts,
        }

    @staticmethod
    def _empty_radar() -> dict[str, Any]:
        """Devolver una estructura vacía de radar."""

        return {
            "available": False,
            "image": None,
            "content_type": "image/png",
            "range": None,
            "timestamp": None,
            "date": None,
            "report_type": None,
            "report": None,
            "frame_count": 0,
            "frames": [],
        }

    @staticmethod
    def _radar_range_start(range_value: object) -> int:
        """Obtener la hora inicial de una captura del radar.

        Ejemplo:
        LocalTime:[12:10:00:000..12:20:00:000)
        """

        if not range_value:
            return -1

        try:
            start = str(range_value).split("[", 1)[1].split("..", 1)[0]

            parts = start.split(":")

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])

            return hours * 3600 + minutes * 60 + seconds

        except (
            IndexError,
            TypeError,
            ValueError,
        ):
            return -1

    @classmethod
    def _radar_timestamp(
        cls,
        range_value: object,
        report_date: datetime,
    ) -> str | None:
        """Convertir el inicio UTC de un fotograma a ISO 8601."""

        seconds = cls._radar_range_start(range_value)

        if seconds < 0:
            return None

        midnight_utc = datetime(
            report_date.year,
            report_date.month,
            report_date.day,
            tzinfo=UTC,
        )

        return (midnight_utc + timedelta(seconds=seconds)).isoformat()

    async def get_radar_report(self) -> dict[str, Any]:
        """Obtener la captura más reciente del radar de precipitación."""

        now = datetime.now().astimezone()
        request_errors: list[EuskalmetAPIError] = []

        # En algunos momentos el informe del día actual puede no estar
        # disponible todavía. Por eso se prueba también el día anterior.
        for days_back in range(2):
            report_date = now - timedelta(days=days_back)

            url = (
                f"{API_BASE}/radar/reports/"
                f"precipitationReport/"
                f"intensity/"
                f"for/{report_date:%Y/%m/%d}"
            )

            try:
                data = await self._request(url)

            except EuskalmetAPIError as err:
                request_errors.append(err)
                _LOGGER.debug(
                    "No se pudo obtener el radar para %s: %s",
                    report_date.date(),
                    err,
                )
                continue

            if not isinstance(data, dict):
                continue

            collection = (
                data.get(
                    "activityAreaReportMapCollection",
                    {},
                )
                or {}
            )

            frames = collection.get("set") or []

            valid_frames = [
                frame
                for frame in frames
                if (isinstance(frame, dict) and frame.get("activityMapContent"))
            ]

            if not valid_frames:
                continue

            # La API no garantiza que las capturas estén ordenadas.
            ordered_frames = sorted(
                valid_frames,
                key=lambda frame: self._radar_range_start(frame.get("range")),
            )
            latest_frame = ordered_frames[-1]

            radar_frames = [
                {
                    "range": frame.get("range"),
                    "timestamp": self._radar_timestamp(
                        frame.get("range"),
                        report_date,
                    ),
                    "content": frame.get("activityMapContent"),
                }
                for frame in ordered_frames
            ]

            encoded_image = latest_frame.get("activityMapContent")

            try:
                image = await asyncio.to_thread(
                    base64.b64decode,
                    encoded_image,
                    validate=False,
                )

            except (
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning(
                    "No se pudo decodificar la imagen del radar: %s",
                    err,
                )
                continue

            if not image:
                continue

            return {
                "available": True,
                "image": image,
                "content_type": "image/png",
                "range": latest_frame.get("range"),
                "timestamp": self._radar_timestamp(
                    latest_frame.get("range"),
                    report_date,
                ),
                "date": data.get("date"),
                "report_type": data.get("reportType"),
                "report": data.get("report"),
                "frame_count": len(radar_frames),
                "frames": radar_frames,
            }

        if len(request_errors) == 2:
            raise request_errors[-1]

        return self._empty_radar()

    async def close(self) -> None:
        """La sesión HTTP la gestiona Home Assistant."""

        return
