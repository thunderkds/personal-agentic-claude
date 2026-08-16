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

---

# Brainstorming: compact the Kanban task-history context (2026-08-12)

**Skill**: `Skill({ skill: "brainstorming" })` | **Tier**: Deep
**Trigger**: user request to "refactor the tasks history by compacting the tasks context", after a
measurement pass identified `PROJECT_KANBAN.md` as the largest context artifact in the repo.
**Gate note**: the request contains *refactor*, so Hard-Stop Gate 2 floors any resulting task at
**C2 / Medium Risk**. Not reducible without explicit user instruction.

## The Problem Space

The stated goal is reducing context tokens. The measured baseline:

| Artifact | Chars | ~Tokens | How it enters context |
|---|---:|---:|---|
| `PROJECT_KANBAN.md` | 98,726 | **~24,700** | read in full by `wake`, every session |
| `memory/MEMORY.md` | 49,518 | ~12,400 | read on demand (49,518 / 50,000 budget — 482 chars headroom) |
| `PROJECT_SPEC.md` | 15,550 | ~3,900 | read on demand |
| `CLAUDE.md` | 15,277 | ~3,819 | auto-injected every session |
| skill roster (descriptions) | 10,256 | ~2,564 | auto-injected every session |
| `AGENTS.md` | 595 | ~149 | auto-injected |

Spawn-side, real T061 telemetry across 7 captured spawns shows 97.6–98.4% of every spawn arrives as
`cache_read` (T064 187,906 total / 184,864 cache_read; bare-`echo` probe 15,727 / 15,294), with
`cache_creation` never exceeding 1,016 tokens regardless of payload. This **re-confirms DDR-0004**:
injected content is nearly free, spawn *count* is the lever. Nothing in this brainstorm should be
justified on spawn-payload savings.

### The reframing that decides this session

`PROJECT_KANBAN.md` breaks down by section as:

```
### Done            97,267 ch  ~24,316 tok   98.5%
### Todo               914 ch     ~228 tok    0.9%
### In Progress          3 ch       ~0 tok    0.0%
### Ready for Review     2 ch       ~0 tok    0.0%
## Stage Tracker       259 ch      ~64 tok    0.3%
## Blocked              26 ch       ~6 tok    0.0%
```

And `.claude/skills/wake/SKILL.md:30` instructs: *"Read full file, then filter to rows with status
`In Progress` or `🔄`"*, with line 56 restating *"Emit task ID + title only — no description, no
other columns."*

**So `wake` reads ~24,316 tokens of Done history every session and discards 100% of it.** The Done
section is expensive not because the rows are verbose but because the only token-paying reader
structurally never uses it. The four hooks that also parse the board
(`pre_bash_block_unsafe_merge.py:275`, `stop_review_reminder.py:29`,
`pre_agent_validate_guide.py:40`, `post_write_register_task.py:64`) read the full file too, but they
are Python processes — **their reads cost zero tokens**. Only the LLM-context read is billed.

This is the same shape as T064, where the registered direction (prose→cards) was rejected at Stage 2
because measurement showed the cost lived in reviewer scaffolding, not reasoning prose. Here the cost
lives in the reader, not the file.

### Constraints that are non-negotiable

1. **`CLAUDE.md:23-24` mandates the opposite of compression** — "keep `PROJECT_KANBAN.md` rows …
   fully detailed — those are the audit trail, not conversation, and simplifying them loses real
   information." Any path that shortens rows must amend this rule, or it ships a board that violates
   a standing instruction on the day it merges.
2. **`CLAUDE.md` is pinned byte-identical** by `test_agent_guide_dedup.py:184` (T066 AC5). Amending
   the rule turns that test RED — the T064 "a test pins a location" family. **T070 is already blocked
   on this identical pin**, so any row-editing path collides with an already-registered task.
3. **No row may contain a `###`** — `find_kanban_section`'s lookahead truncates the section there.
   Recorded 6 times in this hook family (T018/T020/T022/T024/T039/T045).
