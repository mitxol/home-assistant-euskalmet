# Euskalmet 2.12.5

## Correcciones

- Reconoce `GROW_TO_QUARTER`, código utilizado por Euskalmet para la fase
  creciente anterior al cuarto creciente, como `waxing_crescent`.
- Añade compatibilidad preventiva con las familias equivalentes `GROW_TO_*` y
  `SHRINK_TO_*` para las fases crecientes y menguantes.
- Mantiene el código original recibido en `raw_phase` para diagnóstico.
