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

### Phase 1 — Build a feedback loop *(this is the skill)*
A fast, deterministic, agent-runnable pass/fail signal for the bug. Everything else just consumes it. Be aggressive; refuse to give up. Try in roughly this order:
1. Failing test at whatever seam reaches the bug. 2. Curl/HTTP script against a dev server. 3. CLI invocation diffing stdout vs known-good. 4. Headless browser script. 5. Replay a captured trace/payload. 6. Throwaway harness exercising the code path. 7. Property/fuzz loop. 8. Bisection harness (`git bisect run`). 9. Differential old-vs-new loop. 10. HITL bash script (last resort).

Iterate on the loop itself — faster, sharper signal, more deterministic. A 2-second deterministic loop is a debugging superpower; a 30-second flaky one is barely a loop. For non-deterministic bugs, raise the **reproduction rate** (loop 100×, parallelise, inject sleeps) until debuggable. If you genuinely cannot build a loop, **stop and say so** — list what you tried and ask the user for environment access, a captured artifact, or instrumentation permission. Do not proceed to Phase 3 without a loop.

### Phase 2 — Reproduce
Run the loop; watch the bug appear. Confirm it's the **user's** failure mode (not a nearby one), reproducible across runs, with the exact symptom captured.

### Phase 3 — Hypothesise
Generate **3–5 ranked, falsifiable** hypotheses before testing any. Format: "If X is the cause, then changing Y makes the bug disappear." Show the ranked list to the user (cheap checkpoint — they may re-rank instantly); don't block if they're AFK.

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

### Stuck-Loop Checkpoint (mandatory)
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
2. Widen scope — reconsider the mental model itself, not just the next guess.
3. Abandon and escalate this diagnosis approach to the Supervisor.
Record the two disproven hypotheses and the chosen option in the TASK_GUIDE's `### Attempts Log`
(bugfix-flavored guides). For standalone `diagnose` calls with no bugfix-shaped TASK_GUIDE, report
the attempts log directly to the Supervisor instead — never skip the checkpoint just because there
is no field to write it into.

### Phase 5 — Fix + regression test
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
