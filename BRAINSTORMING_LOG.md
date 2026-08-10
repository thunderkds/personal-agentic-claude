# BRAINSTORMING_LOG.md
**Generated**: 2026-08-05
**Task / Context**: Post-implementation / post-bugfix output validation — a Demonstration block in both TASK_GUIDE flavors, feeding a rendered per-task delivery report
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity, resolved via user Q&A across 4 turns)

> Supersedes the 2026-07-17 token-efficiency log (commit `96539ef`), whose subject was retired
> 2026-08-05 by DDR-0002. Recoverable from git history.

---

## The Problem Space

The user's opening instinct was "we should have a number or checklist to validate the output after
implementation or bugfix." Investigation showed the checklists already exist — and that a count over
them would measure the wrong thing.

**What exists today** (verified against the files, not recalled):

| Flavor | Source | Blocks | Checkable items |
|---|---|---|---|
| Implementation | `templates/TASK_GUIDE_template.md` | Requirement Fidelity Gate (4), Evidence table (9), Completion Checklist (9) | 22 |
| Bugfix | `.claude/skills/bugfix/SKILL.md:92-133` | Diagnosis Gates (4), Attempts Log (table), Stuck checkpoint (3), Fix Gates (4), Cleanup (4), Evidence (3), Step-5 review gate (4) | 22 + 1 conditional table |

**The three real defects, in priority order:**

1. **These are conformance checklists, not demonstration artifacts.** Ticking all 22 proves the
   *process ran*. It shows no reader what the implementation does or what the bug did. Only ~4 of 22
   rows on the implementation path (`New test(s) cover AC` file paths, `Verification command run`
   pasted output, plus the Success Criteria table and Verification Command above the Evidence table)
   and ~3 of 22 on the bugfix path (Attempts Log, repro loop, regression test) carry content a reader
   could not predict before the task began. The remainder is a compliance signature.

2. **The implementation path has no before/after anchor.** The bugfix repro loop is the single place
   in the entire system that demonstrates a *delta* — run it, see it broken; apply the fix; run it,
   see it fixed. The implementation path has no equivalent. `Verification command run` pastes output
   proving the new thing passes, but never establishes the contrast that makes a pass meaningful.
   This is the same failure shape as the recorded gotcha *"An assertion never observed failing is not
   evidence"* (3 vacuous-assertion occurrences: T036/T042/T039) — a pass with no observed RED state is
   indistinguishable from a vacuous one.

3. **The bugfix Evidence table is not wired to the merge gate.** The implementation Evidence table
   carries a row whose Check cell is literally `verify` and whose Notes column
   `pre_bash_block_unsafe_merge.py` greps for the word "pass". The bugfix Evidence table has three
   rows — Repro loop / Regression test / Smoke suite — with a free-text `Result` column, no
   `☐ pass / ☐ fail` shape, and **no `verify` row at all**. The mandated gate is therefore not
   failing on a bugfix; it is structurally absent. Same shape as the recorded gotchas
   *"security-review unrunnable"* and *"'It runs now' is not 'it applies now'"*. The bugfix table also
   lacks negative-cases, blast-radius-scope, and the three UI rows, so Hard-Stop Gates 5 and 6 have
   nothing to bind to on a bugfix task.

**Non-negotiable constraints:**

- Whatever is added must apply to **both** flavors — implementation and bugfix. (Explicit user
  instruction, 2026-08-05.)
- It must not become another row that can be ticked by claim. Recorded precedent: *"Post-/compact
  recovery: a checkmark is a claim, not a fact"*, *"Evidence naming a commit must be re-run, not
  trusted"* (2 false-Evidence occurrences, T035/T039), *"The merge gate's own evidence is a substring
  match"*.
- `html-report` is scoped to Stage 4 *review findings* (code-review / security-review /
  blast-radius) and renders `templates/report_template.html`. A delivery report is a different
  artifact with a different trigger; per the recorded decision *"thinking-report is separate from
  html-report"*, this repo's precedent is a separate skill + separate template, not an overloaded one.

---

## Questions for the User

Resolved during the session:

1. ~~Summary score over existing checks, or genuinely new checks?~~ → Neither alone; the gap is
   demonstration, not counting.
2. ~~Demonstration block (a), rendered report (b), or both (c)?~~ → **(c), with the block feeding the
   report.** Confirmed 2026-08-05.
3. ~~Implementation only, or bugfix too?~~ → **Both.** Confirmed 2026-08-05.

