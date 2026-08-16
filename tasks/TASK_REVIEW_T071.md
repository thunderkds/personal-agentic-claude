# TASK_REVIEW — T071: Vital Slice — extend Simplicity First in the guaranteed channel

> Sibling of `tasks/TASK_GUIDE_T071.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_vital_slice.py` — **new**, 330 lines, 37 tests covering AC1–AC13. `python -m pytest .claude/hooks/tests/test_vital_slice.py -q` → `37 passed in 0.37s`. Written as part of this task, not pre-existing. Also amended: `test_guide_sections.py` (baseline split, AC14) and `test_agent_guide_dedup.py` (one constant repointed) |
| Verification command run | ☑ pass | Re-run by the **reviewer** (Supervisor), not copied from the implementer. `python -m pytest .claude/hooks/tests/ -q` → `442 passed in 9.58s` (exit 0); `bash scripts/test-agent-template.sh` → `test-agent-template: all checks passed` (exit 0). Branch base was `405 passed`; +37 new |
| Negative cases hold | ☑ pass | 7 implementer mutation controls observed RED then restored (SC5 delete AC-immunity → RED; SC6 insert `20%` into `qa.md` → RED; SC7a blank-line padding → RED; SC7b non-blank padding → RED; SC8 duplicate paragraph across guides → RED; AC15a `CLAUDE.md` append → RED; AC15b `common-infrastructure.md` +400 chars → RED). **The reviewer independently re-ran the two that matter most for the baseline split**: mutating `## Approach` (new ref) → RED, mutating `## Edge Case Checklist` (old ref) → RED, restored → GREEN. SC7 was deliberately run both blank and non-blank because T067's P3 was exactly that blindness |
| verify | ☑ pass | `/verify` run by the user 2026-08-16 — **pass**. Driven at the installer surface (this repo is a kit; its runtime surface is `setup.sh` delivering files into a target project, not the suite — T070 precedent). Installed this branch into two fresh `git init` targets via `SUPERVISOR_REPO=<worktree>`: exit 0, 95 file hashes locked. At the target, all four role guides carry vital-slice + cut-list + AC-immunity (1/1/1 each); `grep` for `80/20\|Pareto\| 20%\| 80%` over the four guides and the template → **0**; `grep -c '80/20' CLAUDE.md` → **1**; template fields present at lines 150-151. **Brownfield probed via pty** (`script -qec`, answer `2`) → `CLAUDE source: CLAUDE_LEGACY.md`, rule present, number correctly absent. Probes: idempotent re-install exit 0; `harness-lock.json` covers all 5 agent files; whole-target sweep found the number only in `CLAUDE.md` and the new test. One ⚠️ finding, pre-existing and out of scope: `setup.sh` silently downgrades brownfield→greenfield under a pipe (`[ ! -t 0 ]`), registered as T072 |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Scoped to `git diff b69410c..HEAD` = 16 files + the 3 test modules that pin them. **The built-in `security-review` mis-scoped** — it diffs the checked-out branch vs `origin/HEAD`, pulling in ~70 files of T059–T070 work; 8th recorded occurrence. Re-run manually against the real range and labelled. Conditional reviewers `performance`/`migration`/`api` skipped: no I/O, no schema, no public API in the diff |
| Full smoke suite still green (no regression) | ☑ pass | `442 passed`, 0 failed, exit 0. No pre-existing test was modified to make it pass: `test_agent_guide_dedup.py` changed **one constant** (`T070_BASELINE_REF` → `c512ae9`) and `test_guide_sections.py` gained **one new constant** (`APPROACH_BASELINE_REF = 1b71821`) with `BASELINE_REF` left at `2612a05`. Every assertion body byte-untouched |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure documentation/template task — no UI component, no rendered surface. The guide's UI/Design AC section was deleted at Stage 2 accordingly |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI component — see above |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI component — see above |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-08-16, on `feat/vital-slice-t071-impl` at `b69410c`, before any
implementation commit exists — this task changes documentation and template text, so BEFORE is the
verbatim prior content of every section T071 will change):