4. **The board is test-covered** — `test_find_kanban_section_on_real_current_board` reads the LIVE
   file; `[x]` must mean Done. A Kanban edit is a code change; re-run pytest after it.

### What is actually at risk if rows are compressed

Verified rather than assumed:

- **The row prose is NOT duplicated in the task's own guide.** Of T069's 38 substantial sentences,
  2 appear in `TASK_GUIDE_T069.md` / `TASK_REVIEW_T069.md`. The board is the unique home of the
  Stage 2/3/4 narrative. (This corrected an incorrect claim the Supervisor made earlier in session.)
- **But 59 of 67 Done tasks are already represented in `memory/`** — `decisions.md` (136,650 ch) +
  `learnings.md` (84,684 ch), both cold-tier and never auto-loaded. Absent: T002, T003, T004, T006,
  T007, T008, T009, T011 — the bootstrap tasks.
- **Every full row is recoverable from git.** 84 commits touch the board; `git log -S'AC9 is a
  predicted-zero'` finds T069 at `bd06cc1`, `-S'TraceCoder'` finds T060 at `88d441e`. So compression
  is a demotion to a colder tier, not destruction. Residual risk is discoverability: recovery
  requires knowing a phrase to search for.

## Alternative Paths

| Option | Name | Summary | Invasiveness | Regression Risk | Saving | Recommended? |
|---|---|---|---|---|---:|---|
| A | Full-board compression | Rewrite all 67 Done rows to a 5-field schema | **High** | Medium | ~23,000 tok | |
| B | Recency split | Compress the older 62, keep the last 5 full | Medium | Medium | ~20,000 tok | |
| C | **Fix the reader** | `wake` reads only the sections it uses | **Very Low** | **Very Low** | ~24,300 tok | ✅ **Yes** |

### Option A — Full-board compression

**Approach**: Rewrite each of the 67 Done rows to the fixed 5-field schema selected by the user
(outcome | Stage 4 defect counts | test count | the one durable lesson | refs to guide/review/memory),
sourced from the existing `memory/` entry where one exists (59 of 67) and template-literal for the 8
bootstrap tasks. Amend `CLAUDE.md:23-24`, repoint the T066 AC5 pin, add a test asserting every Done
row carries all five fields and contains no `###`.

**Pros**: Board becomes readable by a human again. Format returns to what
`templates/PROJECT_KANBAN_template.md` already publishes downstream. Saving is durable — future rows
are born compact.
**Cons**: 67 hand-written summaries; amends a Permanent-Rules-adjacent instruction; collides with
T070 on the AC5 pin; the largest edit ever made to the most parse-fragile file in the repo.
**Why it might fail**: The fidelity risk has no strong oracle. A schema test verifies *shape, not
truth* — a confidently wrong summary passes, which is the vacuous-assertion shape recorded 7 times
here. The repo has two recorded incidents (T061, T068) of a fixture claiming provenance it lacked,
both seeded by whoever wrote the artifact. Compressing 67 rows is 67 chances to repeat that, and the
check would be run by the same party doing the compressing.
**50% version**: template-literal rows only (title | C-level | date), discarding the 5-field schema.
Saves marginally more and removes the fidelity problem entirely — but discards the defect/test/lesson
signal, and still pays every structural cost above.

### Option B — Recency split

**Approach**: Keep the last ~5 Done tasks at full narrative, compress the older 62, rotate on a
cadence.
**Pros**: Preserves the actively-referenced working set at full fidelity; most of the saving.
**Cons**: Introduces an ongoing rotation chore and a judgment call ("when does a row age out?") that
nothing enforces. Inherits every constraint of Option A — `CLAUDE.md` amendment, AC5 pin, fidelity —
while saving less.
**Why it might fail**: An un-enforced periodic chore decays silently. T065 recorded exactly this: a
budget without an in-code rule naming it a ratchet gets relaxed the first time it is inconvenient.
The board would drift back within ~10 tasks and nothing would go red.

### Option C — Fix the reader (recommended)

