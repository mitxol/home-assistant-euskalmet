"""WebSocket para los resúmenes históricos diarios de Euskalmet."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN


@websocket_api.websocket_command(
    {
        vol.Required("type"): "euskalmet/history",
        vol.Optional("entry_id"): str,
        vol.Optional("station_id"): str,
        vol.Required("year"): vol.Coerce(int),
        vol.Required("month"): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
    }
)
@websocket_api.async_response
async def websocket_history(
    hass: HomeAssistant, connection: Any, msg: dict[str, Any]
) -> None:
    """Devolver los resúmenes diarios de un mes bajo demanda."""

    coordinators = hass.data.get(DOMAIN, {}).get("coordinators", {})
    entry_id = msg.get("entry_id")
    station_id = msg.get("station_id")
    if entry_id:
        coordinator = coordinators.get(entry_id)
    elif station_id:
        coordinator = next(
            (
                item
                for item in coordinators.values()
                if item.api.station_id == station_id
            ),
            None,
        )
    elif len(coordinators) == 1:
        coordinator = next(iter(coordinators.values()))
    else:
        coordinator = None
    if coordinator is None:
        connection.send_error(msg["id"], "entry_not_found", "Entrada no encontrada")
        return
    try:
        date = datetime(msg["year"], msg["month"], 1, tzinfo=coordinator.api.time_zone)
        document = await coordinator.api.get_aggregated_month_summary(date)
    except Exception as err:
        connection.send_error(msg["id"], "history_unavailable", str(err))
        return
    connection.send_result(
        msg["id"],
        {
            "station": coordinator.api.station_id,
            "year": msg["year"],
            "month": msg["month"],
            "items": [
                {
                    "measureType": item.get("measureType"),
                    "measureId": item.get("measureId"),
                    "dailySummaries": item.get("dailySummaries", []),
                }
                for item in document.get("items", [])
                if isinstance(item, dict)
            ],
        },
    )


def async_register_history_websocket(hass: HomeAssistant) -> None:
    """Registrar el comando histórico."""

    websocket_api.async_register_command(hass, websocket_history)
