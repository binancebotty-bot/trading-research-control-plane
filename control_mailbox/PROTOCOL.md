# Pine Control Mailbox Fallback v1

Purpose: preserve the existing Pine authority chain when GitHub Issue comment delivery is unavailable or materially degraded.

Primary surface remains GitHub Issue #1 (General Operations / Evidence Board).
This branch is fallback transport only. It does not create new authority, does not supersede Issue #1 when Issue #1 is healthy, and does not grant product/live/trading authority.

## Authority

- Human Authority: richard:operator
- Project Architect: gpt:project-architect
- Reviewer/Controller: gpt:reviewer-controller
- Implementation owner: hermes:implementation-owner
- Governing protocol SHA: 0df93c7a2d31e235915d61712c17d28c822e7da9
- Build-4 contact/fallback: forbidden

## Envelope paths

Controller -> Hermes:
`control_mailbox/controller/<utc>-<nonce>.json`

Hermes -> Controller:
`control_mailbox/hermes/<utc>-<nonce>.json`

Envelopes are append-only. Never overwrite a consumed envelope. Each envelope must carry sender role, recipient role, nonce, responds_to, created_at_utc, directive/result type, body, and exact authority/safety bounds.

## Failover semantics

1. Issue #1 is primary.
2. Fallback activates only after a concrete primary delivery/read failure (timeout, unavailable API, or verified missing delivery).
3. A fallback envelope is authoritative only for the same logical role that could have emitted the equivalent Issue #1 message.
4. `SEEN != CONSUMED` remains locked.
5. `NO_REPLY_IS_NOT_PERMISSION` remains locked.
6. Hermes final action remains: durable result -> `PINE_CONTROLLER_STANDDOWN_OR_NEXT_ACTION_REQUEST` -> wait/read Controller response.
7. If primary recovers, do not replay already-consumed fallback envelopes. Reconcile by nonce/high-water and return to Issue #1.
8. Duplicate/stale envelopes are transport noise and must not trigger execution.
9. Fallback branch commits are control transport only and must never be merged into `master` as product code.
10. No delegate or secondary worker may write implementation changes. Hermes remains sole implementation writer.

## Local Hermes fallback

When Issue #1 API access is unavailable, Hermes may use its existing authenticated Git/GitHub path to fetch this branch and read new Controller envelopes. Hermes may write only its own append-only result/request envelopes under `control_mailbox/hermes/` on this branch. It must not modify Controller envelopes or product files on this branch.
