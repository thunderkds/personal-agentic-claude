# TASK_REVIEW — T079: Description triggering + the instruction-pattern library

> Sibling of `tasks/TASK_GUIDE_T079.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_skill_reference_pointers.py` — 7 tests (SC3 existence + depth, parametrized over every relative SKILL.md link; SC6 zero-links + known-pointer guards; extractor-exclusion unit test). Guard was observed RED before the reference files existed: `2 failed, 1 passed, 2 skipped` at 2026-08-18T14:46Z. |
| Verification command run | ☑ pass | `$ date -u && python3 -m pytest .claude/hooks/tests/ -q` → `Tue Aug 18 02:48:47 PM UTC 2026` / `648 passed in 9.80s` (641 before this task + 7 new). SC1 (T078 conformance, unmodified) and SC2 (existing suite) both inside that run. |
| Negative cases hold | ☑ pass | **Mutation A** (rename `descriptions.md`→`desc.md`, pointer untouched): `FAILED ...::test_sc3_pointer_target_exists[write-better-skill:31:references/descriptions.md]` — `1 failed, 6 passed`. **Mutation B** (add pointer to `references/deep/nested/x.md`, file created): `FAILED ...::test_sc3_pointer_stays_one_level_deep[...:194:references/deep/nested/x.md] — assert 3 <= 1`, `1 failed, 8 passed` — the existence assertion passed on the same link, so the depth assertion is not vacuous. **Mutation C** (scratch copy, all 6 relative links stripped from every `SKILL.md`): `FAILED ...::test_sc6_extraction_finds_at_least_one_pointer` + `test_sc6_extraction_includes_a_known_pointer` — `2 failed, 1 passed, 2 skipped`; the suite does **not** free-pass on zero links. Each mutation reverted and the suite re-run green (`7 passed`) before the next; implementation was committed (`f24474b`) before mutation-testing began, per the `git checkout` gotcha in `memory/learnings.md`. |
| verify | ☑ pass | **User-run `/verify` at Stage 5, 2026-08-18 — verdict PASS.** Driven at the gate's real surface via a throwaway `.claude/skills/probe-skill/`, not by replaying the suite. Six scenarios: (1) pointer to a nonexistent file → RED naming file, line and resolved path; (2) pointer two levels deep with the target genuinely present → RED on **depth**, not existence, proving the two rules independent; (3) **the taught inline-code form pointing at a missing file → `7 passed`, green** — the P2 below, demonstrated rather than argued; (4) `../other/z.md` → RED twice, non-existence *and* "escapes the skill root"; (5) pointer inside a fenced block → correctly ignored, regression check on `bc42fae`'s fence fix holds; (6) valid pointer to a real file → `9 passed`, no false-FAIL. Working tree verified clean after every probe. **P2 found at verify and fixed before merge**: the gate resolves Markdown links only, but `SKILL.md:91` — the canonical example teaching what a context pointer *is* — was written in inline-code form, so an author following the documented example produced a pointer nothing checked. Steps 1 and 3 are the same broken target with opposite verdicts; the only difference is link syntax. Fixed by rewriting line 91 to require link syntax, name the test that enforces it, and point at this file's own two pointers as the worked examples — deliberately **not** by converting the illustrative `references/api-errors.md` path into a link, which would have made the gate RED on its own documentation. Re-verified after the fix: `648 passed`, extracted pointer inventory unchanged at the 2 real ones, `SKILL.md` 192 lines. Note the prose half of this task (both `references/` files and the `teach` wiring) has no runtime surface — agent-facing text verifiable only by observing a future drafting session; this PASS rests on the gate. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 5 files in the guide's Files-to-Change table. Skipped: the other 29 `SKILL.md` files (retroactive application out of scope) and `test_skill_spec_conformance.py` (T078 owns it, unmodified — confirmed by `git diff main --stat`). |
| Full smoke suite still green (no regression) | ☑ pass | `648 passed in 9.80s`, 0 failures. Line budget (AC11): `write-better-skill/SKILL.md` 140 → 192 lines, under the 500 cap asserted by T078's test; both reference files are one level below the skill root. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure-documentation + test task: two Markdown reference files and one pytest module. No rendered surface, no design tokens, no viewports. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Pure-documentation + test task: two Markdown reference files and one pytest module. No rendered surface, no design tokens, no viewports. |
| **UI: Responsiveness at target viewports** | ☑ N/A | Pure-documentation + test task: two Markdown reference files and one pytest module. No rendered surface, no design tokens, no viewports. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-08-18T14:43:40Z, before any implementation commit on `fix/t079-impl`):

