# TASK_GUIDE — T007: QA — Unit Tests + Sample Traces + Smoke Suite
**Date**: 2026-06-11
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: QA-Automation-Agent
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. Apply C2 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T002, T003, T004, T005 (all implementation tasks must be complete)

---

## Requirement (Pillar 1 — Adapt the requirement)

Create the full QA suite for supervisor-viz Phase 1:
1. **Sample trace fixtures** in `examples/sample-traces/` — realistic JSONL files based on Claude Code's actual log schema, covering the key scenarios the tool must handle.
2. **Comprehensive unit tests** for all core modules (parser, HITL detector, GraphState) — filling any gaps left by the implementing agent.
3. **Integration smoke test** — runs `supervisor-viz trace` against the sample fixture and asserts the exit code and basic output.
4. **CI configuration** — `pyproject.toml` test configuration + a `Makefile` or `scripts/test.sh` that runs the full suite in one command.

**Restated intent**: Any developer can run `pytest` from the project root and see 100% of the acceptance criteria for all Phase 1 tasks verified by automated tests, with no manual steps required.

**Out of scope**:
- Performance benchmarks (manual for now)
- UI screenshot tests
- Load/stress tests

**Requirement Refs**:
- FR-001 through FR-009: all Phase 1 FRs must have at least one test
- NFR-001: HITL alert latency — verified via sample corpus (100% recall)
- NFR-004: Graceful degradation — at least one test per command
- NFR-005: mypy --strict must pass across the full src/ tree

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `pytest` from project root exits 0 with all tests passing | All FRs |
| 2 | `examples/sample-traces/sample_with_hitl.jsonl` exists and contains at least one `AskUserQuestion` tool_use event | FR-004 |
| 3 | `examples/sample-traces/sample_no_hitl.jsonl` exists and contains a valid multi-event session with no HITL | FR-002 |
| 4 | Running `supervisor-viz trace examples/sample-traces/sample_no_hitl.jsonl` exits 0 (smoke) | FR-005 |
| 5 | Running `supervisor-viz trace examples/sample-traces/sample_with_hitl.jsonl` exits 0 and HITL is detected (smoke — checked via captured output or exit marker) | FR-004, FR-005 |
| 6 | `supervisor-viz status` with no logs exits 0 with "No active sessions found." | NFR-004 |
| 7 | `mypy --strict src/` exits 0 across the entire source tree | NFR-005 |
| 8 | `HITL detection accuracy`: all `AskUserQuestion` events in both sample files are detected — 100% recall | NFR-001 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `pytest -q` | Zero failures, zero errors | CI / manual |
| 2 | `mypy --strict src/` | Zero errors | CI / manual |
| 3 | `supervisor-viz trace examples/sample-traces/sample_with_hitl.jsonl` | Exit 0 | Smoke test |
| 4 | Feed `sample_with_hitl.jsonl` to parser + HITL detector | 100% of AskUserQuestion events flagged | pytest assertion |

### Verification Command

```bash
pytest -q && mypy --strict src/ && supervisor-viz trace examples/sample-traces/sample_no_hitl.jsonl
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to tests/ + examples/ | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

### 1. Sample Trace Fixtures

Create realistic JSONL files that mirror Claude Code's actual log format. Each line is a JSON object. Key event types to cover:

**`sample_with_hitl.jsonl`** (minimum 8 events):
```jsonl
{"type":"session_start","session_id":"test-001","timestamp":"2026-06-11T10:00:00Z"}
{"type":"assistant","session_id":"test-001","timestamp":"2026-06-11T10:00:01Z","message":{"content":[{"type":"text","text":"Starting task..."}]}}
{"type":"tool_use","session_id":"test-001","timestamp":"2026-06-11T10:00:02Z","name":"Bash","input":{"command":"ls -la"}}
{"type":"tool_result","session_id":"test-001","timestamp":"2026-06-11T10:00:03Z","content":"file1.txt"}
{"type":"tool_use","session_id":"test-001","timestamp":"2026-06-11T10:00:04Z","name":"AskUserQuestion","input":{"questions":[{"question":"Should I delete file1.txt?","options":[{"label":"Yes"},{"label":"No"}]}]}}
{"type":"user","session_id":"test-001","timestamp":"2026-06-11T10:00:30Z","message":{"content":[{"type":"text","text":"No"}]}}
{"type":"assistant","session_id":"test-001","timestamp":"2026-06-11T10:00:31Z","message":{"content":[{"type":"text","text":"OK, keeping the file."}]}}
{"type":"session_end","session_id":"test-001","timestamp":"2026-06-11T10:00:32Z"}
```

**`sample_no_hitl.jsonl`** (minimum 6 events — no AskUserQuestion):
A straightforward session: session_start, assistant text, tool_use (Bash), tool_result, assistant text, session_end.

### 2. Gap-filling unit tests

Review all existing tests from T002–T006. Write additional tests for any AC not yet covered:
- Parser: inode rotation detection
- HITL: multiple consecutive HITL events
- GraphState: edge cases (unknown event types, empty stream)
- CLI: `trace` with non-existent file → exit 1

### 3. Smoke test script

Create `tests/test_smoke.py`:
```python
def test_trace_no_hitl(cli_runner):
    result = cli_runner.invoke(app, ["trace", "examples/sample-traces/sample_no_hitl.jsonl"])
    assert result.exit_code == 0

def test_trace_with_hitl(cli_runner):
    result = cli_runner.invoke(app, ["trace", "examples/sample-traces/sample_with_hitl.jsonl"])
    assert result.exit_code == 0

def test_status_no_sessions(cli_runner, tmp_path):
    result = cli_runner.invoke(app, ["status", "--log-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No active sessions" in result.output
```

### 4. pyproject.toml test config

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
strict = true
```

---

## Edge Case Checklist

- [ ] Sample fixture has a partial/truncated last line: verify parser skips it gracefully
- [ ] `AskUserQuestion` event with empty `questions`: verify HITL detected, fallback text shown
- [ ] `supervisor-viz trace` with a binary file (not JSONL): verify error message, exit 1
- [ ] All event types in the sample fixture have valid `session_id` fields

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `examples/sample-traces/sample_with_hitl.jsonl` | Create (may exist as stub from T004 — verify/extend) |
| `examples/sample-traces/sample_no_hitl.jsonl` | Create |
| `tests/test_smoke.py` | Create |
| `tests/core/test_parser.py` | Extend with gap-fill tests if needed |
| `tests/core/test_hitl_detector.py` | Extend if gaps found |
| `tests/core/test_trace.py` | Extend if gaps found |
| `pyproject.toml` | Add pytest + mypy config sections |
| `scripts/test.sh` | Create — one-command test runner |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `src/supervisor_viz/` | QA does not modify implementation — only tests and fixtures |
| `CLAUDE.md` | Supervisor config |

---

## Test Plan

- Run `pytest -q` — all tests pass
- Run `mypy --strict src/` — zero errors
- Run smoke: `supervisor-viz trace examples/sample-traces/sample_with_hitl.jsonl`
- HITL recall: feed sample files through `is_hitl_event` — count detected vs. expected

---

## Completion Checklist

- [ ] Sample fixtures created and validated
- [ ] `pytest -q` exits 0
- [ ] `mypy --strict src/` exits 0
- [ ] Smoke tests pass
- [ ] 100% HITL recall on sample corpus verified
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T007 ready for Stage 4 review
