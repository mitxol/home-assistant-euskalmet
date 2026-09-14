# Euskalmet 2.12.6

## Correcciones

- La tarjeta de radar antigua `weather-radar-card-euskalmet` deja de usar los basemaps raster de CARTO, que desde finales de agosto de 2026 muestran la marca `API KEY REQUIRED` si no se envía una clave.
- El estilo automático y los estilos heredados pasan a usar capas públicas de Esri Canvas como mapa base, manteniendo una estética clara y sin clave externa.
- El modo satélite mantiene la capa base de Esri, pero ya no añade la capa de etiquetas de CARTO.
- Corrige la atribución del mapa base del radar.
- Corrige el marcador por defecto de `zone.home` en el radar para que use un SVG embebido y no dependa de archivos externos que podían mostrarse como imagen rota.

## Actualización

- Actualiza el recurso JavaScript del radar a `/euskalmet_static/weather-radar-card-euskalmet.js?v=5` para forzar la recarga del navegador o de la app móvil.
