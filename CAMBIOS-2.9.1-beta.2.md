# Euskalmet 2.9.1-beta.2

Segunda beta de mantenimiento posterior a la versión estable 2.9.0.

## Correcciones

- Adapta la publicación de previsiones a la firma utilizada por Home Assistant
  2026.7, indicando todos los tipos mediante `async_update_listeners(None)`.
- Trata como situación temporal esperada el 404 del resumen diario durante los
  primeros minutos después de medianoche.
- Evita conservar como resumen de hoy el total correspondiente al día anterior
  mientras Euskalmet prepara el nuevo documento.
- Mantiene las correcciones de `2.9.1-beta.1`: previsión horaria combinada de
  hoy y mañana y respaldo agregado para detectar magnitudes.

Los recursos JavaScript no cambian.
