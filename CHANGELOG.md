# Changelog

## 2.9.0-beta.4

- Corrige todos los avisos de Ruff detectados por GitHub Actions.
- Sustituye `timezone.utc` por el alias moderno `UTC`.
- Normaliza los imports y la tabla de sensores estadísticos.
- Mantiene autoplay, opacidad completa y animación a 8 fps en el radar.

## 2.9.0-beta.3

- Incorpora la versión funcional `2.9.0-beta.3` de la integración.
- Añade `CONFIG_SCHEMA` para indicar que la integración solo se configura mediante Config Entries.
- Actualiza a beta 3 los recursos JavaScript de avisos, históricos y radar.
- Documenta el registro manual de los tres recursos en el README principal y en el README del frontend.
- Ordena y completa `manifest.json` para las validaciones de Hassfest y HACS.
- Actualiza las acciones de GitHub para usar Node.js 24.

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
