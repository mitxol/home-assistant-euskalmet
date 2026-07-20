# Euskalmet 2.9.0-beta.15

- Evita el conflicto del radar cuando existen varias estaciones: al ser un
  producto común de Kapildui, utiliza automáticamente una entrada disponible.
- La tarjeta histórica deduce la estación desde el atributo `station` de la
  entidad configurada.
- Mantiene `entry_id` y `euskalmet_entry_id` como alternativas avanzadas.
- Separa la revisión de los recursos JavaScript de la versión de la integración:
  histórico `v=2` y radar `v=3`.
- Actualiza el README con la configuración multiestación.

