# TASK_REVIEW — T089: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T089.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-08-21T10:47:53Z, before any implementation commit — worktree at `main` + T087 content):

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-08-21T10:47:53Z

$ grep -c '<nav' site/index.html
0

$ grep -c '^<section' site/index.html
11

$ grep -c '<section id=' site/index.html
0

$ python3 -m pytest .claude/hooks/tests/ tests/ -q
702 passed in 10.20s
```

Structural problem: 11 stacked top-level `<section>` elements, **zero** `<nav>` elements, **zero**
section `id`s — nothing on the page is linkable or navigable; the only way to find anything is to
scroll the whole document. Visual baseline at 1280px: `reports/t089/before-1280.png` — a single
narrow (72ch) content column with the hero card overhanging every section below it (the T086
measure inconsistency), no sidebar, no sense of position or of what else exists.

**AFTER** (same commands, post-change, 2026-08-21):

```
$ grep -c '<nav' site/index.html
1

$ grep -c '^<section id=' site/index.html
11

$ python3 -m pytest tests/test_site_content.py -q
14 passed in 0.03s

$ python3 -m pytest .claude/hooks/tests/ tests/ -q
706 passed in 9.21s          # 702 baseline + 4 new T089 assertions
```

Scroll-spy proof (headless probe that scrolls to `#hooks`, then reads the active link):

```
scrollY=4145 ACTIVE=Hooks -> #hooks
```

Screenshots: `reports/t089/after-{320,375,768,1280}.png`, `after-scrollspy-frame.png`
(sticky sidebar + active "Hooks" link mid-document), `after-375-nojs.png` (script-stripped copy).

**DELTA**: a reader can now see the whole document's structure at once and jump straight to any of
the 11 sections from a persistent grouped sidebar that tracks where they are — instead of scrolling
a ~5,000px unlabelled page — and the sidebar cannot silently rot, because a dead link or an
unreachable section now fails the suite.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
