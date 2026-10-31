# agterm-extras

Small scripts and Claude Code plugins for [agterm](https://github.com/umputun/agterm)
and companion tools.

| Item | Type | Path |
|---|---|---|
| `codex-peer` | Script | `scripts/codex-peer` |
| `agt-extra` | Claude Code plugin | `plugins/agt-extra` |
| `check_package.py` | Release check, not installed | `scripts/check_package.py` |

## Install

`make install` installs the scripts only. Install the plugin through Claude Code; see
[agt-extra](#agt-extra). `make install` leaves out `scripts/check_package.py`, which runs only from
this checkout.

Run `make` or `make install` from this directory to install the scripts in
`~/.local/bin`. This directory must be on `PATH`.

The scripts install to `$PREFIX/bin`. Set `PREFIX` to install elsewhere. This
command installs them in `/usr/local/bin`:

```sh
make install PREFIX=/usr/local
```

## codex-peer

Launch Codex with the current agterm session ID. The wrapper adds
`-c shell_environment_policy.set.AGTERM_SESSION_ID="<session-id>"` so commands run by
Codex can identify their agterm session. It writes no config files, so Codex keeps
the trust saved in its base config across restarts and new panes.

Requires Python 3 and `codex` on `PATH`. `codex-peer --test` requires Python 3.11 or
newer.

Use it like Codex:

```sh
codex-peer
codex-peer resume --last
```

`resume --last` continues the most recent Codex session for the current directory
without opening the session picker. Run `codex-peer resume` to choose a session.

The wrapper forwards all other arguments unchanged, including `--profile`. Without
`AGTERM_SESSION_ID`, it runs Codex unchanged. If `AGTERM_SESSION_ID` is not a UUID, it
exits with status 2 and does not start Codex.

Earlier versions generated `agterm-*.config.toml` profiles in `$CODEX_HOME`, or
`~/.codex` when it is unset. The wrapper no longer selects, changes or deletes these
files.

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

The plugin does not include these parts. Install them first:

- The `peer-chat` skill for Claude Code, installed in `~/.claude/skills/peer-chat`.
- The `peer-chat` skill for Codex, installed in `~/.codex/skills/peer-chat`. Codex
  needs it to send its answer back.
- The `peer-chat.py` command on `PATH`.
- An agterm session with a split, and Codex running in the other pane.

Note: Codex must run with `shell_environment_policy.set.AGTERM_SESSION_ID` set.
Start it with [codex-peer](#codex-peer), which sets this.

Type `/agt-extra:say-hello`.

1. The skill sends the hello. If the send fails, it prints `ERR: Codex is not available`.
2. It prints `Hello sent. Waiting up to 90 seconds for Codex.` and ends the turn.
3. If Codex answers within 90 seconds, it prints `OK: Codex is available`.
4. If Codex does not answer, it prints `ERR: Codex is not available`.

Codex's answer shows in the pane as a `Chat from Codex:` prompt. This is how
`peer-chat` delivers a reply, so it cannot be hidden.

## Releases

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
./scripts/codex-peer --test
python3 scripts/check_package.py --test
```

The `codex-peer` tests use fake commands and temporary directories. They cover argument
forwarding, config preservation and a bad session ID. Shared-server behavior is not
covered.

The `check_package.py` tests run real `git` on temporary repositories with no network. They
cover the release checks.
