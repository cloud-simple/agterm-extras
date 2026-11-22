#!/usr/bin/env python3
"""Run the Codex side of say-hello through the UserPromptSubmit hook."""

import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


WAIT_SECONDS = 90
COMMANDS = {"say-hello", "$say-hello", "agt-extra:say-hello", "$agt-extra:say-hello"}
AGENTS = {"claude": "Claude Code", "codex": "Codex"}
NO_AGENT = "ERR: no agent is available in the other pane"
TIMEOUT = "[say-hello timeout] "
REPLY = re.compile(r"\[peer chat\] say-hello reply ([0-9a-f]{32})\s*")


def mailbox(*args, message=None):
    result = subprocess.run(["mailbox-chat.py", *args], input=message, text=True,
                            capture_output=True, check=True, timeout=10)
    reply = json.loads(result.stdout)
    if not isinstance(reply, dict) or "error" in reply:
        raise ValueError("Invalid mailbox response")
    return reply


def read_state(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None


def write_state(path, state):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as file:
        temp = Path(file.name)
        try:
            json.dump(state, file)
            file.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def start(path, pane, thread, state):
    if state and state["pane"] == pane and time.time() < state["deadline"]:
        return f"Hello already sent. Waiting for {state['agent']}."
    try:
        agent = AGENTS.get(mailbox("status").get("receiver"))
    except (OSError, ValueError, subprocess.SubprocessError):
        return NO_AGENT
    if not agent:
        return NO_AGENT

    codex = shutil.which("codex")
    if not codex:
        return "ERR: could not find Codex to report the timeout"
    token = uuid.uuid4().hex
    message = ("This is a connection test from say-hello. Reply once through mailbox-chat.py say "
               f"with exactly this line: say-hello reply {token}\nDo nothing else.")
    try:
        sent = mailbox("say", "--stdin", message=message)
        if not sent.get("sent") or sent.get("receiver") == "none":
            return f"ERR: {agent} is not available"
    except (OSError, ValueError, subprocess.SubprocessError):
        return f"ERR: {agent} is not available"

    agent = AGENTS.get(sent.get("receiver"), agent)
    deadline = time.time() + WAIT_SECONDS
    write_state(path, {"token": token, "agent": agent, "pane": pane, "deadline": deadline})
    try:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--timeout", str(path),
                          token, codex, thread, str(deadline)], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        path.unlink(missing_ok=True)
        return "ERR: the hello was sent but the reply timer could not start"
    if sent.get("peerBusy"):
        return f"Hello sent. {agent} is mid-turn. Waiting up to {WAIT_SECONDS} seconds."
    return f"Hello sent. Waiting up to {WAIT_SECONDS} seconds for {agent}."


def run_timeout(path, token, codex, thread, deadline):
    time.sleep(max(0, deadline - time.time()))
    state = read_state(path)
    if state and state["token"] == token and not state.get("timed_out"):
        subprocess.run([codex, "queue", "--thread", thread, "--message", TIMEOUT + token],
                       check=True, timeout=15)


def handle(event, data, pane):
    prompt = event.get("prompt", "").strip()
    # The recipe appends a blank line and its reply instructions to every peer message.
    reply = REPLY.fullmatch(prompt.split("\n", 1)[0])
    timeout = prompt.startswith(TIMEOUT)
    if prompt not in COMMANDS and not reply and not timeout:
        return None
    if not pane:
        return NO_AGENT if prompt in COMMANDS else ""

    thread = str(uuid.UUID(event["session_id"]))
    data.mkdir(parents=True, exist_ok=True)
    path = data / f"{thread}.json"
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(path)
        if prompt in COMMANDS:
            return start(path, pane, thread, state)
        token = reply[1] if reply else prompt[len(TIMEOUT):]
        if not state or state["pane"] != pane or state["token"] != token:
            return ""
        agent = state["agent"]
        if reply:
            path.unlink()
            late = " (late reply)" if state.get("timed_out") else ""
            return f"OK: {agent} is available{late}"
        if state.get("timed_out") or time.time() < state["deadline"]:
            return ""
        state["timed_out"] = True
        write_state(path, state)
        return f"ERR: {agent} is not available"


