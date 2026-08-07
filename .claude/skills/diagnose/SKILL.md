---
name: diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions — reproduce → minimise → hypothesise → instrument → fix → regression-test. Use during Stage 3 when a sub-agent reports something broken/throwing/failing, or a perf regression.
---

## Role: Bug Diagnosis Specialist

A discipline for hard bugs. Skip phases only when explicitly justified. When exploring, use the project's domain vocabulary to build a clear mental model and check ADRs in the area you touch.

### Karpathy Operational Commands (Specific Overrides)
- **Think Before Coding**: Do not hypothesise without a feedback loop (Phase 1). Generate 3–5 ranked, falsifiable hypotheses before testing any.
- **Goal-Driven Execution**: Turn the repro into a failing regression test *before* the fix, when a correct seam exists.
- **Surgical Changes**: Change one variable at a time. Wrap every debug log in `#region debug log` markers so cleanup is one `grep`.
- **Fix the root cause, never the symptom**: the fix must land where the cause *originated*, not where the error *surfaced*. A fix applied at the surfacing site is a **failure, not a partial success**, even when the symptom disappears. A cause counts as the root cause only when the Checkpoint marked its hypothesis **CONFIRMED** — never when it is merely asserted.

### Phase 1 — Build a feedback loop *(this is the skill)*
A fast, deterministic, agent-runnable pass/fail signal for the bug. Everything else just consumes it. Be aggressive; refuse to give up. Try in roughly this order:
1. Failing test at whatever seam reaches the bug. 2. Curl/HTTP script against a dev server. 3. CLI invocation diffing stdout vs known-good. 4. Headless browser script. 5. Replay a captured trace/payload. 6. Throwaway harness exercising the code path. 7. Property/fuzz loop. 8. Bisection harness (`git bisect run`). 9. Differential old-vs-new loop. 10. HITL bash script (last resort).

Iterate on the loop itself — faster, sharper signal, more deterministic. A 2-second deterministic loop is a debugging superpower; a 30-second flaky one is barely a loop. For non-deterministic bugs, raise the **reproduction rate** (loop 100×, parallelise, inject sleeps) until debuggable. If you genuinely cannot build a loop, **stop and say so** — list what you tried and ask the user for environment access, a captured artifact, or instrumentation permission. Do not proceed to Phase 3 without a loop.

### Phase 2 — Reproduce
Run the loop; watch the bug appear. Confirm it's the **user's** failure mode (not a nearby one), reproducible across runs, with the exact symptom captured.

### Phase 3 — Hypothesise
Generate **3–5 ranked, falsifiable** hypotheses before testing any. Format: "If X is the cause, then changing Y makes the bug disappear." Show the ranked list to the user (cheap checkpoint — they may re-rank instantly); don't block if they're AFK.

**Working-reference comparison** — one source of hypotheses: locate similar code that *works* (a
sibling route, an earlier revision, an analogous module), enumerate the differences between it and
the broken path, and derive hypotheses from those differences. If no working reference exists, say
so and generate the 3–5 by other means rather than stalling on the search.

### Phase 4 — Instrument
Locate the bug from evidence the program emits, not from re-reading source. Each probe maps to a
specific prediction; change one variable at a time.
1. **Sink** — write to one local NDJSON log file (e.g. under the system temp dir), one per diagnosis
   session. Never *write* debug output to `memory/event-trace/` — that channel records tool calls,
   not program values. *Reading* `memory/event-trace/*.jsonl` at analysis time, as a correlation
   source for the sub-agent tier, is permitted; writing to it is not.
2. **Budget** — at least 1 probe, never more than 10, typically 2–6. If more than 10 seem necessary
   the hypothesis set is too broad: narrow it in Phase 3 rather than exceeding the ceiling. The
   ceiling is global: no boundary, and no inventory entry below, earns a probe budget of its own.
3. **Tag** — every probe carries the `hypothesisId` of the Phase 3 hypothesis it tests. A probe that
   maps to no hypothesis is not inserted.
