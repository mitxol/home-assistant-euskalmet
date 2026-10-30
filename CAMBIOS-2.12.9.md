# Euskalmet 2.12.9

## Correcciones

- La clave privada se acepta aunque se pegue en una sola línea, por ejemplo
  desde el móvil. La integración reconstruye las líneas `BEGIN`/`END` y el
  formato PEM, y quita espacios, `\n` literales y caracteres invisibles del
  portapapeles. También vale pegar solo el cuerpo de la clave.
- Las instalaciones ya configuradas con una clave mal pegada empiezan a
  funcionar sin tener que reconfigurar la integración.

## Novedades

- El campo de la clave privada es ahora multilínea, en la configuración y en
  la reautenticación.
- Si la clave no se puede leer, el formulario muestra un error específico
  bajo el campo en lugar de un error genérico.
