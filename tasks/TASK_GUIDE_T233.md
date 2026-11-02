# TASK_GUIDE — T233: Plugin package and MIT LICENSE at the repo root
**Date**: 2026-11-02
**Complexity Level**: C1
**Risk Level**: Low
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

User, 2026-11-02: chose the five-task split ("T233 Plugin package + LICENSE. Manifest and marketplace at repo root.") and the MIT license.

**Restated intent**:
> The repo is a valid Claude Code plugin named `easy-kit` and its own one-plugin marketplace. It carries an MIT `LICENSE`. Nothing advertises the plugin yet.

**Supervisor design decisions** (binding):
- **D1** `LICENSE`: standard MIT text, `Copyright (c) 2026 thunderkds`.
- **D2** `.claude-plugin/plugin.json`: name `easy-kit`, version equal to the version the site shows, author `thunderkds`, license `MIT`. `.claude-plugin/marketplace.json`: marketplace name `easy-kit`, one plugin, source the repo root.
- **D3** `hooks/hooks.json` wires the same 11 hooks and matchers as `.claude/settings.json`, with `${CLAUDE_PLUGIN_ROOT}/.claude/hooks/<name>.py`. A test keeps the two lists equal.
- **D4** The marketplace lists no easy-memory entry: T217 stays deferred because `easy-memory-mcp` is private. T217's branch also adds `.claude-plugin/marketplace.json`, and that branch is not merged here.

**Out of scope**: skill and agent names (T234), `init` (T235), README or site text (T236).

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` Option C.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user approved this task's text, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D4
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T232
**Entry point**: `.claude-plugin/plugin.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `claude plugin validate .` passes, and `--profile` reports no `LICENSE_MISSING` | D1, D2 |
| 2 | A test fails when `hooks/hooks.json` and `.claude/settings.json` list different hooks or matchers | D3 |
| 3 | `marketplace.json` holds exactly one plugin, `easy-kit`, and no remote repo source | D2, D4 |
| 4 | `setup.sh` smoke install is unchanged: `sh scripts/smoke-install.sh` passes, and no new root file lands in an installed project unless the smoke test expects it | regression |
| 5 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | `claude --plugin-dir .` in a temp kit project | the plugin loads, and a hook blocks a `git push` with an open task | headless run, budget at most $0.50, on model haiku |

### Verification Command (exact, runnable)

```bash
claude plugin validate . && python3 -m pytest tests/test_plugin_package.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T233.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T233.md`.

---

## Approach

**Pattern reference**: `experiments/plugin-spike/ekspike/.claude-plugin/plugin.json`, `experiments/plugin-spike/ekspike/hooks/hooks.json`.

**Vital slice**: AC 1 and AC 2.
**Cut list**: a Codex manifest; a root copy of `plugin.json`.

---

## Edge Case Checklist

- [ ] The repo's `skills/` and `agents/` are found as plugin content through their symlink-free canon paths
- [ ] `experiments/plugin-spike` still validates

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `LICENSE` | new |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | new |
| `hooks/hooks.json` | new |
| `tests/test_plugin_package.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `lib/harness-*.sh`, `MANIFEST` semantics | in-repo mode stays as it is |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: `tests/test_plugin_package.py`. Add the files. Run `claude plugin validate .`, then the headless run, then the smoke install and the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T233.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked N/A: no UI
- [ ] Supervisor notified: task ready for Stage 4 review
