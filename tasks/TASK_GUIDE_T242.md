# TASK_GUIDE — T242: Smaller plugin source: a `plugin/` folder of symlinks
**Date**: 2026-11-03
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`
**Mode**: auto (the user's `[auto]` tag, 2026-11-03)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `tasks/TASK_REVIEW_T236.md` (D5 size table, AC 1/AC 2 isolation recipe)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-03: "continue [auto]". T242 is the P2 follow-up T236 left on the board: "Smaller plugin source: a git install copies ~28 MB (12 MB cache + 16 MB marketplace clone, `tasks/` 4.7 MB) while the plugin runs from ~2–2.5 MB (T236 D5)".

**Restated intent**:
> A plugin install copies only what the plugin runs from. The documented install commands, the in-repo (`setup.sh`) mode, the hooks and `/easy-kit:init` keep working unchanged.

**Facts (official docs, read 2026-11-03, code.claude.com plugins pages):**
- No exclude mechanism; unknown keys are ignored. Install copies the plugin source directory into `cache/<marketplace>/<plugin>/<version>/`.
- In a plugin subdirectory, a symlink to elsewhere in the same marketplace repo is dereferenced (content copied); a symlink inside the plugin dir is kept; a symlink outside the marketplace is skipped.
- A `git-subdir` source checks out only its subdirectory, so links out of it would not resolve: do not use it.
- `marketplace add owner/repo` clones the repo; the 16 MB clone is out of reach of a source change.

**Supervisor design decisions** (binding; D2 was DEBATED, see `## Questions Log`):
- **D1 — Prove first.** Before any doc or test edit, build `plugin/` on the branch, commit it, and install from a git marketplace that is copied (not a local directory marketplace, which loads in place): e.g. `claude plugin marketplace add file:///<worktree>` or a local bare clone, in an isolated `CLAUDE_CONFIG_DIR` + scratch `HOME` (T236 recipe). Show: install succeeds; `find <cache> -type l` prints nothing (links became files); cache size; `.claude/hooks/tests` absent. If the links arrive dangling or are skipped, stop and report `Status: blocked` with a `Question:` line.
- **D2 — Layout (DEBATED).** `plugin/` holds one symlink per runtime path: `hooks`, `commands`, `skills`, `agents`, `templates`, `scripts`, `AGENTS.md`, `LICENSE`, `docs/claude-md`, `.claude/sensitive-paths.txt`, `.claude/hooks/lib`, and one link per `.claude/hooks/*.py` (so `.claude/hooks/tests/` is left out). `plugin/.claude-plugin/plugin.json` is a symlink to the root `.claude-plugin/plugin.json`, which stays a real file (root behaviour unchanged). Marketplace entry: `"source": "./plugin"`. The agent confirms the runtime path list from the code; add any path the code reads that this list misses, and say so.
- **D3 — Guard test.** A new test proves: every `${CLAUDE_PLUGIN_ROOT}/...` path in `hooks/hooks.json`, `commands/` and `skills/` resolves under `plugin/`; every `plugin_init.TREES`/`FILES` path resolves under `plugin/`; every link in `plugin/` resolves inside the repo; `.claude/hooks/tests` is not under `plugin/`; `claude plugin validate plugin/` passes (skip if no `claude`). The existing root validate test stays.
- **D4 — No doc command change.** README/site install commands stay as T236 pinned them. Only a size sentence may change if one exists.

**Out of scope**: the 16 MB marketplace clone (`--sparse`, a dist branch); T243 (icon, root `CLAUDE.md` warning); Windows `core.symlinks=false` (note it only).

**Requirement Refs**: `tasks/TASK_REVIEW_T236.md` (D5), `memory/decisions.md` T236 entry.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — auto (Supervisor), 2026-11-03
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D4
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T236
**Entry point**: `.claude-plugin/marketplace.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A real git-marketplace install of the branch succeeds; the cache holds no symlink, no `.claude/hooks/tests`, and its size is pasted next to T236's 12 MB | D1 |
| 2 | In a fresh repo, the installed copy's `/easy-kit:init` Step 1 (`scripts/plugin_init.py`) runs and the two T236 gate checks still block (hook-level run as in T236's first AC 2 evidence is enough) | Restated intent |
| 3 | The D3 guard test exists and fails on `main` | D3 |
| 4 | `marketplace.json` source is `./plugin`; README/site commands unchanged | D2, D4 |
| 5 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q`, `sh scripts/smoke-install.sh` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a git marketplace of the branch | cache ≈ 2–2.5 MB, real files only | real install + `du`/`find -type l` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_plugin_package.py tests/test_plugin_source.py -q && sh scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T242.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T242.md`.

---

## Approach

**Pattern reference**: `tests/test_plugin_package.py`.

**Vital slice**: D1 and AC 1.
**Cut list**: shrinking the marketplace clone; a release build step.

---

## Edge Case Checklist

- [ ] `project_root.py`: in the cache `_FILE_ROOT` and `$CLAUDE_PLUGIN_ROOT` are both the copied `plugin/`; with `--plugin-dir ./plugin` (links kept) `_FILE_ROOT` is computed with `abspath`
- [ ] `setup.sh`/MANIFEST must not ship `plugin/`
- [ ] `test_plugin_names.py` / site sweeps that walk the tree must not double-count `plugin/` links
- [ ] Windows `core.symlinks=false`: note in the review file

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `plugin/**` (symlinks), `.claude-plugin/marketplace.json` | new layout, source |
| `tests/test_plugin_source.py` (new), `tests/test_plugin_package.py` | guard + pins |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |
| `README.md`, `site/*` install commands | D4 |
| GitHub, the user's real Claude config | the user's |

---

## Test Plan

D1 first, and stop on failure. Red: `tests/test_plugin_source.py` on `main`. Add `plugin/`, change the source. AC 2 hook-level run. Run the suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T242.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked N/A with a reason
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)

---

## Questions Log

- 2026-11-03 DEBATE How should the kit shrink what a plugin install copies? → A: `plugin/` of per-path symlinks, `"source": "./plugin"`, root `plugin.json` kept real (Advocate 1: A with per-path links, root plugin.json linked or removed; Advocate 2: A with per-path links, plugin.json moved into `plugin/`) ⚠ decided for you — please review
- 2026-11-03 USER: decision 3's trace mismatch (Advocate calls filed under T241) accepted as recorded, option 1; no re-debate, no trace edit