Still open (must be answered at Stage 2, before TASK_GUIDE generation):

1. Should the delivery report be **gate-blocking** (merge refused when the Demonstration block is
   incomplete) or **advisory** (rendered, surfaced, but never blocks)? This decides whether the work
   touches `pre_bash_block_unsafe_merge.py` — which changes the Risk level and pulls in the hook test
   suite. Note the recorded history: this hook family has produced 6 regex/parsing defects
   (T018/T022/T024/T042/T045 + the Kanban `###` truncation).
2. Does the BEFORE state need to be a **pasted terminal capture** (agent-run, timestamped) or is a
   written statement of prior behavior acceptable for C0/C1 tasks?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Simple Path | Demonstration block added to both guides; existing `html-report` gains a `mode=delivery` arg | Low | ~120 lines | Low | |
| B | The Scalable Path | Demonstration block in both guides + new `delivery-report` skill + new template + Evidence parity | Medium | ~400 lines | Medium | ✅ Yes (reduced form) |
| C | The Minimalist Path | Demonstration block only, in both guides; no report, no rendering | Low | ~60 lines | Very Low | |

### Option A — The Simple Path

**Approach**: Add a `## Demonstration` section to `templates/TASK_GUIDE_template.md` and to the guide
skeleton the `bugfix` skill emits (`.claude/skills/bugfix/SKILL.md` Step 3). Extend the existing
`html-report` skill with a `mode=delivery` argument that reads the Demonstration block instead of
Stage 4 findings and fills the same `templates/report_template.html`.

**Pros**:
- Smallest diff; one new template section, one new arg.
- Reuses a template already proven to render (dark-neon theme, `<pre>`-wrapped findings).
- No new skill to register, no MANIFEST change.

**Cons**:
- `report_template.html`'s slots are review-shaped: `{{RISK_SCORE}}`, `{{QUALITY_SCORE}}`,
  `{{EFFORT_SCORE}}`, `{{FINDINGS_ROWS}}`. A delivery report has no risk score and no findings — those
  slots would need dummy values or conditional suppression, which the template does not support.
- Overloads a skill whose description says "from the immediately preceding Stage 4 skill output".
  Directly contradicts the recorded decision *"thinking-report is separate from html-report"*, whose
  stated reason was different templates and different triggers — exactly this situation.

**Why it might fail**: The slot mismatch forces either fake scores (a number that measures nothing —
reintroducing the original problem in rendered form) or template surgery that breaks the existing
Stage 4 reports. The recorded gotcha *"{{RISK_SCORE}} must be bare integer"* shows the template's
slots are load-bearing in both HTML and CSS width attributes; conditional suppression is not the
low-risk edit it appears to be.

### Option B — The Scalable Path

**Approach**: Three coordinated pieces.

1. **`## Demonstration` block** added to both guide flavors, with an identical structure so one
   renderer reads both:

   | Field | Implementation flavor | Bugfix flavor |
   |---|---|---|
   | BEFORE | What did not exist / did not work, with the command that shows it (expect: fail/absent) | The Phase 1 repro loop (expect: bug reproduces) |
   | AFTER | The same command, post-change (expect: pass/present) | The same repro loop (expect: bug gone) |
   | DELTA | One sentence: what a user can now do that they could not before | One sentence: what now behaves correctly |
   | WITNESS | Who ran it and when — Supervisor or QA agent, never the implementing agent alone | same |

   The BEFORE/AFTER pairing is what makes this non-tickable: a RED state must be captured before the
   fix exists, which cannot be back-filled from a finished branch.

2. **New `delivery-report` skill** + **new delivery template**, following the `thinking-report`
   precedent exactly (own skill, own template, own trigger). Renders BEFORE/AFTER side by side, the
   DELTA sentence as the headline, the Evidence table as a supporting grid, and a completion count
   (`filled / total / N-A`) — a count that is now over demonstration content, not conformance
   boilerplate.

3. **Bugfix Evidence-table parity**: extend the bugfix Evidence table from 3 rows to match the
   implementation flavor's gate-visible shape, including the `verify` row the merge gate greps. This
   fixes defect #3 independently of the report.

**Pros**:
- Fixes all three defects, not just the presentation one.
- Applies to both flavors by construction — the shared block structure is what lets one renderer serve
  both.
- Follows this repo's own established precedent for a second report type.
- The count the user originally asked for exists, and now counts something meaningful.

