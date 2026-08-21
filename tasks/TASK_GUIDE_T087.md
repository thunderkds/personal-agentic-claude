# TASK_GUIDE — T087: Extend the landing page to carry the reference content the README now points at
**Date**: 2026-08-21
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: frontend-developer
**Agent guide**: `.claude/agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC_SITE.md` — this task's spec, **not** `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` in full
3. Read this file completely
4. Read `.claude/agents/frontend.md`
5. C2 → read `memory/codebase-map.md`
6. Read `site/index.html` and `tests/test_site_content.py` — you are extending both, not replacing them

---

## Requirement (Pillar 1)

T085 slimmed `README.md` from 477 to 55 lines and told readers the full reference "lives on the
project site". **It does not.** Measured on `feat/t085-readme`:

```
pack              site:0  README:3      Memory System      site:0  README:2
brownfield        site:0  README:0      Codebase Map       site:0  README:0
SUPERVISOR_PATH   site:0  README:0      Repository layout  site:0  README:1
```

Root cause is a Stage 2 planning conflict the Supervisor created, not an implementer error: **T083's
cut list deliberately dropped the pack matrix from the page** ("keep v1 to the four rosters"), while
**T085's cut list assumed the site would carry it**. Both were written by the Supervisor. The user's
decision (2026-08-21) is to close it by extending the site.

**Restated intent**:
> Every reference section the slimmed README promises is on the site is actually on the site, and a
> test fails if that stops being true.

**Out of scope**:
- Editing `README.md` — T085 owns it and is unmerged. If a promise in the README is wrong even after
  this task, report it; do not edit it.
- Redesigning the page. Match the existing structure, palette, and markup patterns exactly.
- Any build step, JS, or external asset. The no-dependency constraint from T083 is unchanged.
- The deployed URL. Still not deployed.

**Requirement Refs**: N/A — traces to the T085 Stage 4 P1 and the user's decision, recorded above.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-21, from the user's explicit choice among three options)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] Requirement Refs recorded N/A with reason

---

## Dependencies & Reachability

**Depends on**: T083 — `site/index.html` exists and is merged into `release/v1-kit-site`.

**Entry point**: `site/index.html` — the deployed document root.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The page gains a **packs** section: the five packs (`mobile`, `data`, `devops`, `ai-agent`, `api`), each with its domain, its agent, and its skills, plus the pack install command. Content comes from `packs/*/PACK.md` and the pre-slim README (recoverable at `git show 78ebfa1:README.md`) | README promises packs |
| 2 | The page gains an **update flow** section: `update.sh`, the hash-lock/per-file-prompt behaviour, and what "untouched" vs "customized" means | README promises the update flow |
| 3 | The page gains an **options** table: `SUPERVISOR_REPO`, `GITHUB_USERNAME`, `SUPERVISOR_PATH`, `--pack=<name>`, `--copy`, each with default and purpose | README promises the Options table |
| 4 | The page gains a **repository layout** section naming the mandatory folders (`.claude/agents/`, `.claude/skills/`, `tasks/`, `templates/`, `packs/`, `memory/`) | README promises repo layout |
| 5 | The page gains a **memory system** section: the two-tier hot/cold split, what each cold file holds, and that writes are Supervisor-only | README promises the memory system |
| 6 | The page covers the **fork install** and **brownfield vs greenfield** install variants | README line 38's promise |
| 7 | `tests/test_site_content.py` gains an assertion that **every reference topic the README claims is on the site is present on the page**, driven by a list in the test — so a future README promise that the page does not honour fails the suite | the whole task |
| 8 | Every T083 assertion still passes unchanged — the 30 skills, 4 agents, 8 hooks, no-project-state, and no-external-asset guarantees are not weakened | T083 regression |
| 9 | Full suite passes, 0 regressions against the 699 baseline | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | The five pack names from `packs/*/` | each appears on the page | automated test |
| 2 | The topic list in AC7 | every topic present on the page | automated test |
| 3 | The page as committed | still zero `src=`/`href=`/CSS-`url()` external references | existing test |
| 4 | The page as committed | still contains no task ID, no "KANBAN", no "In Progress" | existing test |
| 5 | **Mutation control M1** — delete the packs section from the page | the AC7 topic assertion goes **RED** naming `packs`; revert after observing | Supervisor re-runs |
| 6 | **Mutation control M2** — remove one pack directory name (e.g. `devops`) from the page | the AC1 pack assertion goes **RED** naming it; revert after observing | Supervisor re-runs |
| 7 | **Mutation control M3** — add an external `background-image: url(https://x/y.png)` to the page CSS | the existing external-asset test goes **RED**; revert after observing | Supervisor re-runs |

