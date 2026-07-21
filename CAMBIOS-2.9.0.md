# Euskalmet 2.9.0

Primera versión estable de la integración comunitaria de Euskalmet para Home
Assistant.

## Funciones principales

- Configuración mediante la interfaz y soporte para varias estaciones.
- Observaciones actuales mediante el endpoint agregado diario recomendado por
  Euskalmet, con caché y conservación del último valor válido.
- Previsión horaria y diaria, avisos meteorológicos y radar de Kapildui.
- Sensores de resúmenes diarios, mensuales y anuales para las magnitudes
  disponibles en cada estación.
- Histórico mensual consultado bajo demanda, sin importar datos al Recorder.
- Tarjeta histórica y adaptación de Weather Radar Card incluidas.

## Cambios finales respecto a las betas

- Elimina `login_id` del formulario y de la autenticación.
- Conserva los totales de precipitación sin redondearlos y sugiere un decimal
  para mostrarlos.
- Evita conflictos del radar cuando existen varias entradas.
- Documenta el uso de `entry_id` en históricos multiestación para obtener el
  mismo comportamiento en navegadores y aplicaciones móviles.
- Usa revisiones independientes para los recursos: histórico `v=2` y radar
  `v=3`.

