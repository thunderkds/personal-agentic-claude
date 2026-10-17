# TASK_GUIDE — T148: A rewritten event trace is detectable — hash-chained, with the chain head anchored outside the repo
**Date**: 2026-10-16
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2)

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 9: *"Audit trail that is harder for an agent to rewrite after the fact."* Brainstorm answer 2026-10-16: **anchor outside the repo** — an in-file chain alone only catches careless edits, because a rewriting agent can recompute it.

**Verified state (2026-10-16)**: `post_tool_trace.py` appends one JSON line per tool call to `memory/event-trace/<task>.jsonl`; that directory is **gitignored** (`.gitignore:53`), so no copy exists that an agent can't rewrite. The merge gate reads these traces (`trace_shows_verification`).

**Restated intent**:
> Each trace line carries a hash chained to the previous line, the latest chain head is also appended to a file outside the repo that agents are denied write access to, and a verifier reports whether a task's trace still matches its anchor.

**Out of scope**:
- Making the merge gate block on a broken chain (report first; a later task may wire it in)
- Signing / keys
- Protecting the anchor from the human operator

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (9) and the brainstorm answers.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "anchor" added by this task
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `.claude/hooks/post_tool_trace.py` (writer); `scripts/verify_trace.py <task>` (new, verifier)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Each new trace line gains `prev` and `hash` = sha256(`prev` + canonical JSON of the line without `hash`); the first line's `prev` is `"genesis"` | "hash-chained" |
| 2 | After each append, `<task> <line-no> <hash>` is appended to `~/.claude/harness-anchors/<repo-slug>/<task>.anchors` (overridable by `CLAUDE_TRACE_ANCHOR_DIR` for tests) | "anchored outside the repo" |
| 3 | `.claude/settings.json` gains `permissions.deny` rules for Edit/Write on the anchor directory and Bash commands naming it | "agents are denied write access" |
| 4 | `verify_trace.py <task>` prints `INTACT`, `BROKEN at line N`, `ANCHOR MISMATCH at line N` or `UNANCHORED` (pre-T148 lines) and exits 0/1/1/0 | "a verifier reports" |
| 5 | Existing trace consumers (`trace_shows_verification`, token meter) still parse traces with the two extra fields — their tests pass unmodified | no regression |
| 6 | Anchor write failure never breaks the tool call: the trace line is still written and a `"anchor": "failed"` field is set | tracing must not break work |
| 7 | Concurrent appends to one task's trace are serialised (file lock), so two agents can't fork the chain | concurrency |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Three hook invocations, then verify | `INTACT` | automated |
| 2 | Edit line 2's `summary` without recomputing | `BROKEN at line 2` | automated |
| 3 | Edit line 2 **and** recompute the whole chain | `ANCHOR MISMATCH at line 2` — the case an in-file chain misses | automated |
| 4 | Trace with pre-existing unchained lines then new ones | `UNANCHORED` for old lines, chain checked from the first chained line | automated |
| 5 | Anchor dir unwritable | trace line written, `anchor: failed`, exit 0 | automated |
| 6 | 2 processes × 50 appends | verify `INTACT`, 100 lines | automated |
| 7 | **Mutation control**: verifier skips the anchor comparison | SC3 RED | Supervisor re-runs |
| 8 | Live: agent session tries `Write` to the anchor file | denied by permissions | manual at `/verify` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_trace_chain.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T148.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T148.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/post_tool_trace.py` itself — keep its append and `_untagged` fallback; `.claude/hooks/pre_agent_step_limit.py` — how `session_id` is sanitised into a filename (reuse for `<repo-slug>` and `<task>`).

**Vital slice**: chain + anchor + verifier's ANCHOR MISMATCH case.
**Cut list**:
- Wiring the merge gate to block on a broken chain
- Anchor rotation / cleanup
- Back-chaining existing trace files

**Assumption to verify before coding**: `permissions.deny` path syntax for a `~`-rooted directory. Cite the source in TASK_REVIEW. Record plainly that `Bash` denial is pattern-based and a determined command (e.g. via a variable) can evade it — the anchor raises the bar, it is not a proof.

---

## Edge Case Checklist

- [ ] Canonical JSON: `sort_keys=True, separators=(",", ":")`, UTF-8 — or hashes differ across runs
- [ ] Trace truncated mid-line (crash) — verifier reports the line, doesn't crash
- [ ] Repo moved / renamed — slug from `git rev-parse --show-toplevel` basename + short hash of the remote URL, documented
- [ ] `fcntl` is POSIX-only — on failure to lock, still append and mark `lock: failed`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_tool_trace.py` | chain fields, anchor append, lock |
| `scripts/verify_trace.py` | new |
| `.claude/hooks/tests/test_trace_chain.py` | new |
| `.claude/settings.json` | `permissions.deny` for the anchor dir |
| `PROJECT_SPEC.md` | glossary row "Anchor" |
| `MANIFEST` | ship the verifier |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | no blocking on chain state in this task |
| `scripts/token_meter.py` | must keep working unmodified (AC5) |
| `.gitignore` | traces stay untracked |

---

## Test Plan

Drive the hook via its real stdin protocol with `CLAUDE_TRACE_ANCHOR_DIR` pointed at a temp dir. SC8 live at Stage 5.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium — mandatory)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T148.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
