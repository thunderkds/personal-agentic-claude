# TASK_GUIDE — T006: Mermaid Export (Stretch Goal)
**Date**: 2026-06-11
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Backend-Implementer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Apply C1 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T003 (`GraphState`), T005 (CLI `export` command must call this module)
**Priority**: P1 — implement only after T001–T005 are complete and passing.

---

## Requirement (Pillar 1 — Adapt the requirement)

Implement `src/supervisor_viz/viz/mermaid.py` to convert a `GraphState` into a Mermaid flowchart string and write it to a `.md` file. The `supervisor-viz export <session> --format mermaid` command must call this module and produce a valid Mermaid diagram that renders correctly on GitHub and Notion.

**Restated intent**: A team member runs `supervisor-viz export session.jsonl --format mermaid` and gets a `session_graph.md` file containing a Mermaid flowchart they can paste into a PR or Notion doc.

**Out of scope**:
- PNG/HTML export (Phase 4)
- Interactive React Flow export (Phase 3)
- Mermaid rendering preview in the terminal

**Requirement Refs**:
- FR-006: `export <session> --format mermaid` outputs a Mermaid `.md` file
- US-004: Export session as Mermaid flowchart for sharing/documentation
- NFR-005: Type-hinted, mypy --strict passes

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `graphstate_to_mermaid(state)` returns a string starting with `graph TD` | FR-006 |
| 2 | Each node in `GraphState.nodes` appears as a Mermaid node definition in the output | FR-006 |
| 3 | Each edge in `GraphState.edges` appears as a Mermaid arrow in the output | FR-006 |
| 4 | HITL nodes use `:::hitl` class styling (orange in Mermaid) | FR-006 |
| 5 | The output string is valid Mermaid syntax (no bare `[`, `]`, `"` in labels — must be escaped) | FR-006 |
| 6 | `export_to_file(state, output_path)` writes the Mermaid string wrapped in a fenced code block to a `.md` file | FR-006 |
| 7 | `mypy --strict src/supervisor_viz/viz/mermaid.py` exits 0 | NFR-005 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `GraphState` with 2 nodes, 1 edge | `graphstate_to_mermaid()` returns string with `graph TD`, 2 node defs, 1 arrow | pytest |
| 2 | Node label with special chars `[test "name"]` | Label is sanitized before output | pytest |
| 3 | `export_to_file(state, /tmp/out.md)` | File created, contains ` ```mermaid` fence | pytest |

### Verification Command

```bash
pytest tests/viz/test_mermaid.py -v && mypy --strict src/supervisor_viz/viz/mermaid.py
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to mermaid.py + tests | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

Pure string generation — no external Mermaid library needed. ~60 lines.

```python
def graphstate_to_mermaid(state: GraphState) -> str:
    lines = ["graph TD"]
    # classDef for HITL
    lines.append("    classDef hitl fill:#f96,stroke:#c60")
    for node in state.nodes.values():
        label = _sanitize(node.label)
        shape = f'["{label}"]'
        line = f"    {node.id}{shape}"
        if node.status == "hitl":
            line += ":::hitl"
        lines.append(line)
    for edge in state.edges:
        lines.append(f"    {edge.source} -->|{_sanitize(edge.label)}| {edge.target}")
    return "\n".join(lines)

def _sanitize(s: str) -> str:
    return s.replace('"', "'").replace("[", "(").replace("]", ")")

def export_to_file(state: GraphState, output_path: Path) -> None:
    mermaid_str = graphstate_to_mermaid(state)
    output_path.write_text(f"```mermaid\n{mermaid_str}\n```\n")
```

---

## Edge Case Checklist

- [ ] `GraphState` with zero nodes: output is `graph TD` only — valid Mermaid, no error
- [ ] Node label containing `"`, `[`, `]`: must be sanitized before output
- [ ] Edge label is empty string: use a default label "→" instead
- [ ] Output file path's parent directory does not exist: create it with `mkdir -p` before writing

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `src/supervisor_viz/viz/mermaid.py` | Implement `graphstate_to_mermaid` + `export_to_file` |
| `tests/viz/test_mermaid.py` | Create — unit tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `src/supervisor_viz/core/` | Core modules are locked |
| `src/supervisor_viz/viz/textual_ui.py` | T004's domain |

---

## Test Plan

- Unit: `test_mermaid.py` — graph with known nodes/edges, assert string contents
- Manual: paste output into a GitHub comment to verify rendering

---

## Completion Checklist

- [ ] Implementation done (TDD)
- [ ] `pytest tests/viz/test_mermaid.py -v` all pass
- [ ] `mypy --strict src/supervisor_viz/viz/mermaid.py` exits 0
- [ ] `supervisor-viz export sample.jsonl --format mermaid` produces valid output
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T006 ready for Stage 4 review
