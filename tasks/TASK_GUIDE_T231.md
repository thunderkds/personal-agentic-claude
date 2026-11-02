# TASK_GUIDE — T231: Story landing page — one visual flow on index.html, reference moves to docs.html
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md` (not `PROJECT_KANBAN_SITE.md`: auto verify reads only `PROJECT_KANBAN.md`, as T207/T212/T213 did)

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `tasks/T204_graphite_mint_spec.md` (design system) and `site/theme.css` (the only place colors live)
7. Read `tests/test_site_content.py` and `tests/test_site_visual_first.py` end to end before moving any text

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02, verbatim: "the content of index page still got the complex idea, any way to convert them as the flow, design, visualize the knowledge. Recheck them all, too much things to say here"

User's choice, 2026-11-02 (forced choice between three shapes, each shown as a mock): **"One story, docs moved"**:

```
index.html  (5 screens)
1. What it is: one sentence + install
2. The journey (click a step for more)
   You ask -> It plans -> Agents build -> It checks -> You merge
3. Small or big job?   small: fast path / big: full path
4. What it stops       no test -> blocked / no plan -> blocked / risky push -> blocked
5. Go deeper: cards    Agents | Skills | Memory | Add-ons

docs.html  (reference)
   Settings tool, Hooks, Skills, Packs, Providers, Layout, Update, MCPs
```

**Restated intent**:
> A first-time reader understands what Easy Kit does from one visual flow, in plain words, in about five screens, without opening a fold. All reference content moves unchanged to a new `site/docs.html`. No fact is lost.

**Supervisor investigation (2026-11-02, `main` @ `09d2544c`, rendered at 1400 px)**: 17 sections; 1,543 words visible, 3,021 folded. Diagrams exist but carry internal terms (`C2`, `PreToolUse`, `Gate 5 and 6`, "Stage 1.5"). No diagram shows the path from request to shipped. The Settings tool sits mid-page at about 2,300 px tall.

**Supervisor design decisions** (binding):
- **D1 — Two pages.** `site/index.html` is the story. `site/docs.html` is new and holds all 17 current sections, their ids, their text, their folds, the sidebar, and the Settings tool with its three scripts, moved byte-for-byte. `site/theme.css` serves both. Any CSS in the page's `<style>` that both pages need moves to `theme.css`.
- **D2 — Story screens**, in this order, each a `<section>` with a stable id:
  1. `hero`: one sentence, the install command with its Copy button, one link to the docs page.
  2. `journey`: five linked steps — You ask → It plans → Agents build → It checks → You merge. Each step has one short plain line and links to its `docs.html#<id>` section. It marks which steps are the user's (ask, merge) by a text label, never by color alone.
  3. `paths`: one question ("Small or big job?") splits into a fast path and a full path, in plain words with one example for each. Name the words `minimal` and `extended` once only, so the docs terms still connect.
  4. `stops`: three to five "without X → blocked" pairs. Every pair must be true of a real hook. Name that hook in an HTML comment beside the pair. Say on this screen, in one short line, that the checks run on Claude Code only (Codex and Cursor get the doctrine, not the hooks).
  5. `deeper`: four cards — Agents, Skills, Memory, Add-ons — each with one line and a link into `docs.html`. Add one link to the Settings tool. Add-ons covers packs and MCPs.
- **D3 — Reading budget.** `index.html` `<main>`: at most 300 visible words, counting all text outside `<pre>`, `<code>`, `<script>`, `<style>`, HTML comments. No `<details>` on the page. Length: at most 5 viewport heights at 1440×900.
- **D4 — Plain words.** Visible text on `index.html` holds none of: `C0`–`C3`, `Risk`, `Gate`, `Stage`, `Phase`, `PreToolUse`, `PostToolUse`, `TASK_GUIDE`, `worktree`, `sub-agent`, `doctrine`, `harness`, `Evidence`. Text follows AGENTS.md Writing Principles (ASD-STE100).
- **D5 — Old links keep working.** A small inline script on `index.html`: if `location.hash` names a section id of `docs.html`, `location.replace` to `docs.html` + that hash. The script holds the id list; a test keeps the list equal to the real ids. Visual only otherwise: no JavaScript draws the diagrams, and no library or CDN.
- **D6 — Navigation.** `index.html` has the family header, no sidebar. `docs.html` has the header and the sidebar, with `aria-current` handling correct on each page. Both pages link to each other in the header. The scroll-spy runs on `docs.html`.
- **D7 — Accessible and responsive.** Flows are `<ol>`/`<ul>`. Every color pair meets WCAG AA. Motion is optional and honours `prefers-reduced-motion`. Flows stack at ≤ 768 px, with `scrollWidth == clientWidth` at 375 px, on both pages.
- **D8 — Design system only.** Tokens from `theme.css`. No hex outside it. Mint only on the outcome nodes.
- **D9 — Tests follow the content.** Tests pin the same facts in their new home. `test_site_content.py`, `tests/settings_tool/*.mjs` and `tests/site_scrollspy/` read `docs.html`, or both pages joined where a fact now lives on either. T207's budget constants apply to `docs.html` sections unchanged. No test is deleted and no assertion weakened. A test that must change says why in its commit.

**Out of scope**:
- Changing any fact, number or claim; rewriting reference text on `docs.html`
- Settings tool logic and `settings-catalog`
- `vercel.json`, `.vercelignore`
- A docs page per topic, search, or a build step

**Requirement Refs**: no PRD — traces to the user's 2026-11-02 message and choice above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user picked "One story, docs moved", 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (`minimal`, `extended`, Supervisor keep their meaning; the story page uses plain words by D4)
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D9
- [x] Requirement Refs — N/A, no PRD; traced to the user message

