# TASK_GUIDE — T232: Hooks find the real project when they run from a plugin
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `experiments/plugin-spike/README.md` and `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` (`## Edge Case Checklist for TASK_GUIDE`)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02, verbatim: "do we add the kit as plugin?", then "yes, let continue", then chose "Build core kit plugin" and the five-task split. First task of the split: "Hooks find the real project. Not their own folder; silent outside a kit project; fail closed in one. No gate logic changes."

**Restated intent**:
> A kit hook that runs from a plugin cache reads and writes the user's project, never the plugin folder. Outside a kit project it does nothing and prints nothing. Inside one, a bad input or a broken import never lets a blocking gate pass silently. In-repo (`setup.sh`) behaviour does not change.

**Supervisor investigation (2026-11-02, `main` @ `a60e3d47`)**: `post_write_register_task.py:15`, `post_tool_trace.py:31`, `pre_agent_step_limit.py:53`, `stop_review_reminder.py:16`, `stop_auto_mode_check.py:64`, `pre_agent_validate_guide.py:40`, `stop_auto_verify.py:77` and `pre_bash_block_unsafe_merge.py:26` compute `ROOT` from `__file__`. From a plugin cache that path holds no `PROJECT_KANBAN.md`, so a gate can see no open task and pass. `pre_tool_sensitive_path.py:79` and `lib/task_context.py:180` already prefer `$CLAUDE_PROJECT_DIR`.

**Supervisor design decisions** (binding):
- **D1 — Two roots.** Code location stays `__file__`-based (`HOOKS_DIR`, `lib/` imports). Project data (`PROJECT_KANBAN.md`, `tasks/`, `memory/`, `reports/`, `.claude/verify-runs`, `.claude/hooks/.state`) comes from one new helper, `.claude/hooks/lib/project_root.py`: `$CLAUDE_PROJECT_DIR` when set and a directory, else today's `__file__` path. The module attribute `ROOT` keeps its name, so existing tests that patch it keep working.
- **D2 — Kit project test.** `is_kit_project(root)`: `PROJECT_KANBAN.md` exists, or `.claude/board.json` exists. A hook running from outside `<root>/.claude/hooks` in a non-kit project exits 0 with no output and writes nothing. A hook running in-repo keeps today's behaviour exactly.
- **D3 — No state in the plugin.** No hook writes under its own code folder when it runs from a plugin: `${CLAUDE_PLUGIN_ROOT}` changes on every update.
- **D4 — Fail closed, audited.** For each of the 4 `PreToolUse` hooks and `stop_auto_mode_check.py`, a test feeds non-JSON stdin and a broken `lib/` import inside a kit project, and records the result. A blocking gate that lets the call pass is changed to block or ask. `pre_tool_sensitive_path.py` already asks. Fail-open that a hook's docstring chooses on purpose stays, and the review file lists it with the reason.
- **D5 — Gate logic untouched.** What each gate blocks does not change. Only D1–D4 change.

**Out of scope**: plugin manifest (T233), skill or agent names (T234), `init` (T235), stand-down when both install modes exist (T235), `setup.sh`, `lib/harness-*.sh`, `MANIFEST`, Codex.

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` Option C step 3; T216 spike findings.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user approved this task's text, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D5
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T216 (spike, merged)
**Entry point**: `.claude/hooks/lib/project_root.py`, imported by every hook named above

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | With the hooks copied to a temp folder (a fake plugin cache) and `CLAUDE_PROJECT_DIR` set to a temp kit project holding an In Progress task, `pre_bash_block_unsafe_merge.py` blocks `git push` | D1 |
| 2 | Same setup: `pre_agent_validate_guide.py` blocks a spawn naming a task with no guide, and `post_tool_trace.py` writes its trace under the project, nothing under the fake cache | D1, D3 |
| 3 | Same setup with a non-kit project: each of the 11 hooks exits 0, prints nothing on stdout and creates no file | D2 |
| 4 | The D4 table exists in `tasks/TASK_REVIEW_T232.md`: hook, bad-stdin result, broken-import result, change made or reason kept; a test pins each result | D4 |
| 5 | With `CLAUDE_PROJECT_DIR` unset, in-repo behaviour is unchanged: all existing hook tests pass unedited, except a test whose reason is stated in its commit | D1, D5 |
| 6 | No grep hit for `__file__`-derived data paths in the 8 hooks; a test enforces it | D1 |
| 7 | Mutations, each turns a new test RED, then green on revert: **M1** make the helper ignore `CLAUDE_PROJECT_DIR`; **M2** remove the non-kit exit; **M3** make one hook write state beside its code | guarantees asserted |
| 8 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a real `claude -p` run with `--plugin-dir` on a temp plugin holding copied hooks, in a kit project with an open task | a `git push` attempt is blocked | headless run, budget at most $0.50, on model haiku |
| 2 | the same plugin in a folder with no kit files | no hook message | same run |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_hooks_from_plugin.py .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T232.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T232.md`.

---

## Approach

**Pattern reference**: `lib/task_context.py` root lookup (line 161 onward), and `pre_tool_sensitive_path.py:79`.

**Vital slice**: AC 1 and AC 3.
**Cut list**:
- Plugin manifest and `hooks.json`
- Any change to what a gate blocks

---

## Edge Case Checklist

- [x] `CLAUDE_PROJECT_DIR` is set but the path does not exist
- [x] A sub-agent in a linked worktree: state stays in the main checkout, as today
- [x] `stop_auto_verify.py:354` strips `CLAUDE_PROJECT_DIR` from the headless run's environment: the hook still finds the project
- [x] Board mode `online`: `.claude/board.json` with no `PROJECT_KANBAN.md`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/project_root.py` | new helper |
| `.claude/hooks/*.py` (the 11 hooks) | use the helper; non-kit exit; fail-closed fixes by D4 |
| `.claude/hooks/lib/*.py` | only where a data path comes from `__file__` |
| `tests/test_hooks_from_plugin.py` | new |
| `MANIFEST` | one line for the new helper only if a test or the installer requires it; say so in the commit |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `lib/harness-*.sh` | in-repo mode stays as it is |
| `.claude/settings.json` | wiring unchanged |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: `tests/test_hooks_from_plugin.py`, AC 1–3, and see it fail on `main`. Add the helper, move each hook, run the suites after each hook. Do the D4 audit, then M1–M3. Then the headless run in Success Criteria.

---

## Completion Checklist

- [x] Implementation done
- [x] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T232.md` (Hard-Stop Gate 5)
- [x] UI Evidence rows marked N/A: no UI
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)
