# TASK_GUIDE — T275: `python3` on Windows: hook messages and instructions name a launcher that exists
**Date**: 2026-11-07
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
6. Read `docs/windows-support-plan.md`, `docs/adr/0003-native-windows-support.md` and `docs/windows-parity.md` (the ledger: it says how each file is proven on Windows)
7. Read `lib/windows_hooks.py` (how T266 picks `py` or `python` for hook commands)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-07: continue the Windows migration to a beta release. Evidence: a real Windows 11 run (Python 3.15, no Developer Mode) of `py -3 -m pytest tests .claude\hooks\tests -q` gave `63 failed, 1111 passed, 184 skipped` before a Ctrl-C (a test hangs; location not yet known). The installer, update and the T272 preflight passed on that machine.

**Restated intent**:
> On Windows, `python3` is often missing (the launcher is `py -3`, or `python`). Every command a hook message or a skill tells the agent to run must work there. The cheap, safe fix is a rule plus a small helper: hook messages build their launcher in code; the instructions get one written rule.

**Facts (measured 2026-11-07)**: 29 lines with `python3` in 12 `skills/*/SKILL.md`; 4 other doc files (`agents/`, `templates/`, `docs/claude-md/`, `AGENTS.md`/`CLAUDE.md`); 2 hook messages build `python3 <path>` (`.claude/hooks/pre_agent_validate_guide.py` lines ~319 and ~512). Hook shebangs and `settings.json` commands are NOT in scope (T266 converts the commands).

**Decisions already made (do not reopen)**:
- Do not rewrite the 29 skill lines one by one. Add ONE rule to `AGENTS.md` (under Permanent Rules, 2 to 3 lines, plain words): on Windows read `python3` in any command as `py -3` (or `python` if `py` is absent); the agent runs the same command with that launcher.
- Hook messages: a helper `python_launcher()` in `.claude/hooks/lib/` (new small module or an existing lib file) returns `python3` on POSIX and `py -3` on `sys.platform == "win32"` when `shutil.which("py")`, else `python`. The two messages use it. A POSIX run prints exactly what it printed before.
- The path in the message stays shell-quoted as today (`shlex.quote`). On Windows a quoted path is acceptable; the test regex must accept a quoted path (fix `tests/test_plugin_names.py::test_spawn_hook_names_the_scripts_it_mentions_by_paths_that_exist`).

**Out of scope (cut list)**: editing the 29 skill lines, `settings.json`, `lib/windows_hooks.py`, shell scripts, `site/`, anything under `.github/`.

**Requirement Refs**: `docs/windows-parity.md` (Next steps); `docs/adr/0003-native-windows-support.md` decision 2.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-07)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: T272, T273 (merged into `windows`)

