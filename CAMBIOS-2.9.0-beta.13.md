# Euskalmet 2.9.0-beta.13

- Retira `login_id` del formulario y del proceso interno de autenticación.
- Mantiene compatibles las entradas existentes aunque conserven el antiguo
  campo sin utilizar en sus datos.
- Conserva sin redondear los totales de precipitación diarios y mensuales
  entregados por Euskalmet.
- Calcula el total anual sumando los valores mensuales sin aplicar un redondeo
  posterior.
- Mueve la atribución de Weather Radar Card junto al aviso inicial del README.
- Añade al README un ejemplo YAML para mostrar los avisos meteorológicos.

