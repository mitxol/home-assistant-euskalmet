# Publicación inicial en GitHub y HACS

Este documento presupone:

- usuario de GitHub: `mitxol`;
- repositorio: `home-assistant-euskalmet`;
- rama principal: `main`;
- primera versión: `2.9.0-beta.1`.

Cambia estos valores antes de publicar si no son los definitivos.

## 1. Crear el repositorio

Crea en GitHub un repositorio público vacío llamado `home-assistant-euskalmet`.
No añadas README, licencia ni `.gitignore` desde GitHub porque ya están incluidos.

Configura:

- Description: `Integración comunitaria no oficial de Euskalmet para Home Assistant: estaciones, previsión, avisos, radar e históricos.`
- Topics: `home-assistant`, `hacs`, `euskalmet`, `weather`, `basque-country`.
- Issues: activado.
- Private vulnerability reporting: recomendado.

## 2. Primer envío

Desde la raíz del proyecto:

```bash
git init
git branch -M main
git add .
git commit -m "Prepare Euskalmet 2.9.0-beta.1 for HACS"
git remote add origin https://github.com/mitxol/home-assistant-euskalmet.git
git push -u origin main
```

## 3. Revisar GitHub Actions

Espera a que terminen:

- Validate with HACS;
- Validate with hassfest;
- Python checks.

No publiques la release mientras alguna validación esté en rojo.

## 4. Probar como repositorio personalizado

En HACS:

1. Abre Integraciones.
2. Menú de tres puntos > Repositorios personalizados.
3. Añade `https://github.com/mitxol/home-assistant-euskalmet`.
4. Selecciona `Integration`.
5. Instala Euskalmet.
6. Reinicia Home Assistant.

## 5. Publicar la beta

Cuando las validaciones estén en verde:

```bash
git tag -a 2.9.0-beta.1 -m "Euskalmet 2.9.0-beta.1"
git push origin 2.9.0-beta.1
```

Después crea una Release de GitHub usando esa etiqueta. Marca la release como **pre-release** y utiliza como notas la sección correspondiente de `CHANGELOG.md`.

## 6. Identidad visual

No utilices el logotipo oficial de Euskalmet ni los símbolos institucionales del Gobierno Vasco como icono de la integración, avatar del repositorio o marca de HACS. Euskalmet ha indicado expresamente que su uso como identidad principal podría generar confusión sobre la autoría o el soporte oficial.

La integración debe utilizar un logotipo comunitario propio. Puede incorporar elementos meteorológicos, radar, paisaje o referencias culturales como la ikurriña, siempre que el diseño sea original y no imite una marca institucional ni sugiera respaldo oficial.

Cuando el logotipo comunitario esté terminado, los recursos de marca podrán añadirse en:

```text
custom_components/euskalmet/brand/
```

El logotipo oficial de Euskalmet solo podrá mostrarse dentro de la documentación, en la sección de procedencia de los datos y acompañado de una atribución clara.
