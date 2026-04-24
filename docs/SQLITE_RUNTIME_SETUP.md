# SQLite Runtime Setup

## 1. Purpose

This document defines the default local runtime setup when the messenger runtime uses SQLite persistence.

SQLite is introduced for local and pilot-grade persistence of runtime state that was previously process-local:

- onboarding sessions
- admin invitation codes
- admin follow-up queue items
- admin follow-up messages and outcomes
- outbound delivery outbox
- channel message and delivery ledgers

SQLite does not change the product source of truth defined by the reference documents. It is a local persistence layer for this runtime and should keep table names, state vocabulary, and ownership boundaries aligned with the reference schema.

## 2. Runtime Principle

The runtime must not depend on in-memory state for data that affects user progress or admin handling.

The following state must survive process restart:

- issued invitation codes
- ongoing onboarding sessions
- submitted onboarding drafts
- pending admin follow-up queue items
- admin replies waiting for Telegram delivery
- delivery success or failure state

The following state may remain session-local:

- currently rendered keyboard state
- short-lived UI helper flags
- temporary recovery hints that can be reconstructed from persisted state

## 3. Required Environment Variables

The SQLite runtime requires an absolute database path.

Recommended variables:

```env
SQLITE_DATABASE_PATH=C:\absolute\path\to\runtime.sqlite3
SQLITE_MIGRATIONS_ENABLED=true
SQLITE_BUSY_TIMEOUT_MS=5000
```

Admin API variables remain required when using the browser or API-based admin surface:

```env
ADMIN_API_ENABLED=true
ADMIN_API_HOST=127.0.0.1
ADMIN_API_PORT=8000
ADMIN_OUTBOX_POLL_INTERVAL_SECONDS=1
ADMIN_API_ACCESS_TOKEN=replace_with_local_admin_token
ADMIN_API_ACCESS_ROLE=operator
```

`ADMIN_API_ACCESS_TOKEN` is optional for disposable local-only development. When it is set, every admin route requires authentication.

Supported local authentication methods:

- browser admin pages use the `/admin/login` form and an HTTP-only cookie.
- JSON API requests may use `Authorization: Bearer <token>`.
- JSON API requests may use `X-Admin-Token: <token>`.

The token must not be placed in URLs and must not be committed to version control.

`ADMIN_API_ACCESS_ROLE` controls the local admin role:

- `viewer`: can read admin pages and JSON resources but cannot perform write actions.
- `operator`: can read and perform local admin write actions.

Invalid roles fall back to `operator` for local development compatibility.

Telegram bot execution still requires:

```env
BOT_TOKEN=your_bot_token_here
```

Model-related variables remain optional. If model credentials are missing, the runtime must continue with rules-only behavior.

## 4. Path Rules

`SQLITE_DATABASE_PATH` must be an absolute filesystem path.

The database file must not be committed to version control.

The database parent directory must exist before startup, or the runtime must create it during bootstrap.

The database file should be placed under an operator-controlled local data directory. It should not be placed inside source directories that are commonly committed.

Examples of acceptable path shapes:

```env
SQLITE_DATABASE_PATH=C:\runtime-data\messenger-runtime\runtime.sqlite3
```

```env
SQLITE_DATABASE_PATH=D:\local-state\messenger-runtime\runtime.sqlite3
```

## 5. First Run Sequence

The default first run should follow this order:

1. Create or choose a local data directory.
2. Set `SQLITE_DATABASE_PATH` to an absolute path inside that directory.
3. Enable migrations with `SQLITE_MIGRATIONS_ENABLED=true`.
4. Start the runtime.
5. Confirm migration completion in logs.
6. Open the Admin API health endpoint.
7. Generate an admin invitation code.
8. Start a farmer onboarding flow with `/start <invite_code>`.

The runtime should apply pending migrations before accepting Telegram updates or Admin API writes.

If migration fails, the runtime should fail fast. It should not continue with a partially initialized database.

## 6. Restart Behavior

After restart, the runtime must preserve:

