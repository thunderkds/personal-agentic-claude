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

## Amendment — Round 2 (2026-10-21)

User, 2026-10-21, after reading the round-1 report: *"test more case and update above artifact also, I mean for the close, and resume session also, the token need to reload or anything related, check more to make the correctly compare, move vision, give the final suggestion also"*. Then: *"automate approve, I just want the report"* — user pre-approves the round-1 ground truth, the T172 baseline repoint, and this round's spend.

**Restated intent (round 2)**: make the comparison fairer and wider. Add more questions and harder kinds; add a realistic old way; run real agents on more questions with repeats; measure what a session costs when it is closed and started fresh, or resumed (context reload); measure the index's upkeep cost; end with a recommendation.

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| R1 | Question set grows to ≥35. New kinds, ≥4 each: `multi_hop` (answer needs 2 files, e.g. "which test covers X and where is X"), `exact_text` (a literal error/message string), `callers` ("what calls `fn`"), `negative` (asks for something that does not exist; correct = answer says not found and claims no file; `expected_paths: []`). Round-1 questions stay unchanged. | "test more case" |
| R2 | Script mode gains a third method `old_bounded`: `grep -rlIE` file list ranked by match count, then a ranged Read of ±40 lines around the first match in the top file, grep output capped at 50 lines — how a careful agent works. Report shows all three methods. | "make the correctly compare" |
| R3 | Real-agent mode runs **all** questions once per method, plus 3 repeats of 5 fixed questions per method to show run-to-run spread (min/median/max of tokens, cost, time). Correctness graded per question kind. Keep the per-run `--max-budget-usd`; abort the batch if cumulative cost passes **$12**. | "test more case" |
| R4 | New `--lifecycle` scenario, real agents, ≥4 two-question chains (Q2 is a follow-up that needs Q1's finding), per method: (a) **same session** — Q1, then Q2 via `--resume <session_id>` right away; (b) **resume after cache expiry** — Q1, wait ≥6 min, then `--resume` Q2; (c) **closed + fresh** — Q1, then Q2 in a new session that must re-find. Record per step: input, output, `cache_read_input_tokens`, `cache_creation_input_tokens`, cost, time, correct. Session persistence ON for these runs only. | "close, and resume session … the token need to reload" |
| R5 | Index upkeep: time a full re-index (`index_path force=true`) and an incremental one after touching 1 and 10 files; report seconds. One staleness probe: after editing a file and before re-index, does `search_semantic` return the old text? Revert every edit; never leave the main checkout modified. | "move vision" |
| R6 | Report (md) gains: per-kind accuracy, three-method script table, lifecycle table, run-to-run spread, upkeep, and a **Recommendation** paragraph (when to use which method), backed by numbers. Also emit `reports/context-search-benchmark-<date>.json` with all raw rows for the HTML report. | "give the final suggestion" |
| R7 | Unit tests cover the new scoring (negative kind; multi-hop = all expected files needed for hit@5, any for hit@1 — or state otherwise), the bounded old way, budget abort, and lifecycle record parsing, with fakes (no server, no `claude`). | Hard-Stop Gate 5 |

---

## Amendment — Round 3 (2026-10-22)

User, 2026-10-22: *"this repos is heavy of document, so I want to try out another repos ~/workspace/project/beautifly/github/tapchat-apis."* Earlier the same session: *"automate approve, I just want the report"*.

**Restated intent (round 3)**: rerun the comparison on a code-heavy repo — `tapchat-apis` (NestJS, 558 `.ts` of 588 tracked files) — so the verdict is not driven by this repo's Markdown share. Same methods, same scoring, new ground truth.

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| T1 | `--questions <path>` selects the question file (default unchanged). New fixture `tests/fixtures/context_search_questions_tapchat.json`: ≥35 questions about tapchat-apis — ≥6 each of conceptual, symbol, callers, multi_hop (source + its spec/test), exact_text; ≥4 negative (zero grep matches, checked); ≥3 doc (its 6 `.md` files). Ground truth checked by grep in that repo. | "try out another repos" |
| T2 | Grep exclusions configurable per target: for tapchat add `dist`, `coverage`, `node_modules`, `reports`, and grep only git-tracked content is preferred (`git grep` or equivalent) so ignored build output never counts. State the choice in the report. | fair compare |
| T3 | Runs: script mode (3 methods), real-agent mode all questions once + 3 repeats of 5 questions, `--root /home/hungnguyenhuu/workspace/project/beautifly/github/tapchat-apis`. Lifecycle: 2 chains per method, no expiry wait. Upkeep: timing only (full + no-op re-index), **no staleness probe** (it would write a file into the target repo). Cap: **$10** total. | "try out" |
| T4 | Target repo is **read-only**: no file written, staged, or deleted in it; `git status --short` there identical before and after (it has pre-existing user changes: staged `tsconfig.json`, untracked `reports/`). Real-agent runs use only read/search tools. | safety |
| T5 | Output: `reports/context-search-benchmark-tapchat-2026-10-22.{md,json}` in the T171 worktree, same JSON shape as round 2, plus a short "this repo vs tapchat" comparison section in the md. | "combine" |
| T6 | Unit tests for `--questions` and the per-target exclusions / tracked-only grep. | Hard-Stop Gate 5 |

---

## Amendment — Round 4 (2026-10-22): hybrid vs grep-only, keep-or-drop decision

User, 2026-10-22: *"try out the new way apply first … use the grep as default and use the context for the case, when we combine them, is it better than the only grep one … I need the evidence to keep the context solution or just drop it"*.

**Restated intent (round 4)**: test the proposed combined rule as it would ship, against grep-only, on both repos, and decide from evidence whether to keep easy-context or drop it.

**Methods (real agents only, `claude -p`, same flags as rounds 2–3):**
- `grep_only`: tools `Grep,Glob,Read`. Prompt = the round-2/3 old-agent prompt.
- `hybrid`: tools `Grep,Glob,Read` + `mcp__easy-context__search_semantic`, `mcp__easy-context__get_slice` (no `get_related`: the rule routes callers to Grep). Prompt = the same prompt plus this routing rule, verbatim:
  > How to search: use Grep/Glob and ranged Reads by default — for names, exact text, callers, a file and its tests, and checking that something does not exist. Use `search_semantic` first only for a question in plain words about intent, docs or decisions ("where is X done", "why did we choose X") when you have no good keyword; then confirm with a ranged Read.

**Pre-registered decision rule (fixed before any run; do not change after seeing results):**
- Per question, paired difference d = hybrid − grep_only, using the mean of the 2 runs per method. Report mean d for cost and tokens with a 95% bootstrap CI (10,000 resamples over questions, seed 171), pooled over both repos and per repo; also per question kind.
- **KEEP** context search if hybrid correctness ≥ grep_only on both repos AND (pooled cost CI upper bound ≤ 0, OR hybrid correctness is strictly higher on at least one repo with pooled cost CI upper bound ≤ +10%).
- **DROP** if pooled cost CI lower bound > 0 and hybrid correctness is not strictly higher on either repo.
- Otherwise **INCONCLUSIVE** — report which way it leans.

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| H1 | Both methods run on all questions of both repos (39 + 49), **2 runs per method per question**, interleaved (q1 grep, q1 hybrid, q2 …) so time-of-day/cache drift hits both equally. Same graders as rounds 2–3 (negative = opens with NOT FOUND). | "is it better than the only grep one" |
| H2 | Use `--output-format stream-json --verbose` (or equivalent) to record which tools each run called. Report for `hybrid`: share of runs that called `search_semantic` per question kind (route adherence), and cost of hybrid runs that never called it vs grep_only (= the fixed overhead of carrying the tools). | evidence for the cause |
| H3 | Report section "Round 4: hybrid vs grep-only" in a new `reports/context-search-hybrid-2026-10-22.{md,json}`: totals per repo, paired mean d + CI (pooled, per repo, per kind), correctness, route adherence, overhead, and the verdict line `VERDICT: KEEP | DROP | INCONCLUSIVE` computed by code from the rule above. | "I need the evidence" |
| H4 | Spend cap **$20** for this round; abort and report if cumulative would pass it. tapchat-apis stays read-only (`git status --short` identical before/after). | safety |
| H5 | Unit tests: paired-diff + bootstrap CI (fixed seed, known input), the verdict function on KEEP/DROP/INCONCLUSIVE fixtures, tool-call extraction from a stream-json sample. | Hard-Stop Gate 5 |

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
