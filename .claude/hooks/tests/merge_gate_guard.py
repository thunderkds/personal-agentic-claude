"""Who may change the merge gate — the shared tripwire behind two suites (T188 P2).

`.claude/hooks/pre_bash_block_unsafe_merge.py` is the Stage 5 gate: it decides whether a push or a
merge may proceed. A change to it is the cheapest way to make every other gate stop gating, so two
suites assert that it was only ever changed by a task that was authorised to change it:

  * `.claude/hooks/tests/test_stop_auto_mode_check.py::test_merge_gate_is_untouched`
  * `tests/test_auto_mode.py::test_ac4_merge_gate_file_is_unchanged`

Each suite pins its own `BASE_REF` (the gate as that task's branch found it) and both call this one
helper, so the rule has a single definition.

**An allowlist, not one task.** This check used to read `all("T182" in s for s in subjects)`: one ID,
matched as a bare substring of the commit subject. T188 then had to change the gate for a documented
reason — T182's D5 run-record rule now also resolves a minimal-track `verify:` line from a Decision
record — and its subject names both T188 and T182, so the substring check passed. It would equally
have passed for any future commit that merely *mentions* T182 while changing the gate, which is the
one thing this check exists to catch. The authorised tasks are named explicitly instead, and matched
whole (`\\bT182\\b`), so "mentions an authorised ID" and "is an authorised task" stop being the same
test.

**Adding a task is the record.** A task that must touch the gate adds its ID to `AUTHORISED_TASKS`
with the Supervisor's sign-off, and says in its TASK_GUIDE which rule it owns there. That edit is
the audit trail; a green test is deliberately not the easy path.

**Fails closed.** A `git log` that does not succeed, and any uncommitted change to the gate, are both
reported as problems — the check never passes because it could not look.
"""
import re
import subprocess

GATE_REL = ".claude/hooks/pre_bash_block_unsafe_merge.py"

# Task IDs authorised to change the merge gate, oldest first, each with the rule it owns there:
#   T182 — D5: an `auto-run by hook` `verify` Evidence row counts only with the hook's run record,
#          for that task and the head commit, saying pass.
#   T188 — D5 on the second track: the same rule for a minimal-track `verify:` line in a Decision
#          record (`tasks/MINIMAL_LOG.md`), and nothing weaker — a hand-typed line counts for
#          nothing there (`tasks/TASK_GUIDE_T188.md` D5, AC 5).
#   T190 — FR-004: a checked `☑ fail` in the Companion score row or a UI design row blocks the
#          push. Fail-open on every absence (FR-006), so a machine with neither companion tool
#          behaves as before (`tasks/TASK_GUIDE_T190.md`, AC 2-7). Authorised by the user,
#          2026-10-28.
#   T197 — D1-D4: a `git push` of one task's branch is judged by that task alone; every
#          unresolved push, and every merge, still checks the whole board
#          (`tasks/TASK_GUIDE_T197.md`). Authorised by the user, 2026-10-28.
#   T196 — the attribution remedy text names the per-session state file; no gate logic change
#          (`ATTRIBUTION_REMEDY` only, `tasks/TASK_GUIDE_T196.md` D6). Authorised by the user,
#          2026-10-29.
#   T210 — D1-D4: `git pull` is gated as a merge; `git merge-base` is not; a `timeout <N>`
#          test run counts; for a merge or narrowed push of a task branch the `verify` row counts
#          only when committed on that branch (`tasks/TASK_GUIDE_T210.md`). Authorised by the
#          user, 2026-10-29.
AUTHORISED_TASKS = ("T182", "T188", "T190", "T197", "T196", "T210")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def unauthorised_gate_commits(root, base_ref, gate=GATE_REL, authorised=AUTHORISED_TASKS):
    """Every reason the merge gate is not as its authorised owners left it, or `[]`.

    A problem is: a commit since `base_ref` that changes `gate` whose subject names none of
    `authorised`; an uncommitted change to `gate`; or a `git log` that failed.
    """
    log = _git(root, "log", "--no-merges", "--format=%s", f"{base_ref}..HEAD", "--", str(gate))
    if log.returncode != 0:
        return [f"git log failed for {gate} ({log.stderr.strip()}) — cannot confirm who changed it"]
    names = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(t) for t in authorised))
    problems = [f"commit names no task authorised to change {gate} "
                f"({', '.join(authorised)}): {subject!r}"
                for subject in log.stdout.splitlines() if not names.search(subject)]
    if _git(root, "diff", "--quiet", "HEAD", "--", str(gate)).returncode != 0:
        problems.append(f"{gate} has uncommitted changes — commit them under an authorised task "
                        "so the subject is on the record")
    return problems