- unused invitation codes
- used invitation history
- pending onboarding sessions
- approved or rejected onboarding sessions
- open admin follow-up queue items
- closed admin follow-up history
- pending outbox messages
- failed outbox messages available for retry

After restart, the runtime may re-render the latest user-facing state from persisted records instead of preserving every transient session value.

## 7. Backup And Reset

SQLite backup is file-based.

Before destructive local testing, copy the database file to a backup location.

Resetting the local runtime means stopping the process and deleting or replacing the SQLite database file. This should be treated as data loss.

The reset procedure must not be used to resolve migration errors unless the data is disposable.

## 8. Version Control Rules

The following must be committed:

- migration SQL files
- migration runner code
- repository code
- tests
- documentation
- `.env.example` entries

The following must not be committed:

- SQLite database files
- SQLite journal files
- SQLite WAL files
- local backups
- real Telegram bot tokens
- real model API keys

The ignore rules should cover at least:

```gitignore
*.sqlite
*.sqlite3
*.db
*.db-journal
*.sqlite-wal
*.sqlite-shm
runtime-data/
local-state/
```

## 9. Admin Feature Boundary

SQLite-backed admin features should remain limited to runtime-safe operations:

- create invitation code
- list invitation codes
- view onboarding submissions
- approve or reject onboarding submission
- view admin follow-up queue
- reply to farmer through bot-mediated outbox
- close follow-up with an outcome
- view local admin audit events

The local admin surface should not introduce product behavior that is absent from the reference documents.

The admin surface should not bypass bot-mediated delivery. Admin replies must be written to the outbox and delivered by the bot delivery loop.

When `ADMIN_API_ACCESS_TOKEN` is configured, the local admin surface is protected by a runtime access-token gate. `ADMIN_API_ACCESS_ROLE` additionally allows a local read-only viewer mode. These are local safety controls for development and pilot verification. They are not replacements for production RBAC, audit logging, or upstream admin identity.

Local audit logging records write-oriented admin actions to `admin_audit_events`. Audit details must remain metadata-only and must not include tokens, message body, phone numbers, or other sensitive user input.

## 10. Outbox Retry Policy

Outbox delivery is bot-mediated and retryable.

Current local runtime rules:

- newly created outbox messages start as `pending`.
- delivery claim moves an item to `sending`.
- successful Telegram delivery marks the item `sent`.
- failed Telegram delivery marks the item `failed` and increments `retry_count`.
- failed messages are not retried immediately.
- retry eligibility uses a fixed local backoff window based on `retry_count`.
- messages at or above the configured maximum retry count remain `failed` for manual review.

## 11. Farmer Flow Boundary

The farmer flow should be aligned to the reference onboarding contract:

- `/start <invite_code>`
- language selection
- name input
- phone number input
- phone normalization
- project context confirmation
- pending approval
- approval completion

Allowed phone country codes for the current MVP baseline are:

- `+855`
- `+880`

The existing local profile sample must not be treated as product onboarding. It may remain only as a structured-input UX sample until replaced or hidden from the main product flow.

## 12. Operational Checks

Before considering the SQLite runtime ready, verify:

- migration table exists
- all required tables exist
- Admin API health endpoint responds
- invitation code can be created
- `/start <invite_code>` creates or resumes one onboarding session
- invalid phone numbers are rejected
- approved participants can enter the main farmer menu
- admin follow-up queue items survive restart
- pending outbox messages survive restart and are delivered after restart
- failed outbox messages wait for the retry backoff before being claimed again

Current verification coverage:

- repository tests verify invitation, onboarding, approval, follow-up, and outbox persistence.
- Admin API tests verify invitation creation, onboarding approval and rejection, follow-up reply, close, and browser page behavior.
- delivery tests verify pending outbox claim, successful delivery, failed delivery, retry backoff, and persisted delivery state.
- end-to-end tests verify invitation to approval after restart and support handoff to admin reply delivery after restart.
- model credentials are optional; when missing, the runtime remains in rules-only mode.