**Approach**: Change `.claude/skills/wake/SKILL.md` so Step 1 reads only the sections it consumes —
`### Todo`, `### In Progress`, `### Ready for Review` — via a bounded read (`Grep` for the section
headers, or `Read` with `offset`/`limit`), never the full file. The Done section is never pulled into
context. Not one row is touched.

**Pros**: ~24,300 of the ~24,700 tokens recovered — **more than Option A**, because it also drops the
Todo/Blocked/Stage-Tracker bytes that Option A keeps. Zero information loss; the audit trail stays
exactly where CLAUDE.md mandates. **No `CLAUDE.md` amendment**, so **no T066 AC5 collision and no
T070 entanglement**. No fidelity problem, because nothing is summarized. Cost is one edit to one
skill file. It also fixes the cost for every downstream repo, since `wake` ships and instance content
does not — the T065 mechanism-vs-content distinction, applied correctly.
**Cons**: The board keeps growing on disk and stays unreadable to a human scrolling it. Does not
address `wake`'s own truncation problem — the file already exceeds the 25,000-token tool-output cap,
so a naive full read is silently truncated *today* (observed this session).
**Why it might fail**: A skill instruction is not a guarantee — **this is exactly what T065
disproved about `craft-spawn-prompt` element 4**, where the mandate said one thing and practice did
another for 49 spawns. If `wake` is re-run by a future agent that reads the file wholesale anyway,
the saving evaporates with nothing going red. **Mitigation, and it must be an AC**: pair the
instruction with an executable check, so the property is enforced rather than requested. Second
failure mode: a bounded read that mis-locates a section silently returns the wrong rows — the
`find_kanban_section` defect family, now in an LLM-driven reader instead of a regex.
**50% version**: change only the wording at `wake/SKILL.md:30` with no test. Rejected — that is the
instruction-without-enforcement failure named above, and it is the single most repeated lesson in
this repo's memory.

## Adversarial Review — the strongest case against the recommendation

Option C optimizes the measurement, and the measurement was taken during `/wake`. If the Supervisor
or a human opens `PROJECT_KANBAN.md` for any other reason — reviewing history, answering "what did
T060 decide?" — the full 98,726 chars still land in context, and Option C has done nothing. The
honest scope of Option C is therefore *"remove the unconditional per-session cost"*, *not* "make the
board cheap to consult". If board consultation is frequent, A or B recover value C cannot.

Counter-evidence, recorded: `git log -S` and the `memory/` cold tier already serve targeted historical
lookup at a fraction of a full-board read, and 59 of 67 tasks are covered there. So the frequent-
consultation scenario has a cheaper answer than compressing the board.

## Surgical Scope

**Must be touched (Option C)**
- `.claude/skills/wake/SKILL.md` — Step 1 source table (line 30) and Step 3 (line 56)
- `.claude/hooks/tests/` — one new test asserting the enforced property

**Must NOT be touched (Option C)**
- `PROJECT_KANBAN.md` — not one row
- `CLAUDE.md` — no amendment needed; AC5 byte-identity pin stays green; T070 stays independent
- The four board-parsing hooks — their full-file reads are free and correct
- `templates/PROJECT_KANBAN_template.md` — already correct; the live board drifted from it, not the reverse

**Additionally in scope only if A or B is chosen**
- `CLAUDE.md:23-24`, `test_agent_guide_dedup.py:184` (AC5 repoint), and coordination with T070

## Edge Case Checklist for TASK_GUIDE

1. Board with an empty `### Done` section (new downstream repo) — bounded read must not error.
2. Board where `### Done` precedes `### Todo` (section order not guaranteed by the template).
3. A row containing `###` inside its text — the 6-times-recorded truncation defect.
4. `PROJECT_KANBAN.md` missing entirely — `wake`'s existing degradation note must still fire.
5. A task sitting in `Ready for Review` — currently empty, so an untested path in the reader.
6. File exceeding the 25,000-token tool-output cap — already true today; the fix must make this
   unreachable, not merely unlikely.
7. `🔄` status marker used instead of the `In Progress` section (both are honoured by `wake` today).
8. The enforced check must fail RED when the instruction is reverted — mutation-verify from two
   directions, per the 7 recorded vacuous-assertion incidents.

