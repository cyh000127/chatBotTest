# SQLite Implementation Runbook

## 1. Purpose

This document defines how to run, implement, and verify the SQLite-backed messenger runtime.

It is a runbook for the next implementation phase. It does not claim that all SQLite-backed behavior already exists in code.

Current state:

- the bot runtime and local Admin API can run in one process
- admin follow-up queue and outbox behavior are available for local verification
- admin follow-up state is still process-local unless SQLite persistence is implemented

Target state:

- onboarding, invitation, follow-up queue, admin reply, and outbox state survive process restart
- the Admin API reads and writes through repositories backed by SQLite
- admin replies are still delivered through the bot-mediated outbox
- the farmer-facing flow remains rule-first and guided

## 2. Required Runtime Setup

The runtime requires the usual bot token and Admin API settings.

```env
BOT_TOKEN=your_bot_token_here
ADMIN_API_ENABLED=true
ADMIN_API_HOST=127.0.0.1
ADMIN_API_PORT=8000
ADMIN_OUTBOX_POLL_INTERVAL_SECONDS=1
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
- missing model credentials must not block the rules-only runtime.

## 3. Current Execution Flow

Before SQLite persistence is implemented, the local runtime is started with the existing package entrypoint.

```powershell
python -m pip install -e "C:\absolute\path\to\runtime-workspace[dev]"
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

Admin reply example:

```powershell
$json = '{"message":"입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."}'
$body = [System.Text.Encoding]::UTF8.GetBytes($json)

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/admin/follow-ups/{follow_up_id}/reply" `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

Important current limitation:

- restarting the process clears in-memory admin follow-up state
- old follow-up ids may return `open follow-up not found`
- this limitation is exactly what the SQLite implementation must remove

## 4. Target Execution Flow After SQLite

After SQLite is implemented, the same process start should be enough.

```powershell
python -m pip install -e "C:\absolute\path\to\runtime-workspace[dev]"
python -m PROJECT.main
```

Startup order must be:

1. load settings
2. validate SQLite path when SQLite is enabled
3. open SQLite connection
4. enable foreign keys and busy timeout
5. apply pending migrations
6. construct repositories
7. start Admin API when enabled
8. start Telegram polling

The runtime must fail fast if migration fails. It must not accept Telegram updates or Admin API writes against a partially initialized database.

## 5. Target Farmer Onboarding Flow

The SQLite-backed onboarding flow should align to the reference onboarding contract.

1. Admin creates an invitation code.
2. Farmer sends `/start <invite_code>`.
3. Runtime validates the invitation code.
4. Farmer selects a language.
5. Farmer enters name.
6. Farmer enters phone number.
7. Runtime normalizes the phone number.
8. Farmer confirms the onboarding draft.
9. Runtime creates a pending enrollment.
10. Admin approves or rejects the enrollment.
11. Approved farmer can access the main farmer menu.

Allowed MVP phone country codes:

- `+855`
- `+880`

Invalid or unsupported phone numbers must not create active enrollment.

## 6. Target Admin Flow

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

## 7. Implementation Commits

The SQLite implementation should be split into small commits.

### Commit 1: SQLite Settings And Connection

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

Commit message:

```text
feat: 관리자 초대 코드 생성 API 추가
```

Scope:

- create invitation repository
- add Admin API endpoint to create invitation codes
- add Admin API endpoint to list invitations
- add minimal admin page action if useful for local verification

Tests:

- invitation code is unique
- issued invitation is persisted
- revoked or expired invitation cannot be used

### Commit 5: Start Command Invitation Parsing

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

Commit message:

```text
feat: outbox delivery 상태를 SQLite에 저장
```

Scope:

- load pending outbox messages from SQLite
- mark sending, sent, and failed states
- retry failed messages according to current retry policy
- keep Telegram delivery inside bot delivery loop

Tests:

- pending outbox survives restart
- successful delivery marks sent
- failed delivery remains retryable
- Admin API never calls Telegram directly

### Commit 10: End-To-End Verification

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
