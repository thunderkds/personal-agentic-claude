# TASK_GUIDE — T058: diagnose — evidence-driven instrumentation loop (NDJSON logs, hypothesis-tagged)
**Date**: 2026-08-06
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. C2 task — read `memory/codebase-map.md` for directory layout and blast-radius hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

Original user request, verbatim across the session:

> "with the bug fix, I think we missing the skill for debugging the issues"

> "for the debug, I just care about how can the agent depend on the data to proceduce, we will focus on the logs, insert logs, trace them, and analyze to focus on the bugs"

> "agent should logs for debug purpose the event trace is served for another purpose"

> "I have a repos for you related, let take a look if any update https://github.com/millionco/debug-agent"

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A sub-agent running `diagnose` must locate a bug from evidence it collects by instrumenting the
> program — inserting its own structured debug logs, running the Phase 1 feedback loop, reading the
> emitted values, and resolving each hypothesis against them — rather than from reasoning over
> source code alone. `diagnose` Phase 4 currently states a one-line *preference* between instrument
> types and gives no procedure. This task replaces it with a concrete evidence loop, and closes the
> three downstream holes that loop exposes in Phases 5 and 6 and in the Stuck-Loop Checkpoint.

**Prior art consulted**: `https://github.com/millionco/debug-agent` (MIT), reviewed 2026-08-06 at the
Supervisor's request. Its `packages/debug-agent/skill/SKILL.md` is a mature implementation of this
exact idea. Eight of its mechanisms are adopted below; its transport layer is explicitly rejected.
Where our `diagnose` is stronger — the Phase 1 feedback-loop ladder, and the T052 Stuck-Loop
Checkpoint, neither of which it has — ours is kept unchanged.

**Out of scope** (what this task explicitly does NOT do):
- The `npx debug-agent` daemon, its HTTP ingest server, session IDs, ports, and the hosted remote-relay mode. Rejected for three reasons: it introduces a Node runtime dependency into a Python/shell repo; it routes program values through an external network hop; and it duplicates, over HTTP, what an append-to-file NDJSON write already achieves. The log sink is a plain local file.
- Any Complexity-gating of `diagnose` phases (the C0–C3 phase ladder explored earlier this session). Dropped by user redirect, not deferred. Line 8's `"Skip phases only when explicitly justified"` clause stays byte-identical.
- Any change to `memory/event-trace/*.jsonl` or the hooks that write it. Ruled out explicitly by the user: the event-trace records *tool calls*, serves the merge gate and the token-audit generator, and cannot carry program values. Debug logs are the agent's own, written to their own file.
- Any change to `.claude/skills/bugfix/SKILL.md`. Its Step 4 already wires `diagnose` in as mandatory first action; that wiring is correct and unchanged.
- Adding `diagnose` to the trigger-threshold table in `general-agent-template.md` — part of the dropped gating direction.
- Any new skill, and any hard-bug/easy-bug split of `diagnose`. Rejected at brainstorming: a second scaling mechanism would compete with the Complexity matrix.
- Replacing Phase 1's repro ladder with the prior art's "ask the user to reproduce" step. Ours is strictly stronger (10 automated rungs before HITL) and stays first.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):
- None — framework-internal skill authoring, not a PRD-tracked product requirement. Traceability runs to the verbatim user requests quoted above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — confirmed by the user 2026-08-06, including the explicit approval to fold in the prior-art mechanisms and bump C1→C2
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — `grill-with-docs` run this session; terms needing sharpening were *debug log* vs *event trace* (resolved: separate channels, see Out of scope) and *disproven* vs *REJECTED/INCONCLUSIVE* (resolved: see AC8)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist — N/A, see above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `### Phase 4 — Instrument`

---

## Acceptance Criteria