## Decisions locked in this session (carry into Stage 2 if A or B is revived)

- **Destination**: compress in place; git history + `memory/` are the surviving copies.
- **Row schema**: fixed 5 fields — outcome, Stage 4 defect counts, test count, durable lesson, refs.
- **Fidelity rule**: summaries must be traceable to the existing `memory/` entry; the 8 tasks with no
  entry get template-literal rows; Supervisor spot-checks a random sample against `git log -S`
  originals. A summary stating a fact absent from both `memory/` and the original row fails.

## Recommended Path

**Option C**, with the enforcement AC treated as load-bearing rather than optional. It achieves the
user's stated goal more completely than the path selected mid-session, at roughly 2% of the
invasiveness, without amending a standing rule, without colliding with T070, and without creating 67
opportunities to record a fact that was never true.

The three answers given during this session (compress in place / 5-field schema / memory-derived
fidelity) were sound **given the premise that the file's size was the cost**. Measurement showed the
premise was wrong. They are preserved above so that if the board's human readability is independently
worth paying for, Stage 2 can pick them up without re-litigating.

## Next Actions

1. **User selects a path** — C alone, or C now and A/B registered separately as a readability task.
2. If C: register one task, C2/Medium per Gate 2, targeting `wake/SKILL.md` + one enforcing test.
3. Run `Skill({ skill: "grill-with-docs", args: "mode=plan" })` against the selected path.
4. Note independently: `memory/MEMORY.md` sits at 49,518 / 50,000 chars — ~482 chars of headroom.
   The next memory pass trips the gate. Sanctioned response is `/compact-memory`; never raise the
   budget (T065 ratchet rule). Not part of this task.

---
---

# Session: Pareto Focus for downstream feature delivery
**Generated**: 2026-08-16
**Task / Context**: Apply the Pareto principle (80/20) so that repos **installing this kit** deliver
a feature by building the vital 20% of code that carries 80% of the value, and cutting the rest.
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Deep (architectural; changes a standing principle set that propagates to every downstream repo)

> Appended below the 2026-08-05 session, which remains **open** — its Option C was never selected.
> Nothing above this line is modified.

---

## The Problem Space

The user's target is **not** this repo's tidiness. It is the product code written in a repo that has
installed this kit. The operative quote: *"80% of the software's outcomes, value, or performance
overhead stem from a vital 20% of its codebase"* — so at feature-delivery time, identify the vital
20% and **cut** the other 80%, subject to one hard constraint the user stated explicitly: **the
feature must still work correctly.**

Two facts sharpen the problem.

**1. Karpathy already covers part of this, and the user noticed.** `CLAUDE.md`'s Simplicity First
reads: *"Prohibit speculation. Reject any feature or abstraction not explicitly requested. If 200
lines can be 50, rewrite."* That is a **prohibition on the unrequested**. Pareto is a strictly
stronger and different claim: even among what the user **did** request, most of it is not carrying
the value. Simplicity First has no authority to cut a requested feature; Pareto claims exactly that
authority. The overlap is real but partial — this is not a redundant principle, it is an escalation.

**2. The cut has to survive the Acceptance Criteria gate.** The kit's whole enforcement spine runs
through `templates/TASK_GUIDE_template.md`'s AC table (line 67) and Hard-Stop Gate 5 (no tests
covering AC = not done). "The feature must still work correctly" translates, in this kit's own
vocabulary, to: **a Pareto cut may never remove an Acceptance Criterion.** It cuts *implementation
surface* — abstraction layers, configurability, generality, defensive breadth, premature
extensibility — not *acceptance surface*. If the cut is negotiating with the AC table, it has
stopped being Pareto and become descoping, which is the user's call, not the principle's.

### Verified ground truth (claim-verification gate)

