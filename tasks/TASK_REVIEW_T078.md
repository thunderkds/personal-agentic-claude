# TASK_REVIEW — T078: Agent Skills spec conformance — write it down, then enforce it

> Sibling of `tasks/TASK_GUIDE_T078.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_skill_spec_conformance.py` (new, 190 tests: 6 parametrized checks × 30 skills + 10 discovery/parser unit tests). AC7 → `test_skill_md_exists`, `test_frontmatter_parses`, `test_name_field_conforms`, `test_description_field_conforms`, `test_skill_md_within_line_budget`, `test_compatibility_field_within_budget`. AC8 → `test_ac8_no_hardcoded_skill_list`, `test_discovery_ignores_nested_non_skill_dirs`. AC9 → `test_ac9_discovery_finds_at_least_one_skill`, `test_ac9_discovery_includes_a_known_skill`. SC7 → the line-budget and description tests parametrized on `write-better-skill` itself (174 lines, description 330 chars). |
| Verification command run | ☑ pass | `cd <worktree> && python3 -m pytest .claude/hooks/tests/ -q` at 2026-08-18T11:07:14Z → `641 passed in 8.91s` (451 pre-existing + 190 new). Re-run after the symlink fix: `641 passed in 8.86s`. |
| Negative cases hold | ☑ pass | Four mandatory mutation controls SC3–SC6 all observed, each reverted before the next — full output below. Plus two edge cases from the guide's checklist run ad hoc: a stray `.claude/skills/stray-folder/` with no `SKILL.md` and a broken symlink `.claude/skills/broken-link -> /nonexistent` **both fail loudly** (`broken-link is a directory under .claude/skills/ with no SKILL.md …`, same for `stray-folder`) rather than being skipped. That second case exposed a real defect in the first commit — `os.DirEntry` has no `.exists()`, so a broken symlink raised `AttributeError` at import and the entire conformance module failed to collect. Fixed in `1c039c8`. |
| verify | ☑ pass | **User-run `/verify` at Stage 5, 2026-08-18 — verdict PASS.** Driven at the gate's real surface rather than by re-running the suite (re-running it would only replay the author's own evidence). Six steps against malformed skills created live under `.claude/skills/`: (1) a realistic "skill 31", `My_New_Skill/SKILL.md` with `name: My_New_Skill` — the exact scenario the task exists for → RED, `` My_New_Skill/SKILL.md `name` violates the spec: contains characters outside lowercase a-z, 0-9 and `-` (uppercase is not allowed) ``, `1 failed, 195 passed`; (2) `description` at 1025 chars → RED, `` `description` is 1025 chars, spec max is 1024 `` — boundary exact, not off-by-one; (3) skill dir with no `SKILL.md` → RED, fails loudly by name; (4) **regression check on `1c039c8`** — dangling symlink under `.claude/skills/` → fails loudly, confirmed it no longer crashes collection with `AttributeError`; (5) `name: something-else` in `probe-mismatch/` → RED, `` must match the parent directory name (name='something-else', directory='probe-mismatch') `` — this is the rule the guide's SC3 could not reach, now driven directly; (6) a **valid** new skill → `196 passed`, clean — the gate does not false-FAIL on conforming work. Working tree verified clean after every probe. Two P3 findings raised, neither blocking: a missing `SKILL.md` fans out to 6 FAILED lines (1 actionable + 5 raw `FileNotFoundError`), and the broken-symlink message says "is a directory" for what is a dangling symlink. The `write-better-skill/SKILL.md` half of the diff has no runtime surface — content confirmed consistent with what the test enforces (same five `name` rules, same 1024/500 numbers), but it is agent-facing prose and effectively SKIP; this PASS rests on the gate. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the two files in the guide's *Files to Change* table only — `.claude/skills/write-better-skill/SKILL.md` and the new `test_skill_spec_conformance.py`. Skipped deliberately: the other 29 `SKILL.md` files (guide's *Files Must NOT Touch* — they are the gate's subjects, not its scope; all 30 pass unmodified), `test_memory_channel_and_budget.py` (T075 in flight), `README.md` / `CLAUDE.md` / `memory/MEMORY.md` (T080), `teach/SKILL.md` (T079). `git status` clean at HEAD; no file outside the predicted set was modified. |
| Full smoke suite still green (no regression) | ☑ pass | `641 passed in 8.86s` — the 451 pre-existing tests are all still green; the new module contributes 190. No pre-existing test changed. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Pure-documentation + test task: one Markdown reference file and one pytest module. No rendered surface exists to regress. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI component, no design token consumed. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No viewport; nothing is laid out. |

---

