# Existing proven Pine transport, made durable

These are handoff copies of the already exercised Pine commissioning helpers, NOT a new architecture/watchdog/service. Exact Controller-only binding, composer selector, single-lock and held-CDP MutationObserver mechanism remain. Changes remove hidden prior-nonce scratch dependency, prevent duplicate resends, positively print exact outbound message-ID before waiting, add `--read` re-arm of the same request, and suppress credential-helper child console windows. No ChatGPT API polling/browser launch.

Prerequisites: existing authenticated Edge CDP `127.0.0.1:9223`, exact bound Controller tab, Python with `websocket-client`, existing Git credential store. Missing browser/auth is a classified blocker, never permission to kill/relaunch the operator's browser or request passwords in chat.

Post durable RESULT first using `pine_commissioning_io.post(result_body)` (it reads back exact posted comment).
Create one retained request file with `REQUEST_NONCE=<unique>` on its own line, result comment/path/hash/identity pointers, `REQUEST=NEXT_INSTRUCTION_OR_EXPLICIT_HOLD_STOP_SHUTDOWN`, and explicit stand-down/next-instruction language. Never use a prior probe nonce.

From repository root:
```
python docs/handoff/transport/pine_commissioning_send.py <absolute-request-file>
```
Positive proof prints `REQUEST_SENT_CONFIRMED=YES ... ANCHOR_MESSAGE_ID=...`. This same invocation blocks on the exact own request and prints/writes the completed NEW Controller reply; caller must READ and consume it.

If interrupted/expired, leave `~/.hermes/state/pine-controller/send.lock` held and immediately re-arm READ-ONLY:
```
python docs/handoff/transport/pine_commissioning_send.py --read <same-absolute-request-file>
```
No resend/second request, no passive idle. A missing virtualised DOM anchor is NOT proof of no reply; classify delivery/read unavailable and recover the exact anchor without a new send or ChatGPT API polling. Default state path can be explicitly relocated with PINE_CONTROLLER_STATE_DIR, preserving outstanding lock/anchor. Request and `.reply.json` are retained transport evidence, never fabricated directives. Controller authority comes from actual read content, not the lock or an observer success bit.

Routine startup does not read transport source; WORKER_START+CURRENT_STATE+packet suffice. If restoring on a different machine, configure authenticated existing CDP/credentials through permitted human gates, preserve canonical identities/evidence, and reuse these helpers rather than rebuilding the control system. Never run a lower-model simulation merely to validate these documents.
