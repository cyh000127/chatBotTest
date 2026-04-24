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

Tables intentionally not included in the current local SQLite migrations:

- `ai_follow_up_attempts`
- `participant_identity_link_reviews`
- `participant_reachability_states`
- `reminder_deliveries`
- `escalations`
- evidence submission and review tables
- field registry tables
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

The SQLite schema intentionally defers these reference areas:

- evidence submission and review
- field binding and field registry
- AI follow-up attempt lifecycle
- reminder scheduling
- reachability projection
- escalation issue tracking
- identity conflict review workflow
- production-grade admin authorization

Deferring these areas keeps the local runtime aligned with the reference flow without pretending to implement the full product.
