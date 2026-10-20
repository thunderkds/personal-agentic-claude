# TASK_REVIEW — T168: An "MCPs" section lists the companion MCP servers

> Sibling of `tasks/TASK_GUIDE_T168.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py`: new `test_mcps_section_is_linked_from_the_reference_nav_group` (AC1), `test_mcps_section_has_one_named_entry_per_server` (AC2), `test_ui_mcp_entry_has_four_to_five_one_line_highlights` + `test_ui_mcp_entry_links_the_repo_safely_and_invents_no_site` (AC4), `test_mcps_section_says_separate_and_never_claims_kit_integration` (AC5); T135 verifier tests + T165 AC6 test updated to read the `#verifier` entry inside `#mcps` (AC3, AC6). RED before page change: `8 failed, 54 passed`; after: `74 passed` |
| Verification command run | ☑ pass | 2026-10-20: `pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q` → `74 passed in 0.26s`; `pytest .claude/hooks/tests tests -q` → `1398 passed, 25 subtests passed in 41.62s`; `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | Page mutated, `tests/test_site_content.py` run, page restored each time. M1 remove easy-ui-mcp repo link → `1 failed`; M2 add "The kit uses easy-ui-mcp." → `1 failed`; M3 nav link back to `#verifier` → `2 failed`; M4 drop `id="verifier"` → `4 failed`. All RED |
| verify | ☐ pass / ☐ fail / ☑ N/A | **Waived by the user, 2026-10-20** ("no need to verify, mark done"). Not run. Evidence on record instead: Supervisor Stage 4 re-run of the full suite and DevTools-emulated screenshots/measurements at 1280px and 375px (see the Stage 4 section below). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `1398 passed, 25 subtests passed` (T165 caps, T166 flow, T167 tables, `test_docs_t151.py` included) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Screenshots viewed: `/tmp/t168shots/mcps-1280.png`, `/tmp/t168shots/mcps-375.png` (DevTools emulation, `behavior:'instant'`). Two cards stacked under a lead; headings green, bullets legible. First shot showed GitHub links in default browser blue on the dark card; fixed with `.agent-card a { color: var(--cyan) }` and re-shot — links now cyan |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Reuses `.agent-card`; the only CSS added is two rules using existing tokens (`.agent-card h3` → `var(--green)`, `.agent-card a` → `var(--cyan)`). No new colors, fonts, images, scripts or external assets |
| **UI: Responsiveness at target viewports** | ☑ pass | 1280px: `scrollWidth 1265 == clientWidth 1265`; 375px: `scrollWidth 375 == clientWidth 375` — no page overflow. Cards stack at both widths |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (Supervisor, 2026-10-20, `site/index.html` @ `d7874e7`) — verbatim sidebar Reference group:

```html
    <p class="nav-group-title">Reference</p>
    <ul>
      <li><a href="#packs">Packs</a></li>
      <li><a href="#providers">Providers</a></li>
      <li><a href="#repository-layout">Repository layout</a></li>
      <li><a href="#memory-system">Memory system</a></li>
      <li><a href="#verifier">easy-verifier-mcp</a></li>
      <li><a href="#options">Options</a></li>
    </ul>
```

Verbatim `#verifier` section:

```html
<section id="verifier">
<h2>easy-verifier-mcp</h2>
<p class="lead">
  A separate companion tool, not part of this kit: a no-LLM evidence engine you can run alongside Stage 4 review.
</p>
<ul>
  <li>No LLM and no model API key — ratings are deterministic rules over cited metrics</li>
  <li>Seven independently callable dimensions, from architecture to blast-radius</li>
  <li>Auditable coverage — a "found 4/6" always shows the sources it did not find</li>
  <li>Read-only and local — never runs the target repo's code, no outbound network</li>
  <li>Kit-aware mode treats this kit's specs, task guides and memory as ground truth</li>
</ul>
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a> &middot; <a href="https://easy-verifier.vercel.app/" target="_blank" rel="noopener noreferrer">Easy Verifier site</a></p>
</section>
```

**AFTER** (`site/index.html`, this task's commit) — nav: `<li><a href="#mcps">MCPs</a></li>` in place of the `#verifier` link. Section: `<section id="mcps">` → `<h2>MCPs</h2>`, lead "Two separate companion tools, not part of this kit: MCP servers you can run alongside it, each from its own repository.", then two `<div class="agent-card">` entries: `id="verifier"` (`<h3>easy-verifier-mcp</h3>`, the five original highlights and both links, unchanged) and `id="easy-ui-mcp"` (`<h3>easy-ui-mcp</h3>`, five highlights, link `https://github.com/thunderkds/easy-ui-mcp`). Screenshots: `/tmp/t168shots/mcps-1280.png`, `mcps-375.png`.

**DELTA**: A reader finds both companion MCP servers, easy-verifier-mcp and easy-ui-mcp, in one "MCPs" section with a link to each repo, and is told neither is part of the kit.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Stage 4 — code-review (Supervisor, 2026-10-20) — accepted

P0 0 · P1 0 · P2 0 · P3 1. Supervisor re-run `1398 passed, 25 subtests passed`; screenshots at 1280px and 375px (DevTools emulation) — `#mcps` shows two cards, links cyan, `#agent-roles` cards unchanged by the new `.agent-card h3`/`a` rules. No stray processes left by the implementer. Startup reads line names partial reads honestly.

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P3 | `site/index.html` `#mcps` | "separate companion tool, not part of this kit" appears in the section lead and again in each card's lead — three times in one section | 75 | Optional trim; left as is (the T135 honesty tests read each card) |

Security-review not required (Low): two outbound links, both `target="_blank" rel="noopener noreferrer"`; no script, form or external asset.