1. `.claude/agents/backend.md:48-53` — the section exists, and says nothing about ranking a
   requested surface by value:

   ```
   ## Simplicity First (your defining constraint)

   As the core engineer you set the architectural tone, so over-engineering here costs the whole
   project. Default to the simplest design that satisfies the TASK_GUIDE. **Reject any abstraction not
   required by the requirement or an approved decision (ADR).** Heavier patterns are decision-gated —
   see the appendix; never reach for them speculatively. If 200 lines can be 50, write 50.
   ```

2. `.claude/agents/frontend.md:49-54` — same shape, same silence:

   ```
   ## Simplicity First (your defining constraint)

   Default to the simplest UI that satisfies the TASK_GUIDE. **Reject any abstraction not required by
   the requirement or an approved decision (ADR)** — no premature component libraries, no speculative
   state machines, no design-system scaffolding the task didn't ask for. Reuse before you build. If a
   heavier pattern seems warranted (see appendix), propose it; don't introduce it unilaterally.
   ```

3. `.claude/agents/common-infrastructure.md` — **the section does not exist at all.** Verbatim
   prior state, mechanically established rather than asserted:

   ```
   $ grep -c '^## Simplicity First (your defining constraint)$' .claude/agents/common-infrastructure.md
   0
   $ grep -n '^## ' .claude/agents/common-infrastructure.md
   8:## Role
   12:## Mandatory Startup Sequence
   29:## Karpathy Engineering Principles (Compact)
   38:## Responsibilities
   48:## Constraints (inherits General Agent Template)
   55:## Environment Health Checklist
   68:## Complexity & escalation
   85:## Available skills — scale to the task's Complexity Level
   96:## Communication Protocol
   113:## Output Format
   ```

   The only Simplicity First text this role guide carries is the pinned Karpathy table row at
   line 34, which T071 must not touch.

4. `.claude/agents/qa.md` — **the section does not exist at all**, same as (3):

   ```
   $ grep -c '^## Simplicity First (your defining constraint)$' .claude/agents/qa.md
   0
   $ grep -n '^## ' .claude/agents/qa.md
   13:## Mandatory Startup Sequence
   29:## Karpathy Engineering Principles (Compact)
   38:## The independence rule (why this role exists)
   47:## Your part in the three pillars
   56:## Scope boundaries (who owns what)
   66:## Evaluation checklist (apply what the task needs)
   79:## Complexity & escalation
   95:## Available skills — scale to the task's Complexity Level
   107:## Communication Protocol
   ```

5. `CLAUDE.md:111` — the Simplicity First row, with no heuristic mention anywhere in the file
   (`grep -c '80/20' CLAUDE.md` → `0`):

   ```
   | Simplicity First       | Overcomplication and bloated abstractions  | Prohibit speculation. Reject any feature or abstraction not explicitly requested. If 200 lines can be 50, rewrite. |
   ```

6. `CLAUDE_LEGACY.md:186` — the mirror row:

   ```
   | Simplicity First    | Reject unrequested abstractions. |
   ```

7. `templates/TASK_GUIDE_template.md:143-150` — `## Approach` carries `Pattern reference` and no
   `Vital slice` / `Cut list` field:

   ```
   ## Approach

   **Pattern reference**: [path/to/existing/file.ext — what to imitate about it] or `None — no comparable prior art in this repo` (with a one-line reason)
   > Example: `Pattern reference: .claude/hooks/pre_agent_validate_guide.py — structural ID extraction, fail-open error handling`
   > Point at code that already works and should be imitated. Without one, the agent falls back to
   > generic best practice instead of this repo's conventions (Karpathy: Surgical Changes).

   [Recommended approach from brainstorming skill output, or Supervisor's decision for Low-risk tasks. Include the reasoning.]
   ```

