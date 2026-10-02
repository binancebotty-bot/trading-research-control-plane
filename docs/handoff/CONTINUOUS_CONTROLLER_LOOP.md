# Exact continuous Controller continuation
NEXT_INSTRUCTION_REQUEST_REQUIRED=YES
WAIT_ANCHORED_TO_OWN_REQUEST=YES
CYCLE_FINAL_ACTION=READ_CONTROLLER_RESPONSE_TO_OWN_REQUEST
NEXT_TASK_SOURCE=CONTROLLER_RESPONSE
PASSIVE_WAIT_AFTER_REPORT=FORBIDDEN
RICHARD_RELAY_REQUIRED=NO

1. Consume ONE authenticated bounded Controller packet; execute only it.
2. Post bounded result/evidence to `binancebotty-bot/trading-research-control-plane` Issue #1. Read back the exact target comment before claiming posted.
3. Compose ONE explicit request: `PINE_NEXT_INSTRUCTION_REQUEST REQUEST_NONCE=<unique> RESULT_COMMENT_ID=<actual> request=NEXT_BOUNDED_INSTRUCTION_OR_EXPLICIT_HOLD_STOP_SHUTDOWN`. Include logical owner, actual runtime, task ID and exact Controller thread. Never a report-only wake or an unanchored passive wait.
4. Use the adopted proven CDP transport: existing Edge :9223, exact URL thread `6abf60c8-4598-83eb-bc80-57a926d80b2e` ONLY, one outstanding send lock, scoped visible writable `[data-composer-body]` input, positive idle before send, trusted insertion and actual send click. Preserve operator text. No new browser, daemon or ChatGPT API polling.
5. Positively confirm THIS request appears as a user message in THAT conversation and capture actual message ID. Empty composer alone is insufficient. Anchor wait to that exact request/message, not newest assistant, old nonce or old catch-up directive.
6. Use one held CDP socket with MutationObserver push-wait + catch-up. Accept only a subsequent nonempty completed assistant response. Require no Stop control and positively returned idle composer control. Print and READ full reply. If it references a durable instruction, fetch that exact Pine comment and validate role/thread/binding.
7. READ the response as the final action of the cycle. Consume it as next authority; begin next bounded packet and repeat. PASS/FAIL/BLOCKED never implies stand-down.
8. Only explicit Controller HOLD/STOP/SHUTDOWN, genuine HUMAN_ONLY gate or Richard's explicit status-only override permits interruption. Missing packet fields: request the smallest Controller clarification, never invent task scope.

Timeout/interruption: retain send anchor/lock and re-arm READ/push-wait for the SAME outstanding request; do not resend or release lock merely because a timer expired. A held lock means READ, not another send. Connection loss: report exact channel failure, bounded reconnect/read of same request only; never kill/restart browser or silently drop loop.

Transport source pointers for current machine: `C:/Users/wigmore/.hermes/cache/scratch/pine_commissioning_io.py` and `pine_commissioning_send.py`. These are already executed insert/click/lock/anchored MutationObserver transport, not new architecture. Durable snapshots are in `docs/handoff/transport/`; run from there when scratch was pruned. Preserve controller-only assertion. Read mode must never send.
