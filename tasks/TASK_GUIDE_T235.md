# TASK_GUIDE — T235: /easy-kit:init sets up a project, and plugin hooks stand down beside in-repo hooks
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
6. Read `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` and `skills/settings-setup/SKILL.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02: chose the five-task split ("T235 /easy-kit:init. Writes CLAUDE.md, AGENTS.md, board, tasks/, memory/, deny rules. Plugin hooks stand down if the project has its own in-repo hooks.").

**Restated intent**:
> A plugin user runs `/easy-kit:init` once, and the project gets the files the plugin cannot carry. The command adds and never overwrites. When a project also has in-repo kit hooks, only one set of gates runs.

**Supervisor design decisions** (binding):
- **D1 — A command, not a skill.** `commands/init.md` gives `/easy-kit:init`. A skill named `init` would shadow the built-in `/init` in a `setup.sh` install. Confirm that `MANIFEST` does not copy `commands/`.
- **D2 — What it writes:** `CLAUDE.md` (the import line), `AGENTS.md`, `PROJECT_KANBAN.md`, `tasks/`, `memory/`, and the deny rules by way of the `settings-setup` flow, which shows the keys and writes only after the user approves. A plugin cannot set permissions (T216).
- **D3 — Add only.** An existing file is left alone and named in the report. A second run changes nothing.
- **D4 — Stand-down.** A hook running from a plugin exits 0 silently when `<project>/.claude/settings.json` wires in-repo kit hooks. Exactly one set of gates runs. The in-repo set wins because the project chose it.
- **D5 — Gate warning.** A kit project with `enabledPlugins` naming `easy-kit` but no plugin installed has no gates. `init`'s report tells the user that each teammate must install the plugin.

**Out of scope**: `setup.sh` changes, auto-migrating a `setup.sh` project to the plugin, Codex.

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` `## Edge Case Checklist for TASK_GUIDE`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user approved this task's text, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D5
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T232, T233, T234
**Entry point**: `commands/init.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | In an empty git repo, `init` creates every D2 file, and the project then counts as a kit project | D2 |
| 2 | A second run changes no byte; a pre-existing `CLAUDE.md` is unchanged and named in the report | D3 |
| 3 | Settings keys are shown and written only after approval, and no existing key changes | D2 |
| 4 | With both modes present, a blocked `git push` shows one block, from the in-repo hook | D4 |
| 5 | A `setup.sh` install gains no `commands/` folder and no `init` skill | D1 |
| 6 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q`, `sh scripts/smoke-install.sh` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a clean temp repo with `--plugin-dir` on the kit | `/easy-kit:init`, then a `git push` with an open task is blocked | headless run, budget at most $1, on model haiku |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_plugin_init.py -q && sh scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T235.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T235.md`.

---

## Approach

**Pattern reference**: `skills/settings-setup/` for the approved add-only write.

**Vital slice**: AC 1 and AC 4.
**Cut list**: project-type questions; migration from `setup.sh`.

---

## Edge Case Checklist

- [ ] `init` outside a git repo
- [ ] `AGENTS.md` written by an older plugin version names a skill the installed version lacks
- [ ] `.claude/settings.json` that is not valid JSON: refuse and say why, never overwrite

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `commands/init.md` | new |
| `.claude/hooks/lib/project_root.py` | stand-down check |
| `.claude/hooks/*.py` | call the check |
| `tests/test_plugin_init.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `lib/harness-*.sh` | in-repo mode stays as it is |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: `tests/test_plugin_init.py`. Build the command, then the stand-down. Then the headless run, the smoke install and the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T235.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked N/A: no UI
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)