8. Baselines at the same commit — `wc -l`: backend 137, frontend 134, common-infrastructure 129,
   qa 121, `CLAUDE.md` 198, `templates/TASK_GUIDE_template.md` 193 (matches the guide's AC11
   note). Suite at this commit: `405 passed`, `scripts/test-agent-template.sh` exit 0.

**AFTER** (2026-08-16, branch `feat/vital-slice-t071-impl` at `18a9e12`) — the same eight
positions, post-change:

1. `.claude/agents/backend.md` — the section now ranks the requested surface:

   ```
   Then rank what is left: build the **vital slice** the acceptance criteria actually exercise, and
   record what you did not build as a **cut list** — the flag nobody sets, the interface with one
   caller. A cut removes implementation surface, never an Acceptance Criterion, a pipeline stage or a
   Hard-Stop Gate.
   ```

2. `.claude/agents/frontend.md` — same rule, different surface (props/variants/states), no shared
   12-word run with backend (asserted by `test_ac2_no_two_role_guides_share_a_twelve_word_run`).

3. `.claude/agents/common-infrastructure.md` — section **created** where none existed; names the
   role's specific failure (shared services built before a consumer exists to prove the need).

4. `.claude/agents/qa.md` — section **created**; states the inverse duty, that a cut list of
   uncovered error handling, validation and boundary cases "are not a slice, they are a hole".

5. `CLAUDE.md:111` — the Simplicity First row gained the vital-slice rule and the **only** mention
   of `80/20` in the shipping set, labelled "a heuristic for that ranking, never a target".
   `grep -c '80/20' CLAUDE.md` → `1`.

6. `CLAUDE_LEGACY.md:186` — matching row, **same commit** (`c512ae9`), no number.

7. `templates/TASK_GUIDE_template.md` — `## Approach` gained the two advisory fields:

   ```
   **Vital slice**: [the part of this feature's implementation surface carrying most of its value, e.g. `the one happy-path endpoint the AC exercises`] or `None — the whole surface is the slice` (with a one-line reason)
   **Cut list**: [what is deliberately NOT built, one line each, e.g. `pagination (three rows today)`] or `None — nothing was cut`
   > A cut narrows implementation surface only — never an Acceptance Criterion, never a pipeline stage, never a Hard-Stop Gate. Advisory: an unrecorded cut is indistinguishable from an oversight later.
   ```

8. Line counts, all inside their AC11 caps: backend 142/145, frontend 138/142,
   common-infrastructure 135/137, qa 127/129, `CLAUDE.md` 198/200, template 197/197. Suite
   `442 passed` (was 405), `scripts/test-agent-template.sh` exit 0. The negative sweep holds:
   `grep -c '80/20\|80%\|20%\|Pareto'` over all four role guides and the template → `0`.

**DELTA**: An agent implementing a feature in any repo that installs this kit is now told, in the
one file the harness guarantees is in its context, to build the vital slice and record a cut list —
and is told in the same breath that the cut may never reach an Acceptance Criterion, a pipeline
stage or a Hard-Stop Gate; before this task the role guides said only "reject the unrequested" and
had no instruction to rank what *was* requested.

**WITNESS**: Derived from `memory/event-trace/T071.jsonl` — 102 attributed records spanning
2026-08-16T03:33:26Z to 2026-08-16T09:01:11Z (57 `Bash`, 23 `Edit`, 15 `Read`, 2 `Write`, 1
`Agent`), 16 of which reference `pytest`. **Not the implementing agent alone**: the sub-agent
(`common-infrastructure`, opus, 3 sessions totalling ~394k tokens / 117 tool uses) wrote the
implementation and its own 7 mutation controls; the **Supervisor independently re-ran** the full
suite, `scripts/test-agent-template.sh`, and the two baseline-split mutation controls (`## Approach`
→ RED, `## Edge Case Checklist` → RED, restored → GREEN) rather than accepting the reported results.
The sub-agent also halted twice before implementing, on genuine AC conflicts it refused to paper
over; both halts were verified independently before the Supervisor amended the guide.
