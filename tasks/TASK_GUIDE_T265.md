# TASK_GUIDE — T265: Native Windows support, step 4 — portable process start and kill for auto verify
**Date**: 2026-11-06
**Complexity Level**: C2
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
6. C2: read `memory/codebase-map.md`
7. Read `docs/windows-support-plan.md` (this task is T-W4 of it)
8. Read the `### Auto verify (Stop hook)` section of `docs/claude-md/tracks.md` and the merge-gate learnings in your memory slice (`pkill`/`pgrep -f` match their own shell)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "start as parallel if can be").

**Restated intent**:
> `stop_auto_verify.py` starts the headless verify run detached, and kills it with its children on timeout, on Windows as well as on POSIX. One helper holds both ways. POSIX behaviour does not change.

**Out of scope**:
- File locks (T264), hook commands (T266), the merge-gate parser (T267).
- Changing what the verify run does, its budget or its verdict rules.
- A real Windows run (T263 CI; this task tests the Windows branch with injected fakes).

**Requirement Refs**: `docs/windows-support-plan.md` row 4 and T-W4. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None` (the plan lists T263 for CI; the Windows branch is verified there later)

**Entry point**: `start_detached` and `kill_tree` (function names in `.claude/hooks/lib/proc.py`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/hooks/lib/proc.py` exposes `start_detached(argv, **popen_kwargs)` and `kill_tree(proc)` | one helper |
| 2 | `stop_auto_verify.py` uses the helper at its two `start_new_session=True` sites (lines near 206 and 373) and at `os.killpg(proc.pid, signal.SIGKILL)` (line near 380); no direct `os.killpg` or `signal.SIGKILL` is left in that file | "on Windows as well" |
| 3 | POSIX path: a child shell that spawns a sleeping grandchild is killed together with the grandchild by `kill_tree`; both PIDs are gone within 5 seconds | behaviour unchanged |
| 4 | Windows path: with `sys.platform` forced to `win32`, `start_detached` passes `creationflags=CREATE_NEW_PROCESS_GROUP \| CREATE_NO_WINDOW` (0x00000200 \| 0x08000000; changed from `DETACHED_PROCESS` after Stage 4 review, 2026-11-06: a child with no console makes each console child it starts — cmd.exe, node, git — open a visible window) (and no `start_new_session`), and `kill_tree` runs `["taskkill", "/T", "/F", "/PID", str(pid)]` as an argument list, never through a shell | Windows branch |
| 5 | Negative: `kill_tree` on a process that already exited returns without raising (both OSes) | robustness |
| 6 | Negative: the PID passed to `taskkill` is an `int`; a non-int raises `TypeError` before any command runs | High risk: no injection path |
| 7 | The existing `stop_auto_verify` tests pass unchanged | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `sh -c 'sleep 60 & wait'` started with `start_detached`, then `kill_tree` | Parent and `sleep` both gone | automated test |
| 2 | Forced `win32`, fake `subprocess.Popen` and `subprocess.run` | Flags and `taskkill` argument list as in AC 4 | automated test |
| 3 | `kill_tree` twice on the same process | Second call is a no-op | automated test |
| 4 | `kill_tree` replaced by `proc.kill()` only (parent only) | Test of row 1 goes red (grandchild survives) | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_proc.py -q && python3 -m pytest .claude/hooks/tests -q -k "auto_verify or proc"
```

---

## Approach

**Pattern reference**: `.claude/hooks/stop_auto_verify.py` lines 200-210 and 365-385 (current detach and kill).

**Vital slice**: the helper and the three call-site swaps. Do not touch the verdict parsing.
**Cut list**: Windows Job Objects (a more exact tree kill than `taskkill /T`); graceful `SIGTERM` before kill; log rotation.

Safety notes (High risk): never use `shell=True`; never build a command string; test with `pgrep`-free checks (use the PIDs you hold, not `pkill -f`: see the learning in your slice).

---

## Edge Case Checklist

- [ ] The detached child keeps running after the hook process exits (POSIX `setsid` equivalent)
- [ ] `close_fds=True` at line 206 stays on POSIX; on Windows `close_fds` with redirected std handles is allowed since Python 3.7
- [ ] `claude` resolved by `shutil.which("claude")` on Windows (the `.cmd` shim); do not hard-code `claude` with no lookup
- [ ] Exit code and verdict file written the same way on both OSes
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep `docs/claude-md/tracks.md`, README and comments for "setsid", "killpg", "process group"

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/proc.py` | New helper |
| `.claude/hooks/stop_auto_verify.py` | Use the helper |
| `.claude/hooks/tests/test_proc.py` | New tests incl. mutation control |
| Pre-existing pin tests | Grep `.claude/hooks/tests/` and `tests/` for `killpg`, `start_new_session`, `SIGKILL` and a `stop_auto_verify.py` size pin; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/post_tool_trace.py`, `lib/auto_closeout.py`, `scripts/verify_trace.py` | File locks are T264 |
| `.claude/settings.json` | T266 |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | T267 |

---

## Test Plan

Real process-tree test on Linux; injected-fake tests for the Windows branch; a no-raise test for an exited process; run the full hook test directory.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Lint passes