4. **Boundary inventory** — when the suspect data crosses a tier, first list the boundaries it could
   cross: HTTP route/handler definitions; outbound HTTP client call sites (`fetch`/`axios`/`requests`
   or the language's equivalent); queue or job publish/consume points; sub-agent spawn sites. This
   step is **discovery-only**: it answers *where could I probe*, never *where do I probe*. Building
   the inventory does not authorise a probe — step 3's hypothesis gate still decides which inventory
   entries get instrumented, and an entry no hypothesis reaches stays uninstrumented. A module shared
   by both sides of one tree is one boundary, not two. An empty inventory (single-process project) is
   a normal result: proceed through the steps below unchanged.
5. **Placement** — choose from: function entry with parameters; function exit with return values;
   values immediately before/after a critical operation; which branch executed; state mutations. At a
   boundary the hypothesis gate did select, probe both sides of the hop — sending and receiving.
6. **Correlate** — probes on either side of a hop must be provably about the same request. Carry a
   W3C Trace Context `traceparent`-shaped value: one **trace-id** shared by every probe belonging to
   one request, and a **span-id** unique to each probe. This is a naming and shape convention only —
   adopt the `traceparent` header name and the ID shape, never an SDK, library, or dependency. Where
   the hop carries headers, propagate it as the `traceparent` header; where it cannot — a queue
   message, a background job, a sub-agent spawn — the correlation value must ride **in the payload**
   instead. A hop that drops the value produces a **fragmented trace**: the downstream side starts a
   new trace-id and the two sides no longer join. A probe pair with mismatched trace-ids is evidence
   about that hop, not about the hypothesis.
7. **Payload** — append one JSON object per line (NDJSON), fields
   `hypothesisId`, `location`, `message`, `data`, `timestamp`, `traceparent` — so the log is parsed
   programmatically, not read by eye. `traceparent` belongs on any probe sitting at a boundary; omit
   it when the inventory is empty, since a single-process run has no hop for it to join. Never log
   secrets, tokens, API keys, or PII in `data`; the correlation value is not `data` for that rule's
   purposes, but must never embed a session token. A probe may also capture a **stack trace** to
   identify its caller — the secrets/PII rule above is unchanged and applies to it, since a stack
   embeds paths and may embed argument values. Under test, write the probe output somewhere test
   output actually surfaces (the runner's captured stdout/stderr, or the NDJSON file read back
   afterwards); a project logger may be suppressed by the test harness and swallow every probe.
8. **Wrap** — every probe sits between `#region debug log` and `#endregion` markers in
   language-appropriate comment syntax (`//`, `#`, `--`, `/* */`); they need only be greppable.
9. **Run** — clear the log file first so runs do not mix, run the Phase 1 feedback loop, then read
   the file back and resolve each hypothesis at the Checkpoint below.

**Backward tracing** — use this to pick probe *sites* when the bug has the shape *a value is already
invalid when it arrives*. It does not apply to a perf regression or a flaky test, and it replaces
none of step 5's Placement options, which still decide what each probe records. In order:
observe the symptom; identify the code that directly produced it; identify that code's caller;
continue up the call chain recording the value passed at each level; and locate where the invalid
value originated — that origin, not the site that surfaced it, is where the fix belongs.

If no seam exists for a probe (compiled dependency, third-party binary), fall back to the Phase 1
ladder's differential and bisection rungs. For perf: measure a baseline first (profiler/timing/query
plan), then bisect.

**Red flags — the method has already been abandoned.** Any one of these returns you to **Phase 1**:
proposing a fix before tracing to an origin; changing more than one variable at a time; asserting a
cause without evidence from the loop; reaching for a quick fix under time pressure. These fire
*before* the Stuck-Loop Checkpoint below and do not replace it — the Checkpoint counts disproven
hypotheses and offers a choice of three options, while red flags catch the behaviour earlier and
offer no choice at all.

