# Tarjetas de Euskalmet

La integración publica y carga automáticamente sus tarjetas desde
`/euskalmet_static/`. Después de actualizar, reinicia Home Assistant y fuerza
una recarga completa del navegador para descartar recursos antiguos de la caché.

Si las tarjetas no aparecen automáticamente, añade estos recursos desde
**Ajustes > Paneles de control > menú de tres puntos > Recursos**, usando el tipo
**Módulo JavaScript**:

```text
/euskalmet_static/euskalmet-alert-card.js?v=2.9.0-beta.3
/euskalmet_static/euskalmet-history-card.js?v=2.9.0-beta.3
/euskalmet_static/euskalmet-radar-map-card.js?v=2.9.0-beta.3
```

## Radar animado

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
personalizada añade el mapa OpenStreetMap desaturado, la paleta de radar, la
línea temporal y la animación de todos los fotogramas del informe diario.

## Avisos meteorológicos

```yaml
type: custom:euskalmet-alert-card
entity: sensor.nivel_de_aviso
```

También se puede usar `binary_sensor.aviso_meteorologico`.

## Histórico meteorológico

```yaml
type: custom:euskalmet-history-card
entity: sensor.temperatura
```

El histórico se consulta bajo demanda para el periodo elegido y no se importa al
Recorder de Home Assistant.
