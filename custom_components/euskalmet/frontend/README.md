# Tarjetas de Euskalmet

La integración publica sus tarjetas desde `/euskalmet_static/`. Los parámetros
de versión corresponden a la revisión de cada JavaScript y solo cambian cuando
se modifica esa tarjeta.

## Radar animado recomendado

Recurso:

```text
/euskalmet_static/weather-radar-card-euskalmet.js?v=3
```

Tarjeta:

```yaml
type: custom:weather-radar-card-euskalmet
data_source: Euskalmet
map_style: Light
radar_opacity: 1
past_minutes: 360
show_color_bar: false
zoom_level: 7
```

La cámara conserva la última captura como vista previa. La tarjeta añade el
mapa OpenStreetMap, la línea temporal y la animación sin perder el anclaje
geográfico de la capa de precipitación. Si hay varias estaciones, selecciona
automáticamente una entrada porque los fotogramas son comunes a todas ellas.

## Histórico

Recurso:

```text
/euskalmet_static/euskalmet-history-card.js?v=2
```

Tarjeta:

```yaml
type: custom:euskalmet-history-card
entity: sensor.arkauti_temperatura
measure: temperature
```

Los datos se consultan bajo demanda y no se importan al Recorder. La tarjeta
deduce la estación desde la entidad, también cuando hay varias entradas.

## Avisos meteorológicos

Los avisos pueden mostrarse mediante una tarjeta de entidad o template usando
`sensor.nivel_de_aviso` o `binary_sensor.aviso_meteorologico`, sin necesidad de
añadir un recurso JavaScript.

