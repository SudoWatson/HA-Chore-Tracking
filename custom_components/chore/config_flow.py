"""Config flow for the Chore integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DAYS_TILL_DUE,
    CONF_DAYS_TILL_OVERDUE,
    CONF_ICON,
    CONF_IS_OVERVIEW,
    CONF_NAME,
    DEFAULT_ICON,
    DOMAIN,
    OVERVIEW_UNIQUE_ID,
)


def _days_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="days",
        )
    )


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Required(
                CONF_DAYS_TILL_DUE, default=defaults.get(CONF_DAYS_TILL_DUE, 7)
            ): _days_selector(),
            vol.Required(
                CONF_DAYS_TILL_OVERDUE,
                default=defaults.get(CONF_DAYS_TILL_OVERDUE, 10),
            ): _days_selector(),
            vol.Required(
                CONF_ICON, default=defaults.get(CONF_ICON, DEFAULT_ICON)
            ): selector.IconSelector(),
        }
    )


def _validate(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not user_input.get(CONF_NAME, "").strip():
        errors[CONF_NAME] = "name_required"
    due = user_input.get(CONF_DAYS_TILL_DUE)
    overdue = user_input.get(CONF_DAYS_TILL_OVERDUE)
    if due is not None and overdue is not None and overdue <= due:
        errors["base"] = "overdue_not_after_due"
    return errors


def _normalize(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_NAME: user_input[CONF_NAME].strip(),
        CONF_DAYS_TILL_DUE: int(user_input[CONF_DAYS_TILL_DUE]),
        CONF_DAYS_TILL_OVERDUE: int(user_input[CONF_DAYS_TILL_OVERDUE]),
        CONF_ICON: user_input[CONF_ICON],
    }


class ChoreConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle creation of a chore helper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                data = _normalize(user_input)
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_overview(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Create the singleton overview entry. Triggered internally, not user-facing."""
        await self.async_set_unique_id(OVERVIEW_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="Chore Overview", data={CONF_IS_OVERVIEW: True}
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        if config_entry.data.get(CONF_IS_OVERVIEW):
            return ChoreOverviewOptionsFlow(config_entry)
        return ChoreOptionsFlow(config_entry)


class ChoreOptionsFlow(config_entries.OptionsFlow):
    """Handle editing an existing chore helper."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                data = _normalize(user_input)
                self.hass.config_entries.async_update_entry(
                    self._entry, title=data[CONF_NAME], data=data
                )
                return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(user_input or dict(self._entry.data)),
            errors=errors,
        )


class ChoreOverviewOptionsFlow(config_entries.OptionsFlow):
    """The overview entry has nothing user-configurable."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return self.async_abort(reason="no_options")
