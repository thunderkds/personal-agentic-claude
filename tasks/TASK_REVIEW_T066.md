# TASK_REVIEW — T066: De-duplicate the startup read set, in the direction the channel allows

> Sibling of `tasks/TASK_GUIDE_T066.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_agent_guide_dedup.py` — 35 tests covering AC1–AC7, AC9, AC10. AC8 is the mutation control, run manually below. Helper `scripts/measure_agent_guide_tokens.py` produces the AC7 numbers |
| Verification command run | ☑ pass | `pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh` → `373 passed in 8.66s` then `smoke-install.sh: PASS`. Re-run from a clean tree after all mutations were reverted (`git status --short` empty) |
| Negative cases hold | ☑ pass | 20 of 35 assertions were RED before implementation. 3 post-implementation mutations, each confirmed applied before the verdict: **(AC8)** delete `## Communication Protocol` from `qa.md` → `Communication Protocol-qa` RED; **(AC6-i)** delete the whole Karpathy table from the template → RED for all 4 roles; **(AC6-ii)** delete *only* the `## Karpathy...` heading, body left intact (`grep -c "Think Before Coding"` = 1) → RED for all 4 roles. All reverted, suite back to 373 |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed manually (labelled manual — no `code-review` skill available to a sub-agent): the 5 `.claude/agents/*.md` files, `.claude/skills/craft-agent/SKILL.md`, and the two new files. Blast radius checked by grepping the whole suite for the vacated paths/strings before deleting — this surfaced `test_memory_channel_and_budget.py:199`, see the escalation note below. Not reviewed: everything outside `.claude/agents/`, since AC5/AC10 pin `CLAUDE.md` and `MANIFEST` byte-identical and the tests enforce it |
| Full smoke suite still green (no regression) | ☑ pass | `373 passed` (338 pre-existing + 35 new), `smoke-install.sh: PASS` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure-documentation task — the only changed files are Markdown agent guides, a skill file, a pytest module and a measurement script. No UI component exists in this repo |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | As above — no rendered surface is produced or changed |
| **UI: Responsiveness at target viewports** | ☑ N/A | As above — no viewport is involved |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: This task changes documentation text, so BEFORE is the **verbatim prior content** of the
sections being moved, plus the per-role token table as it stood at the pre-task branch tip
`8fc4dd2` (the parent of T066's own Stage 2 guide commit — `3bcc919` predates a `/compact-memory`
pass that edited `CLAUDE.md`, so it is not the right baseline for AC5). Captured 2026-08-09, before
the first implementation commit.

*(1) Per-role loaded size at the baseline — `python3 scripts/measure_agent_guide_tokens.py 8fc4dd2`:*

```
# per-role loaded size — 8fc4dd2
template `.claude/agents/general-agent-template.md`: 7,246 chars (~1,811 tok est.)

| role | role guide chars | template chars | total chars | total tok (est.) |
|---|---|---|---|---|
| c-infra | 2,921 | 7,246 | 10,167 | 2,541 |
| backend | 6,682 | 7,246 | 13,928 | 3,482 |
| frontend | 6,335 | 7,246 | 13,581 | 3,395 |
| qa | 5,502 | 7,246 | 12,748 | 3,187 |
```

The c-infra (2,541) and backend (3,482) totals reproduce the TASK_GUIDE's own per-spawn figures
exactly, which confirms `chars / 4` is the estimator the guide used.

*(2) `general-agent-template.md` — the four sections being removed, verbatim prior content:*

