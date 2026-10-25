# Chore Tracker

> **Personal project, vibe-coded.** This was built for one person's own Home Assistant setup, with no test suite and no guarantee of ongoing maintenance. Feel free to use or fork it, but treat it as a convenience script you're adopting, not a vetted/supported integration.

A tiny Home Assistant integration for tracking "how long since I last did X" chores, with two configurable thresholds (due / overdue) instead of just a single due date.

## What it does

- Add a **Chore** helper (Settings → Devices & Services → Helpers → "+ Create Helper" → Chore) with a Name, an icon, **Days Till Due**, and **Days Till Overdue**.
- That creates one sensor per chore. Its state is simply the number of days since it was last marked done — it persists across Home Assistant restarts with no separate `input_datetime` helper needed.
- A `sensor.chore_overview` entity is created automatically the first time you add a chore. Its state is the worst tier (`ok` / `due` / `overdue`) across every chore you've configured — handy for a single badge/chip somewhere in a dashboard.
- Call `chore.mark_done` (with `entity_id` pointed at a chore sensor) to reset it. A bundled Lovelace card (`custom:chore-card`) does this on tap.
- Edit a chore's thresholds later via its helper's "Configure" option — no need to delete and recreate it.

## Install

1. Add this repository to HACS as a custom repository (Integrations category), then install "Chore Tracker".
2. Restart Home Assistant.
3. Add the card resource: Settings → Dashboards → Resources → Add Resource → `/hacsfiles/chore/chore-card.js`, type **JavaScript Module**.
   - This step is manual because the card can only be auto-registered on storage-mode dashboards. If your dashboard is edited in YAML mode (like this project's `dashboard.yaml`), there's no way around adding the resource by hand once.
4. Settings → Devices & Services → Helpers → "+ Create Helper" → **Chore**.

## Using the card

```yaml
type: custom:chore-card
entity: sensor.water_fountain_filter
icon: mdi:water   # optional, overrides the chore's own icon just for this card
```

Tapping the card calls `chore.mark_done` for that entity immediately — no confirmation dialog.

## Entities

| Entity | State | Notable attributes |
|---|---|---|
| Chore sensor (one per chore) | Days since last done (integer) | `days_till_due`, `days_till_overdue`, `last_done`, `tier` (`ok`/`due`/`overdue`) |
| `sensor.chore_overview` | Worst tier across all chores (`ok`/`due`/`overdue`) | — |

## Service

`chore.mark_done` — target one or more chore entities; sets their "last done" time to now.

## Not included (by design, for now)

- No completion history/streak tracking — just the current last-done timestamp.
- No hour-based chores — everything is day-granularity for now.
- No per-group overview entities — `sensor.chore_overview` covers every chore you have.
- No automated test suite.
