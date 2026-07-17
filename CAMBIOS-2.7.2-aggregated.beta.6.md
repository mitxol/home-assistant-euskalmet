# Euskalmet 2.7.2-aggregated.beta.6

- Añade 14 sensores anuales calculados desde los resúmenes mensuales.
- Las medias anuales se ponderan por el número real de lecturas procesadas.
- Los extremos anuales conservan mes, día y hora del récord.
- Añade la tarjeta `custom:euskalmet-history-card` con selector de mes y
  magnitud para representar los resúmenes diarios históricos.
- Los históricos se solicitan bajo demanda y no se insertan en Recorder.
