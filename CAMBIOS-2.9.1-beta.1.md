# Euskalmet 2.9.1-beta.1

Beta de mantenimiento posterior a la versión estable 2.9.0.

## Correcciones

- Combina la previsión horaria de hoy y mañana. Así Home Assistant no recibe
  una previsión vacía durante las últimas horas del día.
- Conserva la fecha real de cada bloque horario al combinar ambos documentos.
- Notifica a los suscriptores de Home Assistant cuando el coordinador renueva
  las previsiones.
- Si falla por DNS el servidor de lecturas públicas, detecta las magnitudes
  mediante el endpoint agregado autenticado antes de mostrar un aviso.

## Recursos de Lovelace

No cambian los archivos JavaScript ni sus revisiones. Se mantienen los recursos
documentados para la versión 2.9.0.
