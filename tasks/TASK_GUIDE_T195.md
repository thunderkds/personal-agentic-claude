# TASK_GUIDE — T195: Sub-agents can use easy-memory, and read less of `memory/MEMORY.md`
**Date**: 2026-10-28
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
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp/README.md` — what easy-memory does (read-only; do not edit that repo)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-28, verbatim: "yes, run, install and test to make the final report, I plan to replace it with memory we are using as enhancement, so please make sure the result, by the way, it can reduce the token in memory also".

**Restated intent**:
> easy-memory (a hook-and-MCP tool that saves each answer as a note and offers a short index of earlier notes) is installed at user level. Its prompt hook reaches only the Supervisor. This task lets the four base sub-agents call `memory_search` and `memory_read` too, and stops them reading all of `memory/MEMORY.md` (42 KB, about 10,000 tokens) when the spawn prompt already carries a slice of it.

**Out of scope** (what this task explicitly does NOT do):
- No change to the `easy-memory-mcp` repo.
- No removal or shrinking of `memory/MEMORY.md`, `decisions.md` or `learnings.md`. Whether easy-memory can replace them is decided by the report after two weeks of `easy_memory.py report` data.
- No change to `craft-spawn-prompt` or `memory_slice.py` (the slice stays; DDR-0004 holds).
- No pack agents under `packs/`.

**Requirement Refs** (none: the kit has no `PRD.md` for this scope; the source is the user request above)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-28)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist (none needed)

---

## Dependencies & Reachability

**Depends on**: None (easy-memory is already installed at user level, 2026-10-28)

**Entry point**: `mcp__easy-memory__memory_search` (the string must appear in each of the four `agents/*.md` frontmatter `tools:` lines)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The `tools:` line of `agents/common-infrastructure.md`, `backend.md`, `frontend.md` and `qa.md` each lists `mcp__easy-memory__memory_search` and `mcp__easy-memory__memory_read`, and `tests/test_agent_frontmatter.py` still passes | sub-agents can call memory |
| 2 | Each of the four agent guides has one short rule: call `memory_search` once with the task goal before exploring; open a note only if it fits; treat notes as possibly out of date and re-check every changed file the note lists; if the tool is missing, skip it without stopping | sub-agents use memory |
| 3 | In each of the four guides the Startup step that says to read `memory/MEMORY.md` yourself now says: use the spawn-prompt slice; read the whole file only if your work reaches something the slice does not cover | stops the 42 KB read |
| 4 | A new test asserts criteria 1 to 3 for all four base agents, and fails on the current files before the change (red first) | Gate 5 |
| 5 | Negative: no agent guide loses an existing Startup step other than the rewording in criterion 3 | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The four `agents/*.md` after the change | Each `tools:` line has both MCP tool names; frontmatter test passes | `python3 -m pytest tests/test_agent_frontmatter.py tests/test_agent_memory_tools.py -q` |
| 2 | A backend-developer sub-agent spawned in this repo with memory on | Its trace shows a `mcp__easy-memory__memory_search` call | Supervisor live check (Stage 5), pasted into the review file |
| 3 | The old `agents/*.md` | The new test fails | run the new test before editing |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_agent_frontmatter.py tests/test_agent_memory_tools.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T195.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T195.md`.

---

## Approach

**Pattern reference**: `tests/test_agent_frontmatter.py` — stdlib parsing of the agent frontmatter, same `_agent_files()` helper style.

**Vital slice**: the `tools:` allowlist (without it the agent cannot call the tool at all) and the Startup-step rewording (the only token saving).
**Cut list**:
- Packs agents (`packs/*/agents/*.md`): later, if the trial succeeds.
- A spawn-prompt line: not needed, the rule sits in the agent guide.

Add the two tool names to the end of each `tools:` list. Add the memory rule as one numbered line under Mandatory Startup, after the `memory/MEMORY.md` step. Keep each guide's wording style.

---

## Edge Case Checklist

- [ ] easy-memory not installed on the machine: the `tools:` entry is ignored and the rule says to skip, so the agent does not stop
- [ ] The `tools:` value stays one line (the frontmatter test requires it)
- [ ] `.claude/agents` is a symlink onto `agents/`: edit only `agents/`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `agents/common-infrastructure.md`, `agents/backend.md`, `agents/frontend.md`, `agents/qa.md` | `tools:` line + memory rule + reworded MEMORY.md startup step |
| `tests/test_agent_memory_tools.py` | new test for AC 1 to 3 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/*` | the Supervisor owns memory writes |
| `skills/craft-spawn-prompt/*` | DDR-0004; out of scope |
| `PROJECT_KANBAN.md` | the Supervisor owns the board |

---

## Test Plan

Red first: write `tests/test_agent_memory_tools.py`, run it, see it fail on all four agents. Edit the guides. Run the Verification Command, then `python3 -m pytest tests -q -x` to show no other test broke.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T195.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