*Markdown half* — verbatim prior content of `.claude/skills/write-better-skill/SKILL.md`, the only
description-craft material the skill carried (lines 23–29). There was no `references/` directory, no
`## Sourcing` section, and no context pointer anywhere in the file:

```markdown
### Writing the description

A model-invoked description does two jobs: state what the skill is, and list the **branches** that trigger it. Every word is context load — prune harder than the body.

- **Front-load the leading word** — the description is where it does its invocation work.
- **One trigger per branch.** Synonyms that rename a single branch are duplication — collapse them.
- **Cut identity already in the body.** Keep triggers plus any "when another skill needs…" reach clause.
```

`.claude/skills/teach/SKILL.md` step 4 "Draft the SKILL.md" likewise reached no reference file — its
description bullet was self-contained:

```markdown
- **description**: trigger phrasing (model-invoked) or human summary (user-invoked); front-load the leading word; one trigger per branch; no identity prose that belongs in the body.
```

*Test half* — the hook suite before this task's change (no `test_skill_reference_pointers.py` exists):

```
$ date -u && python3 -m pytest .claude/hooks/tests/ -q
Tue Aug 18 02:43:40 PM UTC 2026
641 passed in 9.70s

$ ls .claude/hooks/tests/test_skill_reference_pointers.py
ls: cannot access '.claude/hooks/tests/test_skill_reference_pointers.py': No such file or directory
```


**AFTER**:

*Markdown half* — `write-better-skill/SKILL.md` now reaches both new reference files through context
pointers that name their trigger condition (the rule T078's *Agent Skills Spec Conformance* section
states), and carries a `## Sourcing` section:

```markdown
Read [`references/descriptions.md`](references/descriptions.md) when writing or revising a model-invoked `description` — it carries the rules that decide whether the skill fires at all (imperative phrasing, user intent, pushiness) and the trigger-eval method for testing one.

Read [`references/instruction-patterns.md`](references/instruction-patterns.md) when drafting or restructuring a skill *body* — six reusable structures (gotchas, output templates, checklists, validation loops, plan-validate-execute, bundled scripts) and the rules for calibrating how tightly each part instructs.

## Sourcing

**Start from real expertise.** A skill drafted from the model's general training knowledge produces generic filler — "handle errors appropriately", "follow best practices" — instead of the specific conventions, edge cases, and commands that make a skill worth loading. […]
```

`teach` consults both at the matching points of step 4 rather than as a parallel step:

```markdown
- **description**: … Read `write-better-skill/references/descriptions.md` before writing a model-invoked description — it carries the imperative-phrasing, user-intent, and err-on-the-side-of-pushy rules that decide whether the skill fires at all.

Read `write-better-skill/references/instruction-patterns.md` when the body needs more than plain steps — gotchas, an output template, a checklist, a validation loop, plan-validate-execute, or a bundled script — and to calibrate how prescriptive each section should be.
```

And the gotchas entry routes this repo's accumulated failures back into the skills an agent reads:

```markdown
This repo already stores the material: `memory/learnings.md`, and its index in `memory/MEMORY.md`.
When writing a skill that touches a subsystem that file covers, **mine it** — the entries there were
paid for in real incidents.
```

*Test half*:

```
$ date -u && python3 -m pytest .claude/hooks/tests/ -q
Tue Aug 18 02:48:47 PM UTC 2026
648 passed in 9.80s

$ ls .claude/hooks/tests/test_skill_reference_pointers.py
.claude/hooks/tests/test_skill_reference_pointers.py
```

**DELTA**: A skill author (and `teach`, when it drafts) can now reach a written method for making a
`description` actually trigger and a library of six body patterns whose gotchas entry points at
`memory/learnings.md` — and a broken or too-deeply-nested context pointer in any `SKILL.md` now
fails the suite instead of silently dead-ending the agent that follows it.

**WITNESS**: Common-Infrastructure-Agent, 2026-08-18T14:43Z–14:49Z, worktree
`/home/hungnguyenhuu/workspace/pets/wt-t079` (branch `fix/t079-impl`); Bash calls recorded in
`memory/event-trace/T079.jsonl`. Stage 4/5 reviewer to re-run the verification command independently
before Done — a pasted result is a claim until the reviewer reproduces it.
