# Euskalmet 2.10.0

## Polen

- Añade el recuento total y sensores por tipo polínico mediante la API pública
  de Open Data Euskadi.
- Selecciona automáticamente la estación de Bilbao, Vitoria-Gasteiz o
  Donostia / San Sebastián más cercana a la estación meteorológica configurada.
- Consulta el polen cada seis horas y conserva el último dato si el servicio
  público falla temporalmente.
- Los tipos nuevos aparecen automáticamente como entidades cuando la API los
  publica.

Los datos proceden del Departamento de Salud y se publican con periodicidad
semanal. El atributo `observed_on` indica siempre la fecha real de la muestra.
