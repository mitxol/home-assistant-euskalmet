# Euskalmet para Home Assistant

Integración comunitaria de Home Assistant para consultar datos meteorológicos de Euskalmet / Open Data Euskadi.

> [!IMPORTANT]
> **Proyecto comunitario no oficial.** Esta integración ha sido desarrollada de forma independiente y no está afiliada, patrocinada, mantenida ni soportada por Euskalmet ni por el Gobierno Vasco. Los problemas relacionados con el componente deben comunicarse mediante los **Issues de este repositorio**, no a los canales de soporte de Euskalmet o del Gobierno Vasco.

> Estado: **beta pública**. La versión `2.9.0-beta.1` está preparada para probarse mediante un repositorio personalizado de HACS.

## Funciones

- Configuración completa desde la interfaz de Home Assistant.
- Selección de estaciones meteorológicas oficiales activas.
- Sensores dinámicos según las magnitudes disponibles en cada estación.
- Temperatura, humedad, presión, viento, racha, dirección, radiación y precipitación.
- Entidad meteorológica con condiciones actuales y previsión horaria y diaria.
- Avisos meteorológicos filtrados para la zona de la estación.
- Radar de precipitación de Kapildui con animación sobre mapa.
- Resúmenes diarios, mensuales y anuales.
- Histórico consultado bajo demanda, sin importar datos antiguos al Recorder.
- Caché y consultas agregadas para reducir el número de peticiones.

## Requisitos

1. Home Assistant `2026.7.0` o posterior durante la fase beta.
2. HACS, para la instalación recomendada.
3. Credenciales personales de acceso a la API de Euskalmet:
   - correo electrónico;
   - clave privada;
   - `login_id`, cuando corresponda.

La integración no incluye credenciales compartidas ni claves incorporadas. El JWT se firma localmente mediante RS256 en la instalación de Home Assistant del usuario.

## Instalación mediante HACS

Hasta que la integración entre en el catálogo predeterminado:

1. Abre HACS.
2. Entra en **Integraciones**.
3. Abre el menú de tres puntos.
4. Selecciona **Repositorios personalizados**.
5. Añade `https://github.com/mitxol/home-assistant-euskalmet`.
6. Selecciona la categoría **Integration**.
7. Instala Euskalmet y reinicia Home Assistant.

Después del reinicio, ve a **Ajustes > Dispositivos y servicios > Añadir integración** y busca **Euskalmet**.

## Instalación manual

Copia la carpeta:

```text
custom_components/euskalmet
```

en la carpeta `custom_components` de tu configuración de Home Assistant y reinicia Home Assistant.

## Configuración

El asistente solicita primero las credenciales y después muestra las estaciones meteorológicas activas. Cada estación se configura como una entrada independiente y crea dispositivos separados para observación y estadísticas.

Solo se crean entidades para las magnitudes realmente publicadas por la estación seleccionada.

## Tarjetas incluidas

Los archivos JavaScript se sirven desde la propia integración. Para utilizar las tarjetas, añade estos tres recursos en **Ajustes > Paneles de control > menú de tres puntos > Recursos** con el tipo **Módulo JavaScript**:

```text
/euskalmet_static/euskalmet-alert-card.js?v=2.9.0-beta.1
/euskalmet_static/euskalmet-history-card.js?v=2.9.0-beta.1
/euskalmet_static/euskalmet-radar-map-card.js?v=2.9.0-beta.1
```

La integración también intenta registrar estos recursos automáticamente, pero el alta manual evita problemas en instalaciones o paneles donde no aparezcan cargados. Después de añadirlos o actualizar la integración, reinicia Home Assistant y fuerza una recarga completa del navegador.

### Radar animado

```yaml
type: custom:euskalmet-radar-map-card
entity: camera.radar_de_precipitacion
title: Radar Euskalmet
opacity: 1
frame_interval: 125
```

### Avisos meteorológicos

```yaml
type: custom:euskalmet-alert-card
entity: sensor.nivel_de_aviso
```

También puede usarse `binary_sensor.aviso_meteorologico`.

### Histórico meteorológico

Añade la tarjeta manual y selecciona una entidad de la estación. La información histórica se solicita únicamente al visualizar el periodo elegido y no se copia al Recorder.

```yaml
type: custom:euskalmet-history-card
entity: sensor.temperatura
```

## Actualización y tolerancia a fallos

Las observaciones se actualizan mediante los endpoints agregados recomendados por Euskalmet. Previsión, avisos, radar y estadísticas se tratan como fuentes opcionales: un fallo temporal de una de ellas no impide que el resto de la integración siga funcionando.

La integración utiliza caché para resúmenes mensuales y anuales y conserva rutas anteriores únicamente como respaldo.

## Privacidad y seguridad

- Cada usuario aporta sus propias credenciales.
- La clave privada se almacena en la entrada de configuración de Home Assistant.
- No se envía la clave privada a este proyecto ni a terceros.
- El JWT se firma localmente y se renueva cuando corresponde.
- Antes de compartir diagnósticos o registros, revisa que no contengan información personal.

## Solución de problemas

Antes de abrir una incidencia:

1. Actualiza a la última release.
2. Reinicia Home Assistant.
3. Fuerza una recarga completa del navegador si fallan las tarjetas.
4. Comprueba que tus credenciales siguen vigentes.
5. Adjunta la versión de Home Assistant, la versión de la integración y los registros relevantes, sin incluir claves privadas.

Las incidencias se gestionan en el apartado **Issues** del repositorio.

## Fuente de datos y atribuciones

Los datos meteorológicos utilizados por esta integración son proporcionados por **Euskalmet — Agencia Vasca de Meteorología** a través de **Open Data Euskadi**.

Esta integración es un proyecto comunitario independiente. No es un producto oficial de Euskalmet ni del Gobierno Vasco y no cuenta con soporte institucional. Para informar de errores o solicitar mejoras, utiliza los **Issues de este repositorio**.

El logotipo oficial de Euskalmet y los símbolos institucionales del Gobierno Vasco no se utilizan como identidad visual de la integración, del repositorio ni de HACS. El proyecto empleará una marca comunitaria propia. El logotipo oficial de Euskalmet podrá aparecer únicamente en la documentación, dentro de una sección claramente dedicada a la procedencia de los datos y respetando las condiciones indicadas por Euskalmet.

Leaflet se distribuye con su licencia BSD-2-Clause y los mapas de OpenStreetMap conservan su atribución visible.

## Desarrollo

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para preparar el entorno, ejecutar validaciones y proponer cambios.

## Licencia

El código propio de esta integración se publica bajo licencia MIT. Los componentes de terceros incluidos conservan sus respectivas licencias.
