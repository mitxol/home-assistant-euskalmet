# Euskalmet 2.7.2-aggregated.beta.5

- Corrige caídas temporales de todos los sensores a cero.
- Espera 15 minutos adicionales tras el cierre de cada franja antes de usarla.
- Si una o varias franjas consecutivas contienen cero simultáneamente en
  todas las magnitudes, retrocede hasta la última cohorte publicada.
- Conserva ceros meteorológicos legítimos, como ausencia de precipitación.
- Amplía a 45 minutos el umbral de antigüedad para acomodar el retraso de
  publicación de Euskalmet.
- Incluye las 28 entidades de resumen diario y mensual de beta.4.