## Mutation Controls (SC3–SC6) — mandatory, each observed and reverted

**SC3 — Control A: malformed skill `.claude/skills/Bad--Name/` with `name: Bad--Name`.**

```
$ mkdir -p '.claude/skills/Bad--Name' && printf -- '---\nname: Bad--Name\n...' > '.claude/skills/Bad--Name/SKILL.md'
$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
E       AssertionError: Bad--Name/SKILL.md `name` violates the spec: contains characters
        outside lowercase a-z, 0-9 and `-` (uppercase is not allowed); must not contain
        consecutive hyphens (`--`)
FAILED .claude/hooks/tests/test_skill_spec_conformance.py::test_name_field_conforms[Bad--Name]
1 failed, 195 passed in 0.11s
```

RED on the uppercase and consecutive-hyphen rules. **Discrepancy noted honestly:** SC3 as written
also expects the *directory-match* violation to be named, but the control it specifies has
`name` == directory name (`Bad--Name`), so that rule is genuinely satisfied and the test correctly
does not report it. Reporting it would have been a false positive. The directory-match rule was
therefore attacked with a second variant in the same directory:

```
$ printf -- '---\nname: some-other-name\n...' > '.claude/skills/Bad--Name/SKILL.md'
$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
E       AssertionError: Bad--Name/SKILL.md `name` violates the spec: must match the parent
        directory name (name='some-other-name', directory='Bad--Name')
1 failed, 195 passed in 0.12s
```

Reverted (`rm -rf '.claude/skills/Bad--Name'`); `git status` clean; `190 passed in 0.10s`.

**SC4 — Control B: pad an existing `SKILL.md` past 500 lines.**

```
$ python3 -c "open('.claude/skills/wake/SKILL.md','a').write(...600 padding lines...)"
$ wc -l .claude/skills/wake/SKILL.md
736 .claude/skills/wake/SKILL.md
$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
E       AssertionError: wake/SKILL.md is 736 lines, spec budget is 500 — move detailed
        reference material into a separate file
E       assert 736 <= 500
1 failed, 189 passed in 0.11s
```

Reverted (`git checkout .claude/skills/wake/SKILL.md`); `git status` clean; `190 passed in 0.10s`.

**SC5 — Control C: point the discovery root at an empty temp directory.**

```
$ mkdir -p /tmp/t078-empty-root
$ sed -i 's|^SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "skills")$|SKILLS_DIR = "/tmp/t078-empty-root"|' \
    .claude/hooks/tests/test_skill_spec_conformance.py
$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
E       AssertionError: discovered zero skill directories under /tmp/t078-empty-root — the
        conformance suite would pass vacuously
E       assert 0 > 0
E        +  where 0 = len([])
E       AssertionError: known skill 'write-better-skill' not among discovered skills [] —
        discovery root /tmp/t078-empty-root is wrong
E       assert 'write-better-skill' in []
2 failed, 8 passed, 6 skipped in 0.05s
```

RED via **both** AC9 guards. Note the `6 skipped` — those are the six parametrized conformance
checks, which over an empty skill list assert nothing at all. That is precisely the vacuous pass
AC9 exists to catch.

Reverted (`git checkout` the test file); `git status` clean; `190 passed in 0.11s`.

**SC6 — Control D: delete AC9's guard assertions, then repeat Control C.**

Not skipped despite SC5 passing: SC5 alone shows the suite went red, not that *the guard* caused it.
Both AC9 tests were removed and AC8's real-root assertions neutralised, so the guard is the only
variable; the discovery root stayed at the empty temp directory.

```
$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
..ssssss......                                                           [100%]
8 passed, 6 skipped in 0.02s
```

**GREEN over zero skills.** With AC9's guard gone the suite reports success while checking not one
skill — confirming the guard is load-bearing and is the single thing standing between this suite and
a vacuous pass. Restored (`git checkout` the test file, `rmdir /tmp/t078-empty-root`); `git status`
clean; full suite `641 passed in 8.91s`.

> Both mutations were run against a **committed** fix (`e3e0b3e`), so the `git checkout` reverts
> could not silently take the implementation with them.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (two halves — this task changes non-executable Markdown AND adds executable test code):

*(a) Non-executable half — verbatim prior content of `.claude/skills/write-better-skill/SKILL.md` at commit `640283a`, before any T078 implementation commit.*

The file is 140 lines and contains these headings only — there is **no** `## Agent Skills Spec Conformance` section, and no line anywhere in the file states any spec constraint (no "64", no "1024", no "500 lines"):

