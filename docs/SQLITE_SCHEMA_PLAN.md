# SQLite Schema Plan

## 1. Purpose

This document defines the SQLite schema plan for the local messenger runtime.

The schema follows the reference domains for participant onboarding and messaging follow-up while staying small enough for the current runtime:

- participant / invitation / enrollment
- onboarding session and event ledger
- channel message and delivery ledger
- admin follow-up queue
- admin follow-up outcome ledger
- bot-mediated outbound message outbox
- local admin action audit trail
- field registry and participant field binding

This document is a planning contract for the next migration SQL. It is not a replacement for the reference schema.

## 2. Scope

Tables included in the current local SQLite migrations:

- `schema_migrations`
- `admin_users`
- `projects`
- `project_invitations`
- `participants`
- `participant_private_contacts`
- `participant_identities`
- `onboarding_sessions`
- `onboarding_session_events`
- `project_enrollments`
- `channel_messages`
- `message_deliveries`
- `admin_follow_up_queue`
- `admin_follow_up_messages`
- `admin_follow_up_outcomes`
- `outbox_messages`
- `admin_audit_events`
- `field_registry_versions`
- `field_registry_fields`
- `field_registry_boundaries`
- `participant_field_bindings`
- `field_binding_exceptions`
- `project_seasons`
- `field_seasons`
- `seasonal_events`
- `fertilizer_application_records`
- `yield_records`
- `reminder_deliveries`
- `input_resolution_sessions`
- `input_resolution_attempts`
- `input_resolution_candidates`
- `input_resolution_decisions`
- `evidence_request_events`
- `evidence_submission_sessions`
- `evidence_submissions`
- `evidence_validation_signals`
- `evidence_validation_state_logs`

Tables intentionally not included in the current local SQLite migrations:

- `ai_follow_up_attempts`
- `participant_identity_link_reviews`
- `participant_reachability_states`
- `escalations`
- production-grade governance access tables

These excluded tables are part of the reference architecture but are outside the current local runtime target.

## 3. SQLite Conventions

Primary keys use text ids.

Timestamps are stored as ISO-8601 UTC text.

Boolean values are stored as integers:

- `0`
- `1`

JSON payloads are stored as text.

Foreign keys should be enabled by the connection layer with:

```sql
PRAGMA foreign_keys = ON;
```

The connection layer should also set a busy timeout:

```sql
PRAGMA busy_timeout = 5000;
```

## 4. Migration Ledger

```sql
CREATE TABLE schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
```

Responsibilities:

- records applied migration versions
- prevents duplicate migration execution
- supports idempotent startup

## 5. Admin And Project Seed Tables

