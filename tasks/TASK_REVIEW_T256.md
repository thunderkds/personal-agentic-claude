# TASK_REVIEW — T256: `self-review` skill

> Sibling of `tasks/TASK_GUIDE_T256.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_self_review_skill.py` (AC 1-8, 8 tests); AC 10: full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `3355 passed, 25 subtests passed in 185.38s`. AC 9 (live run twice) left for the Supervisor at Stage 4 |
| Verification command run | ☑ pass | AC 9 live re-run after fix round 1 (SX-7), from the wt-t256 worktree; test register seeded in the main checkout with watermark `982f07ab` (FR-005: register is user-editable) so the first run fits under the 40-file cap. Run 1 (07:39:27Z): `pre` -> `ready 3e3361962487 982f07ab573c 21 0 [] 0` (register resolved in the main checkout, FX-6); one `Explore`/sonnet miner, 5 patterns; `post` -> `reports/self-review/self-review-20261105T074223.md`, `citations: 25 valid of 25 cited`, `Proposals (3, at most 3)` (copy-pins-break-on-every-text-edit 7 tasks, lane-check-counts-tests-and-symlinks 5, memory-pass-breaks-hot-tier-budget 5), `Beyond the cap (not recorded, not proposed): code-review-misses-defect-auto-verify-finds, auto-mode-stop-check-pauses-on-trace-attribution`. Run 2 (07:42:23Z): `self-review: nothing new since 3e3361962487; no miner call needed`, `nothing-new 0`. Event trace `Agent` records: run 1 window = 1, run 2 window = 0. Test register + report moved to the session scratchpad (`ac9b-artifacts/`), not committed |
| Negative cases hold | ☑ pass | SX tests: `disable-model-invocation: true`; nothing-new stops before any `Agent`; miner failure keeps the watermark; report/miner output untrusted. Live: run 2 nothing-new, 0 Agent records |
| verify | ☑ pass | headless auto verify `stop_auto_verify.py --start T256` at `84d1ee92` (T255 code ships on this stacked branch): log `.claude/verify-runs/T256-84d1ee929c71.log` -> `verdict: pass` (11 steps on a throwaway repo: pre ready, forged quote dropped, guardrail flag, nothing-new on rerun, worktree uses main register, decide errors exit 2). Minor: two `post` runs in the same second overwrite the report; replayed `post` with `--head` = watermark is accepted — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 code-review of `main...feat/t256-self-review-skill` only (15 files + direct callers: `skills/learn/SKILL.md`, skill-list pins). 3 reviewers (maintainability sonnet, correctness opus, adversarial opus). lane_check: EXCEEDS on both guides (15 files, 1334 lines, mostly tests) — warn-only, label C2/C1 kept. 7 P1 + 5 P2 fixed in fix round 1 (`093545e9`, FX-1..12 / SX-1..6); left as suggestions: beyond-cap patterns lost, Kanban archive not read for `fixed`, no pre/post lock, `--report` accepts any path |
| Full smoke suite still green (no regression) | ☑ pass | after fix round 1: `python3 -m pytest -q .claude/hooks/tests/ tests/` -> `3383 passed, 25 subtests passed in 191.64s` (07:35:08Z, `093545e9`); self-review tests re-run by Supervisor: `82 passed in 8.95s` |
| **Companion score (easy-verifier)** | ☑ N/A | easy-verifier not run (Risk Low; optional) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | pure-backend script/skill text, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | pure-backend script/skill text, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | pure-backend script/skill text, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Non-executable change (skill-instruction text) plus the 14 red tests T255 left. Captured 2026-11-05T04:48:45Z, before any T256 implementation commit.

`skills/learn/SKILL.md` Step 8, verbatim (lines 113-121):

