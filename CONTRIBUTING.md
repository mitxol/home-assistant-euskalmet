# Contribuir

Gracias por ayudar a mejorar Euskalmet para Home Assistant.

## Antes de proponer un cambio

- Comprueba que no existe ya una incidencia equivalente.
- No incluyas claves privadas, JWT, correos ni otros datos personales.
- Conserva el comportamiento compatible de entidades e identificadores únicos.
- Mantén las atribuciones y licencias de componentes de terceros.

## Validación local

```bash
python -m compileall custom_components/euskalmet
python -m pytest
python -m ruff check custom_components tests
```

Las pull requests también se validan mediante HACS Action y Hassfest.

## Versionado

El proyecto utiliza versionado semántico. Durante la beta pueden producirse cambios antes de la primera versión estable.

## Marca y atribución

No se aceptarán cambios que utilicen el logotipo oficial de Euskalmet o símbolos institucionales del Gobierno Vasco como identidad principal del proyecto. Los recursos gráficos deberán ser originales y mantener claramente el carácter comunitario y no oficial de la integración.
