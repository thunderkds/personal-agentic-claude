# TASK_REVIEW — T135: The landing page references easy-verifier-mcp in a short "Verifier" section

> Sibling of `tasks/TASK_GUIDE_T135.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py`: `test_verifier_section_is_linked_from_the_reference_nav_group`, `..._names_the_tool_and_links_the_repo_safely`, `..._is_short_with_four_to_six_highlights`, `..._does_not_claim_the_kit_uses_it`. Observed RED first: `4 failed, 30 passed`; after change: `34 passed in 0.05s` — pass |
| Verification command run | ☑ pass | `pytest tests/test_site_content.py -q` → `34 passed`; `pytest .claude/hooks/tests tests -q` → `983 passed in 14.48s`; `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | M1 (nav `<li>` deleted) → 2 failed (`test_every_section_has_a_nav_link`, `test_verifier_section_is_linked_from_the_reference_nav_group`). M2 (repo URL replaced) → 1 failed (`..._links_the_repo_safely`). M3 ("The kit uses easy-verifier" inserted) → 1 failed (`..._does_not_claim_the_kit_uses_it`). File restored after each; `34 passed` |
| verify | ☐ N/A | User-run `/verify` — pending; not run by the implementer |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: `site/index.html` (+16 lines: 1 nav `<li>`, 1 section), `tests/test_site_content.py` (+4 tests). Skipped: harness, hooks, deploy config (Must-NOT-Touch) — untouched |
| Full smoke suite still green (no regression) | ☑ pass | `983 passed in 14.48s` (`.claude/hooks/tests` + `tests`) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Headless Chrome at 375px rendered the page and loaded `#verifier` with no script errors; section reuses `<p class="lead">`, plain `<ul>`, and the existing external-link `<a>` — no new markup classes. Screenshot in scratchpad (`v375.png`) shows the page top only, not the section — verdict rests on the DOM measurement, not that image |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `git diff --stat -- site` → 16 insertions, 0 CSS/`<style>`/font/image/script changes; only existing element styles apply |
| **UI: Responsiveness at target viewports** | ☑ pass | 375px iframe in headless Chrome: `{"docScrollW":360,"vw":375,"sectionScrollW":328,"sectionClientW":328}` — no horizontal overflow, section fits its box. Only the 375px viewport was tested |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (non-executable change; verbatim prior content of `site/index.html`, captured 2026-09-26 before any implementation commit):

Sidebar Reference group (lines 200-207):
```html
    <p class="nav-group-title">Reference</p>
    <ul>
      <li><a href="#packs">Packs</a></li>
      <li><a href="#providers">Providers</a></li>
      <li><a href="#repository-layout">Repository layout</a></li>
      <li><a href="#memory-system">Memory system</a></li>
      <li><a href="#options">Options</a></li>
    </ul>
```
`#memory-system` -> `#options` boundary (lines 595-599):
```html
</div>
</section>

<section id="memory-system">  <!-- ...ends at </section> line 596 -->

<section id="options">
<h2>Options</h2>
```
No `id="verifier"` and no `easy-verifier-mcp` string exist anywhere on the page.

**AFTER** (verbatim new content of `site/index.html`):
```html
      <li><a href="#memory-system">Memory system</a></li>
      <li><a href="#verifier">easy-verifier-mcp</a></li>
...
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
<p><a href="https://github.com/thunderkds/easy-verifier-mcp" target="_blank" rel="noopener noreferrer">easy-verifier-mcp on GitHub</a></p>
</section>
```

**DELTA**: A visitor can now find, from the Reference nav, what easy-verifier-mcp is and follow a link to its repo, without the page implying the kit uses it.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
