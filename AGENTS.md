# Agent instructions

This repository holds small standalone helpers for agterm and companion tools.

## Changes

- Keep helpers standalone. Prefer the Python standard library or POSIX shell.
- Preserve command arguments and target the caller's session or pane explicitly.
- Keep tests in each script behind `--test`.
- Tests must use fake external commands and temporary directories.
- Tests must not launch real agents or change live terminal sessions.
- Run each changed script with `--test`.
- Keep executable permissions and update the README when usage changes.

## Writing

- Use Plain Language for prose and agent-facing files.
- Lead with the main point. Use common words, plain verbs and active voice.
- Keep sentences short. State one claim per sentence.
- Use one term for the same item. Use `must` for requirements.
- State instructions directly. Remove repeated or unnecessary words.
- Name the approach to use and when an alternative applies.
- Keep exact identifiers, commands, paths, quotations and the full technical meaning.
