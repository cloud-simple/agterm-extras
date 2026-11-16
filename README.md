# agterm-extras

A Claude Code plugin for [agterm](https://github.com/umputun/agterm) and companion tools.

| Item | Type | Path |
|---|---|---|
| `agt-extra` | Claude Code plugin | `plugins/agt-extra` |
| `check_package.py` | Release check, runs from this checkout | `scripts/check_package.py` |

## agt-extra

A Claude Code plugin that holds the skills in this repository.

| Skill | Command | Purpose |
|---|---|---|
| `say-hello` | `/agt-extra:say-hello` | Test communication with the agent in the other pane |

Install the plugin from this repository's marketplace:

```
/plugin marketplace add cloud-simple/agterm-extras
/plugin install agt-extra@agterm-extras
```

To try a local checkout without installing:

```sh
claude --plugin-dir plugins/agt-extra
```

### say-hello

`/agt-extra:say-hello` sends one hello to the agent in the other pane of the split and
prints one of these lines:

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

Type `/agt-extra:say-hello`.

1. The skill runs `mailbox-chat.py status`. If no running agent serves the other pane,
   it prints `ERR: no agent is available in the other pane` and sends nothing.
2. It sends the hello. If the send fails, it prints `ERR: <agent> is not available`.
3. It prints `Hello sent. Waiting up to 90 seconds for <agent>.` and ends the turn. A
   Claude Code that is mid-turn reads the hello only when that turn ends.
4. If the agent answers within 90 seconds, it prints `OK: <agent> is available`.
5. If the agent does not answer, it prints `ERR: <agent> is not available`. A later
   answer prints `OK: <agent> is available (late reply)`.

The answer shows in the pane as a collapsed `chat received` line. This is how
mailbox-chat delivers a reply, so it cannot be hidden.

## Releases

`main` is protected: every change reaches it through a pull request with a squash merge. Direct
pushes, force pushes and deleting `main` are refused.

To release a new version, raise `version` to the same value in both
`plugins/agt-extra/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` in a pull
request, and release from `main` after it is merged. The release version must be the same as
`version` in `plugin.json`, including for a release that changes only a script. The install
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
```

The `check_package.py` tests run real `git` on temporary repositories with no network. They
cover the release checks.