```markdown
## Mandatory Startup Sequence (Every Agent, Every Task)

Before writing a single line of code, execute in this order:

1. Read `PROJECT_SPEC.md` — project identity, architecture, constraints, known risks
2. Load the hot-tier memory index — **read `memory/MEMORY.md` yourself**. The spawn prompt gives you its path, not its contents, so nothing loads it for you. Follow its links into cold files only when relevant to your task
3. Read your assigned `tasks/TASK_GUIDE_Txxx.md` — task scope, acceptance criteria, files to touch / not touch
4. Read the relevant guide in `.claude/agents/` for your role — role-specific constraints and patterns
5. **If your task is C2/C3 or touches multiple files**: read `memory/codebase-map.md` (if it exists) for directory layout, entry points, and blast-radius hotspots — do not re-explore the repo if this file answers your structural question

If any of the first four files is missing, **stop and notify the Supervisor before proceeding**. Missing `codebase-map.md` is not a blocker — run `/map-codebase` to generate it if needed.
```

```markdown
## Complexity Levels — How Much Process to Apply

Your `TASK_GUIDE` assigns a **Complexity Level**. Scale your effort to it — this is the primary control for how much process you run. **Risk Level is a separate axis**: it gates `security-review` regardless of complexity (a C0 change to auth code is still High risk).

| Level | Scope signal | Process | Skills | Model |
|---|---|---|---|---|
| **C0** Trivial | 1 file, ~≤10 LOC, no design decision (typo, copy, config flag) | Work inline — no worktree, no brainstorm | `code-review` optional | haiku |
| **C1** Simple | 1–2 files, known pattern, no new abstraction | Single agent | `code-review` always; `verify` if user-facing | sonnet |
| **C2** Moderate | 3+ files, *or* a design choice, *or* a new component | Plan before coding | `brainstorming` when >1 viable approach; `code-review` + `verify` | sonnet / opus |
| **C3** Complex | Cross-cutting, architectural, unknowns, or touches shared/core | Decompose into subtasks; multi-agent | `brainstorming` **mandatory**; `code-review` + adversarial `verify` | opus |

If the task proves harder than its assigned level, **escalate and pause** — notify the Supervisor with the new level rather than powering through. Anything larger than C3 is an **Epic** and must be split by the Supervisor at Stage 2 before pickup.

**Risk axis — hub files.** A change touching a **hub file** (one many others import/call) has a large code-dependency blast radius and should be rated higher Risk, even when the edit is small. This is what `docs/legacy/risk-hotspots.md` captures in legacy mode; in greenfield it's a judgment call. Scope your review and testing to that blast radius — the affected callers/dependents/tests — not the whole repo.
```

```markdown
## Available Skills (Callable by Any Agent)

Trigger thresholds for these skills are set by the Complexity matrix above.

| Skill | Invoke | When |
|---|---|---|
| `brainstorming` | `Skill({ skill: "brainstorming" })` | C2 when >1 viable approach; C3 mandatory |
| `code-review` | `Skill({ skill: "code-review" })` | Before reporting task ready for review (C1+); project override adds P0–P3 severity + confidence anchors |
| `security-review` | `Skill({ skill: "security-review" })` | Task Risk Level is Medium or High (independent of complexity) |
| `verify` | `Skill({ skill: "verify" })` | C1+ if user-facing; adversarial at C3 |
| `run` | `Skill({ skill: "run" })` | Launch the app to observe behavior during development |
| `compound` | `Skill({ skill: "compound" })` | After any non-trivial fix or discovery — document the problem→solution to `docs/solutions/` |
| `optimize` | `Skill({ skill: "optimize" })` | When a concrete measurable metric needs iterative improvement (latency, coverage, quality) |
```

```markdown
## Communication Protocol

- Use concise, structured messages
- Always include Task ID (e.g. T001) when reporting status
- Notify Supervisor immediately when a task is ready for review
- Report format:

```
Agent: [agent name]
Task: T[NNN] — [short title]
Status: [in-progress | ready-for-review | blocked]
Changed files: [list]
Blockers / notes: [any]
```
```

*(3) `common-infrastructure.md` — the two sections it does NOT have (AC2). Verbatim, the file's
entire startup section is four lines and there is no Communication Protocol and no Complexity
guidance anywhere in it:*

