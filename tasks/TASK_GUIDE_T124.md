# TASK_GUIDE — T124: Token meter — measure spend and agent focus from session transcripts
**Date**: 2026-09-25 (re-planned; the 2026-09-24 compression-hook plan is parked — DDR-0009)
**Complexity Level**: C2
**Risk Level**: Medium — reads session transcripts, which contain everything a session saw (secrets included)
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. **C2**: read `docs/token-focus-finding-2026-09-25.md` (method, pricing model, and the baseline numbers this meter must reproduce) and `docs/ddr/0009-measure-token-work-from-transcripts-and-aim-at-focus.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: *"the hard things relate to 124 is the evaluation, cause it related to the token
cost, the focusing on price decrease, so let investigate it more ability to test this update"* — then:
*"we have the strategy to send out prompt from agent to agent, so anyway to keep the agent focus on
the request, no overwhelm of content"* — then: *"yes, let do the best"*.

The Supervisor's investigation (finding doc) showed the transcripts already record per-call `usage`,
which makes cost measurable without anyone pasting `/cost` (the instrument DDR-0002 asked for).

**Restated intent:**
> One read-only command that turns Claude Code session transcripts into the numbers every token or
> focus change is judged by — spend by component, what fills a Supervisor session, how much a spawned
> agent reads before it starts, and what a proposed output-shrinking rule would have saved — printing
> aggregates only, never transcript content.

**Out of scope:**
- Any change to how agents are spawned, what they read, or how sessions compact (T125, T126).
- The Bash compression hook (parked, DDR-0009); the meter only *evaluates* such a rule offline.
- Writing reports into the repo, dashboards, HTML output, scheduled runs.
- Calling any API (no `count_tokens`); the 3.5 chars/token estimate is documented, not refined.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's three messages above and DDR-0009.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user: "yes, let do the best", 2026-09-25)
- [x] Domain terms align: *spawned agent*, *Supervisor session*, *pre-edit reading*, *carry cost*, *counterfactual*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `scripts/token_meter.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | New `scripts/token_meter.py`, stdlib only, read-only: it never opens a file for writing and never creates a directory (same rule as `scripts/memory_usage_report.py`, T063) | "evaluation"; T059 lesson |
| 2 | Transcript root: `--projects-dir DIR`; default `$CLAUDE_CONFIG_DIR/projects`, else `~/.claude/projects`. Reads `*.jsonl` recursively, including `<session>/subagents/` | finding § Source |
| 3 | API calls are de-duplicated by `message.id`; cost per call = (input + 2×1h-write + 1.25×5m-write + 0.1×read) × input price + output × output price. Prices are named constants (claude-opus-5 $5/$25) plus `--price-in` / `--price-out` | finding § pricing |
| 4 | **Summary**: transcripts (main/sub), API calls, billed-equivalent spend, and the share by component (input, cache write, cache read, output) | "price decrease" |
| 5 | **Spawns**: a transcript is a spawned agent when its first user message names `TASK_GUIDE_T<digits>`. Per spawn: task ID, calls, spawn-prompt chars, fixed prefix (first call's input+write+read), tokens read before the first `Edit`/`Write`/`MultiEdit`, calls before it, context at it, cost, and pre-edit carry share. Medians across spawns, and `--task Txxx` to filter | "agent to agent… focus" |
| 6 | **Session**: `--session PATH` reports one transcript: calls, spend, latest context size (tokens of the last call), and carry-weighted composition by content kind (tool results by tool name, tool-call inputs, assistant text, user text, attachments by type). Excludes `prompt_snapshot` (a copy of the system prompt, already in the fixed prefix) | T126 needs it; finding § 2 |
| 7 | **Counterfactual**: `--bash-lines N` replays "stdout > N lines → first 40 + error lines (cap 60) + last 60" over every Bash result and reports qualifying outputs, carry-weighted saving and its share of spend, and **recall risk** (an elided line ≥ 25 chars appears in the agent's next 3 outputs) | "ability to test this update"; DDR-0009 gate |
| 8 | **No content ever printed**: output holds counts, sizes, costs, task IDs, file basenames of transcripts, tool names and attachment types only — never transcript text, commands, file contents or prompt text | Risk: secrets |
| 9 | `--json` prints the same data as one JSON object (stable keys, documented in the module docstring) | T126 consumes it |
| 10 | **Fails loudly, not silently:** a file that has assistant entries but no parseable `usage` is counted as `unparsed` and listed by basename; if every file is unparsed, exit 2 with a message naming the expected keys. Malformed lines are skipped and counted | DDR-0009: format is not a public contract |
| 11 | Run against the Supervisor's transcripts at Stage 5, the meter reproduces the finding doc within tolerance: spend ±2%, 45 Bash outputs > 200 lines (±2 for sessions added since), counterfactual share 1.0% ±0.2 pt, spawn median pre-edit reading 16.8k ±10% (new spawns may move it; explain any drift) | Baseline integrity |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The implementing agent must NOT be the sole author of its own acceptance test. The Supervisor owns
> the fixture expectations below (hand-computed) and the mutation controls M1–M6.

### Success Criteria (observable, pass/fail)

All via `subprocess` on committed synthetic fixtures under `tests/fixtures/transcripts/` — not
import-and-call (T085/T093: behavioural claims need the real entry point).

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Fixture with 3 calls of hand-set `usage` (one duplicated `message.id`) | calls = 3; spend equals the hand-computed value to the cent; component shares sum to 100% | pytest |
| 2 | Spawn fixture: first message names `TASK_GUIDE_T901`, two Reads (known sizes) then an Edit | pre-edit tokens = chars/3.5 of those two results; calls-before-edit = hand value; task = T901 | pytest |
| 3 | Non-spawn fixture | not listed under spawns | pytest |
| 4 | Fixture with a 500-line Bash stdout, `FAILED x` on line 250, and a later assistant text quoting an elided line | `--bash-lines 200`: 1 qualifying output, recall risk 1; `--bash-lines 600`: 0 | pytest |
| 5 | Fixtures containing a sentinel string in tool results, prompts, commands and attachments | sentinel absent from stdout in every mode, text and `--json` | pytest |
| 6 | `--session` on a fixture with a `prompt_snapshot` attachment | composition excludes it; latest context = last call's tokens | pytest |
| 7 | Directory of files with assistant entries but no `usage` | exit 2, message names `usage` | pytest |
| 8 | Malformed JSON line mid-file | skipped, counted, rest parsed | pytest |
| 9 | `--json` | valid JSON; keys as documented | pytest |
| 10 | Script source | no `open(..., "w"/"a"/"x")`, no `mkdir`, no `write_text` | structural pytest (pattern from `test_memory_usage_report.py`) |
| 11 | Real transcripts (Stage 5, Supervisor/user-run) | AC11 tolerances | `/verify` |

**Mandatory mutation controls** (each must go RED, then be reverted; paste both runs):
- **M1** — drop `message.id` de-duplication → SC1 RED.
- **M2** — price 1h cache writes at 1.25× → SC1 RED.
- **M3** — count reads after the first Edit as pre-edit → SC2 RED.
- **M4** — print one tool-result excerpt in the session view → SC5 RED.
- **M5** — return exit 0 with zeros when nothing parses → SC7 RED.
- **M6** — drop the recall-risk window → SC4 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_token_meter.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -3      # no regressions
sh scripts/validate.sh
python3 scripts/token_meter.py --bash-lines 200                # Stage 5, on real transcripts (AC11)
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T124.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T124.md`. BEFORE: `python3 scripts/token_meter.py` on `main` →
> file not found. AFTER: the real-transcript run with the AC11 numbers side by side with the finding doc.

---

## Approach

**Pattern reference**:
- `scripts/memory_usage_report.py` + `tests/test_memory_usage_report.py` — read-only analysis script, stdout only, and the structural "never writes" test.
- The finding doc's method section — the exact rules (de-dup, pricing, spawn detection, pre-edit boundary, counterfactual, recall risk).

**Vital slice**: summary + spawns + session (AC4–6) — they are the numbers T125 and T126 are judged by. Counterfactual (AC7) is small and reuses the same pass.

**Cut list**:
- HTML/markdown report output, charts, a skill wrapper — stdout and `--json` only.
- Per-model pricing tables — one price pair plus overrides.
- `count_tokens` calibration of the 3.5 chars/token estimate.
- Stage 4 findings / `/verify` outcome parsing (the quality guard is read from TASK_REVIEW files by the Supervisor, not the meter).

**Design notes (Supervisor, with reasons):**
- **Aggregates only.** Transcripts hold secrets the session saw. The safe design is structural: the code paths that read text only ever take `len()` or run the recall-risk comparison in memory.
- **Loud on format drift.** Claude Code's transcript shape isn't a public contract. Silent zeros would look like a successful optimisation.
- **Pre-edit boundary = first Edit/Write/MultiEdit**, because "reading before starting" is what the focus question asks. An agent that never edits (a reviewer) reports its whole session as pre-edit; say so in output.

---

## Edge Case Checklist

- [ ] Duplicate `message.id` across streamed chunks (SC1)
- [ ] `cache_creation` object absent (older transcripts): treat `cache_creation_input_tokens` as 5-minute writes
- [ ] Tool result `content` as string vs list of blocks
- [ ] `toolUseResult` absent or not a dict
- [ ] Spawn whose first user message is a list of blocks, not a string
- [ ] Session with < 3 calls (report, but exclude from medians and say so)
- [ ] Empty projects dir → clear message, exit 2
- [ ] Very large files (45 MB total today) — stream line by line, no full-file loads
- [ ] Symlinked project dirs — do not follow outside the root

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/token_meter.py` | **New** |
| `tests/test_token_meter.py` | **New.** SC1–10 |
| `tests/fixtures/transcripts/**` | **New.** Synthetic, hand-made; no real transcript content |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `scripts/token_audit.py`, `scripts/token-audit.sh` | Retired instrument (DDR-0002); left as history |
| `skills/**`, `CLAUDE.md`, `agents/**`, `templates/**` | T125–T127 scope |
| `.claude/hooks/**`, `.claude/settings.json` | No hooks in this task |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: write SC1–10 against fixtures first; hand-compute every expected number in the test's comments.
2. Implement until green; record full-suite count before/after.
3. Run M1–M6; paste RED then reverted-GREEN.
4. Stage 5 (user-run `/verify` + Supervisor): run on real transcripts; fill AC11's comparison table.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` — **mandatory (Medium)**; content leakage and path handling in scope
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T124.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M6 mutation controls pasted (RED then GREEN)
- [ ] `/verify` — user-run (Supervisor cannot run it)
- [ ] UI Evidence rows: ☐ N/A — no UI component (CLI script)
- [ ] Supervisor notified: task ready for Stage 4 review
