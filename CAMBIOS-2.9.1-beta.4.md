# Euskalmet 2.9.1-beta.4

## Resúmenes diarios durante las primeras horas

- Si Euskalmet todavía no ha creado `aggregated/byDay`, utiliza como segundo
  respaldo el documento público de lecturas del día.
- Calcula mínimo, media, máximo y total usando la posición con más observaciones
  para evitar mezclar sensores colocados a distintas alturas.
- Cambia automáticamente al documento agregado cuando empieza a estar
  disponible.
- Los resúmenes mensuales y anuales no cambian.

Los recursos JavaScript no cambian.