**Cons**:
- Largest surface: 2 guide flavors + 1 new skill + 1 new template + 1 Evidence-table extension + a
  MANIFEST line + possibly the merge-gate hook.
- Should be split into 2–3 tasks at Stage 2 (C2 minimum under Hard-Stop Gate 2 — process-structure work).

**Why it might fail**:
- **The WITNESS field is the weak point.** It is a name and a date — the most claim-shaped field in
  the design, and the exact pattern memory warns about. Mitigation: derive the witness from the
  event trace (`memory/event-trace/<task>.jsonl`) rather than accepting a typed name, now that
  T043/T047/T048 made attribution actually work. Unmitigated, this reintroduces false Evidence in a
  new location.
- **BEFORE is capturable only at the right moment.** An agent that starts implementing and then
  back-fills BEFORE has produced fiction. The block must be filled at spawn time, before code exists —
  which means `craft-spawn-prompt` needs to carry that instruction, or the requirement is silently
  optional.
- **Not every task has a runnable BEFORE.** Documentation tasks, template edits, and this repo's own
  process work (T049, T051, T052) have no command that fails beforehand. Without an explicit,
  justified N/A path, the block becomes noise on a large fraction of this repo's actual tasks — and
  noise gets ticked without reading.
- Touching `pre_bash_block_unsafe_merge.py` enters a hook family with 6 recorded parsing defects.

### Option C — The Minimalist Path

**Approach**: Add the `## Demonstration` block to both guide flavors. Stop there. No skill, no
template, no rendering — the block is read directly in the TASK_GUIDE.

**Pros**:
- Fixes the substantive defect (no before/after anchor) at ~15% of Option B's cost.
- Zero new machinery to maintain; nothing to keep in sync with `report_template.html`.
- Could ship in one C1 task and start producing value immediately, informing whether the report is
  actually wanted.

**Cons**:
- Does not satisfy the user's stated choice (c) — no rendered artifact.
- "Show off the work" means handing someone a link, not a markdown section inside a guide file they
  would have to know how to find.
- Leaves defect #3 (bugfix Evidence table not wired to the merge gate) untouched.

**Why it might fail**: A markdown block inside a TASK_GUIDE has no reader. The guides are read by
agents at spawn time and by the Supervisor at review; nobody opens one to see what shipped. The block
would be correctly filled and never looked at — real work, zero delivered value against the actual
goal.

---

## 50% Rule Check

> **Superseded in part by grilling, 2026-08-05.** The first bullet below was **rejected by the user**
> — see "Grilling Outcome" section at the end of this log. Retained for the reasoning trail.

For the recommended Option B, the same business goal at roughly half the code:

- ~~**Drop the new HTML template; render Markdown instead.**~~ **REJECTED.** Violated the canonical
  `Report` glossary term on format, stage, and content. The artifact's purpose is to be *shown to
  someone*, and a browsable page serves that better than a Markdown file in a gitignored directory.
  Estimate returns from ~180 to ~300 lines.
- **Do not touch the merge-gate hook.** Make the delivery report advisory. Removes the hook change,
  its test-suite updates, and the 6-defect-history risk entirely. **CONFIRMED** — reminder hook +
  spawn-time warning instead; blocking deferred to a follow-up.
- **Do not extend the bugfix Evidence table in the same task.** It is an independent defect with an
  independent fix; splitting it out lets the Demonstration work land without waiting on gate wiring.
  **CONFIRMED.**

Surviving reduction: ~300 lines against Option B's ~400.

---

## Grilling Outcome (`grill-with-docs`, terminology mode — 2026-08-05)

Three questions asked, three decisions locked. Full rationale in `memory/decisions.md`
(2026-08-05 entry).

| # | Question | Resolution |
|---|---|---|
| 1 | `Report` glossary collision — new term, widen, or conform? | **Conform.** HTML, not Markdown. 3 new terms added (`Delivery Report`, `Demonstration`, `BEFORE capture`); `Report` untouched. |
| 2 | Which stage does it fire at? | **Stage 5, after `verify`, before merge.** Rejected Stage 4 (Evidence still being filled) and post-merge (gitignore/worktree trap). |
| 3 | Is it automatic? | **No — nothing here can auto-invoke a skill.** Reminder hook (`stop_review_reminder.py` pattern) + non-blocking blank-BEFORE warning in `pre_agent_validate_guide.py` at spawn. Merge-gate blocking deferred. |
| 4 | What counts as a valid BEFORE, and what if there isn't one? | **Option C — no N/A path.** Pasted capture when the task changes executable code; verbatim prior-content excerpt for non-executable changes (docs/templates/skill text). |

