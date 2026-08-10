# TASK_REVIEW — T069: Move the Karpathy table into the guaranteed channel

> Sibling of `tasks/TASK_GUIDE_T069.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_agent_guide_dedup.py` — 17 new T069 assertions (AC1 ×4 roles, AC2 ×2, AC5, AC7 ×5, AC9, order-invariant) plus 4 added by the Supervisor at Stage 4 for the P2 fix; `scripts/test-agent-template.sh` AC1 repointed + new AC1b negative. 373 → **394** |
| Verification command run | ☑ pass | Supervisor re-ran all four independently at `f4d6f14`, exit codes captured without a pipe: `pytest .claude/hooks/tests` → **394 passed**, exit 0 · `scripts/test-agent-template.sh` exit 0 · `scripts/validate.sh` exit 0 · `scripts/smoke-install.sh` exit 0 |
| Negative cases hold | ☑ pass | 8 mutation controls, each confirmed applied via `git diff --stat` before its verdict and reverted with `cp`: delete table from `qa.md` → RED naming qa; restore table to template → RED (`t069_ac2`, `ac9`, T066's `ac7`); delete ladder → RED; reword one cell `—`→`-` → RED (AC1 is byte-sensitive); table in neither location → RED on the order-invariant; craft-agent halves ×2 → first pass GREEN, assertion strengthened, both re-run RED. Supervisor's own control: restore the stale startup pointer in `qa.md` → **RED naming qa** (`1 failed, 3 passed`), reverted → 394 passed |
| verify | ☑ pass | Supervisor-run at `f4d6f14`. Independently reproduced, not read from the agent's report: AC1 table byte-identical in all four role guides = True; AC2 gone from template (heading **and** all four operational-command strings) = True; AC7 ladder byte-identical in template and absent from every role guide = True; AC9 pair chars measured through one reader — **pass** |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Scoped to the 9 changed files + the two suites that pin their content (`test_agent_guide_dedup.py`, `test-agent-template.sh`) + `AGENTS.md` as the declared mirror. Repo-wide grep for `Karpathy` limited to finding stale pointers, which is how the P2 was found. `CLAUDE.md` and `docs/claude-md/` deliberately not reviewed — out of scope per the guide, registered as T070 |
| Full smoke suite still green (no regression) | ☑ pass | `scripts/smoke-install.sh` exit 0 at `f4d6f14`; `scripts/validate.sh` exit 0 |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Pure-docs/config task — no UI component; the UI AC section was deleted from the guide at Stage 2 per Hard-Stop Gate 6 |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Pure-docs/config task — no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | Pure-docs/config task — no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-08-10 in worktree `/home/hungnguyenhuu/workspace/pets/wt-t069` at commit
`ad13dc6` — **before any implementation commit existed** (`git log --oneline -1` →
`ad13dc6 docs(T069): Stage 2 guide — move the Karpathy table to the guaranteed channel`).

The Karpathy table's *sole* location, verbatim, `.claude/agents/general-agent-template.md:26-33`:

```
## Karpathy Engineering Principles (Compact)

| Principle | Operational Command |
|---|---|
| Think Before Coding | Ask vs. Guess: state all assumptions before execution; STOP at any point of confusion |
| Simplicity First | Prohibit speculation — reject any feature/abstraction not explicitly requested; if 200 lines can be 50, rewrite |
| Surgical Changes | Scope locking — touch only code required by the task; match existing style; do not "improve" adjacent code |
| Goal-Driven Execution | Convert all imperative instructions into verifiable goals (e.g. "fix the bug" -> "write a failing test, then make it pass") |
```

Grep showing it lives nowhere else in `.claude/agents/`, and is absent from all four role guides —
i.e. it reaches a sub-agent only if that agent chooses to open the template:

```
$ grep -rn "## Karpathy Engineering Principles (Compact)" .claude/agents/
.claude/agents/general-agent-template.md:26:## Karpathy Engineering Principles (Compact)

$ for f in common-infrastructure backend frontend qa; do \
    printf '%s: ' ".claude/agents/$f.md"; \
    grep -cF -e "Ask vs. Guess" -e "Scope locking" ".claude/agents/$f.md"; done
.claude/agents/common-infrastructure.md: 0
.claude/agents/backend.md: 0
.claude/agents/frontend.md: 0
.claude/agents/qa.md: 0
```

The template's own prose asserted the location that this task invalidates —
`general-agent-template.md:14`: ``- Strictly follow all Karpathy Engineering Principles (below — full version with rationale in `CLAUDE.md`, keep both in sync on edit)`` — and
`## Staleness Guard` (line 67-69): "If you edit Base Rules or the Karpathy Engineering Principles
**above**, check `AGENTS.md` …".

**AFTER**: Same greps at `8b5bcb2`. The table is now in the four auto-loaded role guides and
nowhere else; the advisory ladder did not move.

```
$ grep -rn "## Karpathy Engineering Principles (Compact)" .claude/agents/
.claude/agents/frontend.md:29:## Karpathy Engineering Principles (Compact)
.claude/agents/common-infrastructure.md:29:## Karpathy Engineering Principles (Compact)
.claude/agents/qa.md:29:## Karpathy Engineering Principles (Compact)
.claude/agents/backend.md:29:## Karpathy Engineering Principles (Compact)
   (general-agent-template.md: no longer listed)

$ for f in common-infrastructure backend frontend qa; do \
    printf '%s: ' ".claude/agents/$f.md"; \
    grep -cF -e "Ask vs. Guess" -e "Scope locking" ".claude/agents/$f.md"; done
.claude/agents/common-infrastructure.md: 2
.claude/agents/backend.md: 2
.claude/agents/frontend.md: 2
.claude/agents/qa.md: 2

$ grep -rn "## Search Before You Build" .claude/agents/
.claude/agents/general-agent-template.md:28:## Search Before You Build
```

**DELTA**: Every sub-agent now receives the Karpathy Engineering Principles in its auto-loaded
system prompt, which the harness guarantees, instead of one optional read behind a template the
event trace shows was opened 9 times across 66 task buckets.

**AC9 measurement** (chars, `Path.read_text` on both sides — never `git show` bytes against
`read_text` chars, the comparison that manufactured a ~4% saving in T066). Pair = role guide +
template, which is what an agent actually pays. Baseline `8d6d56b`, after `8b5bcb2`:

| role | before | after | delta |
|---|---|---|---|
| c-infra | 9,687 | 9,897 | **+210** |
| backend | 11,786 | 11,996 | **+210** |
| frontend | 11,458 | 11,668 | **+210** |
| qa | 10,583 | 10,793 | **+210** |

**The guide predicted 0 and the real number is +210 — stated as measured, not reframed.** The
table itself is exactly cost-neutral (+622 into each guide, −622 from the template, per-role
components: guide 5,925→6,547 for c-infra, template 3,762→3,350). The residual +210 is the three prose
edits AC6 requires — the header note's verbatim-carry sentence, Base Rules line 14, and the
Staleness Guard — none of which is the table. The claim that survives is the narrower one the
AC9 test asserts: the move did not cost a *copy* of the table (+622 would).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T069.jsonl`, never the
implementing agent alone]

---

## Supervisor Stage 4 record

**code-review — 0 P0 / 0 P1 / 1 P2 (fixed) / 0 P3.**

The P2: all four role guides' startup step 4 still read "Read
`general-agent-template.md` — Base Rules, the Karpathy Engineering Principles, and the
Search-Before-You-Build ladder". As of this task's own change that sentence is false, and it is
**the same defect class T069 exists to fix** — a pointer naming a channel that no longer holds the
content — sitting in the guaranteed channel itself. The guide's Files to Change did predict all
four role guides, but its AC table enumerated only the template's three prose statements: the
recorded "retiring a convention touches more places than the AC table enumerates", repeating.
Fixed at `284592f` after grepping the suite for a pin on the old wording (none), and given its own
assertion plus a mutation control at `f4d6f14`, because a Stage 4 fix ships untested unless someone
writes one.

**security-review — PASS, 0 actionable. Run manually and labelled** (eleventh occurrence of the
built-in diffing the checked-out branch: the work is on `feat/t069-impl` while the Supervisor's
checkout is on the task branch, so the built-in would have diffed the wrong pair and returned a
false PASS on a mandatory gate). Manual scope: every added line across the 9 changed files. The
diff is markdown plus two test harnesses; grep over added lines for
`subprocess|os.system|eval(|exec(|urllib|requests|socket|chmod|rm -rf|curl|wget|shell=True`
returns **0 hits**. No new executable ships — `scripts/test-agent-template.sh` was already
executable and was modified, not created. Its only unquoted expansion is `for path in
$ROLE_GUIDES`, which is deliberate word-splitting over four space-free literal paths defined in the
script itself; every file argument is quoted (`"$ROOT/$path"`), and the script takes no external
input, so there is no injection surface.

**AC9, restated after the P2 fix.** The guide predicted **0 net chars per spawn** and the measured
result is **+258 per role** (was +210 before the P2 fix added two words of prose). Stated as
measured, not reframed: the table move itself is exactly neutral (+622 into each guide, −622 out of
the template), and the entire residual is the prose that AC6 and the P2 fix required. The AC9 test
asserts only `abs(delta) < len(table)` — that the move did not cost a *copy* — rather than
`after <= before`, which would be T065's AC12 again, a scope guard frozen as an invariant that
blocks the next legitimate template edit.

| role | before (`8d6d56b`) | after (`f4d6f14`) | delta |
|---|---|---|---|
| c-infra | 9,687 | 9,945 | +258 |
| backend | 11,786 | 12,044 | +258 |
| frontend | 11,458 | 11,716 | +258 |
| qa | 10,583 | 10,841 | +258 |

**AC8 independently checked**: `AGENTS.md` unchanged and still accurate — it mirrors Base Rules
only and contains no Karpathy content at all (`grep` for `Karpathy`/`Ask vs. Guess`/`Scope locking`
returns nothing), which T051 established deliberately so it would not become a second source of
truth. The agent's claim here was verified, not taken on report.

**WITNESS**: Supervisor, 2026-08-10, from the main checkout at
`/home/hungnguyenhuu/workspace/pets/personal-agentic-claude` against worktree
`/home/hungnguyenhuu/workspace/pets/wt-t069` @ `f4d6f14`. Every number above was re-derived by the
Supervisor's own script, not copied from the implementer's report; the two agree exactly on the
+210 baseline measured before the Stage 4 fix.
