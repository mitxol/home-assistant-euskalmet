# Euskalmet para Home Assistant

Integración comunitaria de Home Assistant para consultar datos meteorológicos
de Euskalmet y Open Data Euskadi.

> [!IMPORTANT]
> **Proyecto comunitario no oficial.** No está afiliado, patrocinado,
> mantenido ni soportado por Euskalmet ni por el Gobierno Vasco. Comunica los
> problemas mediante los **Issues de este repositorio**, no mediante los
> canales de soporte de Euskalmet.

> [!NOTE]
> **Desarrollo asistido por inteligencia artificial.** Este proyecto se ha
> creado y revisado con una ayuda significativa de herramientas de IA. El
> mantenimiento, las decisiones funcionales y las pruebas corresponden al
> responsable del repositorio. Si encuentras un error, puedes comunicarlo
> mediante un Issue para que pueda revisarse.

> [!NOTE]
> El radar animado utiliza una adaptación de la tarjeta de HACS
> [Weather Radar Card](https://github.com/jpettitt/weather-radar-card), creada
> por su comunidad y publicada bajo licencia MIT. La adaptación añade Euskalmet
> como fuente de datos; no convierte esta integración en un proyecto oficial de
> Euskalmet ni de Weather Radar Card.

> Versión `2.12.8`. [Cambios de esta versión](CAMBIOS-2.12.8.md).

## Funciones

- Configuración completa desde la interfaz de Home Assistant.
- Selección de estaciones meteorológicas oficiales activas.
- Sensores dinámicos para las magnitudes publicadas por cada estación.
- Temperatura, humedad, presión, viento, racha, dirección, radiación y
  precipitación.
- Entidad meteorológica con condiciones actuales y previsión horaria y diaria.
- Avisos meteorológicos filtrados para la zona de la estación.
- Radar animado de Kapildui sobre un mapa base claro y sin claves externas.
- Resúmenes diarios, mensuales y anuales en un dispositivo estadístico separado.
- Histórico consultado bajo demanda, sin importar datos antiguos a Recorder.
- Caché y endpoints agregados para reducir el número de peticiones a la API.
- Conservación del último valor válido ante respuestas temporales incompletas.
- Recuento total y sensores dinámicos por tipo polínico.
- Recuperación de especies de polen ya registradas aunque dejen de aparecer
  en la ventana de datos de 60 días, sin perder sus entidades al reiniciar.
- Calendario astronómico oficial con Sol, Luna y mareas de Pasaia.
- Previsión marítima del Cantábrico con oleaje, temperatura y visibilidad.
- Interfaz disponible en castellano y euskera según el idioma de Home Assistant.

## Vista previa

| Mar, estadísticas y polen | Radar, histórico y observaciones |
| --- | --- |
| ![Dispositivos marítimo, estadístico y de polen de Euskalmet en euskera](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/mar-estadisticas-polen-eu.png) | ![Panel de Euskalmet en euskera con radar, histórico, avisos y observaciones](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/radar-historico-observaciones-eu.png) |

La entidad meteorológica ofrece previsión diaria y horaria desde el diálogo
nativo de Home Assistant. La interfaz adapta automáticamente los textos al
idioma general de la instalación:

| Previsión diaria | Previsión horaria |
| --- | --- |
| ![Previsión diaria de Euskalmet en euskera](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/prevision-diaria.png) | ![Previsión horaria de Euskalmet en euskera](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/prevision-horaria.png) |

Los resúmenes diarios, mensuales y anuales se agrupan en un dispositivo
estadístico independiente. El polen se muestra en otro dispositivo con la
captadora oficial más próxima a la estación meteorológica:

![Resúmenes, estadísticas y polen de Euskalmet en euskera](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/resumenes-polen-eu.png)

## Requisitos

1. Home Assistant `2026.8.0` o posterior.
2. HACS para la instalación recomendada.
3. Credenciales personales de acceso a la API de Euskalmet: correo electrónico
   y clave privada (privatekey.pem).

### Obtener las credenciales de Open Data Euskadi

Las credenciales se solicitan en el
[portal de claves de Open Data Euskadi](https://api.euskadi.eus/opendata-apikey#/):

1. Pulsa **Registrarse** y completa el formulario.
2. Activa la cuenta desde el enlace incluido en el correo electrónico que
   recibirás.
3. Accede al portal y descarga el archivo ZIP con las claves. Para configurar
   la integración necesitarás el correo electrónico registrado y el archivo
   `privatekey.pem` incluido en el ZIP.

> **Nota sobre el registro:** actualmente puede haber problemas para recibir el
> correo de confirmación necesario para activar una cuenta. Mientras se
> resuelven, puede utilizarse la opción de registro con Google, con una cuenta
> que no esté pendiente de activación.

![Acceso y registro en Open Data Euskadi](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/registro-opendata-euskadi.png)

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

El asistente solicita las credenciales:

- **Correo electrónico**: el mismo con el que te registraste en Open Data
  Euskadi, ya que va firmado dentro del token.
- **Clave privada**: abre `privatekey.pem` con un editor de texto y pega su
  contenido en el campo. Lo ideal es pegarlo completo, con las líneas
  `-----BEGIN PRIVATE KEY-----` y `-----END PRIVATE KEY-----`.

No hace falta cuidar el formato al pegar la clave: si se pega desde el móvil y
llega en una sola línea, con espacios en lugar de saltos de línea o con
caracteres invisibles del portapapeles, la integración la reconstruye. También
vale pegar solo el bloque central, sin las líneas BEGIN y END. Si aun así la
clave no se puede leer, el formulario lo indica bajo el campo.

Después, el asistente muestra las estaciones meteorológicas activas con los
sensores que tienen disponibles (no todas las estaciones tienen todos los
sensores). Cada estación se configura como una entrada independiente.
La integración crea dispositivos separados para las observaciones actuales,
resúmenes y estadísticas, polen y previsión marítima. El dispositivo marítimo
agrupa también el calendario solar y lunar y las mareas astronómicas de Pasaia.
La captadora de Bilbao, Vitoria-Gasteiz o Donostia / San Sebastián se elige
automáticamente por proximidad a la estación meteorológica.

Solo se crean entidades para las magnitudes publicadas por la estación.
Los tipos polínicos aparecen como entidades cuando la API los publica. Los
datos proceden del Departamento de Salud, tienen periodicidad semanal y
exponen la fecha efectiva de la muestra en el atributo `observed_on`.

### Calendario astronómico

El dispositivo marítimo consulta una vez al día el calendario oficial de
Euskalmet y publica:

- Salida de la Luna.
- Puesta de la Luna.
- Fase lunar.

También crea las entidades de salida y puesta del Sol, pero quedan desactivadas
por defecto porque Home Assistant ya calcula esos horarios para las coordenadas
exactas de la vivienda. Pueden activarse desde la página del dispositivo.

Astro es una fuente opcional: si el endpoint falla temporalmente, la integración
conserva el último calendario válido y continúa actualizando observaciones,
previsión, avisos, radar, resúmenes y polen.

### Previsión marítima

El dispositivo **Euskalmet - Mar Cantábrico** consulta el endpoint oficial
Ocean Forecast y publica:

- Fecha y textos bilingües de la previsión marítima.
- Altura prevista de las olas.
- Temperatura del agua.
- Visibilidad mínima y máxima.

Es una previsión general de la costa vasca y no una medición de la estación
meteorológica seleccionada. Se actualiza cada dos horas, conserva el último
pronóstico válido y no interrumpe las demás fuentes si el servicio no está
disponible.

La visibilidad se publica en kilómetros. La API de producción etiqueta
actualmente el intervalo como metros, pero la página marítima oficial confirma
que valores como `4–10` corresponden a kilómetros.

El mismo dispositivo añade las mareas astronómicas de referencia de Pasaia:

- Estado de la marea: subiendo o bajando.
- Próxima pleamar y su altura.
- Próxima bajamar y su altura.

Se descargan hoy y mañana cada seis horas. La integración interpreta los campos
de producción `phase`, `time` y `high` y conserva también la respuesta original
en el atributo `raw_tides` para diagnóstico.

### Frecuencias de actualización

La integración conserva una caché independiente para cada fuente y evita
consultar con la misma frecuencia datos que cambian lentamente:

- Mediciones actuales y radar: cada 5 minutos.
- Resumen del día y avisos meteorológicos: cada 15 minutos.
- Predicción horaria y resumen mensual: cada hora.
- Predicción diaria: cada 2 horas.
- Previsión marítima: cada 2 horas.
- Mareas de Pasaia: cada 6 horas.
- Polen: cada 6 horas.
- Calendario astronómico: una vez al día.

Si una fuente opcional falla se conserva su último valor válido y el siguiente
intento respeta el intervalo correspondiente. Las observaciones actuales siguen
siendo la única fuente imprescindible para considerar correcta una actualización.

## Tarjetas

Los archivos JavaScript se sirven desde la propia integración. Añade los
recursos que vayas a utilizar en **Ajustes > Paneles de control > menú de tres
puntos > Recursos**, con tipo **Módulo JavaScript**:

```text
/euskalmet_static/euskalmet-history-card.js?v=4
/euskalmet_static/weather-radar-card-euskalmet.js?v=6
/euskalmet_static/euskalmet-alert-card.js?v=2
```

La adaptación registra `custom:weather-radar-card-euskalmet`, por lo que puede
coexistir con la tarjeta original `custom:weather-radar-card` si también la
utilizas con otras fuentes.

Las revisiones de la URL pertenecen a cada archivo JavaScript, no a la versión
de la integración. No hay que modificarlas en cada actualización: solamente
cambiarán cuando se publique una revisión real de la tarjeta. Debe existir una
sola URL por tarjeta; elimina la revisión anterior al actualizarla. Después del
cambio, cierra y vuelve a abrir la aplicación móvil o fuerza una recarga
completa del navegador.

### Radar animado

```yaml
type: custom:weather-radar-card-euskalmet
data_source: Euskalmet
map_style: OSM
radar_opacity: 1
past_minutes: 360
show_color_bar: false
zoom_level: 7
center_latitude: zone.home
center_longitude: zone.home
```

Estilos de mapa disponibles en `map_style`. Ninguno necesita clave ni muestra
marcas de agua:

| Valor | Mapa base |
| --- | --- |
| `Auto` / `OSM` | OpenStreetMap a color, con nombres en castellano y euskera |
| `Voyager` | Topográfico de Esri, con relieve |
| `Light` | Gris claro de Esri, muy neutro para resaltar la lluvia |
| `Dark` | Gris oscuro de Esri, pensado para temas oscuros |
| `Satellite` | Imagen de satélite de Esri con nombres de lugares |

La tarjeta obtiene los fotogramas autenticados a través de la integración. No
expone las credenciales de Euskalmet al navegador. La capa utiliza los límites
geográficos publicados por el visor oficial de Kapildui y permanece anclada al
mapa al desplazarlo, ampliarlo, reproducirlo o pausarlo.

El centro se fija en `zone.home` para que el mapa no siga automáticamente la
ubicación del teléfono cuando se visualiza desde un dispositivo móvil.

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
de larga duración de Home Assistant. El selector de mes permite abrir
directamente cualquier periodo sin recorrer los meses uno a uno. El gráfico
ofrece información detallada por día, escalas adaptativas y una leyenda
interactiva; la precipitación se muestra mediante barras y el resto de
magnitudes mediante líneas.

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

Añade este recurso JavaScript desde **Ajustes > Paneles de control > Recursos**:

```text
/euskalmet_static/euskalmet-alert-card.js?v=2
```

Después añade la tarjeta:

```yaml
type: custom:euskalmet-alert-card
entity: sensor.arkauti_nivel_de_aviso
```

La tarjeta adapta automáticamente sus textos al castellano o al euskera y
muestra cada riesgo activo con su descripción. Cada instalación puede asignar
un ID distinto; copia el ID del sensor «Nivel de aviso» desde sus ajustes y
sustituye el del ejemplo si fuese necesario.

![Aviso meteorológico activo de Euskalmet mostrado en euskera](https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/docs/images/aviso-meteorologico-activo-eu.png)

## Actualización y tolerancia a fallos

Las observaciones actuales se consultan mediante el endpoint agregado diario
recomendado por Euskalmet. Previsión, avisos, radar, resúmenes y polen se
tratan como fuentes opcionales: un fallo temporal de una fuente no impide
actualizar las demás. El polen se consulta cada seis horas y conserva el
último dato válido.

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
2. Comprueba que las credenciales continúan vigentes. Si aparece el error **La clave
   privada no es válida**, copia de nuevo el contenido de `privatekey.pem` desde
   el archivo descargado, no desde un correo o un mensaje reenviado.
3. Actualiza el parámetro `?v=` de los recursos JavaScript.
4. Fuerza una recarga completa o prueba en una ventana privada.
5. Indica las versiones de Home Assistant y de la integración y adjunta los
   registros relevantes, sin claves privadas.

## Fuente de datos, marca y atribuciones

<p align="center">
  <img src="https://raw.githubusercontent.com/mitxol/home-assistant-euskalmet/main/custom_components/euskalmet/brand/icon.png" alt="Símbolo de Euskalmet, fuente de datos de esta integración comunitaria" width="128">
</p>

**Datos meteorológicos proporcionados por Euskalmet — Agencia Vasca de
Meteorología**, a través de Euskalmet y Open Data Euskadi.

El símbolo circular oficial se reproduce para atribuir la procedencia de los
datos, con la autorización indicada por Euskalmet. Se usa
como icono para identificar la fuente de datos y no implica afiliación,
patrocinio, mantenimiento ni soporte oficial de esta integración comunitaria.

La integración incluye únicamente el símbolo circular de la fuente de datos
en `custom_components/euskalmet/brand/`. Desde Home Assistant 2026.3,
Home Assistant utiliza estas imágenes locales sin necesitar una solicitud al
repositorio Home Assistant Brands.

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