**Grounding for Q4**: of the last four completed tasks, only T050 has a runnable BEFORE. T049, T051,
and T052 are template/skill-instruction edits. On this repo's real task mix the non-executable path is
the *majority*, not an edge case — which is why the `N/A` option was rejected as the escape hatch it
would have become (the three UI Evidence rows are the control experiment already running).

**Known weakness, accepted with eyes open**: a non-executable BEFORE *is* reconstructible from
`git show HEAD~1` after the fact, so for the dominant task type BEFORE degrades from un-forgeable
proof to documentation. Partial mitigations: WITNESS derived from the event trace rather than typed,
and the spawn-time warning fires before code exists — making back-fill *detectable*, not impossible.
No full fix exists inside option C.

---

## Recommended Path

**Option B — The Scalable Path, in its 50%-reduced form.**

Justification: Option C fixes the right defect but produces an artifact nobody opens, which fails the
user's actual goal. Option A collides with `report_template.html`'s review-shaped slots and
contradicts a recorded decision made for precisely this situation. Option B is the only path that
addresses all three verified defects and applies to both flavors by construction.

The reduction matters: rendering Markdown instead of HTML and leaving the merge gate advisory removes
both of Option B's genuinely risky components (template surgery, hook family with 6 recorded parsing
defects) while keeping everything that makes the block non-tickable — the BEFORE state must be
captured before the code exists.

The single most important design property to preserve through Stage 2: **the BEFORE capture is what
makes this different from every checklist row already in the system.** If BEFORE becomes back-fillable,
this is another compliance signature with nicer formatting.

---

## Surgical Scope

Files that **should** be touched:

- `templates/TASK_GUIDE_template.md` — add `## Demonstration` section (implementation flavor)
- `.claude/skills/bugfix/SKILL.md` — add the same block to the Step 3 guide skeleton; extend the
  3-row Evidence table to gate-visible parity (separate task)
- `.claude/skills/craft-spawn-prompt/SKILL.md` — instruct agents to capture BEFORE prior to any
  implementation
- `.claude/skills/delivery-report/SKILL.md` — new
- `MANIFEST` — register the new skill so `setup.sh` / `update.sh` deploy it downstream
- `CLAUDE.md` stage index + `CLAUDE_LEGACY.md` — per the recorded sync policy, mirror new skills and
  bump the version
- `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_T053*.md` … — Stage 2 registration

Files that **must not** be touched:

- `templates/report_template.html` — Stage 4 review reports render from it; its slots are load-bearing
  in both HTML and CSS width attributes
- `.claude/skills/html-report/SKILL.md` — separate trigger, separate artifact, per recorded decision
- `.claude/hooks/pre_bash_block_unsafe_merge.py` — advisory-first decision keeps this out of scope;
  revisit only if the user chooses the blocking variant (open question 1)
- `memory/MEMORY.md` — Supervisor-only writes, and only via the diff-driven pass

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Task has no runnable BEFORE (docs, templates, process work — e.g. T049/T051/T052): explicit
      `N/A` with a written one-line justification, never a blank
- [ ] Agent back-fills BEFORE after implementing — the capture must be timestamped and precede the
      first implementation commit
- [ ] BEFORE command is not deterministic (flaky test, network dependency): must be stated, and the
      loop re-run to confirm reproducibility before it counts
- [ ] Bugfix flavor: Demonstration BEFORE duplicates the existing repro loop row — resolve to one
      source of truth, do not maintain two copies that can disagree
- [ ] WITNESS names the implementing agent as sole witness — violates the guide's own rule that the
      implementer must not be its own sole oracle
- [ ] Delivery report generated for a task whose Evidence table is still blank — report must show the
      gap, not silently omit those rows
- [ ] `reports/` is gitignored except the token-audit exception — confirm whether delivery reports
      need to survive a worktree merge before choosing their path (recorded gotcha:
      *"Worktree-isolated files silently die if gitignored"*)
- [ ] Report filename collision on two tasks completing in the same second — follow the recorded
      `<skill>_<branch>_<YYYYMMDDTHHMMSS>` convention
- [ ] Adding a `## Demonstration` H2 to the template: confirm no hook regex depends on the current
      section ordering (`post_write_register_task.py`, `pre_agent_validate_guide.py`) — 6 recorded
      defects in this family, and the recorded gotcha *"A defect can reproduce itself during its own
      write-up"*