```markdown
## Mandatory Startup Sequence

Follow the General Agent Template (`.claude/agents/general-agent-template.md`):
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read assigned `tasks/TASK_GUIDE_Txxx.md`
4. Read this file (`.claude/agents/common-infrastructure.md`)
```

```
$ grep -c "Communication Protocol" .claude/agents/common-infrastructure.md
0
$ grep -ci "complexity" .claude/agents/common-infrastructure.md
1        # a pointer only: "see .claude/agents/general-agent-template.md"
```

*(4) `backend.md` / `frontend.md` / `qa.md` — their Communication Protocol delegates the report
format to the template rather than carrying it:*

```markdown
## Communication Protocol

Use the plain-text report format from the General Agent Template (Agent / Task / Status / Changed
files / Blockers). ...
```

**AFTER**:

*(1) Per-role loaded size after the change — `python3 scripts/measure_agent_guide_tokens.py`:*

```
# per-role loaded size — working tree
template `.claude/agents/general-agent-template.md`: 3,762 chars (~940 tok est.)

| role | role guide chars | template chars | total chars | total tok (est.) |
|---|---|---|---|---|
| c-infra | 5,925 | 3,762 | 9,687 | 2,421 |
| backend | 8,024 | 3,762 | 11,786 | 2,946 |
| frontend | 7,696 | 3,762 | 11,458 | 2,864 |
| qa | 6,821 | 3,762 | 10,583 | 2,645 |
```