> Numbering note: AC1–AC7 rewrite Phase 4. AC8 fixes the Stuck-Loop Checkpoint. AC9–AC11 close the
> Phase 5/6 holes. AC12–AC14 are negative criteria locking scope.

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `### Phase 4 — Instrument` survives as a heading, and its body is a procedure of at least 5 discrete enumerated steps, not a preference sentence | "how can the agent depend on the data to proceduce" |
| 2 | Phase 4 specifies the log format as **NDJSON** — one JSON object per line appended to a single local log file — and gives a concrete payload field list including at minimum `hypothesisId`, `location`, `message`, `data`, `timestamp` | prior art STEP 1; "analyze to focus on the bugs" |
| 3 | Phase 4 states that **every probe must carry the `hypothesisId` of the Phase 3 hypothesis it tests**, and that a probe mapping to no hypothesis must not be inserted | prior art STEP 2; makes T052's counting mechanical |
| 4 | Phase 4 names the placement categories to choose from — at minimum: function entry with parameters, function exit with return values, values before/after a critical operation, which branch executed, and state mutations | "insert logs, trace them" |
| 5 | Phase 4 states an explicit log budget: at least 1, never more than 10, typical 2–6 — and instructs narrowing the hypothesis set rather than exceeding the ceiling | prior art STEP 2; supersedes the vague "never log everything and grep" |
| 6 | Phase 4 requires each probe be wrapped in `#region debug log` / `#endregion` markers using language-appropriate comment syntax | prior art Cleanup; deterministic removal |
| 7 | Phase 4 forbids logging secrets, tokens, API keys, and PII, and requires clearing the log file before each run so runs do not mix | prior art STEP 3 + FORBIDDEN list |
| 8 | The Stuck-Loop Checkpoint resolves each hypothesis as exactly one of **CONFIRMED / REJECTED / INCONCLUSIVE**, each citing specific log lines; and it states that only **REJECTED** increments the consecutive-disproof counter — INCONCLUSIVE neither increments nor resets it, and instead calls for better instrumentation of the same hypothesis | prior art STEP 4; preserves T052's contract under the new vocabulary |
| 9 | Phase 5 states that instrumentation is **kept active through the fix** and must not be removed until a post-fix verification run's logs prove success | prior art STEP 5; closes a real hole |
| 10 | Phase 5 requires reverting code changes made for any hypothesis that came back REJECTED, so speculative guards do not accumulate | prior art Critical Reminders |
| 11 | Phase 6's cleanup step removes instrumentation by the `#region debug log` marker (delete through the matching `#endregion`), then re-greps to confirm zero markers remain, then reviews `git diff` to confirm only the intended fix is left | prior art Cleanup steps 1–4 |
| 12 | `diagnose/SKILL.md` line 8's `"Skip phases only when explicitly justified"` sentence is byte-identical to its pre-change form (negative — proves the dropped gating direction did not re-enter) | Out of scope |
| 13 | The ordered list of `### Phase` headings is unchanged in text, count, and order — no phase added, removed, renamed, or reordered (negative — scope lock) | Surgical Changes |
| 14 | Phase 1, Phase 2, and Phase 3 bodies are byte-identical to their pre-change form (negative — the repro ladder and hypothesis-generation rules are explicitly out of scope) | Out of scope |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The shipped `.claude/skills/diagnose/SKILL.md` | `### Phase 4 — Instrument` extracts with ≥5 enumerated steps | automated test |
| 2 | The extracted Phase 4 block | Contains `NDJSON`, `hypothesisId`, the five placement categories, the numeric budget bounds (1/10), `#region debug log`, and a secrets/PII prohibition | automated test |
| 3 | The extracted Stuck-Loop Checkpoint block | Contains all three of `CONFIRMED`, `REJECTED`, `INCONCLUSIVE`, and states that INCONCLUSIVE does not increment the counter | automated test |
| 4 | The extracted Phase 5 block | States instrumentation is retained until post-fix verification, and requires reverting REJECTED-hypothesis changes | automated test |
| 5 | The extracted Phase 6 block | Cleanup is marker-driven (`#region debug log`), followed by a re-grep and a `git diff` review | automated test |
| 6 | The shipped file, line 8 | Byte-identical to the pre-change sentence (negative — a violation must FAIL) | automated test |
| 7 | The shipped file's `### Phase` heading list | Exactly the pre-change list, same text and order (negative) | automated test |
| 8 | Phase 1/2/3 bodies | Byte-identical to pre-change (negative) | automated test |
| 9 | Phase 4 body collapsed to a single prose sentence (mutation) | SC1 goes RED | mutation check, observed then reverted |
| 10 | `INCONCLUSIVE` deleted from the checkpoint (mutation) | SC3 goes RED | mutation check, observed then reverted |
| 11 | A word altered inside Phase 3's body (mutation) | SC8 goes RED | mutation check, observed then reverted |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q && \
python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_diagnose_evidence_loop.py` — 16 tests, new in this task. Mapping: AC1→`test_sc1_phase4_is_an_enumerated_procedure`; AC2→`test_sc2_phase4_specifies_ndjson_and_payload_fields`; AC3→`..._requires_hypothesis_id_per_probe`; AC4→`..._names_the_placement_categories`; AC5→`..._states_the_log_budget`; AC6→`..._requires_region_debug_log_markers`; AC7→`..._forbids_secrets_and_requires_clearing_the_log`; AC8→`test_sc3_checkpoint_uses_three_verdicts` + `test_sc3_only_rejected_increments_the_counter`; AC9→`test_sc4_phase5_retains_instrumentation_until_post_fix_verification`; AC10→`test_sc4_phase5_reverts_rejected_hypothesis_changes`; AC11→`test_sc5_phase6_cleanup_is_marker_driven` + `test_sc5_retired_debug_prefix_no_longer_referenced`; AC12→`test_sc6_line_8_is_byte_identical`; AC13→`test_sc7_phase_headings_unchanged_in_text_count_and_order`; AC14→`test_sc8_phase_1_2_3_bodies_are_byte_identical` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q` → `................    [100%]` / `16 passed in 0.03s`. Then `python3 -m pytest .claude/hooks/tests -q` → `204 passed in 8.13s` (188 baseline at c0b925f + 16 new). |
| Negative cases hold | ☑ pass | Each mutation applied to the **committed** file (commit `9533de5` made first, backup via `cp`, per the "git checkout also reverts your fix" gotcha), observed RED, then reverted with `git diff --quiet` confirming the fix survived. **SC9** (Phase 4 collapsed to `Instrument the program and read the logs.`) → `7 failed, 9 passed`, incl. `FAILED ...::test_sc1_phase4_is_an_enumerated_procedure`. **SC10** (`INCONCLUSIVE` deleted from the checkpoint) → `1 failed, 15 passed`: `FAILED ...::test_sc3_checkpoint_uses_three_verdicts`. **SC11** (Phase 3 body `3–5` → `3-6`) → `1 failed, 15 passed`: `FAILED ...::test_sc8_phase_1_2_3_bodies_are_byte_identical`, hash diff `be57ad75b66d...` vs expected `d8facfe34524...`. After the third revert: `WORKING TREE CLEAN — all 3 mutations reverted, fix intact` + `204 passed`. |
| verify | ☑ pass | The shipped `.claude/skills/diagnose/SKILL.md` was read back end-to-end after the final revert: Phase 4 is a 7-step procedure, the Checkpoint carries all three verdicts with the only-REJECTED-increments rule, Phase 5 retains instrumentation until post-fix verification, Phase 6 cleanup is marker-driven, and `grep -c '\[DEBUG-'` returns 0 file-wide. A sub-agent reading the file can now follow the loop — pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 2 changed files only — `.claude/skills/diagnose/SKILL.md` (`git diff` re-read after every mutation cycle) and the new test file. Deliberately skipped: `bugfix/SKILL.md` (its Step 4 `diagnose` wiring is unconditional and text-independent), `general-agent-template.md`, and the event-trace subsystem — all three are in "Files Must NOT Touch" and none consumes `diagnose`'s section text. No hook, script, or CI entry point greps `diagnose/SKILL.md`, so the blast radius is the file itself plus its new test. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests -q` → `204 passed in 8.13s`; the 188 pre-existing tests are unchanged and none was modified. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Pure skill-instruction text change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Pure skill-instruction text change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | Pure skill-instruction text change, no UI component |

