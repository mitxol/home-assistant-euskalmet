# Tarjetas de Euskalmet

La integración publica sus tarjetas desde `/euskalmet_static/`. Después de
actualizar, cambia el parámetro de versión del recurso y fuerza una recarga del
navegador para descartar archivos antiguos de la caché.

## Radar animado recomendado

Recurso:

```text
/euskalmet_static/weather-radar-card-euskalmet.js?v=2.9.0-beta.14
```

Tarjeta:

```yaml
type: custom:weather-radar-card-euskalmet
data_source: Euskalmet
map_style: OSM
radar_opacity: 1
past_minutes: 120
show_color_bar: false
autoplay: true
```

La cámara conserva la última captura como vista previa. La tarjeta añade el
mapa OpenStreetMap, la línea temporal y la animación sin perder el anclaje
geográfico de la capa de precipitación.

## Histórico

Recurso:

```text
/euskalmet_static/euskalmet-history-card.js?v=2.9.0-beta.14
```

Tarjeta:

```yaml
type: custom:euskalmet-history-card
entity: sensor.arkauti_temperatura
```

Los datos se consultan bajo demanda y no se importan al Recorder.

## Avisos meteorológicos

Los avisos pueden mostrarse mediante una tarjeta de entidad o template usando
`sensor.nivel_de_aviso` o `binary_sensor.aviso_meteorologico`, sin necesidad de
añadir un recurso JavaScript.
