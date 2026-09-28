# agterm-extras

Small scripts for [agterm](https://github.com/umputun/agterm) and companion tools.

## Install

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

Profiles live in `$CODEX_HOME`, or `~/.codex` when it is unset. Their names combine
the agterm session name and pane ID. Each launch replaces its generated profile.
Renaming a session creates a new filename; old profiles remain.

The wrapper owns profile selection inside agterm, so an additional `--profile`
argument is rejected. Without `AGTERM_SESSION_ID`, it runs Codex unchanged.

## Tests

```sh
./scripts/codex-peer --test
```

The built-in tests use fake commands and temporary directories. They cover profile
creation, pane identity, argument handling and failures. Shared-server behavior is
not covered.
