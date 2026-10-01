---
name: say-hello
description: 'Test communication with Codex by sending it a hello through the peer-chat skill, then report "OK: Codex is available" or "ERR: Codex is not available". Use when the user types /say-hello, or asks "is codex there", "ping codex", "check codex", "test the codex connection", "can you reach codex".'
allowed-tools: Skill, Bash, TaskStop
---

# Say hello to Codex

Send one hello to Codex and report whether Codex answered.

The result is exactly one of these two lines, with no other text:

- `OK: Codex is available`
- `ERR: Codex is not available`

## How the check works

The `peer-chat` skill carries the message. Its replies are asynchronous: Codex answers by typing a
new prompt into this pane, which opens with `Chat from Codex: `. The answer therefore arrives in a
later turn, not in the turn that sends the hello. A timer decides the case where no answer comes.

## Steps

### 1. Send the hello

Load the `peer-chat` skill and follow its sending rules. Send this message:

```bash
peer-chat.py --to codex --stdin <<'CHAT'
Hello from /say-hello. This is a connection test. Please reply with one short line through peer-chat. Do nothing else.
CHAT
```

If the command exits with an error, print `ERR: Codex is not available` and stop. Do not retry, and
do not start the timer. A failed send means the split is missing, Codex is not running in the other
pane, or the pane refused the text.

### 2. Start the timer

Run this command in the background:

```bash
sleep 90
```

Use the Bash tool with `run_in_background: true`. The timer wakes this session after 90 seconds. It
does not read the Codex pane, so it does not break the `peer-chat` rule against watching for a reply.

Then end the turn with this one line:

`Hello sent. Waiting up to 90 seconds for Codex.`

Do not print `OK` or `ERR` in this turn. A typed message proves nothing about Codex yet.

### 3. Report the result

The next event decides the result. Report once.

| Next event | Print |
|---|---|
| A prompt opening with `Chat from Codex: ` arrives | `OK: Codex is available` |
| The timer finishes and no such prompt arrived | `ERR: Codex is not available` |

Any `Chat from Codex: ` prompt that arrives after the hello counts as an answer. Its wording does not
matter.

When Codex answers, stop the timer with the `TaskStop` tool before printing `OK`. Use the task ID
that the background `sleep 90` returned. A stopped timer does not wake the session, so no extra
message follows the result.

If Codex answers after `ERR` was printed, print `OK: Codex is available (late reply)`.

Do not reply to Codex's answer. It is a closing acknowledgement, and `peer-chat` ends the exchange
there.
