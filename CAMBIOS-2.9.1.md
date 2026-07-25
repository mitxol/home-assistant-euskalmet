# Euskalmet 2.9.1

Versión estable de mantenimiento posterior a Euskalmet 2.9.0.

## Correcciones

- Combina la previsión horaria de hoy y mañana para que Home Assistant no
  muestre una previsión vacía durante las últimas horas del día.
- Interpreta las franjas de previsión horaria como UTC y deja que Home Assistant
  las convierta a la zona horaria local, evitando el adelanto de dos horas en
  horario de verano.
- Publica correctamente las renovaciones de previsión mediante la firma usada
  por Home Assistant 2026.7.
- Utiliza el endpoint agregado autenticado para detectar magnitudes cuando
  falla el dominio público de Euskalmet.
- Calcula los resúmenes provisionales del día a partir de las franjas agregadas
  ya publicadas.
- Si el agregado todavía no existe, utiliza como respaldo el documento público
  diario.
- Construye el día local combinando los dos documentos UTC que lo atraviesan;
  esto corrige especialmente el periodo entre las 00:00 y las 02:00 CEST.
- Evita conservar como resumen de hoy los valores acumulados del día anterior.

## Compatibilidad

- No cambia la configuración de las entradas existentes.
- No cambia ningún recurso JavaScript ni las revisiones documentadas para las
  tarjetas de histórico y radar.
- Los resúmenes mensuales y anuales mantienen su funcionamiento anterior.

## Documentación e identidad visual

- Añade un icono comunitario propio en los tamaños utilizados por Home
  Assistant y HACS.
- Incluye capturas del panel y utiliza URLs absolutas para que también se
  muestren dentro de HACS.
- Atribuye los datos a Euskalmet mediante su logotipo oficial únicamente en la
  sección de procedencia de los datos.
- Fija el ejemplo del radar en `zone.home` para impedir que siga la ubicación
  del teléfono.
- Explica cómo utilizar el ID real de la entidad «Nivel de aviso» en la tarjeta
  Markdown.
- Documenta el registro, la activación de la cuenta y la descarga de las claves
  desde el portal de Open Data Euskadi.
