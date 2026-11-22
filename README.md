# agterm-extras

A plugin for [agterm](https://github.com/umputun/agterm) and companion tools. It supports
Claude Code and the Codex CLI.

| Item | Type | Path |
|---|---|---|
| `agt-extra` | Claude Code and Codex plugin | `plugins/agt-extra` |
| `check_package.py` | Release check, runs from this checkout | `scripts/check_package.py` |

## agt-extra

The `say-hello` skill tests communication with the agent in the other pane.

| Agent | Command |
|---|---|
| Claude Code | `/agt-extra:say-hello` |
| Codex | `$say-hello` |

### Install in Claude Code

```
/plugin marketplace add cloud-simple/agterm-extras
/plugin install agt-extra@agterm-extras
```

To try a local checkout without installing:

```sh
claude --plugin-dir plugins/agt-extra
```

### Install in Codex

```sh
codex plugin marketplace add cloud-simple/agterm-extras
codex plugin add agt-extra@agterm-extras
```

To try a local checkout, run `codex plugin marketplace add .` from the checkout and
then run `codex plugin add agt-extra@agterm-extras`. Start a new session and use `/hooks`
to review and trust the plugin's `UserPromptSubmit` hook. The hook sends the hello and reports
the result. It also uses `codex queue` to deliver the timeout to the same Codex session.

### say-hello

`say-hello` sends one hello to the agent in the other pane of the split and prints one of
these lines:

- `OK: <agent> is available`
- `ERR: <agent> is not available`
- `ERR: no agent is available in the other pane`

`<agent>` is `Codex` or `Claude Code`, whichever serves the other pane's mailbox.

The plugin does not include the message transport. It uses agterm's pane mailboxes
through the
[two-agent-mailbox-chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat)
recipe from the agterm cookbook, which needs agterm 0.40.0 or later. The recipe serves
Codex and Claude Code. Install it first, following every step of its Setup section for
the agents you run:

- The `mailbox-chat.py` command on `PATH`.
- The Claude Code hooks in `~/.claude/settings.json`. This Claude Code needs them to
  receive the answer, and a Claude Code in the other pane needs them to receive the
  hello. A running Claude Code normally loads new hooks by itself. If `/hooks` does
  not list them, restart Claude Code.
- The `mailbox-chat` skill for each agent in the other pane: `~/.claude/skills/mailbox-chat`
  for Claude Code, `~/.codex/skills/mailbox-chat` for Codex. The agent needs it to send
  its answer back.
- For Codex: its `SessionStart` hook and sandbox rules, and agterm's `on message` hook.
- An agterm session with a split, and the agent running in the other pane. Start Codex
  with `--no-daemon` and a first prompt, as the recipe's Setup shows. Codex takes no
  messages until its first prompt runs.

In Claude Code, type `/agt-extra:say-hello`. In Codex, type `$say-hello` by itself.
Codex also accepts `agt-extra:say-hello` by itself.

1. The skill runs `mailbox-chat.py status`. If no running agent serves the other pane,
   it prints `ERR: no agent is available in the other pane` and sends nothing.
2. It sends the hello. If the send fails, it prints `ERR: <agent> is not available`.
3. It prints `Hello sent. Waiting up to 90 seconds for <agent>.` and ends the turn. A
   Claude Code that is mid-turn reads the hello only when that turn ends.
4. If the agent answers before the timeout, it prints `OK: <agent> is available`.
   Codex checks that the reply includes the code from its hello.
5. After 90 seconds without a reply, it prints `ERR: <agent> is not available`. A
   reply after that result prints `OK: <agent> is available (late reply)`.

Claude Code shows the reply in a collapsed `chat received` line. Codex shows the reply
and the timeout as queued messages.

## Releases

`main` is protected: every change reaches it through a pull request with a squash merge. Direct
pushes, force pushes and deleting `main` are refused.

To release a new version, raise `version` to the same value in
`plugins/agt-extra/.claude-plugin/plugin.json`, `plugins/agt-extra/.codex-plugin/plugin.json`,
and `.claude-plugin/marketplace.json` in a pull request. Release from `main` after the pull
request merges. Use the same version for the release, including when the release changes only a script. The install
commands above read the plugin from the default branch, so a version that is not merged is not
released. The same pull request adds the new version's section at the top of
[CHANGELOG.md](CHANGELOG.md), and that section is the release notes. The release tag goes on the
merged commit, with no commit after it.

Immediately before creating the release tag, run this command with the selected tag, and stop if
it fails:

```sh
python3 scripts/check_package.py --release <tag>
```

It checks that the tag is `v` plus that version, that the checkout is clean, and that `HEAD` is the
commit of `main` on `origin`.

## Tests

```sh
python3 scripts/check_package.py --test
python3 plugins/agt-extra/.codex-plugin/say-hello.py --test
```

The release tests run real `git` on temporary repositories with no network. The Codex hook
tests use fake commands and leave live panes alone.
