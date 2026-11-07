# TASK_GUIDE — T264: Native Windows support, step 3 — one portable file lock
**Date**: 2026-11-06
**Complexity Level**: C2
**Risk Level**: Medium
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
6. C2: read `memory/codebase-map.md`
7. Read `docs/windows-support-plan.md` (this task is T-W3 of it)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "start as parallel if can be").

**Restated intent**:
> The three places that lock a file with `fcntl.flock` use one helper instead. On POSIX the behaviour is byte-for-byte the same as today. On Windows the helper locks with `msvcrt.locking`. No hook crashes on `import fcntl`.

**Out of scope**:
- Process control (`killpg`; T265) and hook commands (T266).
- Changing what is locked, the lock order or the trace file format.
- Running on a real Windows host (T263's CI does that; this task tests the Windows branch with a fake `msvcrt`).

**Requirement Refs**: `docs/windows-support-plan.md` row 3 and T-W3. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None` (the plan lists T263 for CI; the code change does not need it, the Windows branch is verified there later)

**Entry point**: `file_lock` (the helper function name in `.claude/hooks/lib/filelock.py`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/hooks/lib/filelock.py` exists and exposes `file_lock(handle, shared=False)` as a context manager: exclusive by default, shared when `shared=True` | one helper |
| 2 | `post_tool_trace.py` (`_lock`, line 181), `lib/auto_closeout.py` (line 192) and `scripts/verify_trace.py` (line 50, `LOCK_SH`) use the helper; no `fcntl` import is left in those three files | "no hook crashes on import fcntl" |
| 3 | POSIX path: two processes append 200 lines each to one file under the lock; the file holds 400 whole lines, none interleaved | behaviour unchanged |
| 4 | Windows path: with `sys.platform` forced to `win32` and a fake `msvcrt` module injected, the helper calls `msvcrt.locking` with `LK_LOCK` then `LK_UNLCK`, and does not import `fcntl` | Windows branch |
| 5 | Negative: if locking raises, `post_tool_trace.py` still appends and still reports "unlocked" (today's fail-open behaviour at line 185); `auto_closeout.py` still fails closed (done not moved) | keep each caller's failure rule |
| 6 | The hook chain hash (`chain_hash`) of the trace file is unchanged for an identical input sequence | trace format unchanged |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Two `multiprocessing` workers, 200 appends each | 400 intact lines | automated test |
| 2 | `sys.platform = "win32"` plus fake `msvcrt` | `locking(fd, LK_LOCK, n)` then `locking(fd, LK_UNLCK, n)` called | automated test |
| 3 | Helper whose POSIX call raises `OSError` | Caller-specific behaviour of AC 5 | automated test |
| 4 | Helper with the lock call replaced by a no-op | The two-process test of row 1 goes red (interleaved or lost lines) | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_filelock.py -q && python3 -m pytest .claude/hooks/tests -q
```

---

## Approach

**Pattern reference**: `.claude/hooks/post_tool_trace.py` lines 53-56 and 181-186 (optional import, fail-open) and `.claude/hooks/lib/auto_closeout.py` lines 187-197 (context manager with `LOCK_EX`).

**Vital slice**: the helper plus swapping the three call sites. Keep `post_tool_trace.py` degrade-gracefully semantics: the helper returns normally when locking is unavailable and tells the caller (so `_lock` can still return `False`).
**Cut list**: timeouts and retry on lock contention; a cross-platform lock for directories; lock files separate from data files.

Windows note for the implementer: `msvcrt.locking` locks a byte range from the current position and is mandatory on Windows. Lock one byte at offset 0 (`handle.seek(0)` before, restore the position after), and document that choice in the helper docstring.

---

## Edge Case Checklist

- [ ] A file opened in append mode: the lock offset is 0, not the end of file
- [ ] The helper unlocks in `finally`, also when the body raises
- [ ] `scripts/verify_trace.py` reads under a shared lock: Windows has no shared lock in `msvcrt`, so the helper takes an exclusive lock there and the docstring says so
- [ ] Plugin copies under `plugin/` are symlinks to these files: do not duplicate the helper
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep `docs/`, `site/` and comments for "fcntl" and "POSIX" claims

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/filelock.py` | New helper |
| `.claude/hooks/post_tool_trace.py` | Use the helper |
| `.claude/hooks/lib/auto_closeout.py` | Use the helper |
| `scripts/verify_trace.py` | Use the helper (import path: check how it reaches `.claude/hooks/lib` today) |
| `.claude/hooks/tests/test_filelock.py` | New tests incl. mutation control |
| Pre-existing pin tests | Grep `.claude/hooks/tests/` and `tests/` for `fcntl`, `flock` and a hook line-count or size pin (`test_agent_guide_dedup.py`, memory budget tests); handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/stop_auto_verify.py` | Process control is T265 |
| `.claude/settings.json` | T266 |
| `setup.sh`, `lib/*.sh` | T268 |

---

## Test Plan

Real two-process test on Linux; fake-`msvcrt` test for the Windows branch; failure-mode tests for the two callers; a full hooks test run to show nothing else changed.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Lint passes
