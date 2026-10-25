"""The Chore integration."""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_IS_OVERVIEW, DOMAIN, SERVICE_MARK_DONE

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

SERVICE_MARK_DONE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional("when"): cv.datetime,
    }
)

CARD_URL_BASE = "/chore_tracker_frontend"
CARD_JS_PATH = f"{CARD_URL_BASE}/chore-card.js"
CARD_JS_URL = f"{CARD_JS_PATH}?v=5"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {"chores": {}})

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_BASE, str(Path(__file__).parent / "www"), cache_headers=False
            )
        ]
    )
    await _async_register_lovelace_resource(hass)

    async def handle_mark_done(call: ServiceCall) -> None:
        entity_ids = set(call.data[ATTR_ENTITY_ID])
        when = call.data.get("when")
        for sensor in hass.data[DOMAIN]["chores"].values():
            if sensor.entity_id in entity_ids:
                await sensor.async_mark_done(when)

    hass.services.async_register(
        DOMAIN, SERVICE_MARK_DONE, handle_mark_done, schema=SERVICE_MARK_DONE_SCHEMA
    )
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Best-effort: register chore-card.js in Lovelace's resources collection.

    This relies on an internal, undocumented Home Assistant API that has
    already changed shape across versions (e.g. LovelaceData.resource_mode
    was renamed/removed in some 2025.11 builds). Any failure here is logged
    and swallowed - it must never prevent the rest of the integration
    (sensors, services) from setting up.
    """
    try:
        from homeassistant.components.lovelace import LOVELACE_DATA

        lovelace = hass.data.get(LOVELACE_DATA)
        if lovelace is None:
            raise LookupError("Lovelace data not found in hass.data")

        mode = getattr(lovelace, "resource_mode", getattr(lovelace, "mode", "yaml"))
        if mode != "storage":
            raise LookupError(f"Lovelace resources are in '{mode}' mode")

        resources = lovelace.resources
        await resources.async_get_info()  # ensures the collection is loaded from disk
        existing = next(
            (
                r
                for r in resources.async_items()
                if r["url"].split("?")[0] == CARD_JS_PATH
            ),
            None,
        )
        if existing is None:
            await resources.async_create_item(
                {"res_type": "module", "url": CARD_JS_URL}
            )
        elif existing["url"] != CARD_JS_URL:
            await resources.async_update_item(
                existing["id"], {"res_type": "module", "url": CARD_JS_URL}
            )
    except Exception:  # noqa: BLE001 - internal HA API, must never break setup
        _LOGGER.warning(
            "Could not auto-register the chore-card resource; add %s as a "
            "dashboard resource manually.",
            CARD_JS_URL,
            exc_info=True,
        )


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
