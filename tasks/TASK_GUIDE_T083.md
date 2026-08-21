# TASK_GUIDE — T083: Static landing page for the kit (`site/index.html`)
**Date**: 2026-08-21
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: frontend-developer
**Agent guide**: `.claude/agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md` (**this task's spec — not `PROJECT_SPEC.md`**, which governs the harness scope)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/frontend.md`
5. C2 → apply the C2 row of the Complexity matrix in your role guide
6. C2 → read `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User request, verbatim:

> "due to the README is too much information at current, we need to simplify it and publish the
> guide, information, or something related to the webpage, I think using vercel to deploy a static
> page will be good to go. This is the release for version 1 of this kit"

and, on scope:

> "I don't want sync the KANBAN, I mean the page just show the purpose, the information, the list
> of agents, list of skills, list of hooks, guide to install..."

**Restated intent**:
> One public page a stranger can read top-to-bottom and come away knowing what the kit is, what
> agents/skills/hooks it ships, and how to install it — with the rosters guaranteed accurate by a
> test rather than by care.

**Out of scope** (explicit non-goals, not deferrals):
- Any project/task state on the page: no KANBAN, no task IDs, no In Progress, no memory contents. The user ruled this out directly.
- Search, client-side routing, JS framework, build step, `package.json`, npm dependency of any kind.
- Per-skill or per-agent detail pages. One line each, one page total.
- Analytics, cookies, forms, external asset hosts (no CDN, no Google Fonts — system font stack only).
- The Vercel config and the deploy itself — that is T084.
- Editing `README.md` — that is T085. **Do not touch `README.md` in this task.**

**Requirement Refs**: none — this task predates `PRD.md` coverage of the site scope; it traces to the
user request quoted above, which `PROJECT_SPEC_SITE.md` records as the governing statement.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-08-21; user answered three scoping questions and said "go")
- [x] Domain terms align with the `PROJECT_SPEC_SITE.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: recorded as N/A with reason above, not left blank

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `site/index.html` — the deployed document root; T084's `vercel.json` will name this exact path.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `site/index.html` exists and is a complete standalone HTML document that renders with **zero network requests** — no `<script src>`, no `<link href>` to any external origin, no remote `<img>`. CSS is inline in a `<style>` block or a same-directory `.css` file. | "static page", non-goals |
| 2 | The page names all **4 spawnable agent roles** (`common-infrastructure`, `backend-developer`, `frontend-developer`, `qa-expert`), each with its `subagent_type` and a one-line purpose. `general-agent-template` is shown separately and explicitly labelled **not directly spawnable** (it is a shared base, per CLAUDE.md). | "list of agents" |
| 3 | The page names **every** directory under `.claude/skills/` (30 at time of writing), one line each, grouped by pipeline stage. | "list of skills" |
| 4 | The page carries a hook table listing **every** hook wired in `.claude/settings.json`, and for each: its event (PreToolUse/PostToolUse/Stop), its matcher, and whether it **blocks** or only **advises**. | "list of hooks" |
| 5 | Hook facts are taken from each hook's own source, **not** from `README.md`. Specifically the page must state that `post_agent_move_to_review.py` **does not move anything and is deliberately inert** (it prints a reminder), and must quote the step limit as **90**. Both facts are wrong in the current README; reproducing them is a task failure. | drift constraint, T081/T085 |
| 6 | The page carries the install command (`curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh \| sh`), the git-repo prerequisite, the `git`/`curl`/POSIX-`sh` prerequisites, the restart-Claude-Code-after-install step, and the update command. | "guide to install" |
| 7 | The page contains **no** task ID (`Txxx`), no "KANBAN", no "In Progress"/"Ready for Review", and no memory-file contents. | "I don't want sync the KANBAN" |
| 8 | `tests/test_site_content.py` exists and enforces AC2/AC3/AC4/AC5/AC7 by reading the source of truth at test time — never a hardcoded copy of the list. | drift constraint |
| 9 | The full suite passes: the pre-existing baseline (680 tests as of `78ebfa1`) plus the new ones, with **0 regressions**. | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The repo as-is | Every `.claude/skills/*` dir name appears in `site/index.html` | automated test |
| 2 | Every agent `name:` in `.claude/agents/*.md` except `general-agent-template` | appears in the page with its `subagent_type` | automated test |
| 3 | Every hook command path in `.claude/settings.json` | its basename appears in the page's hook table | automated test |
| 4 | `STEP_LIMIT` literal parsed from `pre_agent_step_limit.py` (currently `90`) | the same number appears in the page's step-limit row | automated test |
| 5 | **Mutation control M1** — create a throwaway dir `.claude/skills/zzz-fake-skill/` | the skill-roster test goes **RED** naming `zzz-fake-skill`; revert after observing | Supervisor re-runs manually |
| 6 | **Mutation control M2** — change the page's step-limit number from 90 to 40 | the step-limit test goes **RED**; revert after observing | Supervisor re-runs manually |
| 7 | **Mutation control M3** — insert the literal string `PROJECT_KANBAN.md` into the page | the AC7 no-project-state test goes **RED**; revert after observing | Supervisor re-runs manually |
| 8 | `grep -oE 'https?://[^"]+' site/index.html` restricted to `src=`/`href=` asset attributes | zero external asset references | automated test |

> M1–M3 are **mandatory**. Without them, AC8's assertions are satisfiable by a test that checks
> nothing — the vacuous-assertion family this repo has hit 9 times (see `memory/learnings.md`).
> Report each as observed-RED with the exact failure line, or the task is not done.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q && python3 -m pytest .claude/hooks/tests/ tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T083.md`, copied from `templates/TASK_REVIEW_template.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `site/index.html`, full page | Screenshot at 1280px wide + LLM-vision description pasted into the review | Every section from AC2/3/4/6 is visibly present, in order, with readable contrast; no overlapping or clipped text |

> No prior snapshot exists (first version), so this is a **baseline capture**, not a diff. Say so in the evidence rather than claiming a passing diff against nothing.

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match the repo's report palette | CSS audit — grep the declared hex values | Dark base `#0a0a12` with the cyan/green/purple/amber accents already used by `templates/` HTML reports; documented in `memory/decisions.md` as the user's preferred aesthetic |
| Typography | computed style / declared stack | System font stack only (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`) — no webfont, per the no-external-assets non-goal |
| Spacing / layout | declared CSS | One readable measure: content column capped ~`72ch`/`960px`, centered, consistent section rhythm |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (320–480px) | Screenshot | Single column; the hook and skill tables scroll horizontally **inside their own container** — the page body must never scroll sideways |
| Tablet (768px) | Screenshot | Single column, wider measure; no clipped table cells |
| Desktop (1024px+) | Screenshot | Centered capped-width column; tables fully visible without horizontal scroll |

---

## Approach

**Pattern reference**: `templates/` HTML report templates — imitate their dark neon palette, self-contained
single-file structure, and inline-`<style>` approach. That is exactly the constraint here (one file, no deps),
and the palette is already the recorded user preference.

**Vital slice**: the four rosters (agents, skills, hooks, install) plus the drift test. Those carry the
user's stated value; everything else on the page is framing.

**Cut list** (deliberately not built, recorded so a later reader can tell a cut from an oversight):
- Per-skill detail pages — one line each is enough to evaluate the kit.
- Dark/light toggle — the page commits to the dark palette; no toggle to maintain.
- The pack matrix — belongs on the page eventually, but T085 is what frees it from the README; keep v1 to the four rosters and add packs only if it costs nothing.

Build the page from source in this order: parse `.claude/agents/*.md` frontmatter, list `.claude/skills/`,
read `.claude/settings.json` + each hook's module docstring, then write the HTML. **Write
`tests/test_site_content.py` first (red), then the page (green)** — this is a `tdd` task; the test is
the whole defence against drift, so it must be seen failing before the page exists.

Group the 30 skills using CLAUDE.md's own stage index so the grouping matches the documented pipeline:
Stage 0.5 `brainstorming`,`ideate` · Stage 1 `git-guardrails-claude-code`,`map-codebase` · Stage 1.5
`craft-agent` · Stage 2 `grill-with-docs`,`to-issues` · Stage 3 `tdd`,`bugfix`,`diagnose`,`craft-spawn-prompt`,`migration-safety`
· Stage 4 `blast-radius`,`code-review`,`html-report` · Stage 5 `ship`,`delivery-report` · Cross-cutting: the rest.
Derive the "rest" by set difference against the live directory listing — do not hand-type it, or the
grouping silently drops a skill the test then catches as missing.

---

## Edge Case Checklist

- [ ] A skill directory exists but has no `SKILL.md` — the test must still require it on the page (directory listing is the source of truth, per the spec table), or state in the test docstring why not
- [ ] `general-agent-template` must be **excluded** from the spawnable-agent assertion but still appear on the page as a non-spawnable base — an agent that naively lists all 5 as spawnable fails AC2
- [ ] Skill names containing `-` must match exactly; substring matching would let `code-review` satisfy an assertion meant for `compound-refresh`. Assert on whole-word/exact-token presence
- [ ] AC7's forbidden-string check must not false-positive on this repo's own filenames appearing in a URL or code sample — scope the assertion to visible page text
- [ ] The install command contains a `|` — inside an HTML table cell or code block it must be escaped/rendered so the reader can copy it intact
- [ ] `.claude/settings.json` wires one hook with matcher `.*` twice (trace + step-limit); the hook table must list both, keyed by script name not by matcher

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | New — the page |
| `site/style.css` | New, optional — only if inline `<style>` becomes unreadable; a single inline block is preferred |
| `tests/test_site_content.py` | New — the drift test (AC8) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `README.md` | T085 owns it. Two agents editing it concurrently is the collision this board split exists to prevent |
| `PROJECT_KANBAN.md`, `PROJECT_KANBAN_SITE.md` | Supervisor-only; the Supervisor moves rows |
| `memory/**` | Supervisor-only writes (Memory Write Protocol) |
| `.claude/skills/**`, `.claude/agents/**`, `.claude/settings.json` | These are the **source of truth this task is tested against**. Editing them to make a test pass inverts the test |
| `vercel.json` | T084 owns it |

---

## Test Plan

`tests/test_site_content.py`, written first and seen RED:

1. `test_every_skill_dir_appears_on_page` — iterate `.claude/skills/*/`, assert each name in page text.
2. `test_every_spawnable_agent_appears_with_subagent_type` — parse `name:` from `.claude/agents/*.md`, exclude `general-agent-template`, assert each present.
3. `test_base_template_marked_not_spawnable` — assert `general-agent-template` appears near the words "not" + "spawn".
4. `test_every_wired_hook_appears_in_hook_table` — parse `.claude/settings.json`, assert each hook script basename present.
5. `test_step_limit_matches_source` — regex `STEP_LIMIT = int(os.environ.get("CLAUDE_STEP_LIMIT", "(\d+)"))` from the hook, assert that number on the page.
6. `test_move_to_review_hook_documented_as_inert` — assert the page says it does not move / is inert.
7. `test_no_project_state_on_page` — assert no `Txxx` match, no "KANBAN", no "In Progress".
8. `test_no_external_assets` — assert no `src=`/`href=` pointing at `http://` or `//`.

Then build the page until all are green, then run the full suite for regressions, then run M1–M3.

---

## Completion Checklist

- [ ] Implementation done
- [ ] `tests/test_site_content.py` written **first** and observed RED before the page existed — say so explicitly in the report
- [ ] M1, M2, M3 each observed RED with the exact failing assertion pasted, then reverted
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: **N/A** — Low risk, no runtime code path, no user input, no secrets
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T083.md` (Hard-Stop Gate 5)
- [ ] All three UI/Design evidence rows filled with screenshots (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` — **user-run only**; do not claim it
- [ ] Supervisor notified: task ready for Stage 4 review
