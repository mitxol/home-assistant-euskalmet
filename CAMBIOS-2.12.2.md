# Euskalmet 2.12.2

## Compatibilidad

- Actualiza PyJWT a `2.13.0`, la versión incluida por Home Assistant 2026.8.
- Evita el conflicto de dependencias que impedía cargar la integración después
  de actualizar a Home Assistant 2026.8.
- Establece Home Assistant 2026.8 como versión mínima compatible.
- Ejecuta las comprobaciones de Python con la versión 3.14 utilizada por Home
  Assistant 2026.8.
- Actualiza la acción de GitHub `actions/setup-python` de la versión 6 a la 7.

La generación y firma RS256 del token de Euskalmet no cambia.
