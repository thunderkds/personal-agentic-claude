# TASK_GUIDE — T267: Native Windows support, step 6 — merge gate detects PowerShell-spelled git writes
**Date**: 2026-11-06
**Complexity Level**: C3
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. C3: read `memory/codebase-map.md`
7. Read `docs/windows-support-plan.md` (this task is T-W6 of it) and `docs/adr/0003-native-windows-support.md` (on branch `feat/t262-windows-adr`, worktree `/home/hungnguyenhuu/workspace/pets/wt-t262`)
8. Read `.claude/hooks/pre_bash_block_unsafe_merge.py` lines 100-200 (patterns), 830-1100 (narrowing) and 1300-1430 (`main`), and `.claude/hooks/lib/shell_data.py` `strip_quoted_spans`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "[auto]"). Plan task T-W6: "Merge-gate parser for PowerShell … fail closed".

**Restated intent**:
> On native Windows, a `git push`, `git merge`, `git rebase` or `git pull` written in PowerShell spelling (`git.exe push`, ``git` push``, `& "C:\Program Files\Git\cmd\git.exe" push`, `& $g push`, `iex "git push"`) must not slip past the merge gate. A command the gate cannot classify but that may hold a git write goes to the existing whole-board check, never to "allow". POSIX behaviour does not change.

**Decision (Debate, 3 Advocates, 2026-11-06)**: no PowerShell lexer. The gate keeps POSIX `shlex` for narrowing only, and gains a syntax-blind detection fallback. Reason: detection is a regex over the raw text, and a reproduced bypass shows `git.exe push` and ``git` push`` do not match today (`GIT_VERB_PREFIX` at line 108 needs whitespace after `git`); a PowerShell tokenizer is the largest new way to be wrong, and an unresolved command already means "check the whole board" (line 1075).

**Out of scope**:
- A PowerShell lexer or any change to `_command_segments` narrowing.
- `lib/session_work.py` separators (`-and`/`-or`): it is conservative on unparsable input, so it stays.
- `git branch -D` (T266 ships its Python twin of the guardrail).
- cmd.exe-only syntax (cut by ADR-0003 decision 2).
- Any change when the host is not Windows and the command shows no PowerShell marker.

**Requirement Refs**: `docs/windows-support-plan.md` row 6 and T-W6; `docs/adr/0003-native-windows-support.md` decision 2. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor), 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `WINDOWS_GIT_FALLBACK` (the new pattern name in `.claude/hooks/pre_bash_block_unsafe_merge.py`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A new detection fallback runs in `main()` next to `BLOCKED_PATTERNS`, on the raw command with backticks and quote characters removed (not on the `strip_quoted_spans` output). It matches `\bgit(?:\.exe\|\.cmd)?\b` followed on the same line by `push`, `merge` (not `merge-base`), `rebase`, `pull` or `alias.`; and it matches an indirection marker (`& $name`, `& "<path>git.exe"`, `iex`, `Invoke-Expression`, `cmd /c`, `powershell -c`, `powershell -Command`, `-EncodedCommand`) together with one of those verbs | PowerShell spellings must not slip past |
| 2 | The fallback is active only when `sys.platform == "win32"` or the raw text carries a PowerShell marker (backtick, `$env:`, `-and`, `-or`, `Invoke-Expression`, `iex`, `& $`, `.exe`). On Linux and macOS, with a plain POSIX command, behaviour is identical to today | POSIX does not change |
| 3 | A command the fallback flags but the POSIX tokenizer cannot resolve takes the existing "unresolved → whole board" path (`pushed_task_ids` returns None). It never exits 0 without the Evidence checks that a plain `git push` gets | fail closed |
| 4 | Test matrix (platform forced to `win32` by monkeypatch): `git.exe push origin main`, ``git` push``, `& "C:\Program Files\Git\cmd\git.exe" push`, `$g="git"; & $g push`, `$env:X='1'; git push`, `echo 'it''s'; git merge feat`, `iex "git push"`, `cmd /c git push`, `git.exe -C . pull`: each gets the SAME verdict as the plain `git push` / `git merge` / `git pull` in the same fixture (block when evidence is missing, allow only when the plain command is allowed) | AC 1, 3 |
| 5 | Negative: `git status`, `git.exe status`, `git log`, `git.exe merge-base a b`, `echo hello`, `Get-ChildItem` are allowed on `win32` | no new false blocks on non-write commands |
| 6 | Existing gate tests pass unchanged: `python3 -m pytest .claude/hooks/tests -q -k "merge or gate or unsafe"` and the whole `.claude/hooks/tests` directory | POSIX unchanged |
| 7 | `docs/claude-md/` or README text that describes what the gate detects is updated for the new fallback (stale-reference sweep), or the sweep records none exists | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Each spelling of AC 4 with a fixture board that has an In Progress task and no evidence | Same block as plain `git push` | automated test |
| 2 | The same spellings with complete Evidence | Same allow as plain `git push` | automated test |
| 3 | AC 5 commands | Exit 0 | automated test |
| 4 | Fallback pattern deleted from `main()` (mutation) | The `git.exe push` test goes red | mutation control |
| 5 | `sys.platform = "linux"` and a plain command | Verdict unchanged against a recorded baseline | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_windows_merge_gate.py -q && python3 -m pytest .claude/hooks/tests -q
```

---

## Approach

**Pattern reference**: `.claude/hooks/pre_bash_block_unsafe_merge.py` lines 105-120 (`BLOCKED_PATTERNS`, `GIT_VERB_PREFIX`) and 1300-1430 (`main`, `block_unreadable_input`: the fail-closed style), and the existing gate tests in `.claude/hooks/tests/` that build a fixture board (find them with `grep -ln pre_bash_block_unsafe_merge .claude/hooks/tests/*.py`).

**Vital slice**: one new compiled pattern, one helper that builds the "syntax-blind" text, one branch in `main()`, and the test matrix.
**Cut list**: PowerShell tokenizer; `session_work.py` separators; `git branch -D`; cmd.exe syntax; alias expansion beyond the existing `defines_git_alias`.

Write the failing tests first (they must go red against the current code: the Advocate reproduced `git.exe push` not matching). Keep the fallback conservative: over-matching is the accepted direction (`pre_bash_block_unsafe_merge.py:835` "Seeing more text than bash runs can only make this global").

---

## Edge Case Checklist

- [ ] `merge-base` is not a merge (keep the existing exclusion)
- [ ] A quoted `"git push"` inside `echo` on `win32` with PowerShell markers: may over-block; record the behaviour in a test so it is a known decision
- [ ] Unreadable hook input still goes to `block_unreadable_input`
- [ ] The compiled pattern has no catastrophic backtracking (test with a 10 000-character input under 1 s)
- [ ] The merge-gate authorised-task list (`merge_gate_guard.AUTHORISED_TASKS`) is not touched
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep `docs/claude-md/`, README, `site/`, comments for "shlex", "POSIX", "bash only" claims about the gate

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | New fallback pattern, helper, one branch in `main()` |
| `.claude/hooks/tests/test_windows_merge_gate.py` | New test matrix with mutation control |
| Pre-existing pin tests | Grep `.claude/hooks/tests/` and `tests/` for a size, line-count or text pin of `pre_bash_block_unsafe_merge.py` and for `BLOCKED_PATTERNS`; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/session_work.py` | Cut list |
| `.claude/settings.json`, `plugin/hooks/hooks.json` | T266 |
| `.claude/hooks/stop_auto_verify.py`, `lib/proc.py`, `lib/filelock.py` | T264 / T265 |
| `setup.sh`, `lib/*.sh` | T268 |

---

## Test Plan

A fixture-board harness like the existing gate tests, run with `sys.platform` forced to `win32`; the matrix of AC 4 and 5; a Linux baseline test; a timing test for the regex; a mutation control that removes the fallback branch.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Lint passes
