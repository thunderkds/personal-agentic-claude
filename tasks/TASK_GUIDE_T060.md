# TASK_GUIDE — T060: diagnose — cross-tier boundary instrumentation and correlated trace reporting
**Date**: 2026-08-07
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
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots

Also read the current `.claude/skills/diagnose/SKILL.md` in full and `.claude/hooks/tests/test_diagnose_evidence_loop.py` before editing either — T058 shipped both together and this task extends, not replaces, that work.

---

## Requirement (Pillar 1 — Adapt the requirement)

Verbatim user request:

> "I expect the debug skill can automate logs the debug point, depend on the data response from the BE, FE, or Agent if any. Ability to logs, trace and throw the result better."

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> When a bug's suspect data crosses a tier boundary — frontend to backend, backend to a sub-agent's
> tool calls, or any network/process hop — `diagnose` Phase 4 should place probes at those boundaries
> rather than leaving placement to unaided judgment, should correlate the probes on either side of a
> hop so they are provably about the same request, and should report a reconstructed data path showing
> where a value first went wrong, instead of only per-hypothesis verdicts.

**Out of scope** (what this task explicitly does NOT do):
- Any new skill. This is an edit to `diagnose`, exactly as T058 was.
- Any daemon, ingest server, collector, or remote relay. T058 rejected that transport layer outright and this task does not reopen it.
- Any OpenTelemetry SDK, library, or runtime dependency. We adopt the W3C Trace Context *ID shape and header name* as a convention; we do not import an implementation.
- Writing debug output to `memory/event-trace/`. Still forbidden — see the Approach section for the read-vs-write distinction this task does introduce.
- Changing Phases 1, 2, 3, or 6, or the Stuck-Loop Checkpoint's counting rules.
- Auto-instrumenting a production or shared environment. Probes remain local, temporary, and marker-wrapped.

**Requirement Refs**: none — `PRD.md` does not enumerate skill-level FRs; this task traces to the verbatim user request above and to DDR-0003's diagnosis-quality line of work.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

---

## Dependencies & Reachability

**Depends on**: T059 — the destructive test at `.claude/hooks/tests/test_token_audit_generator.py:235` must be fixed first. Any Stage 3 spawn for this task runs in a worktree, where that test wipes the tracked `reports/token-audit_2026-07-21.md`. Landing T060 through a worktree before T059 reproduces a known data-loss incident.

**Entry point**: `### Phase 4 — Instrument`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Phase 4 contains a **Boundary inventory** step that names the concrete artifacts to scan for: HTTP route/handler definitions, outbound HTTP client call sites (`fetch`/`axios`/`requests`/equivalent), queue or job publish/consume points, and sub-agent spawn sites | "depend on the data response from the BE, FE, or Agent" |
| 2 | The inventory step is explicitly **discovery-only**: it states that building the inventory does not authorise a probe, and that the existing hypothesis gate still decides which inventory entries get instrumented | Simplicity First; preserves the no-orphan-probe rule |
| 3 | Phase 4's NDJSON payload gains a correlation field carrying a **W3C Trace Context** `traceparent`-shaped value (trace-id shared across a request's probes, span-id unique per probe), with the header name `traceparent` named literally | "trace ... better" |
| 4 | Phase 4 states that when a hop cannot carry headers (queue message, background job, sub-agent spawn), the correlation value must ride **in the payload** instead, and names those three cases | async/queue/agent boundaries |
| 5 | Phase 4 states that a hop which drops the correlation value produces a **fragmented trace**, and that a probe pair with mismatched trace-ids is evidence about the hop itself, not about the hypothesis | prior-art failure mode |
| 6 | The Stuck-Loop Checkpoint gains a **path reconstruction** step: before assigning verdicts, order the collected probes by trace-id then timestamp and state the first boundary at which an observed value diverged from the predicted value | "throw the result better" |
| 7 | Path reconstruction explicitly reports `path incomplete` when probes for a trace-id exist on only one side of a boundary — it must not infer the missing side | must not launder absence into evidence |
| 8 | For the sub-agent tier, Phase 4 states that `memory/event-trace/*.jsonl` may be **read** as a correlation source at analysis time, and restates that debug output must never be **written** there | user's chosen Agent-tier definition |
| 9 | The 1–10 probe budget ceiling is unchanged, and the boundary inventory does not introduce a per-boundary budget that could exceed it | Simplicity First |
| 10 | Negative: `### Phase 1`, `### Phase 2`, and `### Phase 3` bodies are byte-identical to their pre-task content | scope lock |
| 11 | Negative: the full ordered list of `### Phase` headings is unchanged in text, count, and order | scope lock |
| 12 | Negative: no occurrence of `daemon`, `ingest server`, or `relay` is introduced into `diagnose/SKILL.md` | T058's rejected transport must not re-enter |
| 13 | All 19 pre-existing tests in `test_diagnose_evidence_loop.py` still pass unmodified | T058's guarantees are not weakened |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The edited `diagnose/SKILL.md` | Phase 4 section matches a boundary-inventory assertion naming all four artifact classes from AC1 | automated test |
| 2 | The edited `diagnose/SKILL.md` | Phase 4 contains the literal string `traceparent` and describes trace-id/span-id roles | automated test |
| 3 | The edited `diagnose/SKILL.md` | Checkpoint section contains the ordered path-reconstruction step and the `path incomplete` case | automated test |
| 4 | The edited `diagnose/SKILL.md` | Phase 1/2/3 bodies hash-identical to the pre-task capture; Phase heading list unchanged | automated test (extend the existing hash fixtures) |
| 5 | Negative: a draft that adds a probe-per-boundary rule with no hypothesis gate | test asserting the discovery-only wording fails | automated test, mutation-verified RED |
| 6 | Negative: a draft reintroducing `daemon`/`ingest server`/`relay` | file-wide substring assertion fails | automated test, mutation-verified RED |
| 7 | Full hook suite | no regression | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q && python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure-instruction change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure-instruction change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure-instruction change, no UI component |

