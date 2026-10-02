# Worker start — read only this and the named inputs
1. Read `CURRENT_STATE.json` here. Only GPT contact: `6abf60c8-4598-83eb-bc80-57a926d80b2e`; Oversight is human-only; Build-4 is out of scope.
2. Read the one Controller-supplied task packet; validate against `BOUNDED_TASK_PACKET.schema.json`. Verify its directive comment directly in Pine Issue #1 and state version/high-water. Do NOT read full history unless explicitly requested or the exact source is genuinely missing/conflicting.
3. Read `CONTINUOUS_CONTROLLER_LOOP.md` and `ANTI_DRIFT.md` once on startup. Read only packet-named input artifacts/evidence. Verify exact task baseline and actual Git status; preserve unrelated dirt.
4. Execute only REQUIRED_ACTIONS within surface/budget. Do not infer or choose a follow-on task.
5. Return `BOUNDED_RESULT.schema.json` evidence. Post to Pine Issue #1, read back exact comment, then perform the explicit next-instruction-request -> confirmed send -> anchored push wait -> READ response cycle. Continue from that response, not passive waiting.
6. Missing/conflicting authority, exhausted budget or unexpected blocker: post BLOCKED/FAIL with exact evidence and request Controller correction; READ the response. Only explicit Controller HOLD/STOP/SHUTDOWN, a genuine HUMAN_ONLY gate, or Richard's explicit status-only override interrupts the loop.
No simulation/model switch is authorised by startup. Current Phase-1 restrictions are NOT permanent exclusions from the overall platform mission.