**AC7 — measured, per role** (chars; token column is the guide's own `chars / 4` estimate, and it
reproduces the guide's 2,541 / 3,482 figures exactly at the baseline):

| role | before (chars) | after (chars) | delta | before (tok est.) | after (tok est.) | reduction |
|---|---|---|---|---|---|---|
| c-infra | 10,167 | 9,687 | −480 | 2,541 | 2,421 | **4.7%** |
| backend | 13,928 | 11,786 | −2,142 | 3,482 | 2,946 | **15.4%** |
| frontend | 13,581 | 11,458 | −2,123 | 3,395 | 2,864 | **15.6%** |
| qa | 12,748 | 10,583 | −2,165 | 3,187 | 2,645 | **17.0%** |

All four go down, so AC7 holds — but the honest reading is that **the spread is wide and c-infra is
close to a null result at −4.7%**. That is expected and not a defect: c-infra is the one role that
was *missing* two of the four shared sections, so it pays for new content (Complexity, Communication
Protocol, a fuller startup sequence, `code-review`/`security-review` rows) out of the same template
saving the others bank outright. Its guide grows 2,921 → 5,925 chars. The edge-case check the guide
asked for holds: 5,925 alone is well under the 10,167-char pair it replaces.

*(2) `general-agent-template.md` — what remains (7,246 → 3,762 chars). The four moved sections are
gone; Base Rules, the Karpathy table, the Search-Before-You-Build ladder, Output Requirements and the
Staleness Guard stay, and a new lead note states why:*

```markdown
> **What lives where.** The harness auto-loads `.claude/agents/<your-role>.md` as your system
> prompt, so your role guide always reaches you; this file reaches you only if you open it. Anything
> every role needs in its own words — the startup read sequence, the Complexity matrix, the skills
> table, the Communication Protocol — therefore lives in each **role guide**, not here. What remains
> below is the universal material that is stated once, in one place, and referenced from all four.
```

*(3) `common-infrastructure.md` — the two sections it had zero chars of now exist (AC2):*

```
$ grep -c "## Communication Protocol" .claude/agents/common-infrastructure.md
1
$ grep -c "^## Complexity & escalation" .claude/agents/common-infrastructure.md
1
```

```markdown
## Complexity & escalation

Your TASK_GUIDE assigns a **Complexity Level** — scale process to it. **Risk is a separate axis**:
it gates `security-review` regardless of complexity (a C0 change to auth config is still High risk).

| Level | Scope signal | Process |
|---|---|---|
| **C0** Trivial | 1 file, ~≤10 LOC, no design decision (config flag, typo) | work inline, no worktree; `code-review` optional |
| **C1** Simple | 1–2 files, known pattern, no new abstraction | single agent; `code-review` always |
| **C2** Moderate | 3+ files, *or* a design choice, *or* a new component | plan before acting; `brainstorming` when >1 viable approach; `code-review` + `verify` |
| **C3** Complex | cross-cutting, architectural, unknowns, or touches shared/core | decompose into subtasks; `brainstorming` **mandatory**; adversarial `verify` |

A change to a **hub file** (one many others import/call) raises Risk even when the edit is small —
scope review and testing to that blast radius, not the whole repo. If the task proves harder than
its assigned level, **escalate and pause** — notify the Supervisor with the new level rather than
powering through. Anything larger than C3 is an Epic and must be split by the Supervisor at Stage 2.
```

*(4) Startup step 4 no longer points an agent at its own system prompt (AC4). Every role guide now
reads, in place of "Read this file":*

```markdown
4. Read `.claude/agents/general-agent-template.md` — Base Rules, the Karpathy Engineering
   Principles, and the Search-Before-You-Build ladder
```

**DELTA**: Every sub-agent now receives its startup sequence, Complexity matrix, skills table and
Communication Protocol in the one file the harness guarantees to load — most visibly
common-infrastructure, which previously received no Complexity guidance and no Communication
Protocol at all unless it chose to open a second file — while each role's total loaded text drops
between 4.7% and 17.0%.

**WITNESS**: *Left for the reviewer, deliberately.* Every command above was run by the T066
implementing agent (common-infrastructure) in the worktree
`/home/hungnguyenhuu/workspace/pets/pac-t066` on 2026-08-09, with the active-task pointer armed to
`T066` before the first verification command, so the runs should be derivable from
`memory/event-trace/T066.jsonl`. Per the guide, WITNESS must be derived from the trace and never
from the implementing agent alone — typing a name here would launder exactly the claim T054 built
its AC7 to refuse.

> **The `verify` row is left as the untouched template placeholder, on purpose.** `Skill()` is not
> in a sub-agent's toolset (Read/Write/Edit/Bash/Glob/Grep), so the implementer did not and could
> not run the `verify` skill — the Supervisor runs it at Stage 4. Two things were tried and rejected
> before settling on "leave it": writing a verdict would be the fabricated-evidence pattern this
> project has recorded five times, and writing a *prose explanation* into the Notes column turned
> `test_ac6_old_vs_new_pattern_over_real_corpus_differs_only_on_placeholders` (T068) RED — correctly,
> because a row whose Result is still `☐ pass` while its Notes contain the word "pass" is precisely
> the shape T068 taught the merge gate to stop accepting. The explanation lives here instead of in
> the cell. The verification command itself *was* run; see the row above.

---

## Escalation — a pre-existing test that *nearly* contradicted AC3

`.claude/hooks/tests/test_memory_channel_and_budget.py:199` (T065) asserts:

```python
template = _read(".claude/agents/general-agent-template.md")
assert "read `memory/MEMORY.md` yourself" in template
```

That string lived inside the template's **Mandatory Startup Sequence** — the exact section AC3
requires be removed. This is the "a test can pin a section's *location*" family recorded from T064.

**It was resolved without touching the test**, and without weakening either criterion: the sentence
was preserved byte-identical as a **Base Rule**, which is content the template legitimately keeps
(it is not one of the four sections all four role guides carry, so AC3 is satisfied), while T065's
contract — that the template states the real path-not-paste memory channel — stays true. The
startup *sequence* is gone from the template; the *rule* about who reads memory remains, and it is
also now stated in all four role guides.

No existing test was modified. Flagging it because the near-miss is the actionable part: the fix
only existed because the suite was grepped for the vacated section's strings *before* deleting it.
