# Euskalmet para Home Assistant

Integración comunitaria de Home Assistant para consultar datos meteorológicos
de Euskalmet y Open Data Euskadi.

> [!IMPORTANT]
> **Proyecto comunitario no oficial.** No está afiliado, patrocinado,
> mantenido ni soportado por Euskalmet ni por el Gobierno Vasco. Comunica los
> problemas mediante los **Issues de este repositorio**, no mediante los
> canales de soporte de Euskalmet.

> [!NOTE]
> El radar animado utiliza una adaptación de la tarjeta de HACS
> [Weather Radar Card](https://github.com/jpettitt/weather-radar-card), creada
> por su comunidad y publicada bajo licencia MIT. La adaptación añade Euskalmet
> como fuente de datos; no convierte esta integración en un proyecto oficial de
> Euskalmet ni de Weather Radar Card.

> Estado: **candidata final de mantenimiento**. La versión actual es
> `2.9.1-beta.7`.
> Corrige la previsión horaria al final del día, la detección de magnitudes ante
> fallos del dominio público y los resúmenes diarios durante el cambio de fecha
> entre UTC y la zona horaria de Home Assistant.

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

## Vista previa

![Panel de Euskalmet con radar, históricos, avisos y observaciones](docs/images/panel-euskalmet.png)

La entidad meteorológica ofrece previsión diaria y horaria desde el diálogo
nativo de Home Assistant:

| Previsión diaria | Previsión horaria |
| --- | --- |
| ![Previsión diaria de Euskalmet](docs/images/prevision-diaria.png) | ![Previsión horaria de Euskalmet](docs/images/prevision-horaria.png) |

## Requisitos

1. Home Assistant `2026.7.0` o posterior.
2. HACS para la instalación recomendada.
3. Credenciales personales de acceso a la API de Euskalmet: correo electrónico
   y clave privada (privatekey.pem).

La integración no incorpora credenciales compartidas. El JWT se firma
localmente mediante RS256 en la instalación de Home Assistant del usuario.

## Instalación mediante HACS

Hasta que la integración entre en el catálogo predeterminado:

1. Abre HACS y entra en **Integraciones**.
2. Abre el menú de tres puntos y selecciona **Repositorios personalizados**.
3. Añade `https://github.com/mitxol/home-assistant-euskalmet` como
   **Integration**.
4. Instala Euskalmet y reinicia Home Assistant.
5. Ve a **Ajustes > Dispositivos y servicios > Añadir integración** y busca
   **Euskalmet**.

## Instalación manual

Copia `custom_components/euskalmet` dentro de la carpeta `custom_components`
de Home Assistant y reinicia.

## Configuración

El asistente solicita las credenciales. Hay que introducir email y privatekey.pem
(incluyendo ------BEGIN PRIVATE KEY---- y ------END PRIVATE KEY----)
después muestra las estaciones meteorológicas activas  con los sensores que 
tiene disponibles (no todas las estaciones tienen todos los sensores). 
Cada estación se configura como una entrada independiente. 
La integración crea un dispositivo para las observaciones
actuales y otro para resúmenes y estadísticas.

Solo se crean entidades para las magnitudes publicadas por la estación.

## Tarjetas

Los archivos JavaScript se sirven desde la propia integración. Añade los
recursos que vayas a utilizar en **Ajustes > Paneles de control > menú de tres
puntos > Recursos**, con tipo **Módulo JavaScript**:

```text
/euskalmet_static/euskalmet-history-card.js?v=2
/euskalmet_static/weather-radar-card-euskalmet.js?v=3
```

La adaptación registra `custom:weather-radar-card-euskalmet`, por lo que puede
coexistir con la tarjeta original `custom:weather-radar-card` si también la
utilizas con otras fuentes.

Las revisiones `v=2` y `v=3` pertenecen a cada archivo JavaScript, no a la
versión de la integración. No hay que modificarlas en cada actualización:
solamente cambiarán cuando se publique una revisión real de la tarjeta. Después
de ese cambio, cierra y vuelve a abrir la aplicación móvil o fuerza una recarga
completa del navegador.

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

El radar de Kapildui es común para todas las estaciones. Si existen varias
entradas, la tarjeta selecciona automáticamente una de ellas. Opcionalmente
puede fijarse una entrada concreta mediante:

```yaml
euskalmet_entry_id: ID_DE_LA_ENTRADA
```

### Histórico meteorológico

```yaml
type: custom:euskalmet-history-card
entity: sensor.TU_ESTACION_temperatura
measure: temperature
```

La tarjeta consulta los resúmenes de Euskalmet al visualizar el periodo. Los
datos históricos no se copian al Recorder ni se mezclan con las estadísticas
de larga duración de Home Assistant.

Con una sola entrada no hace falta indicar nada más. Cuando hay varias
estaciones, se recomienda seleccionar explícitamente la entrada para obtener un
comportamiento idéntico en navegadores y en la aplicación móvil:

```yaml
type: custom:euskalmet-history-card
entry_id: ID_DE_LA_ENTRADA
measure: temperature
title: Histórico de Arkaute
```

La ID puede obtenerse desde **Ajustes > Dispositivos y servicios > Euskalmet >
Copiar ID de la entrada**.

### Avisos meteorológicos

Los avisos pueden mostrarse sin JavaScript adicional mediante una tarjeta de
entidad o una tarjeta Markdown/template utilizando `sensor.nivel_de_aviso` o
`binary_sensor.aviso_meteorologico`.

```yaml
type: markdown
title: Avisos meteorológicos
content: >-
  {% set aviso = states('sensor.nivel_de_aviso') %}
  {% if aviso not in ['unknown', 'unavailable', 'none', 'Sin avisos'] %}
    **Nivel de aviso:** {{ aviso }}

    {{ state_attr('sensor.nivel_de_aviso', 'description') | default('', true) }}
  {% else %}
    No hay avisos meteorológicos activos.
  {% endif %}
```

Sustituye el identificador por el de tu entidad si Home Assistant ha añadido
el nombre de la estación.

## Actualización y tolerancia a fallos

Las observaciones actuales se consultan mediante el endpoint agregado diario
recomendado por Euskalmet. Previsión, avisos, radar y resúmenes se tratan como
fuentes opcionales: un fallo temporal de una fuente no impide actualizar las
demás.

Los resúmenes mensuales se almacenan en caché y los anuales se calculan a partir
de los meses disponibles. Las rutas individuales anteriores se conservan como
respaldo cuando resulta necesario.

Home Assistant puede conservar una precisión de visualización elegida
anteriormente para cada entidad. Si una precipitación de `2,5 mm` aparece como
`3 mm`, abre los ajustes de la entidad y selecciona un decimal en **Precisión de
visualización**. La integración conserva el valor numérico original.

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

<p align="center">
  <img src="docs/images/euskalmet-logo.jpg" alt="Euskalmet — Agencia Vasca de Meteorología" width="360">
</p>

**Datos meteorológicos proporcionados por Euskalmet — Agencia Vasca de
Meteorología**, a través de Euskalmet y Open Data Euskadi.

El logotipo oficial se reproduce únicamente para atribuir la procedencia de los
datos, con la autorización indicada por Euskalmet. No forma parte de la
identidad visual de esta integración y no implica afiliación, patrocinio,
mantenimiento ni soporte oficial. El icono comunitario de la integración es un
diseño independiente.

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
