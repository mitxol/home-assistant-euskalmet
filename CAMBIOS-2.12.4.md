# Euskalmet 2.12.4

## Correcciones

- El catálogo de entidades de polen se construye usando todos los registros del
  periodo consultado, no solo la última muestra. Esto evita que Home Assistant
  deje entidades como restauradas y no disponibles después de un reinicio.
- Los taxones presentes en el periodo histórico que la API omite en la muestra
  diaria más reciente se muestran como `0,0 grains/m³`.
- Una estación sin muestra diaria válida continúa mostrando sus sensores de
  polen como no disponibles, para no confundir la ausencia de datos con un
  recuento real de cero.

## Publicación

- Versión preparada para solicitar la inclusión del repositorio en el catálogo
  predeterminado de HACS.
