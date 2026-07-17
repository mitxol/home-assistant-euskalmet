# Euskalmet 2.7.2-aggregated.beta.1

Versión de prueba de la migración de lecturas al endpoint oficial agregado.

- Usa `readings/aggregated/byDay/forStation` como fuente principal.
- Obtiene todas las magnitudes de la estación en una sola petición normal.
- Ignora las franjas de diez minutos que todavía no han terminado, aunque la
  API las publique provisionalmente con valor cero.
- Consulta el día anterior solamente durante el cambio de día o si hoy no
  proporciona ninguna franja terminada.
- Mantiene el documento público diario como primer respaldo.
- Mantiene las consultas autenticadas por sensor como último respaldo.
- Conserva identificadores y entidades existentes de Home Assistant.

Esta beta no crea todavía sensores diarios, mensuales o anuales.
