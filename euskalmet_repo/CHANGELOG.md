# Changelog

Todos los cambios relevantes se documentarán en este archivo.

## [2.9.0-beta.1] - 2026-07-16

### Añadido

- Observaciones y resúmenes mediante endpoints agregados de Euskalmet.
- Resúmenes diarios, mensuales y anuales.
- Tarjeta de histórico meteorológico bajo demanda.
- Dispositivo separado para estadísticas.
- Tarjetas de radar, avisos e histórico incluidas en la integración.

### Cambiado

- Las credenciales son individuales y se configuran mediante Config Flow.
- Los meses cerrados se conservan en caché durante el arranque.
- El radar usa por defecto opacidad completa y reproducción a 8 fps.
- El manifiesto declara la integración como servicio.

### Corregido

- Tratamiento de ceros provisionales de franjas todavía no publicadas.
