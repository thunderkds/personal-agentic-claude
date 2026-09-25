# TASK_GUIDE — T125: Focused handoff — a spawned agent gets the memory lines its task touches, not the whole index
**Date**: 2026-09-25
**Complexity Level**: C2
**Risk Level**: Medium — changes what context every spawned agent starts with
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` — this task changes how that file reaches agents, so you need all of it
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. **C2**: read `docs/token-focus-finding-2026-09-25.md` § 3, `docs/ddr/0009-measure-token-work-from-transcripts-and-aim-at-focus.md`, and `.claude/hooks/tests/test_memory_channel_and_budget.py`'s docstring (T065: why the channel is a path today)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: *"we have the strategy to send out prompt from agent to agent, so anyway to keep
the agent focus on the request, no overwhelm of content"* — then *"yes, let do the best"*.

**Measured baseline** (finding doc § 3, 14 spawns): a spawned agent reads a median **16.8k tokens
before its first edit**, `memory/MEMORY.md` (41k chars ≈ 12k tokens, a whole-project index) most
often; that reading is **17%** of spawn spend and a third of the context at the first edit.

**History that constrains the fix:**
- T063/T065: "full contents verbatim" in the spawn prompt was a fiction — 0 of 49 spawns carried it;
  agents opened the file themselves. The channel became a **path**, stated honestly.
- T069: a pointer does not guarantee the agent reads it — context does not arrive on its own.
- DDR-0004: trimming the **spawn prompt** saves little (it is already in the Supervisor's cache). This
  task instead removes a **read the agent does itself**, which is new tokens in the agent's context.

**Restated intent:**
> When the Supervisor spawns an agent for a task, the spawn prompt carries the few `MEMORY.md` lines
> that concern that task's files and dependencies — produced by a deterministic command, pasted
> verbatim, and checked at spawn time so it cannot silently go missing — and the agent reads the full
> index only when its work reaches something the slice doesn't cover.

**Out of scope:**
- `PROJECT_SPEC.md`, the TASK_GUIDE and the role guide stay mandatory reads (Permanent Rule).
- Changing `MEMORY.md`'s content, budget or structure; `/compact-memory`.
- Semantic/LLM relevance ranking — matching is deterministic and explainable.
- Supervisor session length (T126); reply style (T127).
- Rewriting existing TASK_GUIDEs; only the template changes.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's messages above and DDR-0009 § Decision 2.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (2026-09-25)
- [x] Domain terms align: *memory slice*, *spawn prompt*, *pre-edit reading*, *hot tier*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T124 — the meter measures this task's baseline and its evaluation window

**Entry point**: `scripts/memory_slice.py` (invoked by `skills/craft-spawn-prompt/SKILL.md` element 4)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | New `scripts/memory_slice.py <guide-path>`, stdlib, read-only. It extracts match keys from the guide: every backticked path in the *Files to Change* and *Files Must NOT Touch* tables (full path and basename), every `T<digits>` on the `**Depends on**` line, and the task's own ID | deterministic |
| 2 | It prints every `MEMORY.md` index line (a `- [` bullet) that contains any key, grouped under its `###` heading, in file order, wrapped in `<!-- memory-slice:Txxx -->` … `<!-- /memory-slice -->`, with a one-line header naming the keys matched and `N of M index lines` | explainable |
| 3 | Caps: at most 30 lines / 4,000 chars; beyond that, the lines with the most key hits win and the output says how many were dropped. Zero matches prints the markers with "no memory lines matched this task's files" | focus |
| 4 | `craft-spawn-prompt` element 4 becomes: run `memory_slice.py` on the guide and paste its output verbatim, then the instruction *"Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover."* The skill's pre-flight (step 4) flags a prompt with no `memory-slice` marker | T069: arrive, don't point |
| 5 | `pre_agent_validate_guide.py` emits a **non-blocking warning** when an `Agent` spawn prompt names a `TASK_GUIDE_Txxx.md` but has no `<!-- memory-slice:` marker. Never blocks | can't silently go missing |
| 6 | The "read `MEMORY.md` yourself" rule is updated consistently in `agents/general-agent-template.md`, `templates/TASK_GUIDE_template.md` (Mandatory Startup step 2), `docs/claude-md/pipeline-stages.md` (Memory injection), `docs/claude-md/memory-write-protocol.md` and the `CLAUDE.md` Memory Write Protocol line — same meaning everywhere: slice in the prompt, full file on need | one rule, no drift |
| 7 | T065's tests stay meaningful: `test_memory_channel_and_budget.py` still forbids claiming the **full** file is injected; any assertion changed is changed only to admit the slice, named with its reason in the TASK_REVIEW. `setup.sh`'s seeded stub (T065 AC8) carries the new rule if it carries the old one | Surgical Changes |
| 8 | Size budgets hold: `test_agent_guide_dedup.py` stays green; if the template line breaches a role's floor, repoint only that role with before/after numbers (T082/T100 practice) | Surgical Changes |
| 9 | **Measured on a live spawn** (Stage 5): one real spawn through the new element 4, measured with `token_meter.py --task`; its pre-edit reading and whether it opened the full `MEMORY.md` are recorded next to the baseline | "ability to test this update" |

**Evaluation window (after Done, recorded in DDR-0009 follow-up — not a Done blocker):** the next ≥ 5
spawns. **Target:** median pre-edit reading ≤ 8.4k tokens (−50% of 16.8k). **Quality guard:** Stage 4
P0+P1 findings per task and `/verify` first-pass rate no worse than the last 10 Done tasks. **Revert
trigger:** target missed, or the guard worsens, or a Stage 4 finding traces to a memory decision the
slice omitted.

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The Supervisor owns the fixture expectations and M1–M5.

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Fixture guide touching `scripts/validate.sh`, depending on `T122`; fixture MEMORY with 3 matching and 20 non-matching bullets | exactly the 3 lines, under their headings, in order, inside markers; header says `3 of 23` | pytest via subprocess |
| 2 | Fixture with 60 matching bullets | ≤ 30 lines, ≤ 4,000 chars, "dropped" count correct, highest-hit lines kept | pytest |
| 3 | Guide with no tables / no matches | markers + "no memory lines matched" | pytest |
| 4 | Real `tasks/TASK_GUIDE_T124.md` against real `memory/MEMORY.md` | runs, exit 0, ≤ caps (content not asserted — it changes) | pytest |
| 5 | Hook: spawn prompt naming a guide, without marker | warning on stderr, allowed; with marker → silent | pytest via the hook's stdin protocol |
| 6 | The five docs in AC6 | each states slice-in-prompt + full-file-on-need; none says "read `memory/MEMORY.md` in full" unconditionally | structural pytest |
| 7 | Script source | never writes | structural pytest |

**Mandatory mutation controls** (RED then reverted-GREEN, both pasted):
- **M1** — match basenames only (drop full paths) → still green? If green, add a fixture where only the full path disambiguates; SC1 must go RED.
- **M2** — remove the cap → SC2 RED.
- **M3** — drop the marker → SC1 and SC5 RED.
- **M4** — make the hook block instead of warn → SC5 RED.
- **M5** — restore "read `memory/MEMORY.md` in full" in the template → SC6 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_memory_slice.py .claude/hooks/tests/test_pre_agent_validate_guide.py .claude/hooks/tests/test_memory_channel_and_budget.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -3
sh scripts/validate.sh
python3 scripts/memory_slice.py tasks/TASK_GUIDE_T125.md
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T125.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T125.md`. BEFORE: element 4's current text verbatim, plus the
> baseline row from the finding doc. AFTER: the new element 4, `memory_slice.py` output for a real
> guide, and AC9's live-spawn measurement.

---

## Approach

**Pattern reference**:
- `.claude/hooks/pre_agent_validate_guide.py` — spawn-time, non-blocking warnings (Depends-on check).
- `scripts/memory_usage_report.py` — read-only script shape.
- `.claude/hooks/lib/guide_sections.py` — if it already parses guide sections/tables, reuse it rather than re-parsing.

**Vital slice**: AC1–4 (the slice reaches the prompt). AC5 is the guarantee it keeps arriving.

**Cut list**:
- Glossary-term matching, fuzzy/semantic matching.
- Slicing `decisions.md`/`learnings.md` (cold tier is already read on demand).
- Auto-inserting the slice from the hook (hooks must not rewrite spawn prompts).

**Design notes (Supervisor):**
- **Paste, don't point** — T069. A pointer to the full file is kept as the escape hatch, not the default.
- **Deterministic keys from the guide's own tables** — the Supervisor wrote those tables at Stage 2; they are the best statement of what the task touches, and anyone can re-run the slice and get the same lines.
- **The risk is omission**, not noise: a relevant decision whose line names no touched file. The escape-hatch instruction and the evaluation window's revert trigger are the mitigation; name it in the TASK_REVIEW.

---

## Edge Case Checklist

- [ ] Guide paths with globs (`tests/fixtures/transcripts/**`) — match the prefix before the glob
- [ ] Very short basenames (`ci.yml`, `SKILL.md`) that match many lines — full path wins; plain `SKILL.md` is too generic, require its directory
- [ ] A bullet matched by several keys appears once
- [ ] `MEMORY.md` missing → markers + "MEMORY.md not found", exit 0 (spawn still proceeds)
- [ ] Bugfix-flavoured guides (Mental Model section) — same tables, same behaviour
- [ ] The `⚠️ Session handoff` section: included only by key match, like any other

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/memory_slice.py` | **New** |
| `tests/test_memory_slice.py` | **New.** SC1–4, SC6–7 |
| `tests/fixtures/memory_slice/**` | **New.** Fixture guide(s) and MEMORY |
| `skills/craft-spawn-prompt/SKILL.md` | Element 4 + pre-flight flag |
| `.claude/hooks/pre_agent_validate_guide.py` | Non-blocking marker warning |
| `.claude/hooks/tests/test_pre_agent_validate_guide.py` | SC5 |
| `agents/general-agent-template.md` | Base-rule sentence |
| `templates/TASK_GUIDE_template.md` | Mandatory Startup step 2 |
| `docs/claude-md/pipeline-stages.md`, `docs/claude-md/memory-write-protocol.md`, `CLAUDE.md` | The one rule, consistently |
| `.claude/hooks/tests/test_memory_channel_and_budget.py` | Only as AC7 requires, with reasons |
| `setup.sh` | Only if its seeded stub carries the old rule (AC7) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/*` | Supervisor-only writes |
| `tasks/TASK_GUIDE_T0*.md`, `tasks/TASK_GUIDE_T1[01]*.md` | Historical guides stay as written |
| `scripts/token_meter.py` | T124's |
| `agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md` | No rule bodies in role guides (T100 test) |

---

## Test Plan

1. `tdd`: SC1–7 first; hand-write fixture expectations.
2. Implement; record full-suite count before/after.
3. M1–M5, RED then GREEN, pasted.
4. Stage 5: AC9 live spawn, measured with `token_meter.py --task`; user-run `/verify`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` — **mandatory (Medium)**; hook input handling in scope
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T125.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M5 mutation controls pasted
- [ ] AC9 live-spawn measurement recorded
- [ ] `/verify` — user-run
- [ ] UI Evidence rows: ☐ N/A — no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
