# Euskalmet 2.12.0

## Novedades

- Traducción completa de la integración al euskera y selección automática de
  castellano o euskera según el idioma de Home Assistant.
- Calendario astronómico con fase lunar y horas de salida y puesta de la Luna.
- Previsión marítima del Cantábrico con altura de ola, temperatura del agua y
  visibilidad mínima y máxima.
- Mareas astronómicas de Pasaia con estado, próxima pleamar, próxima bajamar y
  sus alturas.
- Nueva visualización del histórico mensual con selector directo de mes,
  escalas adaptativas, leyenda interactiva y soporte táctil para móviles.

## Optimización y fiabilidad

- Cachés e intervalos independientes para observaciones, predicciones, avisos,
  radar, resúmenes, polen, astronomía, mar y mareas.
- Conservación del último dato válido cuando falla temporalmente una fuente
  opcional.
- Conversión correcta de las fechas y horas UTC de Euskalmet a la zona horaria
  configurada en Home Assistant.
- Corrección de la visibilidad marítima para publicarla en kilómetros.
- Limpieza automática del antiguo dispositivo de astronomía al trasladar sus
  entidades al dispositivo marítimo.

## Documentación

- README actualizado con las funciones, frecuencias de consulta, recursos
  JavaScript y nuevas capturas en euskera.
- Aviso de transparencia sobre el uso de herramientas de inteligencia
  artificial durante el desarrollo y la revisión del proyecto.