```sql
CREATE TABLE admin_users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  project_name TEXT NOT NULL,
  project_status_code TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

These tables exist to support invitation issuance and admin actions in the local runtime.

The first implementation may seed a single default project and a single local admin user. This seed is local runtime scaffolding and must not be treated as a production authorization model.

`invite_code` is the human-operable value used in messenger onboarding. `invite_token_hash` is reserved for bearer-style invitation token handling and should be populated when the implementation issues a secret token rather than a short operator-managed code.

Invitation status vocabulary:

- `issued`
- `used`
- `revoked`

Only non-expired `issued` invitations can start onboarding. Revoked invitations
must remain queryable for audit and operations, but they must not create new
onboarding sessions. `expires_at` is optional; when present, it must be an
ISO-8601 timestamp and the runtime must reject expired invitation start attempts.

## 6. Invitation And Onboarding Tables

```sql
CREATE TABLE project_invitations (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  invite_code TEXT NOT NULL UNIQUE,
  invite_token_hash TEXT,
  invite_status_code TEXT NOT NULL,
  target_contact_type_code TEXT,
  target_contact_normalized TEXT,
  target_contact_raw TEXT,
  target_participant_role_code TEXT NOT NULL DEFAULT 'farmer',
  invited_by_admin_user_id TEXT,
  issued_at TEXT NOT NULL,
  expires_at TEXT,
  used_at TEXT,
  revoked_at TEXT,
  accepted_participant_id TEXT,
  accepted_enrollment_id TEXT,
  used_channel_message_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (invited_by_admin_user_id) REFERENCES admin_users(id)
);
```

```sql
CREATE TABLE onboarding_sessions (
  id TEXT PRIMARY KEY,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  identity_provider_code TEXT NOT NULL DEFAULT 'telegram',
  provider_user_id TEXT NOT NULL,
  provider_handle TEXT,
  participant_identity_id TEXT,
  participant_id TEXT,
  project_invitation_id TEXT,
  project_id TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  preferred_locale_code TEXT NOT NULL DEFAULT 'ko',
  draft_payload_json TEXT NOT NULL DEFAULT '{}',
  last_inbound_channel_message_id TEXT,
  last_outbound_channel_message_id TEXT,
  started_at TEXT NOT NULL,
  last_interaction_at TEXT NOT NULL,
  expires_at TEXT,
  submitted_at TEXT,
  completed_at TEXT,
  abandoned_at TEXT,
  result_participant_id TEXT,
  result_enrollment_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_invitation_id) REFERENCES project_invitations(id)
);
```

```sql
CREATE TABLE onboarding_session_events (
  id TEXT PRIMARY KEY,
  onboarding_session_id TEXT NOT NULL,
  event_type_code TEXT NOT NULL,
  from_step_code TEXT,
  to_step_code TEXT,
  from_status_code TEXT,
  to_status_code TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  channel_message_id TEXT,
  acted_by_type TEXT NOT NULL,
  acted_by_id TEXT,
  occurred_at TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id)
);
```

Onboarding status vocabulary:

- `started`
- `collecting_basic_info`
- `pending_approval`
- `approved`
- `rejected`
- `abandoned`
- `expired`

Onboarding step vocabulary:

- `invite_received`
- `language_select`
- `name_input`
- `phone_input`
- `project_confirm`
- `pending_approval`
- `approved`
- `rejected`

## 7. Participant And Enrollment Tables

```sql
CREATE TABLE participants (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  preferred_language TEXT NOT NULL,
  participant_status_code TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```sql
CREATE TABLE participant_private_contacts (
  id TEXT PRIMARY KEY,
  participant_id TEXT NOT NULL,
  contact_type_code TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 1,
  verified_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (participant_id) REFERENCES participants(id)
);
```

```sql
CREATE TABLE participant_identities (
  id TEXT PRIMARY KEY,
  participant_id TEXT,
  identity_provider_code TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  provider_handle TEXT,
  linked_contact_id TEXT,
  link_provenance TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(identity_provider_code, provider_user_id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (linked_contact_id) REFERENCES participant_private_contacts(id)
);
```

```sql
CREATE TABLE project_enrollments (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  invitation_id TEXT,
  participant_role_code TEXT NOT NULL DEFAULT 'farmer',
  enrollment_status_code TEXT NOT NULL,
  enrollment_source_code TEXT NOT NULL,
  accepted_at TEXT,
  activated_at TEXT,
  activated_by_admin_user_id TEXT,
  revoked_at TEXT,
  revoked_by_admin_user_id TEXT,
  rejection_reason_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (invitation_id) REFERENCES project_invitations(id),
  FOREIGN KEY (activated_by_admin_user_id) REFERENCES admin_users(id)
);
```

Participant status vocabulary:

- `pending`
- `active`
- `rejected`
- `revoked`

Enrollment status vocabulary:

- `pending_approval`
- `active`
- `rejected`
- `revoked`

Allowed phone country code baseline:

- `+855`
- `+880`

Phone numbers outside the allowed country set must not create active participant enrollment.

## 8. Channel Message And Delivery Tables

```sql
CREATE TABLE channel_messages (
  id TEXT PRIMARY KEY,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  direction_code TEXT NOT NULL,
  provider_message_id TEXT,
  participant_identity_id TEXT,
  project_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER NOT NULL,
  canonical_intent_code TEXT,
  message_type_code TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  occurred_at TEXT NOT NULL,
  FOREIGN KEY (participant_identity_id) REFERENCES participant_identities(id),
  FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

```sql
CREATE TABLE message_deliveries (
  id TEXT PRIMARY KEY,
  channel_message_id TEXT NOT NULL,
  delivery_state_code TEXT NOT NULL,
  provider_status TEXT,
  delivered_at TEXT,
  failed_at TEXT,
  failure_reason_code TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (channel_message_id) REFERENCES channel_messages(id)
);
```

Direction vocabulary:

- `inbound`
- `outbound`

Message type vocabulary:

- `text`
- `command`
- `button`
- `system`

Delivery state vocabulary:

- `pending`
- `sent`
- `delivered`
- `failed`

## 9. Admin Follow-Up Tables

```sql
CREATE TABLE admin_follow_up_queue (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  participant_id TEXT,
  field_id TEXT,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  evidence_request_event_id TEXT,
  input_resolution_session_id TEXT,
  onboarding_session_id TEXT,
  issue_type_code TEXT NOT NULL,
  follow_up_status_code TEXT NOT NULL,
  assigned_admin_user_id TEXT,
  priority_code TEXT NOT NULL DEFAULT 'normal',
  created_from_code TEXT NOT NULL,
  route_hint TEXT NOT NULL,
  reason TEXT NOT NULL,
  current_step_code TEXT,
  chat_id INTEGER NOT NULL,
  provider_user_id TEXT,
  locale_code TEXT NOT NULL DEFAULT 'ko',
  recent_messages_summary TEXT,
  failure_count INTEGER NOT NULL DEFAULT 0,
  due_at TEXT,
  assigned_at TEXT,
  first_action_at TEXT,
  closed_at TEXT,
  closure_reason_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
  FOREIGN KEY (assigned_admin_user_id) REFERENCES admin_users(id)
);
```

```sql
CREATE TABLE admin_follow_up_messages (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT NOT NULL,
  direction_code TEXT NOT NULL,
  message_text TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id)
);
```

```sql
CREATE TABLE admin_follow_up_outcomes (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT NOT NULL,
  outcome_code TEXT NOT NULL,
  note TEXT,
  acted_by_admin_user_id TEXT,
  acted_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id),
  FOREIGN KEY (acted_by_admin_user_id) REFERENCES admin_users(id)
);
```

Admin follow-up status vocabulary:

- `open`
- `assigned`
- `in_progress`
- `waiting_farmer`
- `manual_resolution_required`
- `escalated`
- `resolved`
- `closed_no_response`
- `closed_not_actionable`

Issue type vocabulary for the current local runtime:

- `explicit_support_request`
- `repeated_failure`
- `manual_resolution_required`
- `input_resolution_unresolved`
- `onboarding_help`

Outcome vocabulary:

- `reply_sent`
- `assigned`
- `started`
- `waiting_farmer`
- `resolved`
- `closed_no_response`
- `closed_not_actionable`

Allowed minimal transitions:

```text
open -> assigned
open -> in_progress
assigned -> in_progress
in_progress -> waiting_farmer
waiting_farmer -> in_progress
in_progress -> resolved
in_progress -> closed_not_actionable
waiting_farmer -> closed_no_response
manual_resolution_required -> in_progress
manual_resolution_required -> closed_not_actionable
```

Each status-changing action must append an `admin_follow_up_outcomes` row.

## 10. Outbox Table

```sql
CREATE TABLE outbox_messages (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT,
  chat_id INTEGER NOT NULL,
  message_text TEXT NOT NULL,
  delivery_state_code TEXT NOT NULL,
  source_code TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sent_at TEXT,
  failed_at TEXT,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id)
);
```

Outbox delivery state vocabulary:

- `pending`
- `sending`
- `sent`
- `failed`
- `manual_review`

Outbox rules:

- Admin replies must be written to `outbox_messages`.
- The Telegram delivery loop is responsible for sending outbox messages.
- Admin pages and Admin API must not send Telegram messages directly.
- Failed messages remain retryable while below the retry limit.
- Messages that reach the retry limit move to `manual_review` and are not claimed again by the delivery loop.
- Admin may move a `manual_review` message back to `pending`; the delivery loop still owns the actual send.

## 11. Admin Audit Event Table

```sql
CREATE TABLE admin_audit_events (
  id TEXT PRIMARY KEY,
  actor_type_code TEXT NOT NULL,
  actor_id TEXT,
  action_code TEXT NOT NULL,
  target_type_code TEXT,
  target_id TEXT,
  result_code TEXT NOT NULL,
  source_code TEXT NOT NULL,
  request_path TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  occurred_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

Audit rules:

- write-oriented Admin API and admin page actions append an audit row.
- login success and login failure may append an audit row when the audit repository is configured.
- audit detail must not store access tokens, message body, phone numbers, or other sensitive user input.
- audit logs are local hardening metadata; they do not replace production RBAC or upstream admin identity.

## 12. Index Plan

```sql
CREATE INDEX idx_project_invitations_code_status
ON project_invitations(invite_code, invite_status_code);
```

```sql
CREATE INDEX idx_onboarding_identity_status
ON onboarding_sessions(identity_provider_code, provider_user_id, session_status_code);
```

```sql
CREATE INDEX idx_admin_follow_up_status_created
ON admin_follow_up_queue(follow_up_status_code, created_at);
```

```sql
CREATE INDEX idx_outbox_state_created
ON outbox_messages(delivery_state_code, created_at);
```

```sql
CREATE INDEX idx_channel_messages_chat_time
ON channel_messages(chat_id, occurred_at);
```

```sql
CREATE INDEX idx_follow_up_messages_queue_time
ON admin_follow_up_messages(admin_follow_up_queue_id, created_at);
```

```sql
CREATE INDEX idx_admin_audit_events_action_time
ON admin_audit_events(action_code, occurred_at);
```

```sql
CREATE INDEX idx_admin_audit_events_actor_time
ON admin_audit_events(actor_type_code, actor_id, occurred_at);
```

```sql
CREATE INDEX idx_admin_audit_events_target
ON admin_audit_events(target_type_code, target_id);
```

## 13. Reference Alignment Notes

The SQLite schema keeps these reference principles:

- onboarding state is stored separately from participant master data
- phone contact data is separated from participant profile data
- messenger identity is separated from participant master data
- invitation is the project enrollment anchor
- `channel_messages` is the channel source ledger
- `message_deliveries` is separated from message body
- `admin_follow_up_queue` is the operational queue aggregate
- `admin_follow_up_outcomes` is append-only handling history
- admin replies are bot-mediated through an outbox
- admin writes are traceable through local audit events without storing sensitive message content
- evidence request, submission, signal, and validation state are stored as separate lifecycle tables

The SQLite schema intentionally defers these reference areas:

- AI follow-up attempt lifecycle
- reachability projection
- escalation issue tracking
- identity conflict review workflow
- production-grade admin authorization

Deferring these areas keeps the local runtime aligned with the reference flow without pretending to implement the full product.

## 14. Field Registry And Binding Tables

```sql
CREATE TABLE field_registry_versions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  version_label TEXT NOT NULL,
  source_code TEXT NOT NULL DEFAULT 'local_runtime',
  version_status_code TEXT NOT NULL,
  published_at TEXT,
  archived_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, version_label)
);
```

```sql
CREATE TABLE field_registry_fields (
  id TEXT PRIMARY KEY,
  field_registry_version_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  field_code TEXT NOT NULL,
  display_name TEXT NOT NULL,
  area_square_meters REAL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(field_registry_version_id, field_code)
);
```

```sql
CREATE TABLE field_registry_boundaries (
  id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL,
  polygon_json TEXT NOT NULL,
  bounding_box_json TEXT NOT NULL,
  centroid_latitude REAL NOT NULL,
  centroid_longitude REAL NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);
```

```sql
CREATE TABLE participant_field_bindings (
  id TEXT PRIMARY KEY,
  participant_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  field_id TEXT NOT NULL,
  field_registry_version_id TEXT NOT NULL,
  binding_status_code TEXT NOT NULL,
  binding_source_code TEXT NOT NULL,
  onboarding_session_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER,
  location_latitude REAL,
  location_longitude REAL,
  location_accuracy_meters REAL,
  requested_field_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deactivated_at TEXT,
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id),
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id)
);
```

```sql
CREATE TABLE field_binding_exceptions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT,
  onboarding_session_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER,
  field_registry_version_id TEXT,
  exception_type_code TEXT NOT NULL,
  exception_status_code TEXT NOT NULL DEFAULT 'open',
  route_hint TEXT NOT NULL DEFAULT 'manual_resolution_required',
  requested_field_code TEXT,
  location_latitude REAL,
  location_longitude REAL,
  location_accuracy_meters REAL,
  candidate_field_ids_json TEXT NOT NULL DEFAULT '[]',
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id)
);
```

Binding status vocabulary:

- `active`
- `released`

Registry version status vocabulary:

- `draft`
- `published`
- `archived`

Binding exception status vocabulary:

- `open`
- `resolved`
- `closed`

Binding exception type baseline:

- `location_no_candidate`
- `location_multiple_candidates`
- `field_code_not_found`
- `field_code_multiple_matches`
- `field_already_bound`
- `participant_duplicate_binding`

Rules:

- automatic confirm is allowed only when a published version yields exactly one candidate
- one field may have at most one active binding
- one participant may not hold duplicate active bindings to the same field
- ambiguous, missing, or conflicting inputs must create a binding exception instead of silently guessing

## 15. Season Activity Subset Tables

```sql
CREATE TABLE project_seasons (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  season_year INTEGER NOT NULL,
  season_label TEXT NOT NULL,
  season_status_code TEXT NOT NULL DEFAULT 'open',
  season_start_date TEXT,
  season_end_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, season_year)
);
```

```sql
CREATE TABLE field_seasons (
  id TEXT PRIMARY KEY,
  project_season_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_binding_id TEXT NOT NULL,
  field_id TEXT NOT NULL,
  field_season_status_code TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_season_id) REFERENCES project_seasons(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id),
  UNIQUE(project_season_id, field_binding_id)
);
```

```sql
CREATE TABLE seasonal_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  event_type_code TEXT NOT NULL,
  event_status_code TEXT NOT NULL,
  input_source_code TEXT NOT NULL,
  occurred_on TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);
```

```sql
CREATE TABLE fertilizer_application_records (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT NOT NULL,
  field_binding_id TEXT,
  field_id TEXT,
  input_source_code TEXT NOT NULL,
  used_flag INTEGER NOT NULL,
  fertilizer_kind_code TEXT,
  product_name TEXT,
  amount_value REAL,
  amount_unit TEXT,
  applied_date TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (seasonal_event_id) REFERENCES seasonal_events(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);
```

```sql
CREATE TABLE yield_records (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT NOT NULL,
  field_binding_id TEXT,
  field_id TEXT,
  input_source_code TEXT NOT NULL,
  ready_flag INTEGER NOT NULL,
  field_name TEXT,
  amount_value REAL,
  amount_unit TEXT,
  harvest_date TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (seasonal_event_id) REFERENCES seasonal_events(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);
```

Season activity subset rules:

- project season resolution uses calendar year in the local runtime
- field season rows are created only when a field binding is resolved
- seasonal event rows provide the append-only context for confirmed structured input
- fertilizer and yield rows may preserve unresolved field linkage state in structured payload metadata

## 16. Reminder And Input Resolution Tables

```sql
CREATE TABLE reminder_deliveries (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  input_resolution_session_id TEXT,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  reminder_type_code TEXT NOT NULL,
  reminder_status_code TEXT NOT NULL DEFAULT 'pending',
  resume_token TEXT NOT NULL UNIQUE,
  resume_target_code TEXT NOT NULL,
  message_text TEXT NOT NULL,
  due_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sent_at TEXT,
  completed_at TEXT
);
```

```sql
CREATE TABLE input_resolution_sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  target_type_code TEXT,
  method_code TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  raw_input_text TEXT,
  selected_candidate_id TEXT,
  resolved_value_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  escalated_at TEXT
);
```

```sql
CREATE TABLE input_resolution_attempts (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  method_code TEXT NOT NULL,
  raw_input_text TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE input_resolution_candidates (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  input_resolution_attempt_id TEXT NOT NULL,
  candidate_rank INTEGER NOT NULL,
  candidate_type_code TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  normalized_value_json TEXT NOT NULL DEFAULT '{}',
  confidence_score REAL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE input_resolution_decisions (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  selected_candidate_id TEXT,
  decision_code TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL
);
```

Reminder vocabulary baseline:

- `pending`
- `sent`
- `completed`
- `cancelled`

Input-resolution session vocabulary baseline:

- `collecting_target`
- `collecting_method`
- `collecting_raw_input`
- `candidate_review`
- `decision_pending`
- `resolved`
- `manual_review_required`

Rules:

- a reminder token must reopen only the linked unresolved session
- candidate rows are append-only per attempt
- final resolution and manual review escalation must be written as decision rows

## 17. Evidence Submission Tables

```sql
CREATE TABLE evidence_request_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  request_type_code TEXT NOT NULL,
  request_status_code TEXT NOT NULL DEFAULT 'open',
  request_reason_code TEXT,
  requested_via_code TEXT NOT NULL DEFAULT 'runtime',
  due_at TEXT,
  satisfied_at TEXT,
  cancelled_at TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```sql
CREATE TABLE evidence_submission_sessions (
  id TEXT PRIMARY KEY,
  evidence_request_event_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  accepted_location_latitude REAL,
  accepted_location_longitude REAL,
  accepted_location_accuracy_meters REAL,
  accepted_location_recorded_at TEXT,
  draft_payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  abandoned_at TEXT
);
```

```sql
CREATE TABLE evidence_submissions (
  id TEXT PRIMARY KEY,
  evidence_submission_session_id TEXT NOT NULL,
  evidence_request_event_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  provider_message_id TEXT,
  provider_file_id TEXT,
  provider_file_unique_id TEXT,
  file_name TEXT,
  mime_type TEXT,
  file_size_bytes INTEGER,
  artifact_status_code TEXT NOT NULL,
  staged_artifact_uri TEXT,
  checksum_sha256 TEXT,
  captured_at TEXT,
  uploaded_at TEXT NOT NULL,
  submitted_at TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```sql
CREATE TABLE evidence_validation_signals (
  id TEXT PRIMARY KEY,
  evidence_submission_id TEXT NOT NULL,
  signal_type_code TEXT NOT NULL,
  signal_status_code TEXT NOT NULL,
  numeric_value REAL,
  text_value TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE evidence_validation_state_logs (
  id TEXT PRIMARY KEY,
  evidence_submission_id TEXT NOT NULL,
  from_state_code TEXT,
  to_state_code TEXT NOT NULL,
  reason_code TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

Evidence request vocabulary baseline:

- `open`
- `satisfied`
- `cancelled`
- `expired`

Evidence submission session vocabulary baseline:

- `waiting_location`
- `waiting_document`
- `validating`
- `completed`
- `manual_review_required`
- `abandoned`

Evidence artifact status vocabulary baseline:

- `uploaded`
- `signals_ready`
- `accepted`
- `rejected`
- `manual_review_required`

Rules:

- location acceptance must be written before a submission can reach validation-complete state
- document upload metadata and validation result must remain separate records
- validation signals may preserve EXIF, GPS, capture time, and distance metadata without overwriting the original submission row
- validation state history must be append-only
