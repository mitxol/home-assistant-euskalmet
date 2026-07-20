# Euskalmet para Home Assistant

Integración comunitaria de Home Assistant para consultar datos meteorológicos
de Euskalmet y Open Data Euskadi.

> [!IMPORTANT]
> **Proyecto comunitario no oficial.** No está afiliado, patrocinado,
> mantenido ni soportado por Euskalmet ni por el Gobierno Vasco. Comunica los
> problemas mediante los **Issues de este repositorio**, no mediante los
> canales de soporte de Euskalmet.

> Estado: **beta pública**. La versión actual es `2.9.0-beta.12`.

## Funciones

- Configuración completa desde la interfaz de Home Assistant.
- Selección de estaciones meteorológicas oficiales activas.
- Sensores dinámicos para las magnitudes publicadas por cada estación.
- Temperatura, humedad, presión, viento, racha, dirección, radiación y
  precipitación.
- Entidad meteorológica con condiciones actuales y previsión horaria y diaria.
- Avisos meteorológicos filtrados para la zona de la estación.
- Radar animado de Kapildui sobre un mapa OpenStreetMap desaturado.
- Resúmenes diarios, mensuales y anuales en un dispositivo estadístico separado.
- Histórico consultado bajo demanda, sin importar datos antiguos a Recorder.
- Caché y endpoints agregados para reducir el número de peticiones a la API.
- Conservación del último valor válido ante respuestas temporales incompletas.

## Requisitos

1. Home Assistant `2026.7.0` o posterior durante la fase beta.
2. HACS para la instalación recomendada.
3. Credenciales personales de acceso a la API de Euskalmet: correo
   electrónico, clave privada (privatekey.pem)

La integración no incorpora credenciales compartidas. El JWT se firma
localmente mediante RS256 en la instalación de Home Assistant del usuario.

## Instalación mediante HACS

Hasta que la integración entre en el catálogo predeterminado:

1. Abre HACS y entra en **Integraciones**.
2. Abre el menú de tres puntos y selecciona **Repositorios personalizados**.
3. Añade `https://github.com/mitxol/home-assistant-euskalmet` como
   **Integration**.
4. Activa **Mostrar versiones beta**, instala Euskalmet y reinicia Home Assistant.
5. Ve a **Ajustes > Dispositivos y servicios > Añadir integración** y busca
   **Euskalmet**.

## Instalación manual

Copia `custom_components/euskalmet` dentro de la carpeta `custom_components`
de Home Assistant y reinicia.

## Configuración

El asistente solicita las credenciales, introducir email y privatekey.pem 
(incluyendo -------BEGIN PRIVETE KEY----- Y -------END PRIVATE KEY----- en el 
copy-paste). Después muestra las estaciones
meteorológicas activas, con los sensores disponibles que tiene cada estación. 
Cada estación se configura como una entrada
independiente. La integración crea un dispositivo para las observaciones
actuales y otro para resúmenes y estadísticas.

Solo se crean entidades para las magnitudes publicadas por la estación.

## Tarjetas

Los archivos JavaScript se sirven desde la propia integración. Añade los
recursos que vayas a utilizar en **Ajustes > Paneles de control > menú de tres
puntos > Recursos**, con tipo **Módulo JavaScript**:

```text
/euskalmet_static/euskalmet-history-card.js?v=2.9.0-beta.12
/euskalmet_static/weather-radar-card-euskalmet.js?v=2.9.0-beta.12
```

No cargues al mismo tiempo otra copia de `weather-radar-card.js`, ya sea desde
`/local/community/` o desde HACS. Ambas registrarían el mismo elemento
`custom:weather-radar-card`. Elimina o desactiva el recurso anterior antes de
añadir el incluido en Euskalmet.

Después de actualizar un recurso, cierra y vuelve a abrir la aplicación móvil
o fuerza una recarga completa del navegador. El parámetro de versión evita que
se reutilice una copia antigua de la caché.

### Radar animado

```yaml
type: custom:weather-radar-card-euskalmet
data_source: Euskalmet
map_style: Light
radar_opacity: 1
past_minutes: 360
show_color_bar: false
zoom_level: 7
```

La tarjeta obtiene los fotogramas autenticados a través de la integración. No
expone las credenciales de Euskalmet al navegador. La capa utiliza los límites
geográficos publicados por el visor oficial de Kapildui y permanece anclada al
mapa al desplazarlo, ampliarlo, reproducirlo o pausarlo.


### Histórico meteorológico

```yaml
type: custom:euskalmet-history-card
entity: sensor.TU_ESTACION_temperatura
```

La tarjeta consulta los resúmenes de Euskalmet al visualizar el periodo. Los
datos históricos no se copian al Recorder ni se mezclan con las estadísticas
de larga duración de Home Assistant.

### Avisos meteorológicos

Los avisos pueden mostrarse sin JavaScript adicional mediante una tarjeta de
entidad o una tarjeta Markdown/template utilizando `sensor.nivel_de_aviso` o
`binary_sensor.aviso_meteorologico`.

```yaml
type: markdown
title: Avisos meteorológicos
entity_id:
  - binary_sensor.TU_ESTACION_aviso_meteorologico
content: |-
  {% set entity = 'binary_sensor.TU_ESTACION_aviso_meteorologico' %}
  {% if is_state(entity, 'on') %}
  ## ⚠️ Aviso meteorológico

  **Nivel:** {{ state_attr(entity, 'severity') | default('desconocido') }}

  {% for description in state_attr(entity, 'descriptions') or [] %}
  - {{ description }}
  {% endfor %}
  {% else %}
  ✅ No hay avisos meteorológicos activos.
  {% endif %}
```


## Actualización y tolerancia a fallos

Las observaciones actuales se consultan mediante el endpoint agregado diario
recomendado por Euskalmet. Previsión, avisos, radar y resúmenes se tratan como
fuentes opcionales: un fallo temporal de una fuente no impide actualizar las
demás.

Los resúmenes mensuales se almacenan en caché y los anuales se calculan a partir
de los meses disponibles. Las rutas individuales anteriores se conservan como
respaldo cuando resulta necesario.

## Privacidad y seguridad

- Cada usuario aporta sus propias credenciales.
- La clave privada se almacena en la entrada de configuración de Home Assistant.
- La clave privada no se envía a este proyecto ni a terceros.
- El JWT se firma localmente y se renueva cuando corresponde.
- Revisa los diagnósticos y registros antes de compartirlos.

## Solución de problemas

Antes de abrir una incidencia:

1. Actualiza a la última release y reinicia Home Assistant.
2. Comprueba que las credenciales continúan vigentes.
3. Actualiza el parámetro `?v=` de los recursos JavaScript.
4. Fuerza una recarga completa o prueba en una ventana privada.
5. Indica las versiones de Home Assistant y de la integración y adjunta los
   registros relevantes, sin claves privadas.

## Fuente de datos, marca y atribuciones

Los datos proceden de **Euskalmet — Agencia Vasca de Meteorología** a través de
**Open Data Euskadi**. Este repositorio no utiliza el logotipo oficial de
Euskalmet ni símbolos institucionales como identidad visual.

La tarjeta de radar se basa en el proyecto comunitario
[Weather Radar Card](https://github.com/jpettitt/weather-radar-card) y conserva
su licencia MIT. Leaflet mantiene su licencia BSD-2-Clause y los mapas de
OpenStreetMap muestran su atribución. Los datos de radar se atribuyen a
Euskalmet.

## Desarrollo

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para preparar el entorno y ejecutar
las validaciones.

## Licencia

El código propio se publica bajo licencia MIT. Los componentes de terceros
incluidos conservan sus respectivas licencias.
