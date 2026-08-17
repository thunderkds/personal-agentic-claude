# TASK_GUIDE — T074: Preflight hook-wiring validation + hook troubleshooting docs
**Date**: 2026-08-17
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `BRAINSTORMING_LOG.md` (2026-08-17 entry) — it carries the verified root-cause analysis this task implements. **C1, single new file + docs: `memory/codebase-map.md` is not required.**

> **You do not have a `Skill` tool.** The Completion Checklist below names `code-review`,
> `security-review` and `verify`; those are run by the **Supervisor** at Stage 4/5, not by you.
> Implement, test, and report — do not attempt to invoke them.

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request, across two turns:

> "checking about the hooks, and make sure we mention it in the README for awaring"
>
> "I mean you should check all the hook, cause I see the error from the hooks from another machine
> but got no direction to fix, or no information related to the explain I think."

Concrete incident the user supplied as the example:

> "Broken hook: `.claude/settings.json` wires `pre_bash_block_dangerous_git.py` into every Bash call's
> PreToolUse, but that file doesn't exist on disk — so right now all Bash commands fail, not just git
> ones."

**Restated intent** (Supervisor's interpretation):
> When a hook is wired in a settings file but its script is missing from disk, the user currently gets
> a bare exec failure on **every** Bash call with no indication of which hook, why it exists, or how to
> recover — and cannot use Bash to investigate, because Bash is the broken tool. This task makes that
> failure **self-announcing and self-remedying through a channel the failure cannot block**, and
> documents the hook system so a user can tell a framework hook from a third-party one.

**Out of scope** (explicitly NOT this task):
- Modifying any of the 8 existing hooks — their fail-open / fail-closed semantics are load-bearing and separately tested
- Editing `~/.claude/settings.json` — the user's machine-level third-party hooks are **read-only** to us
- Fixing the two open T073 findings (merge gate `__file__` blindness; whole-string command scan) — unrelated, separately registerable
- Auto-repairing a broken settings file — we **report** the fix, the human applies it
- Any change to `pre_bash_block_unsafe_merge.py`'s fail-closed behaviour

**Requirement Refs**: none — this is framework-infrastructure work with no `PRD.md` FR/NFR backing.
The traceability anchor is `BRAINSTORMING_LOG.md` (2026-08-17), Option D, user-approved.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user approved Option D on 2026-08-17
- [x] Domain terms align with the project glossary (`hook`, `settings file`, `fail open`) — no new terms introduced
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A, deviation recorded above (no `PRD.md` coverage for framework infra)

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `session_validate_hook_wiring.py` — registered in `.claude/settings.json` under the `SessionStart` event.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A new hook `.claude/hooks/session_validate_hook_wiring.py` exists and runs on the `SessionStart` event | "no direction to fix" — needs a channel that survives broken Bash |
| 2 | Given a settings file wiring a `.py`/`.sh` path that does not exist, the hook prints a report naming **the missing path** and **the settings file it came from** | the incident: user knew neither |
| 3 | The report names a remedy that uses **`Read`/`Edit` only** — it must contain no Bash command, because Bash is the broken tool | "got no direction to fix" under total Bash loss |
| 4 | The report distinguishes **framework** hooks (`.claude/hooks/*`) from **third-party/machine-level** ones (`~/.claude/*`, any other path), labelling which is not ours | user runs orca / supervisor-viz / node-terminal alongside |
| 5 | When every wired path resolves, the hook prints **nothing at all** and exits 0 | a healthy session must stay silent |
| 6 | The hook **never blocks** session start: missing settings file, malformed JSON, unreadable file, or any raised exception → exit 0, empty stdout, no traceback | constraint 1 — a validator that breaks startup is worse than the bug |
| 7 | An inline-shell wired command with no script path (e.g. `touch /tmp/x`) produces **no** missing-path report | negative: avoid false positives |
| 8 | A piped command (`tee /tmp/x \| supervisor-viz hook-receive --port 7891`) produces no false missing-path report | negative: the user's real config contains these |
| 9 | The same script wired to N events is reported **once**, not N times | report legibility |
| 10 | `README.md` row for `post_agent_move_to_review.py` no longer claims it moves the Kanban row or resets a step counter | "check all the hook" — provably stale |
| 11 | `README.md` row for `pre_agent_step_limit.py` states default **90** (not 40), session+task keying, and that the block **self-clears** | provably stale |
| 12 | `README.md` gains a hook-troubleshooting section covering: the wiring-drift symptom + cure, framework vs. third-party identification, and the `CLAUDE_ACTIVE_TASK` attribution requirement | "make sure we mention it in the README for awaring" |
| 13 | `git-guardrails-claude-code` SKILL.md step 5 verifies the **wired path in settings resolves**, not only that the script runs | the skill's step order is the drift vector |
| 14 | Tests assert against a **real settings file on disk** with a genuinely missing path — not a mocked `os.path.exists` | T047 lesson: a test sharing a root can't detect a root-split defect |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A temp settings file wiring `.claude/hooks/pre_bash_block_dangerous_git.py` (absent) | Report names that exact path, its settings file, and a Read/Edit remedy; exit 0 | automated test |
| 2 | The repo's real `.claude/settings.json` (all 8 resolve) | Empty stdout, exit 0 | automated test |
| 3 | Settings file containing malformed JSON | Empty stdout, exit 0, no traceback | automated test |
| 4 | Settings path that does not exist at all | Empty stdout, exit 0 | automated test |
| 5 | Wired command `touch /tmp/claude-pretooluse-fired` | No missing-path report | automated test |
| 6 | Wired command `tee /tmp/sv-hook-debug.json \| supervisor-viz hook-receive --port 7891` | No missing-path report | automated test |
| 7 | One missing script wired to 3 events | Reported exactly once | automated test |
| 8 | A missing path under `~/.claude/` | Reported and labelled **not a framework hook** | automated test |
| **SC9 (mutation control)** | Delete the `os.path.exists` guard so everything reports as missing | Test for SC2 goes **RED** | run, observe RED, revert |
| **SC10 (mutation control)** | Restore the old README text for `post_agent_move_to_review.py` | AC10 test goes **RED** | run, observe RED, revert |

> **Both mutation controls are mandatory.** Recorded lesson (8 instances): an assertion never observed
> failing is not evidence. Run each, confirm RED, revert, confirm GREEN — and report the mutation
> output, not a claim that you ran it.

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  CLAUDE_ACTIVE_TASK=T074 python3 -m pytest .claude/hooks/tests/ -q
```

> Expect `451 passed` at baseline plus this task's new tests. **Run the whole suite, not just the new
> file** — `test_vital_slice.py` asserts over `.claude/hooks/*.py` as a glob and will see the new hook.

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T074.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T074.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/stop_review_reminder.py` — the closest prior art: a non-blocking,
stderr-printing, report-only hook that scans a project file and stays silent when there is nothing to
say. Imitate its structure, its stderr channel, and its exit discipline. For the fail-open
`try/except` shape and structural parsing, `.claude/hooks/pre_agent_validate_guide.py` is the
secondary reference.

**Vital slice**: the missing-path detection and its report — AC1–AC6. That is the whole value of the
task: the user learns *which* path is missing, from *which* file, and *how* to fix it without Bash.

**Cut list** (deliberately NOT built):
- JSON-schema walk of `hooks.<event>[].hooks[].command` — **cut by the 50% rule.** A regex scan for
  `.py`/`.sh` tokens over the raw settings text gets the missing path and the fix; it loses the event
  name, which is a nice-to-have the user can recover with one grep. Removes JSON-drift risk too.
- Auto-repair / auto-removal of the broken entry — reporting only; the human applies the fix
- `--explain` flags on the existing 8 hooks (rejected Option B)
- A Bash doctor script (rejected Option A — fatally Bash-dependent)
- Validating that a resolvable script is *executable* or has a correct shebang — different failure, not this incident

**Reasoning**: `SessionStart` is the load-bearing choice. It fires when `PreToolUse/Bash` is
unresolvable, so the warning reaches the user **through a channel the failure cannot block**, and it
arrives *before* the first Bash call rather than after a wall of exec errors. Everything else in the
design follows from the constraint that the remedy must not require the broken tool.

---

## Edge Case Checklist

- [ ] Validator must **never** block session start — wrap everything, exit 0 on any exception
- [ ] Settings file absent / malformed JSON / empty → silent exit 0, no traceback
- [ ] `$CLAUDE_PROJECT_DIR` unset, and `~` in a path → both must expand correctly
- [ ] An inline-shell wired command with no script path → must not be reported missing
- [ ] Multi-hook `command` strings with pipes → must not false-positive
- [ ] Same script wired to several events → report once, not N times
- [ ] Report **only** on failure; a healthy session prints nothing
- [ ] Message must name a `Read`/`Edit` remedy, never a Bash command
- [ ] Distinguish framework hooks from third-party ones
- [ ] Test must straddle the boundary: a real settings file with a genuinely missing path, never a mocked `exists()`
- [ ] Do not assert the validator's prose exists — assert it against real on-disk state (T073 AC6 lesson)
- [ ] The new hook is itself a `.claude/hooks/*.py` file — **`test_vital_slice.py` globs that directory.** Run the full suite and confirm the new file does not trip it

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/session_validate_hook_wiring.py` | **New.** The validator (~60 lines after the 50% cut) |
| `.claude/hooks/tests/test_hook_wiring_validation.py` | **New.** Covers AC1–AC9, AC14 + both mutation controls |
| `.claude/settings.json` | Register the hook on `SessionStart` |
| `README.md` | Correct the two stale rows (AC10/AC11); add troubleshooting section (AC12) |
| `.claude/skills/git-guardrails-claude-code/SKILL.md` | Step 5 verifies the wired path resolves (AC13) |
| `MANIFEST` | **Check first** — if `.claude/hooks` is already copied via `cp -r`, add nothing (T054 precedent: an AC written against a file's older shape) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| The 8 existing `.claude/hooks/*.py` | Fail-open/fail-closed semantics are load-bearing and separately tested |
| `.claude/hooks/lib/*.py` | Unrelated to wiring |
| `~/.claude/settings.json` | User's machine-level third-party hooks — read-only to us |
| `memory/MEMORY.md` | At 49,957 of its 50,000 ratchet; needs `/compact-memory` before any entry |
| `PROJECT_KANBAN.md` | Supervisor-owned; the Supervisor closes the row before merge |

---

## Test Plan

New file `.claude/hooks/tests/test_hook_wiring_validation.py`:

1. **Positive detection** — write a temp settings file wiring a genuinely absent `.py`; run the hook as
   a **subprocess**; assert the missing path, the source settings file, and a Read/Edit remedy all
   appear, and that the output contains no `git `/`bash `/`python3 ` command form (AC2, AC3).
2. **Silence when healthy** — run against the repo's real `.claude/settings.json`; assert empty stdout,
   exit 0 (AC5).
3. **Fail-open matrix** — malformed JSON, absent file, unreadable file, empty file: each exit 0, empty
   stdout, no `Traceback` in stderr (AC6).
4. **Negative controls** — inline shell command, piped command: no report (AC7, AC8).
5. **Dedup** — one missing script on 3 events → exactly one report line (AC9).
6. **Labelling** — a missing `~/.claude/` path is labelled not-a-framework-hook (AC4).
7. **README assertions** — assert the stale claims are **absent** (file-wide negative greps for
   "resets that task's step-limit counter" and "default 40"), and the corrected facts present (AC10,
   AC11). A negative grep is the right shape here, per the T058 lesson about retired tokens.
8. **Mutation controls SC9 + SC10** — run each, observe RED, revert, confirm GREEN. Paste the output.

Run the **full** suite (`.claude/hooks/tests/`), not just the new file — the new hook lands inside a
directory `test_vital_slice.py` globs.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — full-suite output pasted into `tasks/TASK_REVIEW_T074.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Both mutation controls (SC9, SC10) run, observed RED, reverted, suite green again — output pasted
- [ ] UI Evidence rows marked ☐ N/A (pure-infrastructure task — the UI/Design AC section is deliberately deleted from this guide)
- [ ] Supervisor notified: task ready for Stage 4 review

> Run by the **Supervisor**, not the implementing agent (no `Skill` tool in a sub-agent):
> `code-review` (mandatory), `security-review` (Medium risk → mandatory), `verify` (user-invoked).
