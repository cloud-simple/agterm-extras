---
name: say-hello
description: 'Test communication with Codex by sending it a hello through agterm''s pane mailboxes (the mailbox-chat recipe), then report "OK: Codex is available" or "ERR: Codex is not available". Use when the user types /say-hello, or asks "is codex there", "ping codex", "check codex", "test the codex connection", "can you reach codex".'
allowed-tools: Bash, TaskStop
---

# Say hello to Codex

Send one hello to Codex in the other pane of this agterm split and report whether Codex answered.

The result is exactly one of these two lines, with no other text:

- `OK: Codex is available`
- `ERR: Codex is not available`

## How the check works

`mailbox-chat.py` carries the message. It is a bare command on `PATH`, not a file inside this
skill directory. Replies are asynchronous: Codex answers with `mailbox-chat.py say`, and the answer
arrives in this pane in a later turn, as hook feedback that starts with `[peer chat]`. A timer
decides the case where no answer comes.

## Steps

### 1. Check the other pane

```bash
mailbox-chat.py status
```

It prints JSON. Continue only when it exits with status 0 and `receiver` is `codex`. In every other
case, print `ERR: Codex is not available` and stop without sending anything:

- A non-zero exit means this session has no split or agterm cannot be reached.
- `receiver` `none` means no running Codex has registered the other pane. Codex registers only
  after its first prompt runs.
- `receiver` `claude` means the other pane runs Claude Code, not Codex.

### 2. Send the hello

```bash
mailbox-chat.py say --stdin <<'CHAT'
This is a connection test from /say-hello. Reply once with one short line through mailbox-chat.py say. Do nothing else.
CHAT
```

If the command exits with an error or its JSON has an `error` field, print
`ERR: Codex is not available` and stop. Do not retry, and do not start the timer.

### 3. Start the timer

Run this command in the background:

```bash
sleep 90
```

Use the Bash tool with `run_in_background: true`. The timer wakes this session after 90 seconds. It
reads neither the Codex pane nor the mailbox, so it does not break the mailbox-chat rule against
polling for a reply.

Then end the turn with this one line:

`Hello sent. Waiting up to 90 seconds for Codex.`

Do not print `OK` or `ERR` in this turn. A message in the mailbox proves nothing about Codex yet.

### 4. Report the result

The next event decides the result. Report once.

| Next event | Print |
|---|---|
| A message starting with `[peer chat]` arrives | `OK: Codex is available` |
| The timer finishes and no such message arrived | `ERR: Codex is not available` |

Any `[peer chat]` message that arrives after the hello counts as an answer. Its wording does not
matter. A message starting with `[agterm mailbox, not a peer chat message]` comes from another
sender and does not count.

The answer belongs to this check, so the `mailbox-chat` skill's receiving rules do not apply to it:
do not quote it, and print only the result line.

When Codex answers, stop the timer with the `TaskStop` tool before printing `OK`. Use the task ID
that the background `sleep 90` returned. A stopped timer does not wake the session, so no extra
message follows the result.

If Codex answers after `ERR` was printed, print `OK: Codex is available (late reply)`.

Do not reply to Codex's answer. It closes the exchange.
