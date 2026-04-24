# Reference Alignment Review

## 1. Purpose

This document reviews whether the local SQLite and Admin API implementation plan preserves the reference interaction and data boundaries.

The conclusion is conditional approval:

- the current plan can be used as a local runtime implementation path
- SQLite must remain local persistence, not a replacement for the production source of truth
- Admin API behavior must remain command and outbox oriented
- sample-only flows must not be promoted into product onboarding
- deferred reference domains must stay explicit and must not be mocked as completed

## 2. Reviewed Scope

The review covers the current local runtime plan in these areas:

- participant invitation and onboarding
- Telegram command and canonical intent mapping
- structured farmer input
- support handoff and admin follow-up queue
- bot-mediated admin replies
- message ledger and delivery state
- limited model assistance and rules-only fallback
- SQLite schema and migration planning

The review does not validate evidence submission, geospatial validation, image verification, export, production authorization, or full operations dashboards.

## 3. Overall Verdict

No blocking conflict is present in the planned local SQLite runtime if the guardrails in this document are followed.

The plan is aligned with the reference direction because it keeps:

- Telegram as a channel adapter
- canonical intent as the internal routing contract
- onboarding state separate from participant master data
- contact data separate from participant profile data
- admin follow-up queue as the operational aggregate
- admin replies delivered through a bot-mediated outbox
- model output limited to structured assistance
- rules-only fallback available when model use is disabled or unsafe

The plan is not a full reference implementation. It intentionally implements a small local subset.

## 4. Alignment Matrix

| Area | Reference requirement | Current or planned behavior | Status | Required guardrail |
| --- | --- | --- | --- | --- |
| Bot boundary | Bot should normalize Telegram input and emit canonical command requests, not own aggregate business decisions. | The runtime keeps channel parsing, dispatch, conversations, and service logic separated. | Aligned with guardrail | Do not add channel-specific business rules inside Telegram handlers. |
| Canonical intent | Slash command, button, text fallback, and guided reply must converge to the same canonical intent. | Planned command surface uses `/start`, `/myfields`, `/yield`, `/fertilizer`, support, and input resolve entry points. | Aligned with guardrail | Internal names must stay `field.list`, `agri.input.start`, `yield.input.start`, `input.resolve.start`, and `support.escalate`. |
| Onboarding identity | Messenger identity, onboarding session, participant, contact, invitation, and enrollment are separate concepts. | SQLite plan separates `onboarding_sessions`, `participants`, `participant_private_contacts`, `participant_identities`, `project_invitations`, and `project_enrollments`. | Aligned | Do not collapse login, contact, participant, and enrollment into one table. |
| Invitation lifecycle | Invitation is the project enrollment anchor and should include secure token handling. | SQLite plan includes human-operable invite code and now includes token hash storage. | Aligned with guardrail | Do not store bearer-style secret invite tokens only as raw text. |
| Admin approval | Participant should not become active before approval. | Planned onboarding reaches pending approval before admin action creates active enrollment. | Aligned | Protected farmer features must require active enrollment. |
| Message ledger | Original channel messages and delivery results should be separated. | SQLite plan has `channel_messages` and `message_deliveries`. | Aligned | Delivery state must not overwrite original message payload. |
| Participant/project message context | Channel messages should be linkable to participant identity and project context. | SQLite plan now includes nullable participant identity and project references on channel messages. | Aligned with guardrail | Fill these columns when identity or project context is known; keep nullable during unauthenticated onboarding. |
| Admin follow-up queue | The admin queue is the canonical operational aggregate for unresolved work. | SQLite plan uses `admin_follow_up_queue` and outcomes. | Aligned | Do not replace the queue with direct chat state or model state. |
| Follow-up context | Queue items may need field, season, event, evidence, or input-resolution context. | SQLite plan now includes nullable reference context columns for future linkage. | Aligned with guardrail | Keep null when the local runtime lacks the domain; do not invent fake field or evidence ids. |
| Admin reply delivery | Admin replies should go through outbox and bot delivery, not direct Admin API provider calls. | Planned flow writes admin reply and outbox row, then bot delivery loop sends. | Aligned | Admin API must not call Telegram directly. |
| State change and outbox | Externally observable state changes should be recorded with outbox work. | SQLite implementation plan requires repository and outbox writes before delivery. | Aligned with guardrail | Approval, rejection, and admin replies should write state and outbox in one local transaction where possible. |
| Model use | Model is assistant, not decision owner. | Policy documents restrict model to recovery classifier, edit intent, candidate extraction, and clarification. | Aligned | Model output must pass schema, validator, state machine, and confirm gates. |
| AI outage | Rules-only fallback plus admin review must continue when model use fails. | Runtime policy and docs keep model credentials optional. | Aligned | Missing model configuration must not block bot startup. |
| Language | Locale must be canonical and user outcome must remain stable across supported languages. | Current catalogs exist for supported languages, and planned onboarding stores locale code. | Aligned with guardrail | Do not use display language labels as stored state. |
| Local SQLite | Reference source of truth is not SQLite. | SQLite is documented as local and pilot-grade persistence only. | Aligned with guardrail | Do not present SQLite as the production source of truth. |
| Local Admin API | Reference ownership expects API command validation, RBAC, audit, and outbox. | Local Admin API exists for verification and will back onto SQLite repositories. | Conditional | Treat local API as a runtime command surface, not production authorization. |
| Sample profile flow | Product onboarding is name, phone, preferred language, invitation, and approval. | Existing profile sample is explicitly isolated as UX sample. | Conditional | Do not reuse residence, district, or birthdate sample as product onboarding. |
| Demo weather/date | Weather/date flows are outside product scope. | Docs exclude them. | Conditional | Do not keep them in main product menu when onboarding is implemented. |

