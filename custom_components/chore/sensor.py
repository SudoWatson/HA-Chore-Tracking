"""Sensor platform for the Chore integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DAYS_TILL_DUE,
    ATTR_DAYS_TILL_OVERDUE,
    ATTR_LAST_DONE,
    ATTR_TIER,
    CONF_DAYS_TILL_DUE,
    CONF_DAYS_TILL_OVERDUE,
    CONF_ICON,
    CONF_IS_OVERVIEW,
    CONF_NAME,
    DOMAIN,
    SIGNAL_CHORE_UPDATED,
    STATE_DUE,
    STATE_OK,
    STATE_OVERDUE,
)

REFRESH_INTERVAL = timedelta(minutes=30)


def _tier(days_since: int, days_till_due: int, days_till_overdue: int) -> str:
    if days_since >= days_till_overdue:
        return STATE_OVERDUE
    if days_since >= days_till_due:
        return STATE_DUE
    return STATE_OK


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry.data.get(CONF_IS_OVERVIEW):
        async_add_entities([ChoreOverviewSensor(entry)])
        return

    sensor = ChoreSensor(entry)
    hass.data[DOMAIN]["chores"][entry.entry_id] = sensor
    async_add_entities([sensor])


class ChoreSensor(RestoreEntity, SensorEntity):
    """Tracks the number of days since a chore was last done."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "d"
    _attr_device_class = SensorDeviceClass.DURATION

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data[CONF_NAME]
        self._attr_icon = entry.data.get(CONF_ICON)
        self._last_done: datetime | None = None

    @property
    def days_till_due(self) -> int:
        return self._entry.data[CONF_DAYS_TILL_DUE]

    @property
    def days_till_overdue(self) -> int:
        return self._entry.data[CONF_DAYS_TILL_OVERDUE]

    @property
    def native_value(self) -> int:
        if self._last_done is None:
            return 0
        return max((dt_util.utcnow() - self._last_done).days, 0)

    @property
    def tier(self) -> str:
        return _tier(self.native_value, self.days_till_due, self.days_till_overdue)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_DAYS_TILL_DUE: self.days_till_due,
            ATTR_DAYS_TILL_OVERDUE: self.days_till_overdue,
            ATTR_LAST_DONE: self._last_done.isoformat() if self._last_done else None,
            ATTR_TIER: self.tier,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.attributes.get(ATTR_LAST_DONE):
            self._last_done = dt_util.parse_datetime(
                last_state.attributes[ATTR_LAST_DONE]
            )
        if self._last_done is None:
            self._last_done = dt_util.utcnow()

        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._handle_refresh, REFRESH_INTERVAL
            )
        )
        async_dispatcher_send(self.hass, SIGNAL_CHORE_UPDATED)

    async def async_will_remove_from_hass(self) -> None:
        self.hass.data[DOMAIN]["chores"].pop(self._entry.entry_id, None)
        async_dispatcher_send(self.hass, SIGNAL_CHORE_UPDATED)

    @callback
    def _handle_refresh(self, _now: datetime) -> None:
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_CHORE_UPDATED)

    async def async_mark_done(self) -> None:
        self._last_done = dt_util.utcnow()
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_CHORE_UPDATED)


class ChoreOverviewSensor(SensorEntity):
    """Reports the worst tier across every configured chore."""

    _attr_should_poll = False
    _attr_name = "Chore Overview"
    _attr_icon = "mdi:format-list-checks"

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_unique_id = entry.entry_id
        self._attr_native_value = STATE_OK

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_CHORE_UPDATED, self._recompute)
        )
        self._recompute()

    @callback
    def _recompute(self) -> None:
        tiers = {sensor.tier for sensor in self.hass.data[DOMAIN]["chores"].values()}
        if STATE_OVERDUE in tiers:
            worst = STATE_OVERDUE
        elif STATE_DUE in tiers:
            worst = STATE_DUE
        else:
            worst = STATE_OK

        if worst != self._attr_native_value:
            self._attr_native_value = worst
            self.async_write_ha_state()
