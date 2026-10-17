#!/usr/bin/env python3
"""T148: a rewritten event trace is detectable.

`post_tool_trace.py` hash-chains every trace line and appends the chain head to
an anchor file outside the repo; `scripts/verify_trace.py <task>` reports
INTACT / BROKEN at line N / ANCHOR MISMATCH at line N / UNANCHORED.

Tests drive the real hook over its stdin protocol, the way the harness does, in
a temp copy of the repo layout (hook + lib + verifier). CLAUDE_TRACE_ANCHOR_DIR
points at a separate temp dir, so neither the real memory/event-trace/ nor the
real ~/.claude/harness-anchors/ is touched.

Run with: python3 -m pytest .claude/hooks/tests/test_trace_chain.py -q
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
from trace_chain import canonical, chain_hash  # noqa: E402

TASK = "T900"


def bash_event(n):
    return {"tool_name": "Bash", "tool_input": {"command": "echo %d" % n}, "tool_response": {}}


class Sandbox:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="t148_root_")
        self.anchor_base = tempfile.mkdtemp(prefix="t148_anchor_")
        hooks = os.path.join(self.root, ".claude", "hooks")
        os.makedirs(hooks)
        shutil.copy(os.path.join(HOOKS_DIR, "post_tool_trace.py"), hooks)
        shutil.copytree(os.path.join(HOOKS_DIR, "lib"), os.path.join(hooks, "lib"))
        os.makedirs(os.path.join(self.root, "scripts"))
        shutil.copy(os.path.join(REPO_ROOT, "scripts", "verify_trace.py"),
                    os.path.join(self.root, "scripts"))
        self.hook = os.path.join(hooks, "post_tool_trace.py")
        self.trace = os.path.join(self.root, "memory", "event-trace", TASK + ".jsonl")

    def env(self, **extra):
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = self.root
        env["CLAUDE_ACTIVE_TASK"] = TASK
        env["CLAUDE_TRACE_ANCHOR_DIR"] = self.anchor_base
        env.update(extra)
        return env

    def run_hook(self, event, **extra):
        result = subprocess.run([sys.executable, self.hook], input=json.dumps(event),
                                capture_output=True, text=True, cwd=self.root, env=self.env(**extra))
        assert result.returncode == 0, result.stderr
        return result

    def verify(self, **extra):
        return subprocess.run([sys.executable, os.path.join(self.root, "scripts", "verify_trace.py"), TASK],
                              capture_output=True, text=True, env=self.env(**extra))

    def lines(self):
        with open(self.trace) as f:
            return f.read().splitlines()

    def records(self):
        return [json.loads(line) for line in self.lines()]

    def write_lines(self, lines):
        with open(self.trace, "w") as f:
            f.write("".join(line + "\n" for line in lines))

    def anchor_files(self):
        found = []
        for dirpath, _, names in os.walk(self.anchor_base):
            found += [os.path.join(dirpath, n) for n in names]
        return found

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.anchor_base, ignore_errors=True)


@pytest.fixture
def sb():
    s = Sandbox()
    yield s
    s.cleanup()


def rechain(records):
    """What a careful rewriting agent does: recompute every prev/hash in-file."""
    prev = "genesis"
    out = []
    for rec in records:
        rec = {k: v for k, v in rec.items() if k not in ("prev", "hash")}
        rec["prev"] = prev
        rec["hash"] = chain_hash(rec)
        prev = rec["hash"]
        out.append(json.dumps(rec))
    return out


# --- AC1: chain fields ------------------------------------------------------

def test_ac1_lines_carry_prev_and_hash_chained_from_genesis(sb):
    for n in range(3):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    assert recs[0]["prev"] == "genesis"
    for i, rec in enumerate(recs):
        body = {k: v for k, v in rec.items() if k != "hash"}
        expected = hashlib.sha256((rec["prev"] + json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)).encode("utf-8")).hexdigest()
        assert rec["hash"] == expected
        if i:
            assert rec["prev"] == recs[i - 1]["hash"]


def test_canonical_json_ignores_key_order_and_spacing():
    a = {"b": 1, "a": "é", "prev": "genesis"}
    b = {"prev": "genesis", "a": "é", "b": 1}
    assert canonical(a) == canonical(b) == '{"a":"é","b":1,"prev":"genesis"}'
    assert chain_hash(a) == chain_hash(b)


# --- AC2: anchor outside the repo --------------------------------------------

def test_ac2_each_append_anchors_task_line_and_hash_outside_the_root(sb):
    for n in range(3):
        sb.run_hook(bash_event(n))
    files = sb.anchor_files()
    assert len(files) == 1 and files[0].endswith(os.sep + TASK + ".anchors")
    assert not os.path.realpath(files[0]).startswith(os.path.realpath(sb.root) + os.sep)
    slug = os.path.basename(os.path.dirname(files[0]))
    assert slug == os.path.basename(sb.root) + "-noremote"  # sandbox is not a git repo
    with open(files[0]) as f:
        anchored = [line.split() for line in f.read().splitlines()]
    assert anchored == [[TASK, str(i + 1), rec["hash"]] for i, rec in enumerate(sb.records())]


# --- SC1-SC4: the verifier's four verdicts -----------------------------------

def test_sc1_three_appends_verify_intact(sb):
    for n in range(3):
        sb.run_hook(bash_event(n))
    result = sb.verify()
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[-1].startswith("INTACT")


def test_sc2_editing_a_line_without_rechaining_is_broken_at_that_line(sb):
    for n in range(3):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    recs[1]["summary"] = '{"command": "python3 -m pytest -q"}'
    sb.write_lines([json.dumps(r) for r in recs])
    result = sb.verify()
    assert result.returncode == 1
    assert result.stdout.splitlines()[-1].startswith("BROKEN at line 2")


def test_sc3_rewrite_with_whole_chain_recomputed_is_an_anchor_mismatch(sb):
    """The case an in-file chain alone misses."""
    for n in range(3):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    recs[1]["summary"] = '{"command": "python3 -m pytest -q"}'
    sb.write_lines(rechain(recs))
    result = sb.verify()
    assert result.returncode == 1, result.stdout
    assert result.stdout.splitlines()[-1].startswith("ANCHOR MISMATCH at line 2")


def test_sc4_pre_chain_lines_are_unanchored_and_the_chain_is_checked_after_them(sb):
    old = [json.dumps({"timestamp": "t", "tool_name": "Bash", "summary": "{}", "is_error": False})] * 2
    os.makedirs(os.path.dirname(sb.trace))
    sb.write_lines(old)
    only_old = sb.verify()
    assert only_old.returncode == 0
    assert only_old.stdout.strip() == "UNANCHORED: lines 1-2 predate the chain"
    for n in range(2):
        sb.run_hook(bash_event(n))
    assert sb.records()[2]["prev"] == "genesis"
    result = sb.verify()
    assert result.returncode == 0, result.stdout
    assert result.stdout.splitlines() == ["UNANCHORED: lines 1-2 predate the chain",
                                          "INTACT: lines 3-4 chained and anchored"]
    recs = sb.records()
    recs[3]["summary"] = "{}"
    sb.write_lines([json.dumps(r) for r in recs])
    assert sb.verify().stdout.splitlines()[-1].startswith("BROKEN at line 4")


# --- deletion / forged append: the anchor catches both -----------------------

def test_deleting_the_last_line_is_an_anchor_mismatch(sb):
    for n in range(3):
        sb.run_hook(bash_event(n))
    sb.write_lines(sb.lines()[:2])
    result = sb.verify()
    assert result.returncode == 1
    assert result.stdout.splitlines()[-1].startswith("ANCHOR MISMATCH at line 3")


def test_a_forged_line_appended_with_a_valid_chain_is_an_anchor_mismatch(sb):
    for n in range(2):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    recs.append({"timestamp": "t", "tool_name": "Bash",
                 "summary": '{"command": "python3 -m pytest -q"}', "is_error": False})
    sb.write_lines(rechain(recs))
    result = sb.verify()
    assert result.returncode == 1
    assert result.stdout.splitlines()[-1] == "ANCHOR MISMATCH at line 3: no anchor recorded for it"


def test_a_forged_append_marked_anchor_failed_is_unverified_not_intact(sb):
    """Fix round 1 P1-a: claiming the anchor write failed must not buy an INTACT."""
    for n in range(2):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    forged = {"timestamp": "t", "tool_name": "Bash",
              "summary": '{"command": "python3 -m pytest -q"}', "is_error": False,
              "anchor": "failed", "prev": recs[-1]["hash"]}
    forged["hash"] = chain_hash(forged)
    sb.write_lines(sb.lines() + [json.dumps(forged)])
    result = sb.verify()
    assert result.returncode == 1, result.stdout
    assert result.stdout.splitlines()[-1] == (
        "UNVERIFIED at line 3: written with anchor: failed — not anchor-checked")


def test_anchor_mismatch_takes_precedence_over_unverified(sb):
    for n in range(2):
        sb.run_hook(bash_event(n))
    recs = sb.records()
    recs[0]["summary"] = "{}"
    recs.append({"timestamp": "t", "tool_name": "Bash", "summary": "{}", "is_error": False,
                 "anchor": "failed"})
    sb.write_lines(rechain(recs))
    assert sb.verify().stdout.splitlines()[-1].startswith("ANCHOR MISMATCH at line 1")


# --- edge cases ---------------------------------------------------------------

def test_a_crash_truncated_line_is_reported_not_crashed_on(sb):
    for n in range(2):
        sb.run_hook(bash_event(n))
    with open(sb.trace) as f:
        data = f.read()
    with open(sb.trace, "w") as f:
        f.write(data[:-20])  # line 2 cut mid-record, no trailing newline
    result = sb.verify()
    assert result.returncode == 1
    assert result.stdout.splitlines()[-1].startswith("BROKEN at line 2")
    sb.run_hook(bash_event(9))  # the next append starts on its own line
    assert len(sb.lines()) == 3
    assert json.loads(sb.lines()[2])["prev"] == json.loads(sb.lines()[0])["hash"]
    assert sb.verify().stdout.splitlines()[-1].startswith("BROKEN at line 2")


def test_bad_task_name_and_missing_trace_exit_2(sb):
    bad = subprocess.run([sys.executable, os.path.join(sb.root, "scripts", "verify_trace.py"), "../x"],
                         capture_output=True, text=True, env=sb.env())
    assert bad.returncode == 2
    assert sb.verify().returncode == 2  # no trace written yet


# --- SC5 / AC6: anchor failure never breaks the tool call ---------------------

@pytest.mark.parametrize("anchor_dir", ["file", "relative"])
def test_sc5_unwritable_anchor_dir_still_writes_the_line_marked_failed(sb, anchor_dir):
    if anchor_dir == "file":
        blocker = os.path.join(sb.anchor_base, "not-a-dir")
        open(blocker, "w").close()
        anchor_dir = blocker  # makedirs under a regular file fails
    else:
        anchor_dir = "relative/anchors"  # must never land under the cwd
    sb.run_hook(bash_event(1), CLAUDE_TRACE_ANCHOR_DIR=anchor_dir)
    (rec,) = sb.records()
    assert rec["anchor"] == "failed"
    assert rec["hash"] == chain_hash(rec)
    assert not os.path.exists(os.path.join(sb.root, "relative"))
    result = sb.verify(CLAUDE_TRACE_ANCHOR_DIR=anchor_dir)
    if anchor_dir == "relative/anchors":
        assert result.returncode == 2  # the verifier refuses a relative anchor dir too
    else:
        assert result.returncode == 1, result.stdout
        assert result.stdout.splitlines()[-1].startswith("UNVERIFIED at line 1")


def test_lock_failure_still_appends_and_is_marked(sb):
    """`fcntl` is POSIX-only: with it unavailable the line is still written."""
    runner = ("import sys, runpy; sys.modules['fcntl'] = None; "
              "runpy.run_path(%r, run_name='__main__')" % sb.hook)
    result = subprocess.run([sys.executable, "-c", runner], input=json.dumps(bash_event(1)),
                            capture_output=True, text=True, env=sb.env())
    assert result.returncode == 0, result.stderr
    (rec,) = sb.records()
    assert rec["lock"] == "failed"
    assert sb.verify().stdout.splitlines()[-1].startswith("INTACT")


# --- SC6 / AC7: concurrent appends don't fork the chain -----------------------

def test_sc6_two_processes_fifty_appends_each_stay_intact(sb):
    driver = ("import json, subprocess, sys\n"
              "for n in range(50):\n"
              "    subprocess.run([sys.executable, %r], input=json.dumps("
              "{'tool_name': 'Bash', 'tool_input': {'command': 'echo %%s-%%d' %% (sys.argv[1], n)}}),"
              " text=True, check=True)\n" % sb.hook)
    procs = [subprocess.Popen([sys.executable, "-c", driver, tag], env=sb.env()) for tag in "ab"]
    assert all(p.wait(timeout=300) == 0 for p in procs)
    assert len(sb.lines()) == 100
    assert all("lock" not in r for r in sb.records())
    result = sb.verify()
    assert result.returncode == 0, result.stdout
    assert result.stdout.strip() == "INTACT: lines 1-100 chained and anchored"
