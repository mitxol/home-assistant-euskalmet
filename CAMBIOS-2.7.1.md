# Euskalmet 2.7.1

- El aviso binario deja de usar la clase `safety`, evitando el color especial
  de seguridad cuando está activo y recuperando el aspecto normal del tema.
- El nivel de aviso se declara como sensor enumerado y traduce sus estados:
  sin avisos, amarillo, naranja y rojo.
- Se añaden iconos específicos para cada nivel. Home Assistant no permite a una
  integración fijar dinámicamente el color de un sensor nativo; los colores
  exactos se muestran en `custom:euskalmet-alert-card`.
- La entidad meteorológica expone `prevision_emitida`, `prevision_valida`,
  `localidad_prevision`, `region_prevision` y `zona_prevision` para diagnosticar
  diferencias entre la estación observada y la previsión oficial.
- La previsión sigue siendo la publicada oficialmente por Euskalmet; no se
  corrige artificialmente con la temperatura observada.
