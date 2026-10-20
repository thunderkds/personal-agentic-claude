# TASK_GUIDE — T165: The landing page reads as a scan-first reference, and links the Easy Verifier site
**Date**: 2026-10-20
**Complexity Level**: C2 — page-wide restructure of `site/index.html` (Hard-Stop Gate 2 floor: *restructure*)
**Risk Level**: Medium — floor from Gate 2; actual exposure is low (static HTML, no secrets, no deploy config)
**Priority**: P1
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md` (site scope, drift constraint)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `site/index.html` in full and `tests/test_site_content.py` in full — every existing assertion must stay green

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-20: *"the page is containing lot of the information with words, and content, let check and update the page more informative to refer. by the way, let add this one https://easy-verifier.vercel.app/ as verifier mcp also"* — then chose **"Scan-first rewrite"** over "trim words only": keep every section and fact; each lead paragraph becomes a one-line summary plus bullets/table; long table cells are shortened with the detail moved into a `<details>` fold-out; a quick-reference card goes at the top.

**Restated intent:**
> Make `site/index.html` fast to scan as a reference without losing any fact. Prose shrinks to
> one-line summaries, bullets and tables; secondary detail moves into native `<details>` fold-outs
> (no JS required). A new quick-reference card near the top gives install/update commands, the stage
> sequence, and roster counts. The `#verifier` section gains a link to the Easy Verifier site,
> https://easy-verifier.vercel.app/, beside its existing GitHub link.

**Baseline (Supervisor-measured 2026-10-20 on `main` @ `2b4c73c`):** 2,699 visible words; 30 `<p class="lead">` paragraphs holding 1,207 words, longest 99; 118 `<td>` cells, 9 over 25 words, longest 43; 0 `<details>` elements.

**Fact-preservation constraint (load-bearing):** moving text into `<details>` is fine; deleting a fact is not. Every `<code>…</code>` token on the BEFORE page must still appear on the AFTER page (visible or inside `<details>`), unless the reviewer accepts a listed exception.

**Honesty constraint (carried from T135):** the verifier section still frames easy-verifier-mcp as a separate companion tool; the kit does not use, ship or require it. The existing T135 tests enforce this — keep them green.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user picked "Scan-first rewrite", 2026-10-20)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md` glossary (*Supervisor, Sub-agent, Skill, Hook, Pack*)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `site/index.html` (served as-is by Vercel from `site/`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Every `<p class="lead">` outside a `<details>` element is ≤ 35 words | one-line summaries |
| 2 | Every `<td>` outside a `<details>` element is ≤ 25 words | shorten long cells |
| 3 | At least one `<details><summary>` fold-out exists; moved detail lives there | detail in fold-outs |
| 4 | A `<section id="quick-reference">` sits first under `<main>` after the header, has a sidebar nav link, and shows: install command, update command, stage sequence, skill count, spawnable-role count, blocking-hook count | quick-reference card |
| 5 | The quick-reference counts are **derived in tests** from source of truth (skills dir, agent frontmatter, `settings.json` + the hook-table tag), never hardcoded in the test | drift constraint |
| 6 | `#verifier` contains `href="https://easy-verifier.vercel.app/"` with `target="_blank" rel="noopener noreferrer"`, alongside the existing GitHub link | add verifier site |
| 7 | Every `<code>` token on the BEFORE page appears on the AFTER page (reviewer diff, see Evidence) | fact preservation |
| 8 | All existing `tests/test_site_content.py` and `tests/test_docs_match_installer.py` assertions stay green | no regression |
| 9 | New tests for AC1–AC6 in `tests/test_site_content.py`, observed RED before the page change | Gate 5 |

**Mutation controls:** **M1** — add a 40-word sentence to any visible lead → AC1 test RED. **M2** — change the quick-reference skill count to 29 → AC5 test RED. **M3** — remove the Easy Verifier site link → AC6 test RED. **M4** — pad a visible `<td>` to 30 words → AC2 test RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_docs_match_installer.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

AC7 diff (run from repo root, base = `2b4c73c`):

```bash
python3 - <<'EOF'
import re, subprocess
before = subprocess.run(["git", "show", "2b4c73c:site/index.html"], capture_output=True, text=True).stdout
after = open("site/index.html").read()
tok = lambda s: set(re.findall(r"<code>(.*?)</code>", s, re.S))
print("missing:", sorted(tok(before) - tok(after)))
EOF
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T165.md`. BEFORE is pre-filled there by the Supervisor.

---

## UI / Design Acceptance Criteria

- Reuse the page's existing tokens, `.tag-*` badges, `.table-wrap` and `<p class="lead">`; new CSS only for `<details>`/`<summary>` and the quick-reference card, using existing `:root` variables — no new colors, fonts, images or external assets.
- `<details>` must work with JS disabled (native element); the sidebar active-link script must still work.
- 375px width: no horizontal page scroll; quick-reference commands wrap or scroll inside their own block.
- Keep the pipeline SVG as is.

---

## Approach

**Pattern reference**: the `#hooks` table (`.tag-block` / `.tag-advise` / `.tag-inert`) for compact Effect cells; the existing install `<pre>` blocks for quick-reference commands.

**Vital slice**: AC1, AC2, AC4, AC6 with AC7 holding. **Cut list**: search box; per-skill pages; collapsing whole sections; any new JS; rewording facts that already read as one line.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Rewrite leads and long cells; add `<details>` fold-outs, `#quick-reference` section + nav link, Easy Verifier site link |
| `tests/test_site_content.py` | AC1–AC6 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `.claude/hooks/**`, `skills/**`, `agents/**` | No harness change in scope |
| `README.md` | Not in scope; `test_readme_current.sh` guards it separately |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Completion Checklist

- [ ] New AC1–AC6 tests observed RED first, then GREEN
- [ ] M1–M4 results pasted in the review's "Negative cases hold" row
- [ ] AC7 diff output pasted (`missing: []` or reviewer-accepted exceptions)
- [ ] All three UI Evidence rows filled
- [ ] `/verify` — user-run
