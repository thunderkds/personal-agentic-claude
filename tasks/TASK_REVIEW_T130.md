# TASK_REVIEW — T130: The site describes the agent-focus work (T124–T129) and stops contradicting it

> Sibling of `tasks/TASK_GUIDE_T130.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` — 5 new T130 tests (after `test_site_names_the_version_it_actually_ships_with`). RED before edit: `3 failed, 23 passed` (memory_md_row, spawn_hook_row, slice_caps). GREEN after: `26 passed in 0.05s`. Mutations, each exactly 1 RED then restored to `26 passed`: M1 ("not pasted" restored) → `test_memory_md_row_describes_the_memory_slice_not_the_old_behaviour`; M2 (`MAX_LINES=31` in memory_slice.py) → `test_slice_caps_on_page_match_memory_slice_source`; M3 (`scripts/token_meter.py` on page) → `test_page_does_not_name_token_meter_while_scripts_are_not_shipped`; M4 (nav link removed) → `test_every_section_has_a_nav_link` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_site_content.py -q` → `26 passed`; `python3 -m pytest .claude/hooks/tests tests -q` → `973 passed in 15.80s`; `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | 973 passed (above); existing site tests unchanged |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | `reports/T130/before_memory-system_1280.png` vs `after_memory-system_1280.png`; new section `after_agent-focus_1280.png` / `_375.png`. Vision verdict: section matches neighbouring h2/table styling; sidebar shows "Agent focus" under The team |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `git diff site/index.html` touches no `<style>` block and adds no custom property; only `table-wrap`, `code`, `tag-*`, `lead` classes reused |
| **UI: Responsiveness at target viewports** | ☑ pass | headless chrome `scrollWidth/innerWidth`: 375 → 485/500 (chrome enforces a ~500px minimum headless window, so 375 was not literally reachable), 768 → 753/768; no horizontal page overflow. Full-page shots `after_full_{375,768,1280}.png`. Scroll-spy highlight not exercised headless |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-09-25, before any implementation commit; `site/index.html` lines 457, 566):

```html
<tr><td>PreToolUse</td><td><code>Agent</code></td><td><code>pre_agent_validate_guide.py</code></td><td><span class="tag tag-block">blocks</span> spawn if the TASK_GUIDE is missing</td></tr>
<tr><td><code>memory/MEMORY.md</code></td><td>Hot</td><td>≤42,000 characters, referenced by path in every sub-agent spawn prompt and read by the agent — not pasted</td></tr>
```

No `#agent-focus` section or nav link existed. Screenshot: `reports/T130/before_memory-system_1280.png`.

**AFTER**: `site/index.html` MEMORY.md row now reads "≤42,000 characters. Each sub-agent spawn prompt carries a pasted memory slice … reads the whole file only if its work reaches what the slice misses"; hook row keeps `blocks` and adds `advises` for a missing memory slice / `**Startup reads**` block; new `#agent-focus` section (`reports/T130/after_agent-focus_1280.png`).

**DELTA**: A visitor can read how the kit keeps agents focused, and the page no longer says the memory index is "not pasted".

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