---

## Demonstration

> This task changes skill-instruction text, not executable code, so BEFORE is the verbatim prior
> content of the changed region.

**BEFORE**: verbatim `.claude/skills/diagnose/SKILL.md` lines 36-40 as of `1ac8cfa`:

```
4. **Placement** — choose from: function entry with parameters; function exit with return values;
   values immediately before/after a critical operation; which branch executed; state mutations.
5. **Payload** — append one JSON object per line (NDJSON), fields
   `hypothesisId`, `location`, `message`, `data`, `timestamp` — so the log is parsed
   programmatically, not read by eye. Never log secrets, tokens, API keys, or PII in `data`.
```

**AFTER**: [verbatim excerpt of the new Placement / Boundary inventory / Payload steps]

**DELTA**: [one sentence]

**WITNESS**: [derived from `memory/event-trace/T060.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_diagnose_evidence_loop.py` — section-extraction by heading, hash-pinned negative criteria, file-wide substring assertions for retired tokens. T058 established this exact shape for this exact file; imitate it rather than inventing a new test style.

The change is confined to Phase 4 and the Stuck-Loop Checkpoint. Three additions:

**1. Boundary inventory before placement.** The current Placement step (line 36-37) is a flat menu of seam types chosen per hypothesis. Add a preceding step that scans the repo for the four artifact classes in AC1 and lists them, then keep the existing hypothesis gate (lines 34-35: "A probe that maps to no hypothesis is not inserted") as the thing that decides which listed boundaries are actually instrumented. Discovery answers *where could I probe*; the hypothesis still answers *where do I probe*. Without that split the 1–10 budget is exhausted by the first real application.

**2. Correlation via W3C Trace Context.** Adopt the `traceparent` convention from the W3C spec — a trace-id shared by every probe belonging to one request, a span-id unique to each probe. This is deliberately a naming and shape convention only, with no SDK: it costs nothing, and if the project under diagnosis already emits real tracing data our NDJSON joins against it. The spec's documented failure mode is directly ours: a hop that drops the header makes the downstream side start a *new* trace, and the spans fragment silently. AC5 turns that into a reported observation rather than a silent gap. The spec's hardest case — async work, queues, background jobs, where context must ride in the payload rather than in headers — is exactly the shape of a sub-agent spawn, hence AC4.

**3. Path reconstruction before verdicts.** The Checkpoint currently emits CONFIRMED/REJECTED/INCONCLUSIVE per hypothesis. Add a step that first orders probes by trace-id then timestamp and names the first boundary where an observed value diverged from the prediction. AC7 is load-bearing: one-sided probe sets must report `path incomplete`, never an inferred opposite side. That is the same discipline as INCONCLUSIVE — weak instrumentation is a finding, not a licence to conclude.

**On the event-trace prohibition.** T058 locked that debug logs must never be routed to `memory/event-trace/`, because that channel serves the merge gate and the token-audit generator and records tool calls rather than program values. The user's chosen definition of the Agent tier (a sub-agent's tool calls) requires reading that channel. This task treats write and read as different operations: writing debug output there stays forbidden and AC8 restates it; reading it at analysis time as a correlation source is new and permitted. This is a deliberate, stated amendment to a T058 decision, not an oversight.

### Prior art consulted (2026-08-07)

Nothing in the agent-skill space covers the cross-tier leg, which is why this task is not a port:

