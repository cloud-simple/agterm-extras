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
| `say-hello` | `/agt-extra:say-hello` | Test communication with Codex |

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

`/agt-extra:say-hello` sends one hello to Codex in the other pane and prints one of
these lines:

- `OK: Codex is available`
- `ERR: Codex is not available`

The plugin does not include the message transport. It uses agterm's pane mailboxes
through the
[two-agent-mailbox-chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat)
recipe from the agterm cookbook, which needs agterm 0.40.0 or later. Install the recipe
first, following every step of its Setup section:

- The `mailbox-chat.py` command on `PATH`.
- The `mailbox-chat` skill for Codex, installed in `~/.codex/skills/mailbox-chat`.
  Codex needs it to send its answer back.
- The Claude Code hooks in `~/.claude/settings.json`. A running Claude Code normally
  loads new hooks by itself. If `/hooks` does not list them, restart Claude Code.
- The Codex `SessionStart` hook and sandbox rules, and agterm's `on message` hook.
- An agterm session with a split, and Codex running in the other pane. Start Codex
  with `--no-daemon` and a first prompt, as the recipe's Setup shows. Codex takes no
  messages until its first prompt runs.

Type `/agt-extra:say-hello`.

1. The skill runs `mailbox-chat.py status`. If no running Codex serves the other
   pane, it prints `ERR: Codex is not available` and sends nothing.
2. It sends the hello. If the send fails, it prints `ERR: Codex is not available`.
3. It prints `Hello sent. Waiting up to 90 seconds for Codex.` and ends the turn.
4. If Codex answers within 90 seconds, it prints `OK: Codex is available`.
5. If Codex does not answer, it prints `ERR: Codex is not available`.

Codex's answer shows in the pane as a collapsed `chat received` line. This is how
mailbox-chat delivers a reply, so it cannot be hidden.

## Releases

`main` is protected: every change reaches it through a pull request with a squash merge. Direct
pushes, force pushes and deleting `main` are refused.

To release a new version, raise `version` to the same value in both
`plugins/agt-extra/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` in a pull
request, and release from `main` after it is merged. The release version must be the same as
`version` in `plugin.json`, including for a release that changes only a script. The install
commands above read the plugin from the default branch, so a version that is not merged is not
released.

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
