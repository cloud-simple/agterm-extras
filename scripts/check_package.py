#!/usr/bin/env python3
"""Check this repository just before a release tag is created.

Usage: python3 scripts/check_package.py --release TAG
       python3 scripts/check_package.py --test

--release only reads. Its one network call is `git ls-remote` to origin.
It fetches nothing and changes no Git refs.
--test uses real git on temporary repositories and no network.
Exit status: 0 all checks passed, 1 a check or a test failed, 2 wrong arguments.
"""

import contextlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

PLUGIN = "agt-extra"
PLUGIN_MANIFEST = f"plugins/{PLUGIN}/.claude-plugin/plugin.json"
MARKETPLACE_MANIFEST = ".claude-plugin/marketplace.json"
RELEASE_REMOTE = "origin"
RELEASE_BRANCH = "main"
REMOTE_TIMEOUT = 30  # seconds for the lookup of main on origin
ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired)
USAGE = "Usage: python3 scripts/check_package.py [--release TAG | --test]"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, args, timeout=30):
    """Run a read-only git command in root and return the CompletedProcess.

    It never prompts. It takes no optional locks, so git status does not rewrite the index.
    On timeout it kills the process group, including the transport, and raises TimeoutExpired.
    """
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    process = subprocess.Popen(["git", "-C", str(root), *args], text=True, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.communicate(timeout=5)  # A process outside the group may hold the pipes.
        raise
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def read_head_json(root, path):
    blob = git(root, ["show", f"HEAD:{path}"])
    require(blob.returncode == 0, f"Cannot read {path} from HEAD: {blob.stderr.strip()}")
    return json.loads(blob.stdout)


def manifest_version(root):
    """Return the version that both manifests in HEAD set for the plugin."""
    plugin_version = read_head_json(root, PLUGIN_MANIFEST).get("version")
    entries = [entry for entry in read_head_json(root, MARKETPLACE_MANIFEST).get("plugins", [])
               if entry.get("name") == PLUGIN]
    require(len(entries) == 1, f"{MARKETPLACE_MANIFEST} must list {PLUGIN} once")
    marketplace_version = entries[0].get("version")
    require(isinstance(plugin_version, str) and plugin_version, f"{PLUGIN_MANIFEST} must set version")
    require(plugin_version == marketplace_version,
            f"Both manifests in HEAD must have the same version: {PLUGIN_MANIFEST} has "
            f"{plugin_version}, {MARKETPLACE_MANIFEST} has {marketplace_version}")
    return plugin_version


def check_release(root, tag):
    """Check that tag matches both manifests in HEAD, the checkout is clean,
    and HEAD is the commit of main on origin, read live from the server."""
    # Read the version from the commit being tagged. Files on disk can differ from HEAD
    # even when git status is empty, for example under git update-index --assume-unchanged.
    version = manifest_version(root)
    require(tag == f"v{version}",
            f"The release tag must be v{version}, the version of both manifests in HEAD, not {tag}")
    status = git(root, ["status", "--porcelain", "--untracked-files=all"])
    require(status.returncode == 0, f"git status failed: {status.stderr.strip()}")
    require(status.stdout == "", "The checkout must be clean: no staged, unstaged or untracked files")
    head = git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    require(head.returncode == 0, f"Cannot read HEAD: {head.stderr.strip()}")
    head = head.stdout.strip()
    ref = f"refs/heads/{RELEASE_BRANCH}"
    try:
        live = git(root, ["ls-remote", "--exit-code", RELEASE_REMOTE, ref], timeout=REMOTE_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ValueError(f"{RELEASE_REMOTE} did not answer within {REMOTE_TIMEOUT} s")
    require(live.returncode != 2, f"{RELEASE_REMOTE} has no {RELEASE_BRANCH} branch")
    require(live.returncode == 0, f"Cannot read {RELEASE_BRANCH} from {RELEASE_REMOTE}: {live.stderr.strip()}")
    lines = live.stdout.strip().splitlines()
    require(len(lines) == 1 and lines[0].split("\t")[1:] == [ref],
            f"Unexpected answer from {RELEASE_REMOTE} for {ref}: {live.stdout.strip()}")
    remote = lines[0].split("\t")[0]
    require(head == remote,
            f"HEAD {head[:12]} is not {RELEASE_BRANCH} on {RELEASE_REMOTE} ({remote[:12]}): tag only the "
            f"merged commit, after git pull --ff-only")
    print(f"PASS release {tag}: manifests, clean checkout and {RELEASE_BRANCH} on {RELEASE_REMOTE}", flush=True)


def main():
    args = sys.argv[1:]
    if args == ["--test"]:
        return run_tests()
    if len(args) != 2 or args[0] != "--release" or args[1].startswith("-"):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        check_release(Path(__file__).resolve().parent.parent, args[1])
    except ERRORS as error:
        print(f"check_package: {error}", file=sys.stderr)
        return 1
    return 0


def run_tests():
    """Check the release rules with real git on temporary repositories and no network."""
    import io
    import time
    import unittest
    from unittest import mock

    script = Path(__file__).resolve()

    class ReleaseTests(unittest.TestCase):
        def setUp(self):
            directory = tempfile.TemporaryDirectory(prefix="check-package-")
            self.addCleanup(directory.cleanup)
            self.temp = Path(directory.name)
            self.root = self.temp / "repo"
            self.remote = self.temp / "remote.git"
            environ = mock.patch.dict(os.environ)  # Restore the environment after each test.
            environ.start()
            self.addCleanup(environ.stop)
            self.isolate_git()
            self.make_repo()

        def isolate_git(self):
            """Keep the user's git settings out of the fixtures."""
            for key in [key for key in os.environ if key.startswith("GIT_")]:
                del os.environ[key]
            empty = self.temp / "empty-gitconfig"
            empty.write_text("")
            os.environ.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1")

        def git_ok(self, cwd, *args):
            result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", *args],
                                    cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)

        def write_manifests(self, plugin_version="1.2.3", marketplace_version="1.2.3"):
            plugin = self.root / PLUGIN_MANIFEST
            marketplace = self.root / MARKETPLACE_MANIFEST
            plugin.parent.mkdir(parents=True, exist_ok=True)
            marketplace.parent.mkdir(parents=True, exist_ok=True)
            plugin.write_text(json.dumps({"name": PLUGIN, "version": plugin_version}))
            marketplace.write_text(json.dumps({"plugins": [{"name": PLUGIN, "version": marketplace_version}]}))

        def make_repo(self):
            """Create a repository with the manifests and this script, and push it to a local bare origin."""
            self.root.mkdir()
            self.write_manifests()
            copy = self.root / "scripts/check_package.py"
            copy.parent.mkdir()
            copy.write_text(script.read_text())
            self.git_ok(self.temp, "init", "-q", "--bare", str(self.remote))
            self.git_ok(self.root, "init", "-q")
            self.git_ok(self.root, "add", "-A")
            self.git_ok(self.root, "commit", "-q", "-m", "package")
            self.git_ok(self.root, "remote", "add", "origin", str(self.remote))
            self.git_ok(self.root, "push", "-q", "origin", "HEAD:refs/heads/main")
            self.git_ok(self.root, "fetch", "-q", "origin")

        def commit_all(self, message="change"):
            self.git_ok(self.root, "add", "-A")
            self.git_ok(self.root, "commit", "-q", "-m", message)

        def assert_passes(self, tag="v1.2.3"):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                check_release(self.root, tag)
            self.assertIn(f"PASS release {tag}", out.getvalue())

        def assert_rejects(self, tag, message):
            with self.assertRaises(ValueError) as context, contextlib.redirect_stdout(io.StringIO()):
                check_release(self.root, tag)
            self.assertIn(message, str(context.exception))

        def test_passes_for_the_tag_of_the_manifest_version(self):
            self.assert_passes()

        def test_rejects_a_tag_that_differs_from_the_manifests(self):
            for wrong in ("v9.9.9", "1.2.3", "agt-extra--v1.2.3"):
                with self.subTest(tag=wrong):
                    self.assert_rejects(wrong, "must be v1.2.3")

        def test_rejects_manifests_with_different_versions(self):
            self.write_manifests(plugin_version="1.3.0")
            self.commit_all()
            self.assert_rejects("v1.3.0", "must have the same version")

        def test_rejects_a_manifest_without_a_version(self):
            (self.root / PLUGIN_MANIFEST).write_text(json.dumps({"name": PLUGIN}))
            self.commit_all()
            self.assert_rejects("v1.2.3", "must set version")

        def test_rejects_a_marketplace_without_the_plugin(self):
            (self.root / MARKETPLACE_MANIFEST).write_text(json.dumps({"plugins": []}))
            self.commit_all()
            self.assert_rejects("v1.2.3", "must list agt-extra once")

        def test_rejects_a_missing_manifest(self):
            (self.root / MARKETPLACE_MANIFEST).unlink()
            self.commit_all()
            self.assert_rejects("v1.2.3", f"Cannot read {MARKETPLACE_MANIFEST} from HEAD")

        def test_rejects_a_checkout_that_is_not_clean(self):
            changed = self.root / "scripts/check_package.py"
            changed.write_text(changed.read_text() + "# changed\n")
            self.assert_rejects("v1.2.3", "must be clean")  # Unstaged.
            self.git_ok(self.root, "add", "-A")
            self.assert_rejects("v1.2.3", "must be clean")  # Staged.
            self.git_ok(self.root, "reset", "-q", "--hard")
            self.git_ok(self.root, "config", "status.showUntrackedFiles", "no")
            (self.root / "notes.txt").write_text("untracked\n")
            self.assert_rejects("v1.2.3", "must be clean")  # Untracked, although git status hides it.

        def test_rejects_head_that_is_not_main_on_origin(self):
            other = self.temp / "other"
            self.git_ok(self.temp, "clone", "-q", "-b", "main", str(self.remote), str(other))
            (other / "later.txt").write_text("later\n")
            self.git_ok(other, "add", "-A")
            self.git_ok(other, "commit", "-q", "-m", "later")
            self.git_ok(other, "push", "-q", "origin", "HEAD:refs/heads/main")
            # origin/main in the checkout still equals HEAD. Only the live lookup sees the new commit.
            self.assert_rejects("v1.2.3", "is not main on origin")
            self.git_ok(self.root, "pull", "-q", "--ff-only", "origin", "main")
            self.assert_passes()
            (self.root / "local.txt").write_text("local commit\n")
            self.commit_all()
            self.assert_rejects("v1.2.3", "is not main on origin")  # A commit that is not merged.

        def test_rejects_a_missing_main_on_origin(self):
            self.git_ok(self.remote, "update-ref", "-d", "refs/heads/main")
            self.assert_rejects("v1.2.3", "origin has no main branch")

        def test_rejects_a_failed_lookup(self):
            self.git_ok(self.root, "remote", "set-url", "origin", str(self.temp / "missing.git"))
            self.assert_rejects("v1.2.3", "Cannot read main from origin")

        def test_reads_the_version_from_head(self):
            for path in (PLUGIN_MANIFEST, MARKETPLACE_MANIFEST):
                self.git_ok(self.root, "update-index", "--assume-unchanged", path)
            self.write_manifests("9.9.9", "9.9.9")
            # git status now shows nothing, but HEAD still has the old version.
            self.assert_rejects("v9.9.9", "must be v1.2.3")

        def test_leaves_the_index_untouched(self):
            index = self.root / ".git/index"
            before = index.read_bytes()
            path = self.root / PLUGIN_MANIFEST
            later = path.stat().st_mtime + 10
            os.utime(path, (later, later))  # Same content, new time: git status would refresh the index.
            self.assert_passes()
            self.assertEqual(index.read_bytes(), before)

        def test_lookup_timeout_stops_the_transport(self):
            pidfile = self.temp / "ssh.pid"
            fake_ssh = self.temp / "fake-ssh"
            fake_ssh.write_text(f"#!/bin/sh\necho $$ > '{pidfile}'\nexec sleep 30\n")
            fake_ssh.chmod(0o755)
            os.environ.update(GIT_SSH_COMMAND=str(fake_ssh), GIT_SSH_VARIANT="ssh")
            self.git_ok(self.root, "remote", "set-url", "origin", "ssh://offline.invalid/repo")
            with mock.patch.dict(globals(), REMOTE_TIMEOUT=3):
                self.assert_rejects("v1.2.3", "did not answer within 3 s")
            self.assertTrue(pidfile.exists(), "the fake ssh helper did not start within the time limit")
            pid = int(pidfile.read_text())
            for _ in range(40):  # The killed helper is reaped shortly after.
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                os.kill(pid, signal.SIGKILL)
                self.fail(f"the ssh helper {pid} still runs after the time limit")

        def test_command_line_exit_status(self):
            def run_script(*args):
                return subprocess.run([sys.executable, str(self.root / "scripts/check_package.py"), *args],
                                      cwd=self.temp, text=True, capture_output=True)

            passed = run_script("--release", "v1.2.3")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertIn("PASS release v1.2.3", passed.stdout)
            failed = run_script("--release", "v9.9.9")
            self.assertEqual(failed.returncode, 1)
            self.assertIn("must be v1.2.3", failed.stderr)
            for args in ((), ("--release",), ("--release", "--test"), ("--release", "v1.2.3", "extra"), ("--tset",)):
                with self.subTest(args=args):
                    wrong = run_script(*args)
                    self.assertEqual(wrong.returncode, 2)
                    self.assertIn("Usage:", wrong.stderr)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