- [`millionco/debug-agent`](https://github.com/millionco/debug-agent) — already mined by T058. Single-process, no boundary concept.
- [`doraemonkeys/claude-code-debug-mode`](https://github.com/doraemonkeys/claude-code-debug-mode) — same hypothesis→instrument→analyze loop, same `#region` wrapping, hypothesis-tagged logs. Explicitly no cross-tier boundaries and no correlation IDs; designed for single-process local debugging. One idea worth borrowing if it fits cheaply: an explicit note that the evidence-collection method adapts when the runtime is a mobile app or remote device.
- [Honeycomb `instrumentation-advisor`](https://docs.honeycomb.io/integrations/agent-skills) — closest published artifact to codebase gap-scanning, but neither its docs nor [its repo](https://github.com/honeycombio/agent-skill) disclose the scanning method. Recorded so it is not re-searched.
- [W3C Trace Context](https://www.w3.org/TR/trace-context/) and [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) — the adopted source for addition 2.

### Recorded risk — the auto-discovery direction has prior art against it

[TraceCoder](https://arxiv.org/pdf/2602.06875) (arXiv 2602.06875) is a trace-driven multi-agent debugging framework whose *Instrumentation Agent* decides probe placement by "lightweight reasoning over previous execution failures" — LLM reasoning over prior failures, **not** static analysis. It is the one system found that has actually built this component, and it chose the approach the user did not.

The user selected codebase auto-discovery with this counter-evidence stated, and the Supervisor was only able to read TraceCoder's abstract-level claim — the PDF body did not render, so the *reasons* for its choice are unread. The mitigation carried into this guide is AC2: the inventory is discovery-only and the hypothesis gate still decides, which keeps hypothesis reasoning load-bearing and makes the static scan an input to it rather than a replacement for it. If Stage 3 or Stage 4 finds the inventory step is producing probes the hypotheses did not motivate, that is the predicted failure and it should be escalated, not worked around.

**Second recorded risk — this repo cannot dogfood the feature.** This is a Python and shell repo with no frontend and no backend, so the boundary-discovery logic has no real target here. Its tests will assert against the skill's instruction text and fixtures, and the first genuine exercise happens in a downstream project. Per the recorded learning that patching a channel in a test does not prove the channel works, do not describe fixture-based tests as end-to-end verification in the Evidence table.

---

## Edge Case Checklist

- [ ] A monorepo where frontend and backend live in one tree — the inventory must not double-count a shared client module
- [ ] A boundary with no seam (third-party binary, compiled dependency) — falls through to the existing Phase 1 differential/bisection fallback, which must remain reachable
- [ ] A single-process project with zero boundaries — the inventory is empty and Phase 4 must proceed exactly as it does today, not stall
- [ ] Repeated requests in one run producing many trace-ids — path reconstruction must group by trace-id, not merge them
- [ ] A retry or redirect producing two spans at the same location within one trace
- [ ] Correlation values must not be treated as `data` for the secrets/PII rule's purposes, but must still never embed a session token
- [ ] A sub-agent spawn whose `memory/event-trace/` records are absent because the trace dir is gitignored in a worktree — must report `path incomplete`, not infer

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/diagnose/SKILL.md` | Phase 4 gains a boundary-inventory step and a correlation field in the payload; Checkpoint gains path reconstruction |
| `.claude/hooks/tests/test_diagnose_evidence_loop.py` | New assertions for AC1–AC12; extend the existing hash-pin fixtures to the new pre-task capture |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/tests/test_token_audit_generator.py` | T059's scope, not this task's |
| `reports/token-audit_*.md` | tracked derived data; a worktree run must never regenerate it (the T059 incident) |
| `memory/event-trace/**` | read-only for this task by construction |
| `.claude/skills/bugfix/SKILL.md` | the T052 stuck-loop counter contract is unchanged here |

---

## Test Plan

Extend `test_diagnose_evidence_loop.py` in its existing style — no new test file. Positive assertions for the boundary inventory, the `traceparent` correlation field, the payload-carried variant, the fragmented-trace case, path reconstruction, and `path incomplete`. Negative assertions: file-wide substring checks that `daemon`/`ingest server`/`relay` are absent, and hash pins on the Phase 1/2/3 bodies and the Phase heading list re-captured against the pre-task state.

Every new assertion must be mutation-verified: break the thing it guards, observe RED, restore, observe GREEN, and paste both. Per the recorded learning about vacuous assertions, an assertion never observed failing is not evidence — this applies with particular force to the negative substring checks, which pass trivially on any file that never mentioned the token.

The implementing agent must not be the sole oracle for its own tests; the Supervisor writes or signs off on at least the AC7 and AC10-AC12 assertions.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk) — run manually and label it if the checked-out branch is not the task branch
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (flag to Supervisor; sub-agents do not write memory)
- [ ] Supervisor notified: task ready for Stage 4 review
