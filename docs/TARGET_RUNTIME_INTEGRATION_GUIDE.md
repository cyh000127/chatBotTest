# Target Runtime Integration Guide

## 1. Purpose

This document explains how to transplant the local messenger runtime into a target runtime without breaking the reference interaction contract.

The goal is not to copy every local feature. The goal is to move only the reusable runtime foundation:

- canonical intent normalization
- rule-first structured interaction
- onboarding and access boundary
- support handoff and admin follow-up relay
- outbox and delivery state handling
- SQLite-backed local persistence skeleton

This guide assumes that the target runtime has its own product vocabulary, approval flow, and domain aggregates.

## 2. Migration Principle

Use these rules during integration:

- move contracts before moving handlers
- move vocabulary before moving UI text
- move persistence boundaries before moving convenience pages
- keep Telegram as a channel adapter, not a domain owner
- keep admin replies bot-mediated through outbox
- keep model assistance optional and policy-gated

The local runtime should be treated as a constrained implementation reference, not as a full product surface.

## 3. What To Reuse

The following parts are reusable as runtime foundation.

### 3.1 Canonical Intent Layer

Reuse the canonical intent pattern where every input path converges to one internal intent vocabulary:

- slash command
- inline button callback
- guided fallback button
- text rule match
- limited model-assisted recovery result

The target runtime should preserve one canonical vocabulary for product entry points and recovery actions.

Minimum reusable intent group:

- `start`
- `help`
- `menu`
- `cancel`
- `restart`
- `back`
- `confirm`
- `edit`
- `field.list`
- `agri.input.start`
- `yield.input.start`
- `input.resolve.start`
- `support.escalate`

### 3.2 Rule Engine Layer

Reuse the rule-first structure:

- input normalization
- global intent rules
- current-step local rules
- cheap gate
- validator set
- recovery context
- structured fallback generation

This is the main reusable interaction skeleton.

### 3.3 Session And Dispatch Layer

Reuse the state-based dispatch pattern:

- current state storage
- guided transition routing
- pending candidate handling
- confirm-before-commit flow
- support handoff state preservation

The target runtime should keep state transitions explicit and testable.

### 3.4 Support Handoff Layer

Reuse the support relay structure:

- support escalation request creation
- follow-up queue item creation
- user follow-up message append
- admin reply relay through outbox
- close-with-notice flow

This is one of the highest-value reusable pieces because it already preserves the bot-mediated admin boundary.

### 3.5 Persistence Skeleton

Reuse the local persistence pattern for:

- invitation lifecycle
- onboarding session storage
- admin follow-up queue
- follow-up messages and outcomes
- outbox delivery state
- admin audit events

The target runtime may replace SQLite later, but the data boundary and state vocabulary should remain compatible.

### 3.6 Admin Runtime Surface

Reuse the command-oriented admin runtime ideas:

- follow-up list and detail
- reply through outbox
- close with user notice
- audit trail
- operational summary

The JSON command surface is more reusable than the local HTML pages.

## 4. What Not To Reuse As-Is

The following local features should not be promoted directly into the target product runtime.

- sample profile input flow
- profile-related repair and fallback surface
- weather, date, and demo menu flows
- local sample login interpretation
- local access-token gate as production identity
- in-memory runtime as durable storage
- local admin HTML pages as a production console
- runtime-local AI gate as the final release gate

If these are needed, they should be rebuilt under the target product vocabulary and product authorization model.

## 5. Required Vocabulary Alignment

Before integration, freeze the target runtime vocabulary and compare it to the local runtime vocabulary.

The following must stay aligned:

- canonical intent names
- follow-up route hints
- outbox delivery status names
- audit action names
- onboarding status names
- recovery reason names

Examples of names that should remain stable once chosen:

- `support.escalate`
- `manual_resolution_required`
- `waiting_admin_reply`
- `open`
- `closed`
- `pending`
- `failed`
- `manual_review`
- `admin.access.denied`
- `admin.follow_up.reply`
- `admin.follow_up.close`

Do not rename these ad hoc inside handlers. Freeze the names in one vocabulary layer first.

## 6. Recommended Integration Order

### Step 1. Freeze Target Vocabulary

Define the target runtime vocabulary before any file transplant:

- canonical intents
- route hints
- delivery status names
- admin action names
- onboarding state names

### Step 2. Move Persistence And Contracts

Move or recreate:

- onboarding session repository contract
- invitation repository contract
- follow-up queue repository contract
- outbox repository contract
- audit repository contract

Do this before moving Telegram-specific behavior.

### Step 3. Move Support Handoff And Outbox Relay

The support relay path is usually the safest first runtime path to integrate because it has clear boundaries:

1. user triggers `support.escalate`
2. bot creates follow-up queue item
3. admin runtime writes reply
4. outbox stores delivery work
5. bot delivery loop sends the reply

This path should work before any advanced model feature is attached.

### Step 4. Move Onboarding And Protected Access Gate

Integrate:

- `/start <invite_code>` or equivalent entry
- onboarding draft storage
- approval-required access gate
- approved-session restoration

Do not bring back local sample login behavior.

### Step 5. Move Structured Input Flows

Only after the runtime boundary is stable should the target runtime move domain-specific structured collection flows.

The move should preserve:

- current-step parser first
- validator before state advance
- pending candidate before confirm
- guided fallback before escalation

### Step 6. Attach Limited Model Assistance

Model assistance should be attached last.

Keep the same boundary:

- current-step recovery only
- structured output only
- no direct final write
- confirm gate remains mandatory
- rules-only fallback remains available

## 7. Integration Shapes

### 7.1 Reuse Without SQLite

If the target runtime already has persistence:

- keep the runtime contracts
- replace SQLite repositories with target repositories
- keep the follow-up queue and outbox semantics
- keep the same delivery state names if possible

### 7.2 Reuse With SQLite As Temporary Bridge

If the target runtime does not yet have production persistence:

- keep SQLite as a local bridge
- clearly document it as non-authoritative
- keep backup and restore procedure explicit
- avoid coupling product-critical domain logic to SQLite-only assumptions

### 7.3 Reuse Admin Relay Without HTML Pages

If the target runtime already has an admin frontend:

- reuse the JSON command surface
- reuse follow-up and outbox contracts
- drop the local HTML pages
- let the target admin UI call the API layer

## 8. Integration Blockers

Stop the transplant if any of the following becomes true:

- Telegram handlers begin to own business decisions directly
- admin replies bypass the outbox and send directly to Telegram
- target onboarding accepts product access before approval
- model output can write confirmed values without validator and confirm gates
- sample profile logic becomes visible on the target main menu or target global routing surface
- local convenience pages are treated as the final admin product

## 9. Minimum Acceptance Checklist

Before calling the transplant complete, verify:

- unauthenticated or unapproved users cannot enter protected farmer features
- target runtime uses canonical intent names consistently across slash command, buttons, and text fallback
- support escalation creates follow-up queue items
- admin reply creates outbox work instead of sending directly
- delivery loop sends outbox replies into the same bot conversation surface
- follow-up queue survives restart
- pending outbox survives restart
- audit events are recorded for reply, close, denied access, and requeue
- rules-only mode still works when model credentials are absent
- sample-only flows remain outside the target product surface

## 10. Final Recommendation

The best transplant strategy is:

1. move contracts and vocabulary first
2. move support handoff and outbox relay second
3. move onboarding gate third
4. move structured collection flows fourth
5. attach model assistance last

This preserves the highest-value runtime behavior while keeping the target runtime aligned with a rule-first, structured, bot-mediated operational model.
