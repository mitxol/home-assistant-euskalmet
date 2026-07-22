# Euskalmet 2.9.1-beta.5

## Resúmenes diarios y cambio de fecha UTC

- Construye el día de Home Assistant combinando los dos documentos UTC que lo
  atraviesan.
- Entre las 00:00 y las 02:00 CEST consulta correctamente el documento UTC del
  día anterior y conserva sólo las franjas pertenecientes al nuevo día local.
- Combina totales, extremos y medias ponderadas sin mezclar observaciones del
  día local anterior.
- Mantiene el respaldo mediante los documentos públicos cuando el agregado de
  una de las fechas UTC todavía no existe.

Los recursos JavaScript no cambian.
