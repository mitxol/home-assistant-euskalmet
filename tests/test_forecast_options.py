"""Exercise real API/flow code with a small Home Assistant boundary adapter.

The repository's unit suite does not install Home Assistant. Network calls are
mocked and only the framework's flow/selector interfaces are replaced here.
"""

import asyncio
import importlib
import sys
from datetime import UTC
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import voluptuous as vol

SOURCE = Path(__file__).parents[1] / "custom_components" / "euskalmet"
CHOICE = "basque_country/donostialdea/errenteria"
LOCATIONS = [
    {"region": "basque_country", "zone": "donostialdea", "location": "donostia"},
    {"region": "basque_country", "zone": "donostialdea", "location": "errenteria"},
]


class FlowBoundary:
    """Return flow results while leaving all selection/error logic under test."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def add_suggested_values_to_schema(self, schema, values):
        self.suggested_values = values
        return schema


class SelectBoundary:
    def __init__(self, config):
        self.options = config["options"]

    def __call__(self, value):
        return vol.In([option["value"] for option in self.options])(value)


@pytest.fixture
def integration(monkeypatch):
    def install(name, **values):
        module = ModuleType(name)
        module.__dict__.update(values)
        monkeypatch.setitem(sys.modules, name, module)
        return module

    entries = install(
        "homeassistant.config_entries", ConfigFlow=FlowBoundary,
        OptionsFlowWithReload=FlowBoundary, ConfigEntry=SimpleNamespace,
        ConfigFlowResult=dict,
    )
    install("homeassistant", __path__=[], config_entries=entries)
    install("homeassistant.core", callback=lambda function: function)
    install("homeassistant.helpers", __path__=[])
    install(
        "homeassistant.helpers.aiohttp_client",
        async_get_clientsession=lambda hass: hass.session,
    )
    install(
        "homeassistant.helpers.selector", SelectOptionDict=dict,
        SelectSelector=SelectBoundary, SelectSelectorConfig=dict,
        TextSelector=lambda config: str, TextSelectorConfig=dict,
        TextSelectorType=SimpleNamespace(EMAIL="email"),
    )
    dt = install("homeassistant.util.dt", get_default_time_zone=lambda: UTC)
    install("homeassistant.util", __path__=[], dt=dt)
    package = "euskalmet_forecast_test"
    install(package, __path__=[str(SOURCE)])
    try:
        yield importlib.import_module(package + ".config_flow")
    finally:
        for name in list(sys.modules):
            if name.startswith(package + "."):
                monkeypatch.delitem(sys.modules, name)


def make_flow(integration):
    flow = integration.EuskalmetOptionsFlow()
    flow.hass = SimpleNamespace(config=SimpleNamespace(language="es"), session=object())
    flow.config_entry = SimpleNamespace(
        data={
            "email": "test@example.invalid", "private_key": "unused-mocked-key",
            "station_id": "C017", "station_name": "Miramon",
            "region": "basque_country", "zone": "donostialdea",
            "location": "donostia", "alert_zone": "GIPUZKOA_COAST",
        },
        options={"existing_option": True},
    )
    return flow


def test_catalog_uses_official_identifiers_and_skips_invalid_rows(integration):
    api = integration.EuskalmetAPI(object(), "test@example.invalid", "unused-key")
    api.get_regions = AsyncMock(return_value=[{}, {"regionId": "basque_country"}])
    api.get_zones = AsyncMock(return_value=[{}, {"regionZoneId": "donostialdea"}])
    api.get_locations = AsyncMock(return_value=[
        {}, {"regionZoneLocationId": "donostia"},
        {"regionZoneLocationId": "errenteria"},
    ])
    assert asyncio.run(api.get_forecast_locations()) == LOCATIONS
    api.get_zones.assert_awaited_once_with("basque_country")
    api.get_locations.assert_awaited_once_with("basque_country", "donostialdea")


def test_flow_uses_server_credentials_without_putting_them_in_options(
    integration, monkeypatch
):
    catalog = AsyncMock(return_value=LOCATIONS)
    monkeypatch.setattr(integration.EuskalmetAPI, "get_forecast_locations", catalog)
    flow = make_flow(integration)
    before = dict(flow.config_entry.data)
    result = asyncio.run(flow.async_step_init())
    assert result["type"] == "form"
    assert result["errors"] == {}
    assert flow.suggested_values == {"forecast_location": "station"}
    assert result["data_schema"]({"forecast_location": CHOICE}) == {
        "forecast_location": CHOICE
    }
    saved = asyncio.run(flow.async_step_init({"forecast_location": CHOICE}))
    assert saved["data"] == {"existing_option": True, "forecast_location": CHOICE}
    assert flow.config_entry.data == before
    catalog.assert_awaited_once()


@pytest.mark.parametrize("selected", ["other/zone/town", [], None])
def test_unknown_municipality_is_rejected_without_saving_options(integration, selected):
    flow = make_flow(integration)
    flow._locations = LOCATIONS
    result = asyncio.run(flow.async_step_init({"forecast_location": selected}))
    assert result["type"] == "form"
    assert result["errors"] == {"forecast_location": "location_not_available"}
    assert flow.config_entry.options == {"existing_option": True}


def test_saved_choice_is_suggested_and_automatic_mode_can_be_restored(integration):
    flow = make_flow(integration)
    flow._locations = LOCATIONS
    flow.config_entry.options["forecast_location"] = CHOICE
    asyncio.run(flow.async_step_init())
    assert flow.suggested_values["forecast_location"] == CHOICE
    result = asyncio.run(flow.async_step_init({"forecast_location": "station"}))
    assert result["data"]["forecast_location"] == "station"


@pytest.mark.parametrize("error_name, expected", [
    ("EuskalmetAuthenticationError", "invalid_auth"),
    ("EuskalmetConnectionError", "cannot_connect"),
])
def test_catalog_errors_preserve_existing_settings_and_allow_retry(
    integration, monkeypatch, error_name, expected
):
    catalog = AsyncMock(
        side_effect=[getattr(integration, error_name)("test"), LOCATIONS]
    )
    monkeypatch.setattr(integration.EuskalmetAPI, "get_forecast_locations", catalog)
    flow = make_flow(integration)
    result = asyncio.run(flow.async_step_init())
    assert result["errors"] == {"base": expected}
    assert flow.config_entry.options == {"existing_option": True}
    result = asyncio.run(flow.async_step_init({}))
    assert result["errors"] == {}
    assert result["type"] == "form"


def test_empty_catalog_does_not_silently_change_the_current_municipality(
    integration, monkeypatch
):
    monkeypatch.setattr(
        integration.EuskalmetAPI, "get_forecast_locations", AsyncMock(return_value=[])
    )
    flow = make_flow(integration)
    result = asyncio.run(flow.async_step_init())
    assert result["errors"] == {"base": "no_forecast_locations"}
    assert flow.config_entry.data["location"] == "donostia"
    assert flow.config_entry.options == {"existing_option": True}
