# TASK_GUIDE — T234: Skills and agents work under the easy-kit prefix
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: Medium
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
6. Read `experiments/plugin-spike/README.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02: chose the five-task split ("T234 Skills + agents work when prefixed. easy-kit:backend-developer and plugin paths for scripts.").

**Restated intent**:
> Every skill and agent works from the plugin under its `easy-kit:` name, and every script a skill calls is found from there. The same files still work unchanged in a `setup.sh` install.

**Supervisor investigation (2026-11-02)**: 26 lines in `skills/` and `agents/` run `python3 scripts|skills|.claude/...` from a repo-relative path; 8 lines name `subagent_type`; 70 name `Skill({ skill: ... })`. T216: a bare agent name fails with `Agent type 'probe' not found`; hooks see the prefixed `subagent_type`. `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` both expanded in a plugin skill.

**Supervisor design decisions** (binding):
- **D1 — First prove, then change.** Test in both modes whether `${CLAUDE_SKILL_DIR}` expands in a skill installed by `setup.sh`. Report the result before changing skill files. If it does not expand in both modes, report `Status: blocked` with a `Question:` line.
- **D2 — One set of files.** Do not fork skills per mode.
- **D3 — Agent names.** `AGENTS.md`'s role table gains the plugin form. `craft-spawn-prompt` reports the right name for the mode. Any hook logic reading `subagent_type` accepts both forms.
- **D4 — Scripts outside a skill.** A skill that calls a shared `scripts/*.py` finds it in both modes by one documented rule.

- **D5 — Carried from T232's review.** (a) `stop_auto_verify.py --start` run from a plugin path finds no project, because `$CLAUDE_PROJECT_DIR` is empty in a Bash tool call: give it a way to find the project. (b) `lib/board/moments.py:51-53` runs `<root>/scripts/board_sync.py`, which from a plugin is a project file: resolve it from the code's own location. `board_sync.py` takes its root from its own location, so it must also take the project root, or it would write into the plugin cache (T233 sweep).

- **D6 — Amendment (user, 2026-11-02, chose "Installer rewrites it").** When the installer projects skills to Codex, it rewrites `${CLAUDE_SKILL_DIR}` to the project path of that skill, on install and on Update. This overrides `Files Must NOT Touch` for `lib/harness-*.sh`, for the Codex projection only. Claude Code copies and source files stay as they are.
- **D7 — From T234 verify.** A plugin ships the kit's own `PROJECT_KANBAN.md`, so `script_project_root()` must never answer with the plugin folder when run from a plugin: with no project found it says so.

**Out of scope**: `init` (T235), Codex, `setup.sh`.

**Requirement Refs**: T216 spike findings.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user approved this task's text, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D4
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T232, T233
**Entry point**: `skills/*/SKILL.md`, `agents/*.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A test finds no repo-relative script call left in `skills/` or `agents/` that fails from a plugin | D1, D4 |
| 2 | A headless plugin run spawns `easy-kit:qa-expert`, and runs one skill script from each of `wake` and `craft-spawn-prompt` | D3, D4 |
| 3 | The same two skills pass in a `setup.sh` install | D2 |
| 4 | Hooks accept both `backend-developer` and `easy-kit:backend-developer`; tests cover both | D3 |
| 5 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | `--plugin-dir .` in a temp kit project | `/easy-kit:wake` prints its briefing | headless run, budget at most $0.50, on model haiku |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_plugin_names.py -q && sh scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T234.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T234.md`.

---

## Approach

**Pattern reference**: `experiments/plugin-spike/ekspike/skills/hello/SKILL.md`.

**Vital slice**: AC 1 and AC 2.
**Cut list**: renaming skills; a mode switch in settings.

---

## Edge Case Checklist

- [ ] Docs that quote `python3 scripts/...` for a human to type stay correct in a `setup.sh` install
- [ ] The Codex skill projection keeps its 8 KB skill-body limit

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/*/SKILL.md`, `agents/*.md` | script paths and names |
| `AGENTS.md` | role table |
| `.claude/hooks/*.py` | both name forms, only where a hook reads `subagent_type` |
| `tests/test_plugin_names.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `lib/harness-*.sh` | in-repo mode stays as it is |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Do D1 first and report it. Red first: `tests/test_plugin_names.py`. Change paths one skill at a time. Then the headless run, the smoke install and the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T234.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked N/A: no UI
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)
