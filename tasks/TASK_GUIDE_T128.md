# TASK_GUIDE — T128: The token meter sees an agent's first edit even when it edits through Bash
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — read-only analysis script; changes one boundary rule
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `tasks/TASK_REVIEW_T125.md` § "AC9" — the measurement this task corrects

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: approved T128 on the integration branch (*"yes, do it in this branch"*), after the
Supervisor's description: the meter counts Bash file writes, so T125's evaluation window can start.

**Observed defect** (`tasks/TASK_REVIEW_T125.md` § AC9): `scripts/token_meter.py` marks an agent's first
edit only at an `Edit`/`Write`/`MultiEdit` tool call (`EDIT_TOOLS`, line ~114). The T126 spawn (transcript
`4b9912b3…`) read and wrote **only through Bash** (`cat > file <<EOF`, `python3 - <<EOF … open(p,'w')`,
`git commit`), so the meter reported "no edit: whole session is pre-edit" (14.4k tokens) where the real
pre-edit reading was 13.3k (calls 1–5; first write at call 6). In auto mode, Bash editing is common — the
T125 evaluation window compares exactly this number against the 16.8k baseline.

**Restated intent:**
> The meter's "first edit" is the first tool call that changes a file — whether through Edit/Write/MultiEdit
> or a Bash command that clearly writes — so pre-edit reading is measured correctly for Bash-editing agents,
> and the report says which rule found the edit.

**Out of scope:**
- Perfect shell parsing; a Bash write the heuristic misses still falls back to today's behaviour ("no edit").
- Any other meter metric, output format change beyond one field, or the `--current`/session views.
- The T129 startup-reads work.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's approval and the T125 AC9 finding.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-25)
- [x] Domain terms align: *first edit*, *pre-edit reading*, *spawned agent*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T124 — `scripts/token_meter.py` must exist (merged on `tokenization-refactor`)

**Entry point**: `scripts/token_meter.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A `Bash` tool call counts as the first edit when its `command` clearly writes a file: output redirection `>`/`>>` to a path other than `/dev/null` or `&N`; `tee` (not `tee /dev/null`); `sed -i`; `cp`/`mv`/`rm`/`touch`/`mkdir`; `git commit`/`git apply`/`git mv`/`git rm`; `patch`; or an inline interpreter body (`python3 - <<…`, `python3 -c`) containing `open(` with a `"w"`/`"a"`/`"x"` mode or `.write_text(` | defect |
| 2 | Redirections into the harness's own state are **not** edits: `.claude/hooks/.state/`, `/tmp/`, `/dev/`. (Every spawn writes `active_task` first — counting that would put every first edit at call 1) | observed: T126 call 1 |
| 3 | `Edit`/`Write`/`MultiEdit` keep working exactly as today; the first matching call of either kind wins | no regression |
| 4 | Each spawn row gains `edit_via`: `"tool"`, `"bash"` or `null` (no edit found); text output shows it in the no-edit/edit note. JSON docstring updated | explainable |
| 5 | On the real T126 transcript `4b9912b3…`, `--task T126` reports the edit at call 6 (0-based index 5 — match the meter's own convention and say which), `edit_via: "bash"`, pre-edit ≈ 13.3k tokens (± 5%) instead of "no edit" | the measurement this corrects |
| 6 | Aggregates-only holds: the command text is matched in memory, never printed (T124 SC5 sentinel test still green; add the sentinel inside a Bash write command) | T124 AC8 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

All via `subprocess` on synthetic fixtures (T085/T093), built in `tmp_path` or under `tests/fixtures/transcripts/`.

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Spawn fixture: Bash `cat f` (read), then Bash `cat > x.py <<'EOF'` | first edit = the second call; `edit_via` `bash`; pre-edit = first result only | pytest |
| 2 | Same with each write form in AC1 (parametrised) | each detected | pytest |
| 3 | Bash `printf … > /abs/.claude/hooks/.state/active_task`, `echo x > /dev/null`, `cmd 2>&1`, `grep x > /tmp/out` | none counted as an edit | pytest |
| 4 | Read-only look-alikes: `grep '>' f`, `echo "a > b"` inside quotes, `git log`, `python3 -c "print(open('f').read())"` | not an edit | pytest |
| 5 | `Edit` tool first, Bash write later | edit at the Edit call; `edit_via` `tool` | pytest |
| 6 | Sentinel string inside a Bash write command | absent from all output | pytest (extends SC5) |
| 7 | Real transcript (Stage 5) | AC5 numbers | `/verify` |

**Mutation controls:** **M1** — drop the state-path exclusion → SC3 RED. **M2** — treat any `>` as a write (ignore quotes) → SC4 RED. **M3** — Bash detection off → SC1 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_token_meter.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
python3 scripts/token_meter.py --task T126
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T128.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T128.md`. BEFORE: `python3 scripts/token_meter.py --task T126` on
> the branch point → "no edit: whole session is pre-edit". AFTER: same command → edit at call 6, `bash`.

---

## Approach

**Pattern reference**: `scripts/token_meter.py` `Transcript._assistant` (where `EDIT_TOOLS` sets `edit_call`); `.claude/hooks/lib/shell_data.py` — the repo's existing quoted-span / heredoc handling (T095/T099) — reuse it to strip quoted data before matching `>`, rather than writing a new shell parser.

**Vital slice**: AC1–3 + AC5.

**Cut list**: full shell tokenisation; detecting writes inside sourced scripts; per-tool edit counts.

---

## Edge Case Checklist

- [ ] `2>&1`, `&>/dev/null`, `>&2` are not file writes
- [ ] Heredoc *bodies* containing `>` are data (use `shell_data.strip_heredoc_bodies` / `strip_quoted_spans`) — **but** check an interpreter heredoc's body (`python3 - <<EOF … open(p,'w')`) for AC1's write patterns *before* stripping it; stripping first would hide the T126 agent's actual writes
- [ ] `mkdir -p <state dir>` for the active_task file is excluded (AC2)
- [ ] Commands chained with `&&`/`;` — any segment that writes counts

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/token_meter.py` | Bash write detection + `edit_via` |
| `tests/test_token_meter.py` | SC1–6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/shell_data.py` | Reuse only; shared with the merge gate |
| `skills/**`, `CLAUDE.md`, `agents/**` | T129's scope |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: SC1–6 first. 2. Implement. 3. M1–M3 RED/GREEN pasted. 4. Stage 5: AC5 on the real transcript.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Risk Low)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T128.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M3 pasted
- [ ] `/verify` — user-run
- [ ] UI Evidence rows: ☐ N/A — no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
