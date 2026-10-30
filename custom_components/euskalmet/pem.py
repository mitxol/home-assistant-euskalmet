"""Normalización de la clave privada PEM sin depender de Home Assistant."""

from __future__ import annotations

import re
import textwrap

_PEM_RE = re.compile(r"-----BEGIN ([A-Z0-9 ]+)-----(.*?)-----END \1-----", re.S)
_INVISIBLE = dict.fromkeys(map(ord, "﻿​‌‍⁠ "), " ")


def normalize_pem(raw: str) -> str:
    """Reconstruir una clave PEM aunque llegue pegada en una sola línea.

    Acepta la clave con saltos de línea perdidos o convertidos en espacios,
    con ``\\n`` literales, con caracteres invisibles del portapapeles o solo
    con el cuerpo en base64 (sin las líneas BEGIN/END).
    """

    text = raw.translate(_INVISIBLE).replace("\\n", "\n").strip()
    match = _PEM_RE.search(text)
    if match:
        label, body = match.group(1).strip(), match.group(2)
    else:
        label, body = "PRIVATE KEY", text

    body = re.sub(r"\s+", "", body)
    if not body:
        return text

    lines = "\n".join(textwrap.wrap(body, 64))
    return f"-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n"
