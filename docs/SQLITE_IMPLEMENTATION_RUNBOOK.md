# SQLite Implementation Runbook

## 1. Purpose

This document defines how to run, implement, and verify the SQLite-backed messenger runtime.

It now describes the implemented local SQLite runtime and the verification steps used to keep it aligned with the reference behavior.

Current state:

- the bot runtime and local Admin API can run in one process.
- invitation, onboarding, follow-up queue, admin reply, and outbox state can be persisted in SQLite.
- the Admin API reads and writes through SQLite-backed repositories when SQLite is configured.
- admin replies are delivered through the bot-mediated outbox, not directly by the Admin API.
- the farmer-facing flow remains rule-first and guided.
- missing model credentials keep the runtime in rules-only mode.

## 2. Required Runtime Setup

The runtime requires the usual bot token and Admin API settings.

```env
BOT_TOKEN=your_bot_token_here
ADMIN_API_ENABLED=true
ADMIN_API_HOST=127.0.0.1
ADMIN_API_PORT=8000
ADMIN_OUTBOX_POLL_INTERVAL_SECONDS=1
ADMIN_API_ACCESS_TOKEN=replace_with_local_admin_token
ADMIN_API_ACCESS_ROLE=operator
```

The SQLite-backed runtime additionally requires a database path and migration settings.

```env
SQLITE_DATABASE_PATH=C:\absolute\path\to\runtime.sqlite3
SQLITE_MIGRATIONS_ENABLED=true
SQLITE_BUSY_TIMEOUT_MS=5000
```

Rules:

- `SQLITE_DATABASE_PATH` must be absolute.
- the database file must not be committed.
- local database, journal, WAL, SHM, and backup files must stay outside version control.
- `ADMIN_API_ACCESS_TOKEN` should be set when the local admin API is exposed beyond a disposable local shell.
- admin tokens must be sent through the login form, `Authorization: Bearer`, or `X-Admin-Token`; tokens must not be sent in URLs.
- `ADMIN_API_ACCESS_ROLE=viewer` makes the local admin surface read-only.
- `ADMIN_API_ACCESS_ROLE=operator` allows local admin write actions.
- missing model credentials must not block the rules-only runtime.

## 3. Execution Flow

The local runtime is started with the package entrypoint.

```powershell
python -m pip install -e "ABSOLUTE_PROJECT_PATH[dev]"
python -m PROJECT.main
```

If `ADMIN_API_ENABLED=true`, the local Admin API starts in the same process.

Health check:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/healthz"
```

Admin follow-up list:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/admin/follow-ups"
```

Admin follow-up list with access token:

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/admin/follow-ups" `
  -Headers @{ "X-Admin-Token" = $env:ADMIN_API_ACCESS_TOKEN }
