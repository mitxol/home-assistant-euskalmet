# Tarjetas de Euskalmet

La integración publica y carga automáticamente sus tarjetas desde
`/euskalmet_static/`. Después de actualizar, reinicia Home Assistant y fuerza
una recarga del navegador para descartar recursos antiguos de la caché.

## Radar animado

Añade una tarjeta manual:

```yaml
type: custom:euskalmet-radar-map-card
entity: camera.radar_de_precipitacion
title: Radar Euskalmet
opacity: 1
frame_interval: 125
autoplay: true
show_header: true
show_controls: true
show_options: true
```

La cámara normal conserva la última captura como vista previa. La tarjeta
personalizada añade el mapa OpenStreetMap desaturado, la paleta oficial, la
línea temporal y la animación de todos los fotogramas del informe diario.

## Avisos meteorológicos

Añade una tarjeta manual con uno de los sensores de avisos:

```yaml
type: custom:euskalmet-alert-card
entity: sensor.nivel_de_aviso
```

También se puede usar `binary_sensor.aviso_meteorologico`. La tarjeta adapta el
color al nivel máximo y muestra debajo la descripción de cada riesgo activo.
