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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [SC9/SC10/SC11 must each be observed RED under mutation, then reverted] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
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

**AFTER**: [verbatim excerpt of the rewritten Phase 4, the amended Stuck-Loop Checkpoint, and the amended Phase 5 / Phase 6 sections]

**DELTA**: [one sentence — what a sub-agent running `diagnose` can now follow that it could not before]

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

- [ ] Phase 4 balloons and unbalances a deliberately terse skill — procedure steps, not prose paragraphs; hold the whole file under ~100 lines
- [ ] Region-marker syntax differs by language (`//` vs `#` vs `--` vs `/* */`) — say "language-appropriate comment syntax", do not hardcode `//`
- [ ] A language with no block-comment or region convention — the marker is a plain comment string, not an IDE feature; it only needs to be greppable
- [ ] Retiring `[DEBUG-xxxx]` without updating Phase 6's checkbox leaves a dangling contract — AC11 covers this; verify both moved together
- [ ] INCONCLUSIVE becomes an escape hatch that never terminates — the checkpoint must say it calls for *better instrumentation of the same hypothesis*, not for moving on
- [ ] A bug with no reachable seam for a log statement (compiled dependency, third-party binary) — must not dead-end; fall back to the Phase 1 ladder's differential/bisection rungs
- [ ] Heisenbugs where a probe's own timing changes the outcome — Phase 1 already covers raising reproduction rate; Phase 4 must not contradict it
- [ ] Logs that would capture secrets/PII in `data` — AC7's prohibition must be inside the extracted Phase 4 block, not merely elsewhere in the file
- [ ] Substring assertions passing on a mere prose mention — assert every literal inside its *extracted section block*, never file-wide
- [ ] Section-extraction regex truncating early on a nested heading — this repo has six recorded defects in that exact family; anchor the terminator with `^###` under `re.MULTILINE`
- [ ] Writing file content via a heredoc containing a guarded command trips the merge gate's prose scan — use the Write/Edit tools

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

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — required)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working
- [ ] `docs/legacy/` updated (N/A — not legacy mode)
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
