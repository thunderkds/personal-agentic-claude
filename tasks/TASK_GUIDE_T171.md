# TASK_GUIDE — T171: Benchmark easy-context search vs. grep + Read on time, correctness and token cost
**Date**: 2026-10-21
**Complexity Level**: C2
**Risk Level**: Low
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
6. Read `memory/codebase-map.md` for directory layout

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-21: *"we will use the context search for searching or finding the evidence, and this repos is testing for that. I need you make some tests related that, you will call from the context and the old way, compare these with the time, the correctly and the token cost."*
User choice (AskUserQuestion, 2026-10-21): method = **Both** — a repeatable script benchmark AND a small real-agent run.

**Restated intent**:
> A runnable benchmark answers one question with numbers: for finding code/evidence in this repo, is the easy-context MCP search faster, more correct and cheaper in tokens than the old way (Grep/Glob + Read)? It has two modes: a deterministic script mode (free, repeatable) and a real-agent mode (`claude -p`, real token usage) on a small question subset.

**Out of scope**:
- Changing agent guides or rules (that is T172).
- Changing or re-indexing the easy-context server itself.
- Running the real-agent mode in CI (it costs tokens; manual only).

**Requirement Refs**: none in `PRD.md` — user-registered tooling task (same as T169).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the user's message + AskUserQuestion answer)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: none (user-registered)

---

## Dependencies & Reachability

**Depends on**: None. Runtime precondition (not a task): easy-context server at `http://127.0.0.1:8767/mcp`, this repo indexed as `personal-agentic-claude-d4124eeecadd` (621 files, 7,180 slices, 2026-10-21).

**Entry point**: `scripts/bench_context_search.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A fixed question set of 15–20 questions about this repo lives in `tests/fixtures/context_search_questions.json`. Each question has: `id`, natural-language `question`, the `grep_pattern` an agent would use the old way, and `expected_paths` (ground-truth file(s), checked by the Supervisor). Mix: ≥5 conceptual ("where do we block a push when a task is In Progress?"), ≥5 exact-symbol (`pull_moment`, `dirty_worktrees`), ≥3 doc/decision lookups (`memory/decisions.md`, `docs/`). | "call from the context and the old way" |
| 2 | Script mode (`python3 scripts/bench_context_search.py`) runs every question both ways and records per question and per method: wall-clock seconds, correctness (hit@1, hit@5 against `expected_paths`), and returned characters + estimated tokens (chars ÷ 4, labeled "estimated"). | "compare … time, correctly, token cost" |
| 3 | Fair "old way" definition: `grep -rn -E <grep_pattern>` over the repo (same exclusions as the index: `.git`, `__pycache__`, `node_modules`), files ranked by match count, then `Read` of the top-ranked file in full. "Context way": `search_semantic(question, k=5)` then `get_slice` of the top hit. Token cost = all text each way returns. Defined in the script's module docstring. | "the old way" |
| 4 | Context mode calls the easy-context server over HTTP JSON-RPC (MCP streamable HTTP: `initialize` → `tools/call`, header `X-Easy-Context-Root`), stdlib only (`urllib`), no new dependency. | Simplicity First |
| 5 | Real-agent mode (`--agent --limit 5`) runs `claude -p --output-format json` per question twice: once with only the easy-context tools allowed, once with only `Grep,Glob,Read`. It records `duration_ms`, `usage` tokens (input + output + cache), `total_cost_usd`, and whether the answer names an expected path. Manual only; it prints the cost estimate and asks to confirm before running unless `--yes`. | method = Both |
| 6 | Both modes write one Markdown report to `reports/context-search-benchmark-<YYYY-MM-DD>.md`: per-question table + a summary row per method (median time, hit@1, hit@5, total tokens) + a one-paragraph verdict. | "compare these" |
| 7 | Server unreachable → script mode exits 2 with `easy-context server not reachable at <url>`; pytest live tests **skip**, not fail. | negative / boundary |
| 8 | Unit tests (no server, no `claude`): scoring (hit@k), path normalisation (`./a/b` vs `a/b`), grep ranking, token estimate, report rendering — against a fake server response. | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Fake MCP response with `expected_paths` at rank 3 | hit@1 = 0, hit@5 = 1 | automated test |
| 2 | Server URL pointing at a closed port | exit 2, message names the URL | automated test |
| 3 | Live server up | report file written; every question has both rows; no row empty | manual run, output pasted in `TASK_REVIEW_T171.md` |
| 4 | `--agent --limit 5 --yes` | 10 runs recorded with real `usage` and `total_cost_usd` | manual run, report pasted |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_bench_context_search.py -q
python3 scripts/bench_context_search.py            # script mode, live server
python3 scripts/bench_context_search.py --agent --limit 5 --yes   # real-agent mode (costs tokens)
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T171.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T171.md`.

---

## Approach

**Pattern reference**: `scripts/pull_moment.py` — stdlib-only script style, exit codes, CLI args; `tests/test_pull_moments.py` — how scripts are unit-tested here.

**Vital slice**: script mode over the full question set + the report. Real-agent mode is a thin loop over the same question file.
**Cut list**:
- No exact tokenizer (no API key / extra dependency): script mode uses chars ÷ 4 and says so; real-agent mode gives true tokens.
- No charts/HTML report — Markdown table only.
- No repeated-trial statistics beyond median of 3 timing runs per question in script mode.

Ground-truth `expected_paths` must be checked by a human (the Supervisor) before results are trusted — the implementing agent drafts them, the Supervisor signs off (oracle rule).

---

## Edge Case Checklist

- [ ] SSE response (`content-type: text/event-stream`): parse the `data:` line, not the raw body.
- [ ] `mcp-session-id` header from `initialize` must be sent on later calls.
- [ ] Result `indexing: true` → report notes the index was not finished.
- [ ] grep finds zero files → old way scores a miss with its (small) token cost, not a crash.
- [ ] `claude -p` not on PATH → `--agent` exits 2 with a clear message.
- [ ] Real-agent mode must not let the agent edit files: allow only read/search tools.
- [ ] Timing: first easy-context call includes model warm-up — do one warm-up call, excluded from results.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/bench_context_search.py` | new — benchmark (both modes) |
| `tests/fixtures/context_search_questions.json` | new — question set + ground truth |
| `tests/test_bench_context_search.py` | new — unit tests + skip-if-no-server live test |
| `reports/context-search-benchmark-2026-10-21.md` | new — first run results |
| `tasks/TASK_REVIEW_T171.md` | new — evidence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `agents/*.md` | owned by T172 (parallel) |
| `.claude/hooks/*` | not in scope |

---

## Completion Checklist

- [ ] Implementation done
- [ ] `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T171.md` (Hard-Stop Gate 5)
- [ ] Script-mode report generated against the live server
- [ ] Real-agent run (5 questions) done and pasted
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
