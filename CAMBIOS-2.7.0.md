# Euskalmet 2.7.0

- Traducción al español de los estados meteorológicos y atributo `condicion`
  legible en la entidad de tiempo.
- Nueva tarjeta `custom:euskalmet-alert-card`, con color según la severidad y
  la descripción de cada riesgo activo.
- Dirección del viento expresada con 16 puntos cardinales (`N`, `NNE`, `NE`,
  `ENE`, etc.); el valor original se conserva en el atributo `degrees`.
- Carga automática de las tarjetas de avisos y radar, con invalidación de caché
  por versión.
- Documentación aclarada: la entidad cámara muestra la última imagen; la
  animación, el mapa gris y la línea temporal pertenecen a la tarjeta de radar.
