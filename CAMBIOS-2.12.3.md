# Euskalmet 2.12.3

## Correcciones

- Reconoce `DECREASE_TO_FULL_MOON`, código utilizado por Euskalmet para la fase
  menguante posterior al tercer cuarto, como `waning_crescent`.
- Añade las variantes previsibles de los códigos `INCREASE_TO_*` y
  `DECREASE_TO_*` para cubrir el ciclo lunar completo aunque Euskalmet alterne
  entre nombres equivalentes.
- Conserva como `raw_phase` cualquier código original recibido para facilitar
  el diagnóstico de futuros cambios de la API.
