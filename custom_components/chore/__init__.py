"""The Chore integration."""
from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_IS_OVERVIEW, DOMAIN, SERVICE_MARK_DONE

PLATFORMS = [Platform.SENSOR]

SERVICE_MARK_DONE_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})

CARD_URL_BASE = "/chore_tracker_frontend"
CARD_JS_URL = f"{CARD_URL_BASE}/chore-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {"chores": {}})

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_BASE, str(Path(__file__).parent / "www"), cache_headers=False
            )
        ]
    )
    add_extra_js_url(hass, CARD_JS_URL)

    async def handle_mark_done(call: ServiceCall) -> None:
        entity_ids = set(call.data[ATTR_ENTITY_ID])
        for sensor in hass.data[DOMAIN]["chores"].values():
            if sensor.entity_id in entity_ids:
                await sensor.async_mark_done()

    hass.services.async_register(
        DOMAIN, SERVICE_MARK_DONE, handle_mark_done, schema=SERVICE_MARK_DONE_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {"chores": {}})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not entry.data.get(CONF_IS_OVERVIEW):
        _ensure_overview_entry(hass)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


@callback
def _ensure_overview_entry(hass: HomeAssistant) -> None:
    has_overview = any(
        entry.data.get(CONF_IS_OVERVIEW)
        for entry in hass.config_entries.async_entries(DOMAIN)
    )
    if not has_overview:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "overview"}
            )
        )
