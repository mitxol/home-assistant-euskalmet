# Euskalmet 2.9.1-beta.6

## Corrección horaria de la previsión

- Interpreta las horas de los bloques de previsión de Euskalmet como UTC.
- Deja que Home Assistant las convierta a la zona horaria configurada.
- Corrige el adelanto visual de dos horas observado durante el horario de
  verano: un bloque de las 09:00 UTC se muestra a las 11:00 CEST.

Mantiene el resto de correcciones candidatas a 2.9.1. Los recursos JavaScript
no cambian.
