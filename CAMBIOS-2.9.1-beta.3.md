# Euskalmet 2.9.1-beta.3

## Corrección de los resúmenes diarios

- Calcula los valores provisionales del día actual a partir de las franjas ya
  publicadas por `aggregated/byDay`.
- No depende de que Euskalmet publique el resumen diario definitivo, que puede
  no existir mientras el día sigue abierto.
- Sólo utiliza franjas cerradas y publicadas; mantiene mínimo, media, máximo,
  total y número de observaciones.
- Los resúmenes mensuales y anuales no cambian.

También conserva las correcciones de las betas de mantenimiento anteriores.
Los recursos JavaScript no cambian.