```
#### Step 8 — Skill Promotion (Conditional)

Scan all active LRs for pattern overlap (same domain area / recurring behaviour / correction type across ≥2 LRs). If found, surface:

> "Pattern detected across LR-NNNN and LR-MMMM: [shared pattern]. Want me to draft a `learn-[slug]` skill stub that encodes this pattern permanently?"

**On user approval only**: draft a `SKILL.md` stub per `templates/SKILL_template.md`, output it as a fenced markdown code block, and instruct: "Save this as `skills/learn-[slug]/SKILL.md` and register it in AGENTS.md."

**Never write the file automatically** — the promotion step outputs a code block and stops; the Write tool must not be called for the stub. If no overlap, skip silently.
```

`AGENTS.md` cross-cutting line, verbatim:

```
**Stage index** (names only): 0=`brainstorming`,`ideate` | 1=`git-guardrails-claude-code`,`map-codebase`,`settings-setup`,`companion-setup`,`craft-agent` | 2=`grill-with-docs`,`to-issues` | 3=`tdd`,`bugfix`,`diagnose`,`craft-spawn-prompt`,`migration-safety`,`ux-evaluate` | 4=`blast-radius`,`code-review`,`html-report` | 5=`ship`,`delivery-report`. Built-ins (no definition file): `security-review`, `verify`, `run`, `update-config`, `fewer-permission-prompts`. Cross-cutting (any stage, not tied to a single one): `compact-memory` (cold memory files), `compact-advisor` (live conversation health — see Self-monitoring rule above), `dotfiles` (shared agent config, optional), `resolve-question` (a confused Supervisor, or a sub-agent `Status: blocked` + `Question:`).
```

`date -u` 2026-11-05T04:48:45Z; `python3 -m pytest .claude/hooks/tests/ tests/ -q 2>&1 | tail -20` (the last lines of the run; it ends 3 minutes later):

```
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_skill_md_exists[self-review]
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_frontmatter_parses[self-review]
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_name_field_conforms[self-review]
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_description_field_conforms[self-review]
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_skill_md_within_line_budget[self-review]
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_compatibility_field_within_budget[self-review]
FAILED tests/test_agents_md_primary.py::test_ac8_validate_fails_when_agents_md_references_a_missing_path
FAILED tests/test_companion_scoring_skills.py::test_ac1_validate_sh_accepts_the_skill
FAILED tests/test_site_content.py::test_every_skill_dir_appears_on_page
FAILED tests/test_site_content.py::test_skills_heading_count_matches_source
FAILED tests/test_site_content.py::test_quick_reference_counts_match_source
FAILED tests/test_site_content.py::test_skills_section_lists_every_skill_dir_exactly_once_and_nothing_else
FAILED tests/test_site_content.py::test_quick_reference_strip_has_four_cells_whose_numbers_match_source
FAILED tests/test_t245_ux_evaluate.py::test_ac1_validate_sh_accepts_the_skill
14 failed, 3331 passed, 25 subtests passed in 199.31s (0:03:19)
```

**AFTER**: Captured 2026-11-05T05:04:50Z, after the T256 commits.

`skills/learn/SKILL.md` Step 8 gains, after "Never write the file automatically ...":

```
**Kit changes are not proposed here.** This step offers only the project-level `learn-[slug]` stub above. A proposal to change the kit itself (a rule, hook, skill or template of Easy Kit) belongs to `self-review` alone: it mines the Stage 4 review records and the user approves each one. Do not suggest a kit change from `learn`.
```

`AGENTS.md` cross-cutting line now ends: "... `resolve-question` (a confused Supervisor, or a sub-agent `Status: blocked` + `Question:`), `self-review` (started only by the user's `/self-review`: mines new Stage 4 review records for defects that recur and proposes kit changes the user approves)."

New files: `skills/self-review/SKILL.md` (6 steps, one miner spawn), `skills/self-review/references/miner-prompt.md`, `tests/test_self_review_skill.py` (8 tests, AC 1-8).

`python3 -m pytest .claude/hooks/tests/ tests/ -q` (finished 2026-11-05T05:04:50Z):

```
3355 passed, 25 subtests passed in 185.38s (0:03:05)
```

**DELTA**: The user can type `/self-review` to run the script's gate, one Sonnet miner and the approve/reject step, and `learn` no longer proposes kit changes.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
