from datetime import timedelta
DOMAIN = "euskalmet"

MANUFACTURER = "Euskalmet"
MODEL = "Estación Meteorológica"

API_BASE = "https://api.euskadi.eus/euskalmet"

STATIONS_GEOJSON_URL = (
    "https://www.euskalmet.euskadi.eus/contenidos/"
    "ds_meteorologicos/estaciones_meteorologicas/opendata/"
    "estaciones.geojson"
)

PUBLIC_READINGS_URL = (
    "https://www.euskalmet.euskadi.eus/vamet/stations/readings"
)

DEFAULT_STATION = "C016"

UPDATE_INTERVAL = timedelta(minutes=5)

# Georreferenciacion publicada por Euskalmet para las capas de intensidad
# y precipitacion acumulada del radar de Kapildui. Leaflet espera el orden
# [[sur, oeste], [norte, este]].
RADAR_BOUNDS = (
    (41.864983, -3.747800),
    (43.655708, -1.28939260),
)
RADAR_CENTER = (42.7671, -2.5363)
RADAR_RANGE_KM = 100


MEASURES = {

    "temperature": {
        "name": "Temperatura",
        "sensor": "R0EV",
        "measure_type": "measuresForAir",
        "measure": "temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
    },

    "humidity": {
        "name": "Humedad",
        "sensor": "R0EV",
        "measure_type": "measuresForAir",
        "measure": "humidity",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
    },

    "pressure": {
        "name": "Presión",
        "sensor": "S008",
        "measure_type": "measuresForAtmosphere",
        "measure": "pressure",
        "unit": "hPa",
        "device_class": "pressure",
        "state_class": "measurement",
        "icon": "mdi:gauge",
    },

    "wind_speed": {
        "name": "Velocidad del viento",
        "sensor": "Y0AT",
        "measure_type": "measuresForWind",
        "measure": "mean_speed",
        "unit": "km/h",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "icon": "mdi:weather-windy",
    },

    "wind_gust": {
        "name": "Racha máxima",
        "sensor": "Y0AT",
        "measure_type": "measuresForWind",
        "measure": "max_speed",
        "unit": "km/h",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "icon": "mdi:weather-windy",
    },

    "wind_direction": {
        "name": "Dirección del viento",
        "sensor": "Y0AT",
        "measure_type": "measuresForWind",
        "measure": "mean_direction",
        "unit": None,
        "icon": "mdi:compass",
    },

    "irradiance": {
        "name": "Radiación solar",
        "sensor": "K0AM",
        "measure_type": "measuresForSun",
        "measure": "irradiance",
        "unit": "W/m²",
        "state_class": "measurement",
        "icon": "mdi:white-balance-sunny",
    },

    "precipitation": {
        "name": "Precipitación",
        "sensor": "G471",
        "measure_type": "measuresForWater",
        "measure": "precipitation",
        "unit": "mm",
        "state_class": "measurement",
        "icon": "mdi:weather-rainy",
    },

}