**Entry point**: `.claude/hooks/pre_agent_validate_guide.py` (the spawn hook)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `python_launcher()` returns `python3` on POSIX; on `win32` it returns `py -3` when `py` is on PATH, else `python`. Tested by monkeypatching `sys.platform` and `shutil.which` | helper |
| 2 | Both hook messages call it. On POSIX the message text is byte-identical to before (a test pins the old text) | no regression |
| 3 | With `sys.platform` patched to `win32` and `py` found, both messages contain `py -3 ` followed by the quoted script path, and no `python3` | the Windows case |
| 4 | `tests/test_plugin_names.py::test_spawn_hook_names_the_scripts_it_mentions_by_paths_that_exist` accepts a quoted path and any launcher, and still proves the path exists | 1 failure |
| 5 | `AGENTS.md` holds the one rule (2 to 3 lines). `CLAUDE.md` is untouched (it imports `AGENTS.md`). Every existing test about `AGENTS.md` still passes (line caps, wording pins) | rule |
| 6 | A test greps `AGENTS.md` for the rule's key words so it cannot be deleted silently | rule |
| 7 | No other `.claude/hooks/*.py` message prints `python3 ` for the agent to run (grep; list the result in the Evidence). Any that do are fixed the same way | completeness |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Linux run | Messages unchanged | pinned text test |
| 2 | `sys.platform="win32"`, `py` present | `py -3 <path>` in both messages | unit test |
| 3 | `sys.platform="win32"`, `py` absent | `python <path>` | unit test |
| 4 | Helper returns `python3` always (mutation) | the win32 test goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests tests -q
```

This machine is Linux. Windows-only behavior cannot be proven here; say so in the Evidence and name what the user must re-run on Windows.

---

## Approach

**Vital slice**: helper + two messages + test (AC 1-4, 7), then the `AGENTS.md` rule (AC 5-6). Tests first (red).
**Pattern reference**: `lib/windows_hooks.py` launcher choice; `.claude/hooks/lib/project_root.py` for a small hook lib.

---

## Edge Case Checklist

- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `docs/windows-support-plan.md`, `docs/windows-parity.md` for text the change makes false
- [ ] `AGENTS.md` pin tests (line count, `tests/test_agents_md_primary.py`, site claims) are listed in the pre-flight row
- [ ] `plugin/` copies of hook files: the plugin tree links to `.claude/hooks`; do not edit `plugin/` copies by hand (`RUNBOOK.md` names the real copies)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/` (new helper file) | `python_launcher()` |
| `.claude/hooks/pre_agent_validate_guide.py` | Two messages call the helper |
| `AGENTS.md` | One rule |
| `.claude/hooks/tests/` (new test file) and `tests/test_plugin_names.py` | Tests |
| Pre-existing pin tests | Grep `tests/` and `.claude/hooks/tests/` for pins on `AGENTS.md` and the two message texts; handle each |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/*/SKILL.md` | 29 lines stay as they are (the rule covers them) |
| `.claude/settings.json`, `lib/windows_hooks.py`, `.github/*` | Not this task |
| `docs/windows-parity.md`, `docs/windows-support-plan.md`, `memory/`, `PROJECT_KANBAN.md` | Supervisor |

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (if your toolset has no Skill tool, say so; the Supervisor reviews)
- [ ] Lint passes
- [ ] No unrelated files modified
- [ ] Evidence table below filled in

---

## Evidence (fill in before Ready for Review)

| Item | Result | Pasted evidence |
|------|--------|-----------------|
| New test(s) cover acceptance criteria | ☐ | |
| Test suite passes (verification command above) | ☐ | |
| Mutation control goes red | ☐ | |
| Pre-existing pin tests | ☐ pre-flight (filled before the AGENTS.md edit; outcome pasted after the full run) | AGENTS.md is 196 lines and 21402 bytes (caps: 200 lines, 32768 bytes). Pins found by grep of `tests/` and `.claude/hooks/tests/`: (1) `.claude/hooks/tests/test_vital_slice.py` `LINE_CAPS["AGENTS.md"] = 196` -> the 2-line rule makes 198: raise the cap to 198 with a dated note; (2) `.claude/hooks/tests/test_agent_guide_dedup.py` `T070_BASELINE_REF` pins AGENTS.md byte-identical to a commit -> commit the AGENTS.md edit, then repoint the ref to that commit (the file's own precedent: 'Repointed, NOT deleted'); (3) `tests/test_agents_md_primary.py` AC 1 `test_ac1_agents_md_carries_every_base_claude_md_line_in_order` rejects a line added after the opening block -> add the rule's two lines to an `ADDED_LINES` allowance, with the reason; its <=200 lines / <=32768 bytes checks stay true (198); (4) `tests/test_tracks.py` (<=200 lines, <=32768 bytes), `tests/test_claude_md_slim.py` (<=200 lines): hold at 198, no edit; (5) message-text pins: `tests/test_plugin_names.py` (the named test, fixed by AC 4; the `my plug$in` quoting test pins the POSIX text `python3 <quoted>`, still true) and `.claude/hooks/tests/test_pre_agent_validate_guide.py:168` (`"memory_slice.py" in context`, still true). Also: a new file under `.claude/hooks/lib/` would fail `tests/test_windows_parity_ledger.py` (no ledger row, and `docs/windows-parity.md` is off limits), so `python_launcher()` goes into the existing `lib/project_root.py`. |
| UI: visual regression | ☐ N/A (no UI) | |
| UI: design-system compliance | ☐ N/A (no UI) | |
| UI: responsiveness | ☐ N/A (no UI) | |