## 5. Required Corrections Applied To The Plan

This review identified schema-plan corrections that should be treated as part of the implementation baseline:

- `project_invitations` includes `invite_token_hash`.
- `channel_messages` includes nullable `participant_identity_id`.
- `channel_messages` includes nullable `project_id`.
- `admin_follow_up_queue` includes nullable field, season, event, evidence, and input-resolution context columns.
- `participant_identity_link_reviews` is explicitly deferred instead of being silently omitted.

These changes keep the local schema closer to the reference model while still allowing the first SQLite implementation to stay small.

## 6. Explicitly Deferred Reference Areas

The following areas are not part of the first SQLite runtime implementation:

- evidence submission and review
- geospatial field registry
- image, EXIF, or vision validation
- AI follow-up attempt lifecycle
- reminder scheduling
- participant reachability projection
- structured escalation issue tracking
- identity conflict review workflow
- production-grade admin authorization
- governance audit and export workflows

Deferral rule:

- deferred areas must remain absent or explicitly marked as pending
- the implementation must not create fake success behavior for deferred areas
- when a deferred domain is needed, add a new migration and a new integration plan instead of overloading local session state

## 7. Implementation Blockers

The implementation should stop if any of the following becomes true:

- an unauthenticated or unapproved user can access protected farmer features
- Admin API sends Telegram messages directly
- model output writes confirmed values without validator and confirm gates
- a local sample profile field becomes part of product onboarding
- demo weather or date functionality returns to the main product menu
- support handoff is described as guaranteed real-time human chat
- local SQLite is documented as the production source of truth
- invitation consumption activates enrollment without admin approval
- user contact data is stored only inside participant profile JSON
- outbox delivery failure is silently dropped

## 8. Acceptance Checklist

Before the SQLite implementation is considered reference-aligned, verify:

- `/start <invite_code>` creates or resumes onboarding, not a local login session
- invalid invitation code does not start protected service access
- language is stored as a canonical locale code
- name and phone are collected as onboarding draft values
- phone normalization rejects unsupported country codes
- submission enters pending approval
- admin approval creates active participant access
- admin rejection does not create active access
- admin reply creates an outbox row
- bot delivery loop sends outbox messages
- follow-up queue items survive restart
- pending outbox messages survive restart
- missing model credentials keep rules-only flow operational
- sample profile, weather, and date flows are excluded from product onboarding

## 9. Final Interpretation

The local SQLite/Admin implementation can proceed without violating the reference documents if it is treated as a constrained runtime subset.

The key implementation stance is:

- build the persistence and admin relay skeleton now
- keep all product-critical state transitions explicit
- do not pretend deferred evidence, field, identity-conflict, or production authorization domains are complete
- keep bot behavior as guided structured interaction, not a free-form chat engine