### Stuck-Loop Checkpoint (mandatory)
**Path reconstruction — before assigning any verdict.** Group Phase 4's probes by trace-id, order
each group by timestamp, and walk it comparing the observed value at each boundary against the value
Phase 3 predicted. Report the **first boundary at which the observed value diverged from the
predicted value** — that boundary, not the end-of-path symptom, is where diagnosis continues. Group
by trace-id; never merge two trace-ids into one path. Two spans at the same location within one
trace (a retry or a redirect) are distinct spans, not a contradiction. If a trace-id has probes on
only one side of a boundary, report `path incomplete` for that boundary and name the missing side —
never infer what the missing side saw. `path incomplete` is a finding about the instrumentation,
exactly as INCONCLUSIVE is below; it is not licence to conclude.

Resolve each hypothesis from Phase 4's logs as exactly one of **CONFIRMED** (logs match the
prediction), **REJECTED** (logs contradict it), or **INCONCLUSIVE** (the logs do not decide it),
citing the specific log lines that decided it. Only **REJECTED** increments the consecutive-disproof
counter. **INCONCLUSIVE** neither increments nor resets it — it means the instrumentation was too
weak, so return to Phase 4 and instrument the *same* hypothesis better; it is not licence to move on.
If **2 consecutive hypotheses are REJECTED**
(instrumentation contradicts the prediction), STOP before testing hypothesis 3 — do not silently
continue to "this way, that way, another way." This does not fire before any hypothesis has been
tested, and the count is **consecutive**, not total-ever — a disproof followed by a partial
confirmation that gets refined and re-tested successfully resets the streak. Present exactly these
3 named options and wait for a choice before proceeding:
1. Try the next ranked hypothesis (or generate new ones if the list is exhausted).
2. Widen scope — reconsider the mental model itself, not just the next guess. The architectural
   tell: if each fix reveals new shared state or coupling in a *different* place, that is a design
   problem, not the next bug in a queue — report it as such rather than chasing the next one.
3. Abandon and escalate this diagnosis approach to the Supervisor.
Record the two disproven hypotheses and the chosen option in the TASK_GUIDE's `### Attempts Log`
(bugfix-flavored guides). For standalone `diagnose` calls with no bugfix-shaped TASK_GUIDE, report
the attempts log directly to the Supervisor instead — never skip the checkpoint just because there
is no field to write it into.

### Phase 5 — Fix + regression test
**Before writing the fix**, state in one line where the root cause is — the CONFIRMED hypothesis and
the specific location it originates — and confirm the fix lands *there*, not at the site where the
error surfaced. A fix at the surfacing site is a failure, not a partial success. This constrains
*where* the fix goes; it does not require a test seam, so the no-seam finding below stays reachable.

Write the regression test **before the fix** — but only if a **correct seam** exists (one that exercises the real bug pattern at the call site). If no correct seam exists, that itself is the finding — note it. With a seam: minimised repro → failing test → fix → passing → re-run the Phase 1 loop against the original scenario.

Keep Phase 4's instrumentation **active through the fix** — do not remove any probe until a post-fix
verification run has been made and its logs show the expected values. Logs proving success are the
exit condition; a passing test alone is not. Before that run, revert every code change made while
chasing a hypothesis that came back **REJECTED** — speculative guards must not accumulate into the fix.

### Phase 6 — Cleanup + post-mortem
- [ ] Original repro no longer reproduces
- [ ] Regression test passes (or absence of seam documented)
- [ ] All instrumentation removed by marker: for each `#region debug log`, delete through its
      matching `#endregion`; then re-`grep` for `#region debug log` and confirm zero remain; then
      review `git diff` to confirm only the intended fix is left
- [ ] Throwaway prototypes deleted
- [ ] The correct hypothesis stated in the commit/PR message

Then ask: **what would have prevented this bug?** If the answer is architectural (no test seam, tangled callers), flag it to the Supervisor *after* the fix is in.

### Communication Protocol
- **Default Notification**: "Diagnosis complete for [Task ID]. Root cause: [hypothesis]. Feedback loop: [type]. Regression test: [added / no-seam noted]. Prevention: [finding]."