---

## Dependencies & Reachability

**Depends on**: T207 (visual sections, merged), T212 (accent), T213 (scroll-spy), T224 (family header)
**Entry point**: `site/index.html` at `https://personal-agentic-claude.vercel.app/`; `site/docs.html` at `/docs.html`. Reachable from the hero link, the `deeper` cards and the header.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `index.html` holds sections `hero`, `journey`, `paths`, `stops`, `deeper`, in that order, and no `<details>` | D2, D3 |
| 2 | `journey` is an ordered list of exactly 5 steps, each with a link to an id that exists in `docs.html`; the ask and merge steps carry a text label that marks them as the user's | D2 |
| 3 | `index.html` `<main>` has ≤ 300 visible words, and none of the D4 terms | D3, D4 |
| 4 | `stops` names, in a comment beside each pair, a hook file that exists in `.claude/hooks/`, and states that the checks run on Claude Code only | D2 |
| 5 | `docs.html` holds all 17 section ids of `index.html` at `09d2544c`, and all three Settings tool script blocks byte-identical to that commit | D1 |
| 6 | No sentence is lost: every `<p>`/`<li>`/`<td>`/`<dd>` text of `index.html` at `09d2544c` appears in `docs.html`. The baseline is a fixture or a hash list in the test | D1 |
| 7 | Opening `index.html#hooks` lands on `docs.html#hooks`; the script's id list equals the ids in `docs.html` | D5 |
| 8 | Each page links to the other in its header; `index.html` has no sidebar; the scroll-spy test passes on `docs.html` | D6 |
| 9 | No hex outside `theme.css`; no third-party `<script src>` or `<link>` on either page | D8 |
| 10 | Every assertion in `tests/test_site_content.py`, `tests/test_site_visual_first.py`, `tests/settings_tool/*.mjs` and `tests/site_scrollspy/` still runs; none deleted or weakened | D9 |
| 11 | Mutations, each turns a new test RED, then green on revert: **M1** delete one journey step; **M2** add the word `PreToolUse` to `paths`; **M3** delete one sentence from `docs.html`; **M4** remove one id from the D5 list; **M5** name a hook file that does not exist in `stops` | guarantees asserted |
| 12 | Full suites pass: `python3 -m pytest tests -q`, `node --test tests/settings_tool/*.mjs`, `node --test tests/site_scrollspy/*.mjs`, `python3 -m pytest .claude/hooks/tests -q` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | `index.html` at 1440×900 | five screens, the journey visible by the second screen, no fold | headless Chrome screenshot |
| 2 | both pages at 375 px | flows stacked, `scrollWidth == clientWidth` | headless Chrome |
| 3 | `index.html#hooks` opened | browser ends on `docs.html#hooks` | headless Chrome |
| 4 | Settings tool on `docs.html` | builds and checks a `settings.json`, as it did before | `node --test tests/settings_tool/*.mjs` and one headless click-through |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_site_visual_first.py tests/test_site_story.py -q && node --test tests/settings_tool/*.mjs && node --test tests/site_scrollspy/*.mjs
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T231.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T231.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| `index.html` | screenshot at 1440 px, before and after | five screens, one flow |
| `docs.html` | screenshot at 1440 px against old `index.html` | same sections, same look |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | AC 9 test | tokens only |
| Typography | computed style of a step title and a card title | Plex Sans / Plex Mono from the theme scale |
| Accent use | visual check | mint only on outcome nodes and primary actions |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1440 / 1024 | screenshot | flows horizontal or branching as designed |
| 768 / 375 | screenshot + `scrollWidth == clientWidth` | flows stacked, no sideways scroll, both pages |

---

## Approach

**Pattern reference**: T207's flow markup in `#tracks` and `#install`; the `.quick-ref` Copy button.

**Vital slice**: the `journey` screen plus `docs.html` with no sentence lost.
**Cut list**:
- Animated or interactive diagrams
- Per-topic docs pages, search
- Rewriting text on `docs.html`

---

## Edge Case Checklist

- [ ] The Copy button works on both pages
- [ ] A hash on `index.html` that is not a docs id stays on the page
- [ ] `docs.html` loads with a hash into a closed fold: the heading stays visible
- [ ] With JavaScript off, both pages read in order
- [ ] The redirect does not add a Back-button trap (`location.replace`)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | replaced by the story |
| `site/docs.html` | new: all reference content |
| `site/theme.css` | shared rules, journey, paths, stops, cards |
| `tests/test_site_story.py` | new: AC 1–9, 11 |
| `tests/test_site_content.py`, `tests/test_site_visual_first.py`, `tests/settings_tool/*.mjs`, `tests/site_scrollspy/test_scrollspy.mjs` | repoint by D9 |
| `tests/test_agents_md_primary.py`, `test_companion_setup.py`, `test_docs_match_installer.py`, `test_docs_t151.py`, `test_memory_slice.py`, `test_resolve_question.py` | repoint only if a test reads moved site text |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | deploy unchanged: `outputDirectory` already serves all of `site/` |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: write `tests/test_site_story.py` and see it fail. Capture the baseline from `09d2544c` for AC 5 and AC 6 before moving anything. Move the reference to `docs.html` and repoint tests, and keep the suites green. Then build the story. Run M1–M5 by hand and paste each RED and green. Take the screenshots above with `google-chrome --headless=new`, with `file://` URLs or a free port (8765 is in use on this machine), and save them outside the repo. Then the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T231.md` (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] Auto verify run started by the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
