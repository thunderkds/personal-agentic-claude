# TASK_GUIDE — T266: Native Windows support, step 5 — hooks fire on the PowerShell tool and the installer can write the Windows hook form
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
7. Read `docs/windows-support-plan.md` (this task is T-W5 of it) and `docs/adr/0003-native-windows-support.md` (branch `feat/t262-windows-adr`, worktree `/home/hungnguyenhuu/workspace/pets/wt-t262`)
8. Read `lib/merge-settings.py` in full and `.claude/hooks/lib/project_root.py` lines 95-150

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: native Windows support for the kit ("by pass the wsl, focus on the native window"; "[auto]"). Plan task T-W5: "Hook launcher".

**Facts from the official docs** (`https://code.claude.com/docs/en/hooks.md`, fetched 2026-11-06 by a docs check; the quotes are the evidence):
- Shell-form hook commands run through `sh -c` on macOS and Linux, "Git Bash on Windows, or PowerShell when Git Bash isn't installed". A `shell` field ("bash" or "powershell") can choose.
- Exec form ("`args` is present") spawns `command` directly with `args` as the argument vector. "There is no shell." `${CLAUDE_PROJECT_DIR}` and `${CLAUDE_PLUGIN_ROOT}` are substituted into `command` and each `args` element. On Windows `command` must resolve to a real executable (`py.exe` and `python.exe` qualify).
- Git for Windows is optional. Without it, Claude Code has no Bash tool; shell commands go through the PowerShell tool (`tool_name` "PowerShell", `tool_input.command`). "Match `Bash|PowerShell` in hooks that inspect shell commands." "A hook that matches only `Bash` never fires there."

**Restated intent**:
> (1) The three kit hooks that inspect shell commands fire for the PowerShell tool as well as Bash, and accept its `tool_name`. (2) The settings merge and the plugin stand-down logic recognise a kit hook written in exec form. (3) A pure function turns the kit's POSIX hook entries into the Windows exec form (`py -3` or `python`, no shell), so the Windows installer (T268) can write them. (4) The repo's own POSIX hook commands (`python3 …`) keep working exactly as today.

**Decision (Debate, 3 Advocates, then a docs fact check, 2026-11-06)**: the Debate's three Advocates all proposed one POSIX `sh -c` command for every OS, and all three named per-OS settings written by the installer as the fallback "if hooks run under PowerShell". The docs show they do, for a Windows user without Git Bash (the user ADR-0003 targets). So the Windows form is written per OS by the installer, as exec form (no shell, no quoting).

