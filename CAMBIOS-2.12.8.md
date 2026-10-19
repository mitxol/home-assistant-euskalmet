# Euskalmet 2.12.8

## Correcciones

- Deja de construir la zona horaria con `ZoneInfo(...)` dentro del cliente de
  la API. `EuskalmetAPI` recibe ahora un `tzinfo` ya resuelto
  (`dt_util.get_default_time_zone()`) desde la configuración de la entrada, el
  flujo de configuración y la migración, de modo que no se lee la base de
  datos de zonas del disco en el event loop de Home Assistant.
- La previsión diaria y horaria, los avisos y el radar calculan la fecha con
  la zona horaria de Home Assistant en lugar de la del sistema operativo.
- Corrige los resúmenes anuales tras el cambio de año: los meses del año
  anterior se descartaban solo al reiniciar y se sumaban a los del año nuevo.
- Al cambiar de mes, el mes recién cerrado se vuelve a descargar para incluir
  sus últimas horas, y el resumen del mes nuevo se pide de inmediato.
- Tras la medianoche, los resúmenes de hoy se renuevan en la primera
  actualización en lugar de mostrar hasta 15 minutos los valores de ayer.
- La media de los resúmenes provisionales se pondera solo con las franjas que
  tienen media.
- Las mareas con altura `0` ya no se descartan como si no tuvieran altura.
- La entidad meteorológica declara la precipitación en milímetros; antes, en
  instalaciones con unidades imperiales, la previsión se mostraba sin
  convertir.
- El coordinador recibe la entrada de configuración de forma explícita.
- Los dispositivos de resúmenes, polen y previsión marítima se enlazan con la
  estación mediante `via_device_id`, y la limpieza del antiguo dispositivo
  astronómico usa `async_get_device_by_identifier`. Elimina los avisos de
  obsolescencia previstos para Home Assistant 2027.8.
- La tarjeta de avisos solo se vuelve a dibujar cuando cambia su entidad.

## Novedades

- Reautenticación: si Euskalmet rechaza las credenciales, Home Assistant
  muestra un aviso para introducir de nuevo el correo y la clave privada sin
  borrar la integración.
- Traducción al inglés (`translations/en.json`). Con Home Assistant en inglés,
  las entidades tienen nombre propio en lugar de uno genérico.


## Radar

- La tarjeta `weather-radar-card-euskalmet` vuelve a usar OpenStreetMap con
  `map_style: Auto` u `OSM`. Desde la 2.12.6 esos estilos mostraban por error
  el lienzo gris de Esri.
- Cada estilo tiene ahora su propio mapa base sin clave ni marcas de agua:
  `Voyager` pasa a ser el topográfico de Esri y `Satellite` vuelve a mostrar
  nombres de lugares con la capa de referencia de Esri.
- La atribución del mapa corresponde al proveedor que se está mostrando.
- La tarjeta `euskalmet-radar-map-card` admite la opción `map_style`
  (`gray`, `osm`, `topo`, `light`, `dark` o `satellite`). Por defecto se
  mantiene `gray`. En los estilos con etiquetas, los nombres se dibujan por
  encima de la lluvia.

## Actualización

- Cambia los recursos a `/euskalmet_static/weather-radar-card-euskalmet.js?v=6`
  y `/euskalmet_static/euskalmet-alert-card.js?v=2` para forzar la recarga.