---

## Next Actions

1. Run `Skill({ skill: "grill-with-docs", args: "mode=plan" })` against this log — pending, requested
   by the user in the opening message.
2. Answer the two open questions above (gate-blocking vs advisory; pasted capture vs written
   statement for C0/C1).
3. Assess whether this warrants a **DDR** — it changes a default process artifact for every future
   task, which is the 2-of-3 gate's territory.
4. Stage 2 split, C2 / Medium minimum (Hard-Stop Gate 2 — process-structure work):
   - **T053** — `## Demonstration` block in both guide flavors + `craft-spawn-prompt` BEFORE-capture
     instruction
   - **T054** — `delivery-report` skill (Markdown output) + MANIFEST + CLAUDE.md/CLAUDE_LEGACY.md sync
   - **T055** — bugfix Evidence-table parity with the gate-visible implementation shape (independent
     defect, independently valuable)
5. Verify at Stage 2 that no hook regex depends on TASK_GUIDE section ordering before the template
   edit lands.

---

## User Selection

> **Approved direction**: Option (c) — Demonstration block feeding a rendered report, applied to
> **both** implementation and bugfix flavors.
> Approved by user on 2026-08-05. **Grilling complete 2026-08-05** — see Grilling Outcome above.
> Final form: HTML Delivery Report (Markdown rejected), Stage 5 post-`verify` trigger, reminder hook
> + spawn-time warning (no merge blocking), BEFORE with no N/A path. ~300 lines, split across 3 tasks.

---

# Ideation: harness agent-performance (2026-08-07)

## Scope constraint set by the user

This harness is built to be installed into **other repos**. Past tasks in this repo are a minor
reference at best, not the basis for evaluation — the 58 completed tasks are all harness-building
work in a Python/shell repo and cannot stand in for a downstream web app or data pipeline.

The operative distinction that follows from this:

| Ships downstream (in scope) | Instance-only (out of scope) |
|---|---|
| `CLAUDE.md` (real copy, `setup.sh:238`) | `MEMORY.md` **content** — `setup.sh:344` seeds a fresh stub |
| `.claude/agents/` incl. `general-agent-template.md` | `PROJECT_SPEC.md` — project-specific, from template |
| `.claude/skills/`, `.claude/hooks/`, `templates/` | the 58 past tasks and their outcomes |
| `docs/claude-md/`, `AGENTS.md` | |

**Correction recorded**: the Supervisor initially led with "`MEMORY.md` costs 10,727 tokens per
spawn, 47% reducible". That number is real but instance-only — a fresh install starts near zero. The
harness defect is not the size of this repo's memory, it is that **the growth mechanism ships**: the
200-line cap test lives in `.claude/hooks/tests`, and the Memory Write Protocol that produced
281-char "one-line summaries" (stated rule: ≤150 chars, 86% of 147 entries violate it) lives in
`docs/claude-md/`. The disease travels; the symptom does not.

## Measured baseline (2026-08-07, no new instrument required)

Per-spawn injected constant: `MEMORY.md` ~10,727 tok + `general-agent-template.md` ~1,817 +
role guide ~730 ≈ 13,274. Plus the guide (T059 3,474 / T060 6,836), plus startup reads
(`CLAUDE.md` 3,794 + `PROJECT_SPEC.md` 3,857) ≈ 24,000–28,000 tok before any work begins.

Measured actuals, taken from the `Agent` tool's own return value: **T059 48,401 tokens / 19 tool
uses (~50% orientation overhead); T060 81,220 / 30 (~33%)**. DDR-0001 spent two measurement windows
failing to capture cost-per-task by hand from `/cost`; the harness has been receiving it
automatically per spawn and discarding it.

## Candidates: 38 generated, 7 survived, then re-ranked under the downstream constraint

Rejected on feasibility: relevance-scored injection and semantic retrieval (no ground truth for
"relevant"), a `recall` tool (does not exist), delta-encoded memory (unreadable by humans), harness-
internal prompt-cache ordering, model-pass compression (spends tokens to save tokens), self-tuning
selection and simulated agents (need a corpus far larger than 58 tasks).

Rejected on impact: dropping the guide paste from spawn prompts (re-opens the recorded
worktree-forks-from-main halt), trimming Kanban rows (not injected, costs nothing per spawn),
cutting Supervisor re-verification (trades correctness for tokens — it caught stale Evidence twice
on 2026-08-07 alone).

