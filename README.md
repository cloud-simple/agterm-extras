# agterm-extras

Small scripts and Claude Code plugins for [agterm](https://github.com/umputun/agterm)
and companion tools.

| Item | Type | Path |
|---|---|---|
| `codex-peer` | Script | `scripts/codex-peer` |
| `say-hello` | Claude Code plugin | `plugins/say-hello` |

## Install

`make install` installs the scripts only. Install plugins through Claude Code; see
[say-hello](#say-hello).

Run `make` or `make install` from this directory to install the scripts in
`~/.local/bin`. This directory must be on `PATH`.

Set `PREFIX` to install elsewhere:

```sh
make install PREFIX=/usr/local
```

## codex-peer

Launch Codex with a separate config profile for the current agterm pane. The profile
sets `shell_environment_policy.set.AGTERM_SESSION_ID` so commands run by Codex can
identify their agterm session. The wrapper selects it with `--profile` instead of
adding `-c`.

Requires Python 3.11+, `agtermctl`, and Codex with support for
`<name>.config.toml` profiles. All three commands must be on `PATH`.

Use it like Codex:

```sh
codex-peer
codex-peer resume --last
```

`resume --last` continues the most recent Codex session for the current directory
without opening the session picker. Run `codex-peer resume` to choose a session.

Profiles must live directly in `$CODEX_HOME`, or `~/.codex` when it is unset.
Codex's `--profile` option rejects directory separators, so it cannot select files
in a `tmp/` or `.tmp/` subdirectory.

Profile names combine the agterm session name and pane ID.
Each launch replaces its generated profile.
Renaming a session creates a new filename; old profiles remain.

The wrapper owns profile selection inside agterm, so an additional `--profile`
argument is rejected. Without `AGTERM_SESSION_ID`, it runs Codex unchanged.

## say-hello

A Claude Code plugin that tests communication with Codex. `/say-hello` sends one
hello to Codex in the other pane and prints one of these lines:

- `OK: Codex is available`
- `ERR: Codex is not available`

The plugin does not include these parts. Install them first:

- The `peer-chat` skill, installed in `~/.claude/skills/peer-chat`.
- The `peer-chat.py` command on `PATH`.
- An agterm session with a split, and Codex running in the other pane.

Install the plugin from this repository's marketplace:

```
/plugin marketplace add cloud-simple/agterm-extras
/plugin install say-hello@agterm-extras
```

To try a local checkout without installing:

```sh
claude --plugin-dir plugins/say-hello
```

Type `/say-hello`. The full name is `/say-hello:say-hello`.

1. The skill sends the hello. If the send fails, it prints `ERR: Codex is not available`.
2. It prints `Hello sent. Waiting up to 90 seconds for Codex.` and ends the turn.
3. If Codex answers within 90 seconds, it prints `OK: Codex is available`.
4. If Codex does not answer, it prints `ERR: Codex is not available`.

Codex's answer shows in the pane as a `Chat from Codex:` prompt. This is how
`peer-chat` delivers a reply, so it cannot be hidden.

## Tests

```sh
./scripts/codex-peer --test
```

The built-in tests use fake commands and temporary directories. They cover profile
creation, pane identity, argument handling and failures. Shared-server behavior is
not covered.
