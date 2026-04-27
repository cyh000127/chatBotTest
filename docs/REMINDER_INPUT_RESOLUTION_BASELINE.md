# Reminder And Input Resolution Baseline

## 1. Purpose

This document defines the local runtime baseline for reminder delivery and input-resolution persistence.

The goal is to make unresolved structured input sessions restart-safe and resumable through a reminder token.

## 2. Scope

This slice covers:

- reminder delivery rows
- reminder resume tokens
- `/start reminder:<token>` re-entry
- input-resolution session persistence
- input-resolution attempt ledger
- input-resolution candidate ledger
- input-resolution decision ledger
- unresolved session escalation to admin follow-up

This slice does not cover:

- full OCR extraction
- image artifact storage
- model-owned resolution decisions
- production notification scheduling

## 3. Reminder Rules

- A reminder row is an operational delivery record, not a conversation draft.
- Reminder rows must contain a resume token.
- Resume tokens must reopen only the linked unresolved session.
- A reminder row must move through explicit status changes:
  - `pending`
  - `sent`
  - `completed`
  - `cancelled`

## 4. Input Resolution Rules

- Input-resolution is a structured side flow, not a free-form chatbot mode.
- A session must store:
  - target type
  - method
  - raw input
  - generated candidates
  - selected candidate
  - final decision
- Candidate generation is rule-first.
- A selected candidate is not authoritative until the user confirms it.
- Repeated failure must escalate rather than loop forever.

## 5. Local Runtime Target Types

The current local runtime target baseline is limited to:

- fertilizer product
- fertilizer amount
- yield field
- yield amount

## 6. Re-entry Rules

- `/start reminder:<token>` must not be treated as an invitation code.
- If the token is valid, the runtime restores the unresolved input-resolution session.
- If the token is missing, invalid, or already closed, the runtime must show a safe retry/help path.

## 7. Escalation Rules

- If the runtime cannot generate a usable candidate after repeated attempts, it must create an admin follow-up item.
- If the user explicitly chooses manual review, it must create an admin follow-up item.
- Escalation must preserve session id and latest raw input in structured form.

## 8. Acceptance Baseline

- SQLite schema contains reminder and input-resolution tables.
- Input-resolution sessions survive process restart.
- A sent reminder can reopen the linked unresolved session through `/start reminder:<token>`.
- Candidate selection and final decision are stored as separate rows.
- Unresolved sessions can be escalated without pretending they were resolved.