| Claim | Verified against | Result |
|---|---|---|
| Kit ships to downstream repos via MANIFEST | `MANIFEST` | `.claude/agents`, `.claude/skills`, `.claude/hooks`, `templates`, `docs/claude-md`, `AGENTS.md` |
| `CLAUDE.md` propagates downstream | `setup.sh:238-241` | Yes — installed as a real copy, **not** via MANIFEST |
| A brownfield fork exists and must be synced | `setup.sh:222-234` | `CLAUDE_LEGACY.md` (629 lines) chosen for brownfield; sync policy is a recorded decision |
| Karpathy principles live in one table | `CLAUDE.md` "Karpathy Engineering Principles" | 4 rows + Task Transformation Table |
| Hard-Stop Gate count | `CLAUDE.md` | **6**, not 8 (an earlier verbal claim of 8 was wrong) |
| Optional-skill precedent exists | `.claude/skills/optimize/SKILL.md` frontmatter | *"Optional skill — invoke only when a concrete metric target exists"* |
| Advisory-field precedent exists | `memory/decisions.md` T046 | `Pattern reference` — one advisory field in the guide, no hook, no gate, no backfill |
| Skills shipped | `ls .claude/skills` | 30 |

---

## The Alternatives

### Option A — Pareto Focus as a 5th mandatory Karpathy principle

