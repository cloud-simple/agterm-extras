---
name: say-hello
description: 'Test communication with the agent in the other pane of this agterm split (Codex or Claude Code) by sending it a hello through agterm''s pane mailboxes (the mailbox-chat recipe), then report "OK: <agent> is available" or an ERR line. Use when the user types /say-hello, or asks "is codex there", "is claude there", "ping codex", "ping the other pane", "check codex", "check the other agent", "test the codex connection", "test the peer connection", "can you reach codex", "can you reach the other agent".'
allowed-tools: Bash, TaskStop
---

# Say hello to the other pane

Send one hello to the agent in the other pane of this agterm split and report whether it answered.

## Codex

The plugin's `UserPromptSubmit` hook runs the check when the prompt is `$say-hello` or
`say-hello` by itself. Both forms also accept `agt-extra:` before `say-hello`. On that turn
and on reply or timeout turns, print the result the hook provides. Call no tools. If the hook
marks an event as stale, end the turn without replying.

If the user asks to test the connection in other words, tell them to enter `$say-hello` by
itself. If the hook gave no result for that prompt, tell them to check that the plugin's hook
is trusted in `/hooks`.

## Claude Code

The result is exactly one of these lines, with no other text. `<agent>` is the agent's name from
the table in step 1.

- `OK: <agent> is available`
- `ERR: <agent> is not available`
- `ERR: no agent is available in the other pane`

## How the check works

`mailbox-chat.py` carries the message. It is a bare command on `PATH`, not a file inside this
skill directory. It reaches any agent that serves the other pane's mailbox through the recipe.
Replies are asynchronous: the agent answers with `mailbox-chat.py say`, and the answer arrives in
this pane in a later turn, as hook feedback that starts with `[peer chat]`. A timer decides the
case where no answer comes.

## Steps

### 1. Check the other pane

```bash
mailbox-chat.py status
```

It prints JSON. Its `receiver` field names the agent that serves the other pane:

| `receiver` | `<agent>` |
|---|---|
| `codex` | `Codex` |
| `claude` | `Claude Code` |
| any other value except `none` | the value as printed |

Continue when the command exits with status 0 and `receiver` is not `none`. In every other case,
print `ERR: no agent is available in the other pane` and stop without sending anything:

- A non-zero exit means this session has no split or agterm cannot be reached.
- `receiver` `none` means no running agent serves the other pane's mailbox. Codex serves it only
  after its first prompt runs. Claude Code serves it only with the recipe's hooks loaded.

### 2. Send the hello

```bash
mailbox-chat.py say --stdin <<'CHAT'
This is a connection test from /say-hello. Reply once with one short line through mailbox-chat.py say. Do nothing else.
CHAT
```

If the command exits with an error or its JSON has an `error` field, print
`ERR: <agent> is not available` and stop. Do not retry, and do not start the timer.

### 3. Start the timer

Run this command in the background:

```bash
sleep 90
```

Use the Bash tool with `run_in_background: true`. The timer wakes this session after 90 seconds. It
reads neither the other pane nor the mailbox, so it does not break the mailbox-chat rule against
polling for a reply.

Then end the turn with this one line:

`Hello sent. Waiting up to 90 seconds for <agent>.`

When the `say` reply has `peerBusy` `true`, end the turn with this line instead:

`Hello sent. <agent> is mid-turn, so it reads the hello when that turn ends. Waiting up to 90 seconds.`

Do not print `OK` or `ERR` in this turn. A message in the mailbox proves nothing about the agent yet.

### 4. Report the result

The next event decides the result. Report once.

| Next event | Print |
|---|---|
| A message starting with `[peer chat]` arrives | `OK: <agent> is available` |
| The timer finishes and no such message arrived | `ERR: <agent> is not available` |

Any `[peer chat]` message that arrives after the hello counts as an answer. Its wording does not
matter. A message starting with `[agterm mailbox, not a peer chat message]` comes from another
sender and does not count.

The answer belongs to this check, so the `mailbox-chat` skill's receiving rules do not apply to it:
do not quote it, and print only the result line.

When the agent answers, stop the timer with the `TaskStop` tool before printing `OK`. Use the task
ID that the background `sleep 90` returned. A stopped timer does not wake the session, so no extra
message follows the result.

If the agent answers after `ERR` was printed, print `OK: <agent> is available (late reply)`.

Do not reply to the agent's answer. It closes the exchange.