---

## Demonstration

> Non-executable change (skill-instruction text), so BEFORE is the verbatim prior content.

**BEFORE**: `.claude/skills/diagnose/SKILL.md` lines 27–28, captured 2026-08-06 before any implementation commit exists:

```
### Phase 4 — Instrument
Each probe maps to a specific prediction. Change one variable at a time. Prefer debugger/REPL > targeted boundary logs > never "log everything and grep". Tag logs `[DEBUG-xxxx]`. For perf: measure a baseline first (profiler/timing/query plan), then bisect.
```

That is the entire section: one heading, one line. It ranks instrument types by preference and never
says what to log, in what format, how many probes, how to tie a probe to a hypothesis, or when to
stop. The corresponding Phase 6 cleanup checkbox reads only
`All [DEBUG-...] instrumentation removed (grep the prefix)`, and neither Phase 5 nor Phase 6 says
anything about *when* removal is allowed.

**AFTER**: `.claude/skills/diagnose/SKILL.md` at commit `9533de5` (file 59 → 90 lines). Verbatim excerpts:

```
### Phase 4 — Instrument
Locate the bug from evidence the program emits, not from re-reading source. Each probe maps to a
specific prediction; change one variable at a time.
1. **Sink** — write to one local NDJSON log file (e.g. under the system temp dir), one per diagnosis
   session. Never `memory/event-trace/` — that channel records tool calls, not program values.
2. **Budget** — at least 1 probe, never more than 10, typically 2–6. If more than 10 seem necessary
   the hypothesis set is too broad: narrow it in Phase 3 rather than exceeding the ceiling.
3. **Tag** — every probe carries the `hypothesisId` of the Phase 3 hypothesis it tests. A probe that
   maps to no hypothesis is not inserted.
4. **Placement** — choose from: function entry with parameters; function exit with return values;
   values immediately before/after a critical operation; which branch executed; state mutations.
5. **Payload** — append one JSON object per line (NDJSON), fields
   `hypothesisId`, `location`, `message`, `data`, `timestamp` — so the log is parsed
   programmatically, not read by eye. Never log secrets, tokens, API keys, or PII in `data`.
6. **Wrap** — every probe sits between `#region debug log` and `#endregion` markers in
   language-appropriate comment syntax (`//`, `#`, `--`, `/* */`); they need only be greppable.