Add a 5th row to the principles table in **both** `CLAUDE.md` and `CLAUDE_LEGACY.md`, plus a row in
the Task Transformation Table (*Instead of "Build Feature Y" → "Rank Feature Y's surface by value,
build the vital slice, record what was cut and why, verify the AC still pass."*). Inherited by every
sub-agent through the General Agent Template.

**Pros**
- Maximum reach: principles are the one block `CLAUDE.md` keeps **inline** (T049 deliberately did not
  split them out), so it is in the Supervisor's context every session.
- Sits next to Simplicity First, where the distinction can be stated once and read in context.
- Zero new machinery — no skill, no hook, no gate.

**Cons**
- Principles are load-bearing and currently 4. A 5th dilutes each, and this file has been through a
  565→198-line reduction (T049) precisely because it had grown.
- Mandatory means it fires on C0 typo-fix tasks too, where it is pure ceremony.
- **A mandatory principle authorizing scope cuts is the highest-risk text this kit could ship** — see
  Adversarial Review.

### Option B — An optional `pareto` skill, invoked at Stage 2 before AC lock

New `.claude/skills/pareto/SKILL.md`, following the `optimize` precedent: *"Optional — invoke only
when a feature's implementation surface is large enough that a vital-few ranking changes what gets
built."* Takes the drafted requirement, produces a ranked surface inventory, a proposed vital slice,
and an explicit **Cut List** with a reason per cut, for user approval before the TASK_GUIDE's AC and
Approach sections are written.

**Pros**
- Opt-in matches the user's own instinct (*"it will be the optional steps"*).
- A skill can carry the whole procedure — ranking method, the AC-immunity rule, the Cut List format —
  which a one-row principle cannot.
- The Cut List is the real artifact. A cut that is not written down is indistinguishable from
  forgetting, and six months later nobody can tell which.
- Fits an existing, proven shape (`optimize`, `ideate`, `strategy` are all optional).

**Cons**
- Optional skills are invocation-triggered, and this repo has recorded that *"already covered" must
  mean reaches-the-context* — `tdd` is cited in memory as covering something it never delivers,
  precisely because it is invocation-triggered. An optional Pareto skill will be skipped exactly when
  a task feels small, which is when it is most needed.
- 31st skill. Marginal cost to every downstream repo's roster injection.

### Option C — Sharpen Simplicity First in place + one advisory TASK_GUIDE field (the 50% version)

No new principle, no new skill. Two surgical edits:
1. One sentence appended to Simplicity First's Operational Command, extending it from *reject the
   unrequested* to *rank the requested and build the vital slice first; the AC table is immune*.
2. One advisory field in `templates/TASK_GUIDE_template.md`'s `## Approach` section — **`Vital slice`**
   and **`Cut list`** — mirroring T046's `Pattern reference`: advisory, no hook, no gate, no backfill.

**Pros**
- **This is the 50%-less-code answer.** Roughly two paragraphs and one template field versus a skill
  (~120 lines) or a principle-set change.
- It lands in the **guaranteed channel**: `templates/` ships via `MANIFEST:11` to every downstream
  repo, and the TASK_GUIDE is the one file the implementing agent re-reads every turn. Per the
  repo's own recorded lesson — *dedupe toward the guaranteed channel, not the tidy one* — a field in
  the guide reaches the implementer; a principle in `CLAUDE.md` **structurally does not** (`CLAUDE.md`
  is not in the sub-agent read list; this is a recorded finding, not a guess).
- Resolves the overlap the user identified rather than shipping two principles that argue.
- The Cut List still exists as a durable artifact, in the file where the task's reasoning already lives.

**Cons**
- Advisory fields are ignorable. T046's `Pattern reference` shipped with no measurement of whether it
  is ever filled in, so there is no evidence base for this shape working.
- Editing Simplicity First's text touches a principle pinned by tests elsewhere; Stage 2 must grep the
  suite for byte-pins before assuming the edit is free (this exact hazard is recorded twice — T064's
  location pins and T066's AC5 byte-identity pin on `CLAUDE.md`).

### Option D — Do nothing; Simplicity First already covers it

Recorded for completeness because the user raised it. **Rejected**, but not vacuously: Simplicity
First prohibits the unrequested and says *"if 200 lines can be 50, rewrite"* — a compression rule
applied **after** the surface is chosen. It contains no instruction to rank a requested surface by
value and decline to build part of it. The user's quote is about selection, not compression. The gap
is genuine.

---

## Adversarial Review — "Why this might fail"

**The laundering risk (applies hardest to A, materially to B and C).**
This kit's two active Learning Records are `LR-0001` (*"refactor to clean architecture" was
mis-evaluated as small and the pipeline was bypassed*) and `LR-0002` (*pipeline compliance is not
enforced in practice; it gets bypassed when tasks feel small*). `DDR-0004` then **rejected** a
proposed exemption to Hard-Stop Gate 1 on exactly this ground: the "it felt small" rationale is the
documented drift mechanism in this repo. A principle that says *most of what you were asked to build
is not worth building* is a **ready-made, principle-sanctioned vocabulary for that same drift.** It
does not merely permit the failure mode — it supplies the justification. Any option that ships must
carry an explicit counter-rule: **Pareto cuts implementation surface, never Acceptance Criteria,
never a pipeline stage, never a gate.** Without that sentence, this is a net-negative change.

**The unmeasured-ranking risk (applies to all).**
"The vital 20%" implies a measurement. This repo has **three recorded instrument-validity failures**
(DDR-0001 and DDR-0002 on token cost; T063's *"a naive metric can measure your own process instead of
the thing"*). A vital-few ranking produced by an agent's judgement, with no baseline and no
counterfactual, is a guess wearing a number. Whatever ships must either (a) require the ranking to be
stated as a **claim with a named basis**, or (b) drop the numeric framing entirely and say
*"vital slice"* — 20% is a heuristic, not a target, and writing "20%" invites someone to hit the
number rather than find the value.

**The correctness risk (the user's own constraint, and the sharpest one).**
"Cut, but make sure it works correctly" is only safe because AC are immune. The dangerous cases are
the ones where correctness is not in the AC table: error handling, boundary conditions, concurrency,
and cleanup are exactly the code that *looks* like the low-value 80% (rarely executed, no user asks
for it) and is exactly where correctness lives. **Tell: if the cut list is mostly `try/except`,
validation, and edge-case branches, the ranking is inverted.** Note the AC table's row 3 is already
templated as *"[negative / boundary condition]"* — the template itself anticipates this.

**Option-specific**
- **A fails** if the 5th principle is read as outranking the 4th. Two principles about doing less,
  one of which permits cutting requested work — an agent resolving that conflict picks the permissive
  one.
- **B fails silently.** No invocation, no trace, no record that it was skipped. It will be invoked on
  the C3 tasks that least need it and skipped on the C1 tasks where the 80% actually accumulates.
- **C fails quietly** — two blank fields in every TASK_GUIDE. That is the honest failure mode though:
  visible in every guide, cheap to detect, cheap to reverse.

---

## Risk Matrix

| Risk | A (principle) | B (skill) | C (sharpen + field) |
|---|---|---|---|
| Becomes a bypass justification | **High** | Medium | Low–Medium |
| Reaches the implementing sub-agent | **No** (CLAUDE.md not in agent read set) | Only if invoked | **Yes** (template is guaranteed) |
| Ignored in practice | Low | **High** | Medium |
| Cost to add | Low | Medium | **Lowest** |
| Cost to reverse | Medium (pinned text, 2 files) | Low (delete a dir) | **Low** |
| Collides with existing tests | Yes — byte-pins on `CLAUDE.md` | No | Yes — must grep first |
| Produces a durable Cut List artifact | No | Yes | Yes |

---

## Surgical Scope

**Should be touched (Option C):**
- `CLAUDE.md` — Simplicity First row, Operational Command cell only
- `CLAUDE_LEGACY.md` — same edit (mandatory under the recorded sync policy; brownfield installs get this file instead)
- `templates/TASK_GUIDE_template.md` — `## Approach` section, two advisory fields

**Must NOT be touched:**
- The AC table structure, Hard-Stop Gates, or any of the 5 stages — Pareto has no authority over the
  pipeline itself; that is precisely the failure this design guards against
- The other three Karpathy rows
- `tasks/TASK_GUIDE_T0*.md` — historical record, byte-identical (T064 fallback-not-migration precedent)
- `.claude/hooks/` — no enforcement; advisory by design (T046 precedent)

---

## Edge Case Checklist (for the eventual TASK_GUIDE)

1. A task with a single AC and no meaningful surface — the fields must be legitimately N/A without tripping any gate.
2. A bugfix-flavored guide — does the field belong there at all? (Pareto on a bug fix is close to nonsense; a fix is at a root cause or it is not — T067.)
3. A cut list that names error handling or boundary conditions → inverted ranking; must be called out at Stage 4 review.
4. Byte-pin collision: grep the suite for assertions over the Simplicity First string **before** editing (T064/T066 lesson).
5. `CLAUDE_LEGACY.md` drift — the sync policy has been missed before; verify both files in the same commit.
6. A downstream repo that installed an earlier version — no backfill, fallback only.
7. The word "20%" appearing as a target anyone tries to hit.

---

## Recommended Path

**Option C**, with the AC-immunity sentence treated as load-bearing rather than decorative.

Reasoning: the user's own instinct (*optional, because Karpathy covers it from the start*) is
correct in substance but points at the wrong mechanism. What they want is not a new ceremony — it is
Simplicity First extended from *don't build the unrequested* to *rank the requested*. C makes exactly
that edit, at roughly 2% of the invasiveness of A or B, and it is the only option that puts the
instruction in the channel the implementing agent is **structurally guaranteed** to read. Option A
puts it in a file sub-agents never open; Option B puts it behind an invocation that the kit's own
Learning Records predict will be skipped when tasks feel small.

The single most important line to ship is not the Pareto framing at all — it is the counter-rule:
**the cut applies to implementation surface, never to Acceptance Criteria, never to a pipeline stage
or gate.** Without it, this change hands the repo's documented failure mode a principle to cite.

---

## Next Actions

1. **User selects a path** — C as recommended, or A/B.
2. Run `Skill({ skill: "grill-with-docs", args: "mode=plan" })` against the selected path — this is a
   principle-level change touching a pinned file, so it likely warrants a DDR (2-of-3 gate).
3. Stage 2: register **one** task. Hard-Stop Gate 2 does not apply (not a refactor), but the file is
   pinned by tests, so **C2 / Medium Risk** is the honest floor.
4. Stage 2 pre-flight, mandatory: grep the test suite for byte-pins over `CLAUDE.md` and the
   Simplicity First string before writing the AC table.
5. Unrelated but blocking soon: `memory/MEMORY.md` is at ~49.5k / 50,000 chars. The next memory pass
   trips the ratchet. Sanctioned response is `/compact-memory`; never raise the budget.
6. Still open from the previous session: its Option C (`wake` enforcement) was never selected.
