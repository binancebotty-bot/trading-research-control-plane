# Worker start — read only this and the named inputs
1. Read `CURRENT_STATE.json` here. Only GPT contact: `6abf60c8-4598-83eb-bc80-57a926d80b2e`; Legacy Oversight provenance is historical; Project Architect is mapped through registered control surfaces; Build-4 is out of scope.
2. Read the one Controller-supplied task packet; validate against `BOUNDED_TASK_PACKET.schema.json`. Verify its directive comment directly in Pine Issue #1 and state version/high-water. Do NOT read full history unless explicitly requested or the exact source is genuinely missing/conflicting.
3. Read `CONTINUOUS_CONTROLLER_LOOP.md` and `ANTI_DRIFT.md` once on startup. Read only packet-named input artifacts/evidence. Verify exact task baseline and actual Git status; preserve unrelated dirt.
4. Execute only REQUIRED_ACTIONS within surface/budget. Do not infer or choose a follow-on task.
5. Return `BOUNDED_RESULT.schema.json` evidence. Post to Pine Issue #1, read back exact comment, then perform the explicit next-instruction-request -> confirmed send -> anchored push wait -> READ response cycle. Continue from that response, not passive waiting.
6. Missing/conflicting authority, exhausted budget or unexpected blocker: post BLOCKED/FAIL with exact evidence and request Controller correction; READ the response. Only explicit Controller HOLD/STOP/SHUTDOWN, a genuine HUMAN_ONLY gate, or Richard's explicit status-only override interrupts the loop.
No simulation/model switch is authorised by startup. Current Phase-1 restrictions are NOT permanent exclusions from the overall platform mission.

## Canonical consolidation — packet 5961894438
- Directive ledger: `CURRENT_STATE.json#DIRECTIVE_CONSUMPTION`; six Architect directives carry constraints/status, not capability proof.
- Single capability registry: `../../registry/capabilities.json#CURRENT_MCP_CENSUS`; current static source inventory, not live activation. Legacy blanket PASS fields are not current certification.
- Four registered control surfaces and high-waters and pending non-governing transport are in `CURRENT_STATE.json`; Pine remains `LEGACY_GOVERNING`. Event Transport PR6 is draft/not adopted.
- Normal bounded workers do NOT reread Issue #1 end-to-end; consume only current packet, promoted state and exact named evidence. Reconcile all four registered surfaces at recovery/material transition/major closure.
- `NEXT_ACTION=CONTROLLER_ONLY`; offline exact-open green does not authorise live HERMES/CDP/TradingView access, saved lifecycle execution or trading. Existing heartbeat180, one owner, dirty-work/protected-buffer rules and Build-4 isolation remain unchanged.

## Company Control v1 alignment — directive 5962898559
- `HUMAN_AUTHORITY=richard:operator`
- `GENERAL_OPERATIONS_EVIDENCE_BOARD=Issue #1`
- `CONTROL_REGISTRY_ROUTING_INDEX=Issue #2`
- `PROJECT_ARCHITECT_CONTROL_BOARD=Issue #3`
- `MANAGING_DIRECTOR_CONTROL_BOARD=Issue #4`
- `PROJECT_ARCHITECT_SESSION_UUID=6abf7e35-26f4-83eb-ac7d-2e238d241d55`
- `REVIEWER_CONTROLLER_SESSION_UUID=6abf60c8-4598-83eb-bc80-57a926d80b2e`
- `HERMES_LOGICAL_OWNER=20260803_100203_2a8a55`
- `MANAGING_DIRECTOR_SESSION_UUID=UNREGISTERED_IN_PINE_DO_NOT_GUESS`
- `COMPANY_CONTROL_PROTOCOL=RICHARD-COMPANY-CONTROL-v1`
- `COMPANY_CONTROL_PROTOCOL_SHA=0df93c7a2d31e235915d61712c17d28c822e7da9`
- `MIGRATION_STATE=CUTOVER_READY`
- `EFFECTIVE_GOVERNANCE=LEGACY_GOVERNING_UNTIL_EXPLICIT_ARCHITECT_V1_CUTOVER`
- `GENERAL_CONTROL_HIGH_WATER=5967092755`
- `PROJECT_ARCHITECT_BOARD_HIGH_WATER=5962793620`
- `ARCHITECT_CONTROL_HIGH_WATER=5966949420`
- `MANAGING_DIRECTOR_CONTROL_HIGH_WATER=5963021075`
- `ISSUE2_BINDING_COMMENT_ID=5967135600`
- `PINE_BUILD4_ISOLATION=PERMANENT`
- `CROSS_PROJECT_FALLBACK=FORBIDDEN`
- `UNRESOLVED_CROSS_SURFACE_CONFLICT=NONE`
- `SEEN_NE_CONSUMED=LOCKED`
- `UNRESOLVED_AUTHORITY_CONFLICT_POLICY=FAIL_CLOSED_AND_ROUTE_UPWARD`
- `PRODUCT_PACKET_5962813500_STATE=SUSPENDED_PRESERVED`
- `PRESERVED_PRODUCT_FINDINGS_COMMENT=5962861901`
- `CONTROL_ALIGNMENT_IMPLEMENTATION=IMPLEMENTED_FOCUSED_GREEN_PENDING_CONTROLLER_ADJUDICATION`
- Company chain: richard:operator -> company:managing-director -> gpt:project-architect -> gpt:reviewer-controller -> hermes:implementation-owner.
- Historical gpt:mission-oversight provenance is preserved; mapped Project Architect identity does not authorise direct Hermes UI contact. Hermes requests/rulings continue through the bound Reviewer/Controller. No MD UUID guessing or other-project fallback.
- Product packet5962813500 stays suspended; findings remain in comment5962861901, not copied into product registries.
- Discovery/fail-closed implementation is focused-test GREEN via `python -m control_plane.registry discover`; independent adjudication remains pending. No V1_GOVERNING cutover is performed by this alignment.
