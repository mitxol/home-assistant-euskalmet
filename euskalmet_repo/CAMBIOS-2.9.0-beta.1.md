# Euskalmet 2.9.0-beta.1

Beta candidata para pruebas previas a HACS.

- Migra observaciones y resúmenes a los endpoints agregados recomendados por
  Euskalmet, manteniendo los respaldos anteriores.
- Usa credenciales individuales mediante Config Flow; no incorpora claves.
- Corrige los ceros provisionales de franjas aún no publicadas.
- Incluye resúmenes diarios, mensuales y anuales en dispositivo separado.
- Incluye tarjetas de radar, avisos e histórico meteorológico.
- El radar usa por defecto opacidad 100 % y reproducción a 8 fps.
- Declara el tipo de integración como servicio en el manifiesto.
