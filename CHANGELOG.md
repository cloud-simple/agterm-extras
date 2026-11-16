# Changelog

Each section is one release. Its version is the `version` in
`plugins/agt-extra/.claude-plugin/plugin.json`, and its tag is `v` plus that version. Numbers in
parentheses are pull requests.

## [0.2.0] - 2026-11-14

### Removed

- The `codex-peer` script and the `Makefile` that installed it. The mailbox transport that
  `say-hello` uses needs no wrapper around Codex. (#12)

### Changed

- The README says that a running Claude Code normally loads new hooks by itself. Restart it only
  when `/hooks` does not list them. (#11)
- `main` takes changes only through pull requests with a squash merge. Release docs name no hosting
  platform and no outside release tool. (#10)

## [0.1.2] - 2026-11-14

### Changed

- `say-hello` sends its hello through agterm's pane mailboxes with `mailbox-chat.py`, from the
  two-agent-mailbox-chat recipe in the agterm cookbook. It replaces the `peer-chat` skill. The
  skill runs `mailbox-chat.py status` first and sends nothing unless a running Codex serves the
  other pane. (#9)

## [0.1.1] - 2026-10-31

### Added

- The release rule: raise `version` in both manifests in a pull request, and release from `main`
  after it is merged. (#7)
- `scripts/check_package.py --release <tag>`. It checks the tag against both manifests, a clean
  checkout, and `HEAD` against `main` on `origin`. (#7)

## [0.1.0] - 2026-10-31

### Added

- The `agt-extra` plugin with the `say-hello` skill. The skill sends one hello to Codex in the other
  pane through the `peer-chat` skill and reports whether Codex answered. (#2, #4, #5)
- The `codex-peer` script. It starts Codex with the agterm session ID, passed with
  `-c shell_environment_policy.set.AGTERM_SESSION_ID`. (#1, #6)
- `make install`, which installs the scripts in `$PREFIX/bin`. (#1, #3)