7. **Run** — clear the log file first so runs do not mix, run the Phase 1 feedback loop, then read
   the file back and resolve each hypothesis at the Checkpoint below.

If no seam exists for a probe (compiled dependency, third-party binary), fall back to the Phase 1
ladder's differential and bisection rungs. For perf: measure a baseline first (profiler/timing/query
plan), then bisect.
```

Stuck-Loop Checkpoint, new opening (the rest of the T052 checkpoint is unchanged):

```
Resolve each hypothesis from Phase 4's logs as exactly one of **CONFIRMED** (logs match the
prediction), **REJECTED** (logs contradict it), or **INCONCLUSIVE** (the logs do not decide it),
citing the specific log lines that decided it. Only **REJECTED** increments the consecutive-disproof
counter. **INCONCLUSIVE** neither increments nor resets it — it means the instrumentation was too
weak, so return to Phase 4 and instrument the *same* hypothesis better; it is not licence to move on.
If **2 consecutive hypotheses are REJECTED**
```

Phase 5, new closing paragraph (the existing seam/regression-test paragraph is unchanged):

```
Keep Phase 4's instrumentation **active through the fix** — do not remove any probe until a post-fix
verification run has been made and its logs show the expected values. Logs proving success are the
exit condition; a passing test alone is not. Before that run, revert every code change made while
chasing a hypothesis that came back **REJECTED** — speculative guards must not accumulate into the fix.
```

Phase 6, the cleanup checkbox (replacing `All [DEBUG-...] instrumentation removed (grep the prefix)`):

```
- [ ] All instrumentation removed by marker: for each `#region debug log`, delete through its
      matching `#endregion`; then re-`grep` for `#region debug log` and confirm zero remain; then
      review `git diff` to confirm only the intended fix is left
```

**DELTA**: A sub-agent running `diagnose` can now follow a concrete evidence loop — tag each probe with its `hypothesisId`, emit NDJSON at named placements within a 1–10 budget, clear-run-read the log, and resolve each hypothesis CONFIRMED/REJECTED/INCONCLUSIVE against specific log lines — where before it had only a one-line ranking of instrument types and no procedure, no log format, no probe budget, no hypothesis linkage, and no rule for when instrumentation may be removed.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T058.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_bugfix_evidence_parity.py` — structural assertions over a SKILL.md's markdown (extract a section by heading, then assert on the extracted block), including negative cases observed RED. Imitate its section-extraction helper; do not write fresh regex.

**Secondary reference (external, read-only)**: `https://github.com/millionco/debug-agent`, file `packages/debug-agent/skill/SKILL.md`. Adopt the *mechanisms* listed in the AC table. Do **not** copy its text wholesale — `diagnose` is 59 lines and terse by design, the prior art is 233 lines and carries a product's install instructions. Do not vendor any of its code; MIT-licensed prior art consulted for design, not imported.