```

Admin reply example:

```powershell
$json = '{"message":"입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."}'
$body = [System.Text.Encoding]::UTF8.GetBytes($json)

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/admin/follow-ups/{follow_up_id}/reply" `
  -Headers @{ "X-Admin-Token" = $env:ADMIN_API_ACCESS_TOKEN } `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

Admin browser pages:

```text
http://127.0.0.1:8000/admin/pages/follow-ups
http://127.0.0.1:8000/admin/pages/invitations
http://127.0.0.1:8000/admin/pages/onboarding/submissions
http://127.0.0.1:8000/admin/pages/outbox
http://127.0.0.1:8000/admin/pages/audit-events
```

Manual-review outbox filter:

```text
http://127.0.0.1:8000/admin/pages/outbox?status=manual_review
```

If `ADMIN_API_ACCESS_TOKEN` is configured, browser requests are redirected to `/admin/login` before accessing admin pages.

## 4. Startup Sequence

Startup order is:

1. load settings
2. validate SQLite path when SQLite is enabled
3. open SQLite connection
4. enable foreign keys and busy timeout
5. apply pending migrations
6. construct repositories
7. start Admin API when enabled
8. register Telegram handlers
9. start Telegram polling

The runtime must fail fast if migration fails. It must not accept Telegram updates or Admin API writes against a partially initialized database.

## 5. Farmer Onboarding Flow

The SQLite-backed onboarding flow aligns to the reference onboarding contract.

1. Admin creates an invitation code.
2. Farmer sends `/start <invite_code>`.
3. Runtime validates the invitation code.
4. Farmer selects a language.
5. Farmer enters name.
6. Farmer enters phone number.
7. Runtime normalizes the phone number.
8. Farmer confirms the onboarding draft.
9. Runtime submits the onboarding draft for pending approval.
10. Admin approves or rejects the enrollment.
11. Approved farmer can access the main farmer menu.

Allowed MVP phone country codes:

- `+855`
- `+880`

Invalid or unsupported phone numbers must not create active enrollment.

## 6. Admin Flow

Admin features remain limited to runtime-safe actions.

Invitation flow:

1. Admin requests a new invitation code through the Admin API or admin page.
2. Runtime stores the invitation in `project_invitations`.
3. Admin shares the code outside the bot.
4. Farmer uses `/start <invite_code>`.
5. Runtime marks the invitation as used only when onboarding progresses to the accepted state defined by implementation rules.

Approval flow:

1. Admin opens pending onboarding submissions.
2. Admin reviews submitted name, phone, language, and invitation context.
3. Admin approves or rejects.
4. Runtime creates or updates participant and enrollment records.
5. Runtime writes an outbox message when the farmer should be notified.

Follow-up flow:

1. Bot creates an `admin_follow_up_queue` item after support escalation or recovery failure.
2. Admin views the queue through the Admin API or page.
3. Admin writes a reply.
4. Runtime stores the reply in `admin_follow_up_messages`.
5. Runtime writes an `outbox_messages` row.
6. Bot delivery loop sends the outbox message to the existing chat.
7. Delivery result updates message and outbox state.

Admin API and admin pages must not send Telegram messages directly.

If the local admin access-token gate is enabled, all admin JSON and browser routes require authentication before queue, invitation, onboarding, or outbox data is exposed.

Audit flow:

1. Admin performs a write-oriented action through the Admin API or admin page.
2. Runtime records an `admin_audit_events` row with action, actor, target, result, source, and request path.
3. Runtime excludes access tokens, message body, phone numbers, and other sensitive user input from audit detail.
4. Admin can inspect local audit events through `GET /admin/audit-events` or `/admin/pages/audit-events`.

Local role flow:

1. Runtime reads `ADMIN_API_ACCESS_ROLE`.
2. `viewer` can inspect queues, submissions, outbox, invitations, and audit events.
3. `viewer` cannot create invitations, approve or reject onboarding, reply to follow-ups, or close follow-ups.
4. Denied write attempts return `403` and append an `admin.rbac.denied` audit event when the audit repository is configured.
5. `operator` keeps the existing local write behavior.

## 7. Implementation Commits

The SQLite implementation was split into small commits. Each item below is implemented and covered by tests.

### Commit 1: SQLite Settings And Connection

Status: implemented.

Commit message:

```text
feat: SQLite 설정과 연결 부트스트랩 추가
```

Scope:

- add SQLite settings fields
- validate absolute database path
- create database parent directory when allowed
- open connection with foreign keys enabled
- apply busy timeout
- keep existing in-memory runtime as fallback until repositories are connected

Tests:

- settings load succeeds without SQLite path when SQLite is disabled
- settings reject relative SQLite path when SQLite is enabled
- connection enables foreign keys

### Commit 2: Migration Runner

Status: implemented.

Commit message:

```text
feat: SQLite migration runner 추가
```

Scope:

- add migration ledger
- execute pending migrations once
- record applied version
- fail fast on migration error

Tests:

- migration applies once
- second startup is idempotent
- failed migration blocks startup

### Commit 3: Initial DDL Migration

Status: implemented.

Commit message:

```text
feat: SQLite 초기 스키마 migration 추가
```

Scope:

- create tables defined in the schema plan
- create required indexes
- seed one local admin user and one local project if needed

Tests:

- all required tables exist
- indexes exist
- seeded project/admin can be used by repository tests

### Commit 4: Invitation Repository And Admin API

Status: implemented.

Commit message:

```text
feat: 관리자 초대 코드 생성 API 추가
```

Scope:

- create invitation repository
- add Admin API endpoint to create invitation codes
- add Admin API endpoint to list invitations
- store a token hash when an invitation uses bearer-style token semantics
- add minimal admin page action if useful for local verification

Tests:

- invitation code is unique
- issued invitation is persisted
- revoked or expired invitation cannot be used

### Commit 5: Start Command Invitation Parsing

Status: implemented.

Commit message:

```text
feat: start 초대 코드 기반 온보딩 진입 추가
```

Scope:

- parse `/start <invite_code>`
- validate invitation code through repository
- create or resume onboarding session
- route invalid invitation to guided fallback
- prevent unauthenticated access to farmer features

Tests:

- valid invitation starts onboarding
- invalid invitation does not start onboarding
- existing pending session resumes safely
- non-approved user cannot access protected features

### Commit 6: Farmer Onboarding Steps

Status: implemented.

Commit message:

```text
feat: farmer 온보딩 입력 수집 추가
```

Scope:

- language selection
- name input
- phone input
- phone normalization for allowed country codes
- onboarding draft confirm
- submit pending approval

Tests:

- happy path reaches pending approval
- unsupported phone country code is rejected
- confirm stores pending submission only
- restart resumes the latest onboarding step

### Commit 7: Admin Approval Flow

Status: implemented.

Commit message:

```text
feat: 관리자 온보딩 승인 흐름 추가
```

Scope:

- list pending onboarding submissions
- approve submission
- reject submission
- create participant, private contact, identity, and enrollment records
- notify farmer through outbox

Tests:

- approval creates active enrollment
- rejection does not create active enrollment
- duplicate approval is idempotent or rejected safely
- notification is written to outbox, not sent directly by Admin API

### Commit 8: Follow-Up Queue Persistence

Status: implemented.

Commit message:

```text
feat: admin follow-up queue SQLite 저장소 연결
```

Scope:

- replace in-memory follow-up storage with SQLite repository
- preserve existing API response shape where possible
- persist user messages and admin messages
- keep route hint vocabulary aligned to `admin_follow_up_queue`

Tests:

- support escalation creates persisted queue item
- queue item survives restart
- admin reply creates persisted admin message and outbox row

### Commit 9: Outbox Delivery Persistence

Status: implemented.

Commit message:

```text
feat: outbox delivery 상태를 SQLite에 저장
```

Scope:

- load pending outbox messages from SQLite
- mark sending, sent, and failed states
- retry failed messages according to the current retry backoff policy
- move messages at the retry limit to `manual_review`
- expose outbox status filtering for operational review
- keep Telegram delivery inside bot delivery loop

Tests:

- pending outbox survives restart
- successful delivery marks sent
- failed delivery increments retry count
- failed delivery waits for retry backoff before being claimed again
- retry-limit exhaustion moves outbox messages to `manual_review`
- Admin API never calls Telegram directly

### Commit 10: End-To-End Verification

Status: implemented.

Commit message:

```text
test: SQLite runtime end-to-end 시나리오 보강
```

Scope:

- add end-to-end tests for invitation to approval
- add end-to-end tests for support handoff to admin reply delivery
- add restart persistence tests
- add regression tests for rules-only fallback without model credentials

Tests:

- full test suite passes
- SQLite tests use disposable temporary databases
- no local database file is committed

## 8. Implementation Gates

Each commit must satisfy:

- no real secrets are added
- no SQLite database files are staged
- tests relevant to the commit pass
- documentation remains aligned with reference vocabulary
- user-facing behavior remains guided and rule-first

Before pushing an implementation commit:

```powershell
python -m pytest
git diff --check
git status --short
```

Current verification snapshot:

- the full unit suite passes with disposable SQLite databases.
- the end-to-end SQLite tests cover invitation to approval, support handoff to admin reply delivery, restart persistence, and rules-only runtime without model credentials.

## 9. Rollback And Recovery

Local rollback rule:

- stop the runtime
- copy the SQLite database file before destructive changes
- restore the previous database file if local data must be recovered
- do not manually edit migration ledger rows unless the database is disposable

Migration rollback is not required for the first local runtime implementation. If a migration is wrong during development, use a disposable database and create a corrective migration before sharing the change.

## 10. Definition Of Done

The SQLite implementation is complete when:

- invitation codes are created by Admin API and stored in SQLite
- `/start <invite_code>` starts the onboarding flow
- onboarding draft reaches pending approval
- admin approval creates active farmer access
- protected farmer features require approved enrollment
- support handoff queue survives restart
- admin replies are delivered through outbox after restart
- all persistence tests use temporary databases
- the runtime still works with model credentials missing
- no demo-only profile, weather, or date flow becomes part of product onboarding

Current status: complete for the local SQLite runtime baseline. Future production hardening is tracked separately from this local runtime baseline.

Implemented local hardening:

- optional `ADMIN_API_ACCESS_TOKEN` gate for Admin API and admin pages
- browser login cookie for local admin pages
- header-based access for JSON API clients
- local `viewer` and `operator` role gate
- local admin action audit trail for write-oriented admin operations
- outbox retry exhaustion to `manual_review`

Remaining production hardening:

- real admin identity provider
- token rotation policy