def main():
    args = sys.argv[1:]
    if args == ["--test"]:
        return run_tests()
    if args and args[0] == "--timeout":
        _, path, token, codex, thread, deadline = args
        run_timeout(Path(path), token, codex, thread, float(deadline))
        return 0

    event = json.load(sys.stdin)
    session = os.environ.get("AGTERM_SESSION_ID")
    pane = os.environ.get("AGTERM_PANE_ID")
    result = handle(event, Path(os.environ["PLUGIN_DATA"]) / "say-hello",
                    f"{session}:{pane}" if session and pane else None)
    if result is not None:
        context = (f"For this turn, print only this say-hello result and call no tools: {result}"
                   if result else "This is a stale say-hello event. End the turn without replying.")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": context,
        }}))
    return 0


def run_tests():
    import unittest
    from unittest.mock import patch

    class SayHelloTests(unittest.TestCase):
        def setUp(self):
            directory = tempfile.TemporaryDirectory()
            self.addCleanup(directory.cleanup)
            self.data = Path(directory.name)
            self.thread = str(uuid.uuid4())
            self.path = self.data / f"{self.thread}.json"
            self.mailbox = self.patch("mailbox")
            self.spawn = self.patch("subprocess.Popen")
            self.patch("shutil.which").return_value = "/fake/codex"
            self.now = self.patch("time.time")
            self.now.return_value = 100

        def patch(self, name):
            patcher = patch(f"__main__.{name}")
            self.addCleanup(patcher.stop)
            return patcher.start()

        def submit(self, prompt, pane="session:left"):
            return handle({"session_id": self.thread, "prompt": prompt}, self.data, pane)

        def send(self, receiver="codex", busy=False):
            self.mailbox.side_effect = [{"receiver": receiver},
                                        {"receiver": receiver, "sent": 120, "peerBusy": busy}]
            self.submit("$say-hello")
            return read_state(self.path)["token"]

        def test_unrelated_prompt_and_missing_peer_send_nothing(self):
            self.assertIsNone(self.submit("Can we edit say-hello?"))
            self.assertEqual(self.submit("$say-hello", pane=None), NO_AGENT)
            self.mailbox.assert_not_called()
            self.mailbox.return_value = {"receiver": "none"}
            self.assertEqual(self.submit("$say-hello"), NO_AGENT)
            self.mailbox.assert_called_once_with("status")
            self.spawn.assert_not_called()

        def test_failed_send_does_not_start_timer(self):
            self.mailbox.side_effect = [{"receiver": "codex"}, ValueError("send failed")]
            self.assertEqual(self.submit("say-hello"), "ERR: Codex is not available")
            self.spawn.assert_not_called()
            self.assertFalse(self.path.exists())

        def test_only_the_matching_reply_completes_the_check(self):
            token = self.send("claude", busy=True)
            self.assertIn(token, self.mailbox.call_args.kwargs["message"])
            self.assertIn("already sent", self.submit("$agt-extra:say-hello"))
            self.assertIn("already sent", self.submit("agt-extra:say-hello"))
            self.assertEqual(self.mailbox.call_count, 2)
            self.assertIsNone(self.submit("[peer chat] an unrelated message"))
            self.assertEqual(self.submit(f"[peer chat] say-hello reply {token}", pane="session:right"), "")
            self.assertEqual(self.submit(f"[peer chat] say-hello reply {token}\n\nReply line"),
                             "OK: Claude Code is available")
            self.assertEqual(self.submit(TIMEOUT + token), "")
            self.assertFalse(self.path.exists())

        def test_timer_queues_once_for_the_pending_check_and_late_reply_is_reported(self):
            token = self.send()
            self.assertEqual(self.submit(TIMEOUT + token), "")
            self.now.return_value = 190
            run = self.patch("subprocess.run")
            self.patch("time.sleep")
            run_timeout(self.path, token, "/fake/codex", self.thread, 190)
            run.assert_called_once_with(["/fake/codex", "queue", "--thread", self.thread,
                                         "--message", TIMEOUT + token], check=True, timeout=15)
            self.assertEqual(self.submit(TIMEOUT + token), "ERR: Codex is not available")
            self.assertEqual(self.submit(TIMEOUT + token), "")
            self.assertEqual(self.submit(f"[peer chat] say-hello reply {token}"),
                             "OK: Codex is available (late reply)")
            run.reset_mock()
            run_timeout(self.path, token, "/fake/codex", self.thread, 190)
            run.assert_not_called()

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SayHelloTests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