Rewrite `### Phase 4 — Instrument` as an ordered procedure:

1. Choose a log path — a single local file, e.g. under the system temp dir, one per diagnosis session. Not `memory/event-trace/`.
2. Pick probe placements from the named categories, one probe per hypothesis minimum, budget 1–10 (typical 2–6). If more than 10 seem necessary, the hypothesis set is too broad — narrow it first.
3. Append one NDJSON object per probe hit: `{hypothesisId, location, message, data, timestamp}`. Machine-parseable so the log can be analysed programmatically rather than by eye.
4. Wrap every probe in `#region debug log` / `#endregion` with language-appropriate comment syntax.
5. Clear the log file, run the Phase 1 feedback loop, then read the file back.
6. Resolve each hypothesis CONFIRMED / REJECTED / INCONCLUSIVE, citing the specific log lines that decided it.

Constraints that must survive the rewrite:
- One variable at a time (existing Surgical Changes override, line 13).
- Each probe still maps to a specific prediction — now enforced structurally via `hypothesisId`.
- The perf sub-case (baseline first via profiler/timing/query plan, then bisect) is retained.
- Never log secrets, tokens, keys, or PII.

The `[DEBUG-xxxx]` prefix convention is **superseded** by the region markers, which make cleanup
deterministic (delete a bounded block) rather than line-by-line. Phase 6's checkbox must be updated
in the same change — leaving it pointing at the retired prefix would break the cleanup contract.

`diagnose` is currently 59 lines and will land around 90–100. That is under the 150-line
`slim-skills` threshold, so no offsetting trim is needed.

---

## Edge Case Checklist

- [x] Phase 4 balloons and unbalances a deliberately terse skill — **file landed at 90 lines** (from 59), under the ~100 target and well under the 150-line `slim-skills` threshold; Phase 4 is 7 numbered steps plus one 3-line fallback paragraph
- [x] Region-marker syntax differs by language — step 6 says "language-appropriate comment syntax" and lists `//`, `#`, `--`, `/* */` as examples rather than mandating one; asserted by `test_sc2_phase4_requires_region_debug_log_markers`
- [x] A language with no block-comment or region convention — step 6 ends "they need only be greppable", framing the marker as a plain comment string, not an IDE feature
- [x] Retiring `[DEBUG-xxxx]` without updating Phase 6's checkbox — both moved in the same commit `9533de5`; also caught the *third* dangling reference on line 13 (the Karpathy Surgical-Changes override still said "Tag every debug log with a unique prefix"), now "Wrap every debug log in `#region debug log` markers". `test_sc5_retired_debug_prefix_no_longer_referenced` asserts `[DEBUG-` appears nowhere in the file (`grep -c` → 0)
- [x] INCONCLUSIVE becomes an escape hatch — the checkpoint says it means "the instrumentation was too weak, so return to Phase 4 and instrument the *same* hypothesis better; it is not licence to move on"; asserted by `test_sc3_only_rejected_increments_the_counter`
- [x] A bug with no reachable seam for a log statement — Phase 4's closing paragraph routes to the Phase 1 ladder's differential and bisection rungs rather than dead-ending
- [x] Heisenbugs — Phase 4 says nothing about determinism or reproduction rate, so it neither contradicts nor duplicates Phase 1's "raise the reproduction rate" guidance; Phase 1's body is byte-identical (AC14)
- [x] Logs that would capture secrets/PII in `data` — the prohibition sits **inside** Phase 4 step 5, and `test_sc2_phase4_forbids_secrets_and_requires_clearing_the_log` asserts it against the extracted Phase 4 block only
- [x] Substring assertions passing on a mere prose mention — every literal is asserted against `extract_section(...)` output. The one deliberate file-wide assertion is `test_sc5_retired_debug_prefix_no_longer_referenced`, which is an *absence* check where file-wide is the strictly stronger scope
- [x] Section-extraction regex truncating early — terminator is `(?=^### |\Z)` under `re.MULTILINE | re.DOTALL`; `extract_section` additionally asserts the extracted body is non-empty, closing the T039 vacuous-extraction mode, and `test_sc8` adds a per-section minimum-length floor so a truncated extraction cannot pass on the hash alone
- [x] Heredoc tripping the merge gate's prose scan — `.claude/skills/diagnose/SKILL.md` and the test file were both authored with the Write/Edit tools; the only heredocs used were throwaway Python mutation scripts, never file content

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/diagnose/SKILL.md` | Rewrite `### Phase 4 — Instrument` (currently lines 27–28) into a ≥5-step procedure; amend the Stuck-Loop Checkpoint with the three-verdict vocabulary; amend Phase 5 (retain instrumentation, revert REJECTED changes); amend Phase 6 (marker-driven cleanup). No other section changes. |
| `.claude/hooks/tests/test_diagnose_evidence_loop.py` | New. Structural tests for AC1–AC14, modelled on `test_bugfix_evidence_parity.py`. |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/bugfix/SKILL.md` | Step 4's `diagnose` wiring is already correct and unconditional; out of scope |
| `.claude/agents/general-agent-template.md` | The trigger-table row was part of the dropped Complexity-gating direction |
| `.claude/hooks/post_tool_trace.py`, `.claude/hooks/lib/task_context.py`, anything under `memory/event-trace/` | The user ruled the event-trace out explicitly; it serves the merge gate and token-audit generator |
| `.claude/skills/diagnose/SKILL.md` line 8, all `### Phase` headings, and the Phase 1/2/3 bodies | Scope lock, asserted by AC12/AC13/AC14 |
| Anything under `packages/` or `apps/` from the prior-art repo | Not vendored; consulted for design only |

