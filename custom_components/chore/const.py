"""Constants for the Chore integration."""

DOMAIN = "chore"

CONF_NAME = "name"
CONF_DAYS_TILL_DUE = "days_till_due"
CONF_DAYS_TILL_OVERDUE = "days_till_overdue"
CONF_ICON = "icon"
CONF_IS_OVERVIEW = "is_overview"

DEFAULT_ICON = "mdi:checkbox-marked-circle-outline"

ATTR_DAYS_TILL_DUE = "days_till_due"
ATTR_DAYS_TILL_OVERDUE = "days_till_overdue"
ATTR_LAST_DONE = "last_done"
ATTR_TIER = "tier"

STATE_OK = "ok"
STATE_DUE = "due"
STATE_OVERDUE = "overdue"

SERVICE_MARK_DONE = "mark_done"

OVERVIEW_UNIQUE_ID = "chore_overview"
SIGNAL_CHORE_UPDATED = "chore_tracker_chore_updated"
