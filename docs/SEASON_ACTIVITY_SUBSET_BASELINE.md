# Season Activity Subset Baseline

## 1. Purpose

This document defines the next local runtime slice after field binding.

The goal of this slice is to stop treating fertilizer and yield confirmation as session-only data and start writing canonical seasonal activity rows into SQLite.

## 2. Scope

This slice covers:

- current project season resolution
- optional field-scoped season resolution when a binding exists
- seasonal event creation for structured chat input
- fertilizer canonical write
- yield canonical write
- minimal field binding resolution for canonical write

This slice does not yet cover:

- reminder scheduling and delivery
- input-resolution session persistence
- evidence submission and validation
- admin review flows for seasonal activity records

## 3. Runtime Rules

- A confirmed fertilizer input must create a canonical fertilizer activity row when SQLite runtime is enabled.
- A confirmed yield input must create a canonical yield activity row when SQLite runtime is enabled.
- The runtime must resolve the current project season from the confirmed activity date.
- If exactly one active field binding exists, the runtime may attach the activity to that field automatically.
- If multiple bindings exist, the runtime must not guess from nothing.
- Yield input may use the typed field text as a narrow matching hint against active bindings.
- Field linkage ambiguity must be preserved as structured metadata rather than silently discarded.

## 4. Season Resolution Rules

- The local runtime uses calendar-year season resolution as the baseline.
- A project season is unique per project and season year.
- A field season is unique per project season and active field binding.
- Seasonal event rows are append-only activity context rows and are not treated as mutable drafts.

## 5. Canonical Write Rules

- Canonical rows are created only after confirm.
- Session draft data is not the source of truth after canonical write succeeds.
- Canonical rows should preserve:
  - participant context
  - project context
  - optional field context
  - optional field-season context
  - seasonal event context
  - original structured values entered by the user
  - field binding resolution metadata

## 6. Field Binding Resolution Levels

- `single_active_binding`
- `matched_field_text`
- `unresolved_no_active_binding`
- `unresolved_multiple_active_bindings`

These levels are storage metadata, not user-facing labels.

## 7. Bot Behavior

- The bot continues to use the current guided structured flow.
- Confirmation UX stays rule-first.
- SQLite write happens behind the existing confirm step.
- If SQLite runtime is disabled, the runtime may continue session-only behavior.
- If SQLite runtime is enabled but canonical write fails, the runtime must not silently pretend success.

## 8. Acceptance Baseline

- SQLite schema contains project season, field season, seasonal event, fertilizer record, and yield record tables.
- Confirmed fertilizer input writes one canonical fertilizer record.
- Confirmed yield input writes one canonical yield record.
- When one active field binding exists, the canonical record references the bound field and field season.
- When no binding exists or multiple bindings remain unresolved, the canonical record still preserves the unresolved linkage state in structured metadata.