Rejected on differentiation: deleting guards (guard efficacy is a different topic, explicitly
redirected away from), task sizing (a Stage 2 judgment, not a harness change).

**Demoted by the user**: replay-eval over past tasks — unrepresentative of downstream projects.

## Selected Direction

**Sequential, by priority — not a single pick.** Order and rationale:

1. **Capture per-spawn telemetry** (`subagent_tokens`, `tool_uses` → `event-trace`). Prerequisite:
   every other candidate is unfalsifiable without it. Ships in `.claude/hooks`, language-agnostic,
   gives each downstream repo its own baseline. Cannot fail as DDR-0001/0002 did — no human in the
   loop. **Open question for brainstorming: does DDR-0002's "retire, don't re-instrument" ruling bar
   this, or did it bar only manual `/cost` logging?**
2. **Prove memory is actually used** — answerable only after (1); gates whether (3) and (4) are
   worth doing at all.
3. **Guide format refactor** — biggest per-task variable; `TASK_GUIDE_template.md` ships.
4. **Injection cap measures chars, not lines** — cheap and ships, but payoff is deferred.
5. **Spawn threshold for C0/C1** — potentially the largest win (eliminates overhead for a task class
   rather than reducing it), held back only because it collides with Hard-Stop Gate 1, which is a
   Permanent Rule and a user decision. **May deserve promotion once (1) produces numbers.**
6. **De-dupe the startup read set** — last; T039 already harvested most of it, and some overlap is
   deliberate cross-context redundancy.

## Investigation outcome (2026-08-07, temporary probe, reverted)

A probe was registered on `PostToolUse`/`Agent`, three spawns were run, and it was removed. Two
hypotheses, one rejected:

- **H1 — the PostToolUse Agent payload carries structured cost fields.** **CONFIRMED.**
  `tool_response` holds `totalTokens`, `totalToolUseCount`, `totalDurationMs`, `resolvedModel`,
  `agentType`, `status`, a full `usage` breakdown, and `toolStats` incl. `linesAdded`/`linesRemoved`.
- **H2 — unique per-task content is paid at `cache_creation` rates, stable injected content is
  served as `cache_read`.** **REJECTED.**

| arm | unique prompt | total | cache_read | cache_creation | output |
|---|---|---|---|---|---|
| A | 29 tok | 15,669 | 15,259 | 405 | 3 |
| B | 1,144 tok | 16,981 | 16,572 | 404 | 3 |

Arm B added 1,115 tokens of novel prompt text and moved `cache_creation` by **−1**. The unique
content landed in `cache_read` like everything else, because the spawn prompt is already inside the
Supervisor's cached context before the agent starts.

**Consequences, which reorder the priority list above:**

1. Token-volume optimization is worth roughly **a tenth** of its nominal figure — nearly everything
   injected is billed as a cache read. Items 3, 4 and 6 are all worth about 10% of what the raw
   counts advertise.
2. The guide-vs-memory inversion stated after the first probe (n=1) is **withdrawn**. Guides are not
   expensive because they are unique; they are cached too.
3. The dominant lever is **spawn count**, not spawn content. Every spawn costs ~15.7k tokens before
   doing any work (arm A: 15,669 for a single `echo`), against 48,401 for T059's real three-line fix
   and 81,220 for T060. **Item 5 is therefore promoted from last to first on evidence** — the
   promotion flagged as possible when the order was written.
4. All of the above rests on **n=3 synthetic spawns** and is not established. This is exactly why
   item 1 ships first regardless of the reordering: standing capture over dozens of real spawns is
   what the next decision should rest on.

**Three corrections the Supervisor made to its own framing during this investigation**, recorded so
the reasoning is auditable rather than looking like it arrived clean: (a) the opening
"`MEMORY.md` costs 10,727 tok/spawn, 47% reducible" figure is instance-only and does not ship
downstream; (b) cache dominance means volume is not cost; (c) H2's inversion was wrong.

## Revised order

1. **T061 — capture per-spawn telemetry** (registered, Stage 2 planned 2026-08-07). Unchanged as
   first build: everything else now depends on real numbers.
2. **Spawn threshold for C0/C1** — promoted from 5th. Blocked on a user decision about Hard-Stop
   Gate 1, and on T061's data.
3. **Prove memory is actually used** — unchanged.
4. **Guide format refactor** — demoted; worth ~10% of nominal.
5. **Injection cap measures chars not lines** — demoted; same reason.
6. **De-dupe the startup read set** — unchanged, last.

Next: Stage 3 on T061.