```
$ grep -n '^#\{1,3\} ' .claude/skills/write-better-skill/SKILL.md
6:## Role: Skill Craft Reference
14:## Invocation
23:### Writing the description
33:## Leading Words
48:## Information Hierarchy
64:## Completion Criteria
79:## When to Split
88:## Pruning
100:## Fidelity Gate (Hallucination Check)
114:## Pipeline Integration (This Framework)
134:## Failure Modes
```

The `## Information Hierarchy` section ends its progressive-disclosure paragraph with a vague,
uncheckable claim (verbatim, line 60):

> **Progressive disclosure** is the move down the ladder — out of SKILL.md into a linked file — so the top stays legible. The pointer's *wording* decides how reliably the agent reaches the material.

The Registration checklist (verbatim, lines 126-130) says nothing about the spec's frontmatter rules
beyond folder-name matching:

> Registration checklist for any new skill:
> - [ ] Folder name matches `name:` frontmatter exactly
> - [ ] Added to the custom-skill table in `CLAUDE.md`
> - [ ] One-liner added to `memory/MEMORY.md` hot tier
> - [ ] `description` uses trigger phrasing (model-invoked) or human summary (user-invoked)

*(b) Executable half — the hook suite as it stands before the change, with no conformance test in it.*

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-08-18T11:03:13Z
$ python3 -m pytest .claude/hooks/tests/ -q
[...]
451 passed in 9.35s

$ ls .claude/hooks/tests/ | grep -c skill_spec_conformance
0
```

451 tests pass, and **zero** of them assert anything about `.claude/skills/`: the 30 skills' spec
compliance is entirely untested at this point.


**AFTER**:

*(a) Non-executable half — `.claude/skills/write-better-skill/SKILL.md` now carries a normative
conformance section (new heading at line 33), with every number quoted from
https://agentskills.io/specification rather than paraphrased:*

> ## Agent Skills Spec Conformance
>
> This framework's skills implement the open [Agent Skills specification](https://agentskills.io/specification). The rules below are **normative** — a skill that breaks one is malformed, not merely unpolished. Checked automatically by `.claude/hooks/tests/test_skill_spec_conformance.py` over every directory in `.claude/skills/`.
>
> **`name`** (required):
> - 1–64 characters
> - unicode lowercase alphanumeric (`a-z`, `0-9`) and hyphens (`-`) only — uppercase is invalid
> - must not start or end with a hyphen
> - must not contain consecutive hyphens (`--`)
> - must match the parent directory name
>
> **`description`** (required): non-empty, max 1024 characters. […]
>
> **Progressive-disclosure budgets** (spec numbers, not prose):
> - metadata (`name` + `description`) ≈ **100 tokens**, loaded at startup for **every** skill […]
> - `SKILL.md` body: **≤ 500 lines** and **≤ 5,000 tokens** once the skill activates
> - resources (`scripts/`, `references/`, `assets/`) load **on demand only**

*The vague pointer claim in `## Information Hierarchy` is now checkable (line 89):*

> A **context pointer** must name the *trigger condition* for loading the file, not just its existence: "Read `references/api-errors.md` if the API returns a non-200 status code", never a bare "see `references/` for details". A pointer without a trigger condition is a pointer the agent cannot decide to follow.

*And the Registration checklist gained one line (line 161):*

> - [ ] Frontmatter satisfies *Agent Skills Spec Conformance* above — verified by `python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py`, not by re-deriving the rules

*(b) Executable half — the same command as BEFORE, post-change:*

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-08-18T11:07:14Z
$ python3 -m pytest .claude/hooks/tests/ -q
641 passed in 8.91s

$ python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q
190 passed in 0.11s
```

451 → 641 tests. 190 of them assert the Agent Skills spec over all 30 skill directories, discovered
from the filesystem with no hardcoded name list.

**DELTA**: A skill author can no longer add a 31st skill that violates the Agent Skills spec —
uppercase or double-hyphened `name`, `name` not matching its directory, missing/oversized
`description`, or a `SKILL.md` over 500 lines — without the hook suite going red and naming the
exact rule broken; and the rules themselves are now written down in `write-better-skill` instead of
having to be re-derived from the spec site.

**WITNESS**: Run by the QA-Automation-Agent in worktree `/home/hungnguyenhuu/workspace/pets/wt-t078`
(branch `fix/t078-impl`) on 2026-08-18. Independently attributable from
`memory/event-trace/T078.jsonl`, which records each command above under the `T078` active-task tag —
including the BEFORE capture at `2026-08-18T11:03:13Z` (before commit `60d5c39`), the four mutation
controls between `11:06:35` and `11:07:23`, and the post-fix full-suite run at `11:07:59`. The
Supervisor must still obtain a user-run `/verify` at Stage 5 (verify is user-only in this project).

