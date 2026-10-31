# Agent instructions

This repository holds small standalone helpers for agterm and companion tools.

## Changes

- Keep helpers standalone. Prefer the Python standard library or POSIX shell.
- Preserve command arguments and target the caller's session or pane explicitly.
- Keep tests in each script behind `--test`.
- Tests must use fake external commands and temporary directories. `scripts/check_package.py`
  is the exception for `git`: its tests run real `git` on temporary repositories with no network.
- Tests must not launch real agents or change live terminal sessions.
- Run each changed script with `--test`.
- Keep executable permissions and update the README when usage changes.

## Releases

To release a new version of the plugin, raise `version` to the same value in both manifests
(`plugins/agt-extra/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`) in a pull
request, and release from `main` after it is merged. The release version must be the same as
`version` in `plugin.json`, including for a release that changes only a script. Users get a new
version only through that field on `main`.
Immediately before creating the release tag, run `python3 scripts/check_package.py --release <tag>`
with the selected tag, and stop if it fails. It checks that the tag is `v` plus that version, that
the checkout is clean, and that `HEAD` is the commit of `main` on `origin`.

## Writing

- Use Plain Language for prose and agent-facing files.
- Lead with the main point. Use common words, plain verbs and active voice.
- Keep sentences short. State one claim per sentence.
- Use one term for the same item. Use `must` for requirements.
- State instructions directly. Remove repeated or unnecessary words.
- Name the approach to use and when an alternative applies.
- Keep exact identifiers, commands, paths, quotations and the full technical meaning.
