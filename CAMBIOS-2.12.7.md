# Euskalmet 2.12.7

## Correcciones

- Recupera las entidades de polen del registro de Home Assistant aunque su
  especie no aparezca en los últimos 60 días de datos. Evita que tras reiniciar
  queden como entidades restauradas sin disponible, conservando sus IDs y
  personalizaciones. Una especie omitida se muestra como cero únicamente si
  existe una muestra válida; sin muestra, su valor sigue siendo desconocido.
- Elimina del manifiesto las versiones fijadas de `PyJWT` y `cryptography`,
  bibliotecas incluidas en Home Assistant, para resolver los errores de
  requisitos detectados por hassfest. La autenticación JWT utiliza las
  bibliotecas proporcionadas por Home Assistant.

## Imágenes de marca

- Incluye únicamente el símbolo circular de Euskalmet en la carpeta local
  `brand`; no distribuye el logotipo completo con nombre y texto de la agencia.
- Sustituye el icono comunitario por el símbolo circular oficial de Euskalmet,
  en PNG de 256 y 512 píxeles con fondo exterior transparente.
- Home Assistant 2026.3 y posteriores admiten estas imágenes locales sin
  presentar un PR al repositorio Home Assistant Brands.
- Mantiene la identificación del proyecto como integración comunitaria no
  oficial.