**Out of scope**:
- `setup.ps1` / `update.ps1` themselves (T268 calls this task's function).
- The merge gate's own code (`pre_bash_block_unsafe_merge.py`): T267 owns it, including its `tool_name` check.
- `plugin/hooks/hooks.json` command strings on Windows (plugin installs keep `python3`; recorded as a known limit). Its matchers ARE widened.
- The `git-guardrails` Python twin (moved to T268's follow-ups).
- A `shell`/`onFailure` field on any hook.

**Requirement Refs**: `docs/windows-support-plan.md` row 5 and T-W5; `docs/adr/0003-native-windows-support.md` decision 3. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor), 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `to_windows_settings` (function in `lib/windows_hooks.py`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | In `.claude/settings.json` and `plugin/hooks/hooks.json`, every `matcher` that is `Bash` becomes `Bash|PowerShell`, and `Edit|Write|Bash` becomes `Edit|Write|Bash|PowerShell`. No other matcher or command string changes. The T233 D3 test that keeps the two lists in sync still passes | (1) |
| 2 | `pre_tool_sensitive_path.py` (check at line ~312) and `post_bash_memory_update.py` accept `tool_name` "PowerShell" and read `tool_input.command` exactly as for Bash. `pre_bash_block_unsafe_merge.py` is NOT edited | (1) |
| 3 | A `Read`/`Glob` event still exits 0 in both hooks, and an event with no `command` fails the same way as for Bash today | (1) |
| 4 | `lib/merge-settings.py` `hook_paths` and `.claude/hooks/lib/project_root.py` `wires_in_repo_hook` find the `.claude/hooks/<name>` path in `command` OR in any `args` element. A shell-form entry gives the same keys as before | (2) |
| 5 | `lib/windows_hooks.py` exposes `to_windows_settings(settings, launcher)` (pure, returns a new dict) with `launcher` "py" or "python". Each kit hook entry `python3 "<root>"/.claude/hooks/x.py` becomes `{"type":"command","command":"py","args":["-3","${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"]}` (for "python": `command":"python"`, `args` without `-3`). Matcher, `description`, `timeout` and every other key are kept; non-kit entries and `permissions` are untouched | (3) |
| 6 | A `${CLAUDE_PLUGIN_ROOT}` entry converts the same way with `${CLAUDE_PLUGIN_ROOT}/.claude/hooks/x.py` in `args`. No string in the output contains `python3`, `sh -c`, `"$CLAUDE_PROJECT_DIR"` or a shell quote | (3) |
| 7 | Round trip: running `merge-settings.py` with the converted file as the project file and the repo's `settings.json` as upstream replaces each converted entry by upstream's (same `group_key`) and creates no duplicate. Converting the same file twice gives the same result (idempotent) | (2), (3) |
| 8 | `lib/windows_hooks.py` has a CLI: `python3 lib/windows_hooks.py <in.json> <out.json> --launcher py\|python`; an unknown launcher exits 2 and writes nothing | (3) |
| 9 | POSIX: every non-matcher byte of `.claude/settings.json` is unchanged (the diff is the matcher lines only) and the existing tests pass: `bash tests/test_settings_merge.sh`, `python3 -m pytest .claude/hooks/tests tests -q` | (4) |
| 10 | Negative: a hook entry in exec form whose `args` path points outside `.claude/hooks/` is NOT a kit entry (user entry, left alone by the merge) | (2) |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Matchers in both JSON files | Exactly the AC 1 set | automated test (parse JSON) |
| 2 | `{"tool_name":"PowerShell","tool_input":{"command":"cat .env"}}` to `pre_tool_sensitive_path.py` on a fixture with `.env` listed | Same verdict as the Bash event | automated test |
| 3 | The repo's settings.json through `to_windows_settings(…, "py")` | 11 entries in exec form, no `python3` anywhere | automated test |
| 4 | Convert, then merge against upstream | No duplicate kit entries | automated test |
| 5 | `windows_hooks.py` with the conversion body replaced by identity (mutation) | Test of row 3 goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_windows_hooks.py -q && bash tests/test_settings_merge.sh && python3 -m pytest .claude/hooks/tests tests -q
```

---

## Approach

**Pattern reference**: `lib/merge-settings.py` (pure functions plus a CLI, `die()` exit 2) and `tests/test_settings_merge.sh` / the Python settings tests it sits beside.

**Vital slice**: matcher widening, the two hook edits, `args`-aware path detection, the pure converter with its CLI.
**Cut list**: `shell`/`onFailure` fields; converting `plugin/hooks/hooks.json` command strings; the git-guardrails twin; `.ps1` hook scripts; auto-detecting the launcher (T268 probes `py` then `python` and passes it in).

Write failing tests first. Keep every change to a shared file minimal: `lib/merge-settings.py` is used by `setup.sh` and `update.sh` for every current user.

---

## Edge Case Checklist

- [ ] `args` missing, not a list, or holding non-strings: ignored, never an exception
- [ ] A `command` that is only an exec-form launcher (`py`) with the path in `args[1]`: found
- [ ] `HOOK_PATH_RE` still stops at whitespace and quotes
- [ ] Matcher regexes: `Bash|PowerShell` must not match `PowerShellFoo` in the harness (matcher is a regex on the tool name; keep it exact as the docs show)
- [ ] The 11 entries keep their order and `description` text
- [ ] Windows paths in `args`: forward slashes via the placeholder, never a literal `C:\`
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep README, `site/`, `docs/claude-md/`, `agents/`, comments for "matcher: Bash", "python3" hook claims and a hook-command count

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/settings.json` | Matchers only |
| `plugin/hooks/hooks.json` | Matchers only |
| `.claude/hooks/pre_tool_sensitive_path.py` | Accept `PowerShell` |
| `.claude/hooks/post_bash_memory_update.py` | Accept `PowerShell` |
| `lib/merge-settings.py` | `hook_paths` reads `args` |
| `.claude/hooks/lib/project_root.py` | `wires_in_repo_hook` reads `args` |
| `lib/windows_hooks.py` | New: converter and CLI |
| `tests/test_windows_hooks.py` | New tests incl. mutation control |
| `MANIFEST` | Add `lib/windows_hooks.py` if the manifest lists `lib/` files (check first) |
| Pre-existing pin tests | Known pins: `tests/test_settings_merge.sh:235` (`python3 "$CLAUDE_PROJECT_DIR"` prefix), `tests/test_subagent_sandbox_profile.py:160`, the T233 D3 settings/hooks.json sync test, any test pinning matcher strings. Grep `.claude/hooks/tests/` and `tests/`; handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | T267 |
| `.claude/hooks/stop_auto_verify.py`, `lib/proc.py`, `lib/filelock.py` | T264 / T265 |
| `setup.sh`, `update.sh`, `lib/*.sh` | T268 |

---

## Test Plan

JSON-level tests for the matchers and the converter; subprocess tests for the two hooks with PowerShell events; a merge round trip through the real `lib/merge-settings.py`; the existing shell merge suite; the full Python suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Lint passes