---

## Test Plan

New file `.claude/hooks/tests/test_diagnose_evidence_loop.py`, following `test_bugfix_evidence_parity.py`:

1. A section-extraction helper reading the real shipped `.claude/skills/diagnose/SKILL.md`, terminating on `^###` under `re.MULTILINE` (see Edge Case Checklist — recorded defect family).
2. AC1 — extracted Phase 4 block contains ≥5 enumerated steps.
3. AC2–AC7 — one test each: NDJSON + payload fields; `hypothesisId` per probe; the five placement categories; the 1/10 budget bounds; `#region debug log` markers; secrets-PII prohibition + clear-between-runs.
4. AC8 — extracted checkpoint block contains all three verdicts and the INCONCLUSIVE-does-not-increment rule.
5. AC9/AC10 — extracted Phase 5 block: retain-until-verified, and revert-REJECTED-changes.
6. AC11 — extracted Phase 6 block: marker-driven removal, re-grep, `git diff` review.
7. AC12 — line 8 asserted byte-identical.
8. AC13 — full ordered `### Phase` heading list asserted against the known pre-change list.
9. AC14 — Phase 1/2/3 bodies asserted byte-identical against fixtures captured before the change.
10. Mutation controls, each observed RED then reverted, per SC9–SC11 and the Negative-cases Evidence row: (a) collapse Phase 4 to one prose sentence → SC1 RED; (b) delete `INCONCLUSIVE` from the checkpoint → SC3 RED; (c) alter a word in Phase 3's body → SC8 RED.

Then the full hook suite (`188 passed` at `1aa04dc`) must remain green.

---

## Completion Checklist

- [x] Implementation done — commit `9533de5` on `t058-work`
- [x] Self-review run — 2 changed files re-read against the AC table and the "Files Must NOT Touch" list; one finding acted on (the line-13 Karpathy override still referenced the retired `[DEBUG-xxxx]` prefix — see Edge Case Checklist and the note to the Supervisor below)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — required) — **left for the Supervisor at Stage 4**. Note for the reviewer: the change introduces no code, no data path, and no new dependency; the only security-relevant content is the *added* secrets/tokens/API-keys/PII logging prohibition in Phase 4 step 5, which strictly tightens the prior state (the old Phase 4 had no such prohibition). MEMORY also records that the built-in gate diffs the checked-out branch, so it must be invoked from `t058-work`, not from `main`
- [x] Lint passes — no linter configured for markdown in this repo; the Python test file was compiled and run clean under pytest (`16 passed`), and `.claude/hooks/tests` is fully green at 204
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `verify` run — feature confirmed working (see the `verify` Evidence row)
- [x] `docs/legacy/` updated (N/A — not legacy mode)
- [ ] `memory/MEMORY.md` updated — **Supervisor-only write** (Memory Write Protocol). Two candidate entries flagged below in the report to the Supervisor
- [x] Supervisor notified: task ready for Stage 4 review
