from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, RADAR_BOUNDS


@websocket_api.websocket_command(
    {
        vol.Required("type"): "euskalmet/radar_frames",
        vol.Optional("entry_id"): str,
        vol.Optional("index"): vol.Coerce(int),
    }
)
@callback
def websocket_radar_frames(
    hass: HomeAssistant,
    connection: Any,
    msg: dict[str, Any],
) -> None:
    """Listar fotogramas o devolver un PNG codificado en Base64."""

    coordinators = (
        hass.data.get(DOMAIN, {}).get("coordinators", {})
    )
    entry_id = msg.get("entry_id")

    if entry_id:
        coordinator = coordinators.get(entry_id)
    elif len(coordinators) == 1:
        coordinator = next(iter(coordinators.values()))
    else:
        coordinator = None

    if coordinator is None:
        connection.send_error(
            msg["id"],
            "entry_not_found",
            "No se encontro la entrada de Euskalmet",
        )
        return

    radar = (coordinator.data or {}).get("radar", {})
    frames = radar.get("frames") or []
    requested_index = msg.get("index")

    if requested_index is None:
        connection.send_result(
            msg["id"],
            {
                "entry_id": coordinator.config_entry_id,
                "count": len(frames),
                "bounds": RADAR_BOUNDS,
                "frames": [
                    {
                        "index": index,
                        "range": frame.get("range"),
                        "timestamp": frame.get("timestamp"),
                    }
                    for index, frame in enumerate(frames)
                ],
            },
        )
        return

    if requested_index < 0 or requested_index >= len(frames):
        connection.send_error(
            msg["id"],
            "frame_not_found",
            "El fotograma solicitado no existe",
        )
        return

    frame = frames[requested_index]
    content = frame.get("content")

    if not isinstance(content, str) or not content:
        connection.send_error(
            msg["id"],
            "frame_unavailable",
            "El contenido del fotograma no esta disponible",
        )
        return

    connection.send_result(
        msg["id"],
        {
            "index": requested_index,
            "content_type": "image/png",
            "image": content,
        },
    )


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Registrar los comandos WebSocket de radar una sola vez."""

    websocket_api.async_register_command(
        hass,
        websocket_radar_frames,
    )