> M1–M3 mandatory. **Confirm each mutation actually changed bytes** (`git diff` or grep the mutated
> string back) before concluding anything from a green result: a no-op mutation and a vacuous
> assertion both produce a green suite and are otherwise indistinguishable. This has now bitten this
> project twice in one session, in both directions — a false P1 on T083 and a real vacuous assertion
> on T085 that a landed mutation exposed.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q && python3 -m pytest .claude/hooks/tests/ tests/ -q
```

> Use the two-path form. `python3 -m pytest tests/ -q` collects 8 tests, not 699 — the harness suite
> lives in the hidden `.claude/hooks/tests/`, which bare pytest skips.

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T087.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `site/index.html`, the new sections | Screenshot at 1280px + LLM-vision description | New sections render in the existing visual language; no clipped or overlapping text; page still reads top-to-bottom in a sensible order |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors | CSS audit | No new hex values — reuse the existing tokens only |
| Typography | declared stack | Unchanged system font stack; no webfont |
| Spacing / layout | declared CSS | New sections reuse the existing section/card/table classes rather than introducing new ones |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (320–480px) | Screenshot | New tables scroll **inside their own container**; page body never scrolls sideways |
| Tablet (768px) | Screenshot | Single column, no clipped cells |
| Desktop (1024px+) | Screenshot | Consistent with the existing sections |

---

## Approach

**Pattern reference**: `site/index.html` itself — the hook table and skill-group cards are the
patterns to imitate for the new tables and grouped lists. Reuse the existing classes.

**Vital slice**: AC1–AC6 content plus AC7's promise-honouring test. The test is what stops this
recurring, and it is the reason this task is not just "paste some sections".

**Cut list**: no per-pack detail pages (one row each); no search; no nav/table-of-contents unless the
page becomes genuinely hard to scan, in which case a simple anchor list at the top is acceptable.

Recover the original content from `git show 78ebfa1:README.md` and from `packs/*/PACK.md` — do not
re-invent the pack descriptions or the Options table from memory. Where the two disagree, `packs/`
and the actual scripts win; note any disagreement in your report.

---

## Edge Case Checklist

- [ ] `SUPERVISOR_PATH` is packs-only and is **not** used by the core install — the pre-slim README says so explicitly. Do not flatten that distinction into "the install path"
- [ ] The pre-slim README documents a `~/.supervisor` persistent clone as still required **for packs only**. That is a real caveat, not stale text — carry it
- [ ] The `curl … | sh --pack=x` form does **not** work (sh parses its own flags first); the pre-slim README explains this at length. Do not silently simplify it into a working-looking one-liner
- [ ] AC7's topic list must not become a copy of the README's wording — assert on topic keywords present on the **page**, or the test just compares the README to itself
- [ ] Adding sections must not introduce a `Txxx`-shaped string (e.g. a task ID in recovered prose) — `test_no_project_state_on_page` will catch it, but check before you paste recovered README text, which is full of them
- [ ] Recovered README prose mentions "KANBAN" in places — same problem, same test

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | New sections per AC1–AC6 |
| `tests/test_site_content.py` | AC7 assertion + pack-name assertion |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `README.md` | T085 owns it and is unmerged |
| `packs/**`, `.claude/**` | Sources of truth this page is tested against |
| `PROJECT_KANBAN*.md`, `memory/**` | Supervisor-only |
| `vercel.json`, `.vercelignore` | T084 owns them |

---

## Test Plan

Extend `tests/test_site_content.py`:
1. `test_every_pack_appears_on_page` — iterate `packs/*/`, assert each name present.
2. `test_readme_promised_topics_are_on_the_page` — a list of topic keywords (packs, update, options, layout, memory, fork, brownfield), each asserted present on the page.
Then the full suite for regressions, then M1–M3 with byte-change confirmation.

---

## Completion Checklist

- [ ] Implementation done
- [ ] New assertions written and observed RED before the content existed
- [ ] M1, M2, M3 each observed RED with the failing assertion pasted — **and the mutation confirmed to have changed bytes** before drawing any conclusion
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: **N/A** — Low risk, no runtime code path
- [ ] Tests pass — output pasted into `tasks/TASK_REVIEW_T087.md` (Gate 5)
- [ ] All three UI/Design evidence rows filled with screenshots (Gate 6)
- [ ] Report any disagreement found between `packs/*/PACK.md`, the scripts, and the pre-slim README
- [ ] Supervisor notified: ready for Stage 4 review
