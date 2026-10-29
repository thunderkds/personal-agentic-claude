# TASK_REVIEW — T181: README and site describe the two tracks, the Debate step and `[auto]`

> Sibling of `tasks/TASK_GUIDE_T181.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` (6 new T181 tests) and `tests/test_readme_slim.py` (1 new). RED first (commit 59358cc): `6 failed, 66 passed` (site), `1 failed, 4 passed` (README). After the change: `77 passed` for the two files. |
| Verification command run | ☑ pass | `pytest tests/test_site_content.py tests/test_readme_slim.py -q` -> `77 passed in 0.10s`; `pytest .claude/hooks/tests tests -q` -> `1756 passed, 25 subtests passed in 56.87s`; `sh scripts/validate.sh` -> `validate.sh: PASS`. |
| Negative cases hold | ☑ pass | M1 (delete nav `<li>`): `2 failed, 70 passed` (test_tracks_nav_link_exists, test_every_section_has_a_nav_link). M2 (`[auto]` -> `[x]` in section): `1 failed, 71 passed` (test_tracks_section_states_announcement_lines_and_override). M3 (insert "auto mode merges your branch"): `1 failed, 71 passed` (test_tracks_section_does_not_say_auto_merges...). Page restored after each; `git status` clean. |
| verify | ☑ pass | User ran `/verify T181` 2026-10-28 at `f686fa0` (T181 branch; 7 commits on `main`). Surface: `site/index.html` served by a local HTTP server and rendered in headless Chrome (`google-chrome --headless=new`), plus `README.md` as shipped. Desktop 1280 px and phone 375 px (in a 375 px iframe; headless Chrome will not go below ~485 px): sidebar shows `Minimal and extended tracks` under Overview; DOM order `#what-you-get` (14774) < `#tracks` (18779) < `#install` (21539); section at y=1845 (desktop) / 2135 (phone), screenshots read: h2, lead, 4 bullets, `Auto mode` h3, Risk list, Debate paragraph, auto verify paragraph ending **Merge, push and Done stay with you.** Phone width: `SCROLLW=360 CLIENTW=360 TRACKS_OVERFLOW=0`. Text checks on the rendered section: has `Track: minimal`, `Track: extended`, `[auto]`, `/verify`, `full`, `at most 3 Debates`, `decided for you — please review`, `auto verify`; absent `merges your branch`, `Ready for Review`, `asks you nothing`; diagram `<desc>` says `These stages are the extended track.` README intro lines 8–9 state the two tracks, `full`/`minimal`, `[auto]`, and that merge stays with you (75 lines). Findings (not blockers): the flag `⚠ decided for you — please review` wraps with the ⚠ alone at a line end on desktop; the lead paragraph uses the page's existing dim lead colour. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 code-review (Supervisor, 2026-10-27): `git diff 39e123e..HEAD` — `site/index.html` (nav `<li>`, `<section id="tracks">`, one `<desc>` sentence), `README.md` (intro), `tests/test_site_content.py` (+6), `tests/test_readme_slim.py` (+1), this file. lane_check: `lane: C1, 4 files, 118 lines, FITS; unpredicted: tests/test_readme_slim.py`. Every sentence of the section checked against `docs/claude-md/tracks.md` (track rule rows incl. the user-data row, the two announcement lines, `full`/`minimal`, never moved down, 7-step minimal flow incl. new branch + commit without asking, `[auto]` exact tag, Debate size by Risk, cap 3, `### Auto verify (Stop hook)`): no mismatch. Full suite `1756 passed, 25 subtests passed`. **0 P0. P1 (process, resolved):** the agent's first report skipped the Permanent-Rule reads (`PROJECT_SPEC.md`, `PROJECT_SPEC_SITE.md`, `agents/frontend.md`); sent back, it read them and fixed 2 overclaims in `a5f6aea` ("asks you nothing" → names the stops that stay; the glossary term **Auto verify** now on the page). **P2 (conf 75):** to stay at the 75-line cap, the README intro dropped the aside that `post_agent_move_to_review.py` is an inert reminder-only hook since T044 — true information removed outside the request; acceptable for the cap, recorded. P3: README's `v2.1.0` and `AGENTS.md` `Version: 1.17` are the release step's, not this task's. |
| Full smoke suite still green (no regression) | ☑ pass | `1756 passed, 25 subtests passed` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Headless Chrome 375px iframe render ran; layout intact, no overflow (see responsiveness). Section reuses existing markup only; no pixel-diff baseline exists in the repo. Verdict: no new CSS, so no regression expected; only structural check done. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | `git diff 453b2d5 -- site/index.html`: no added `<style>`, `<script>`, `<img>`, `<link>`, font or class except existing `<p class="lead">`; only `<h2>`, `<h3>`, `<p>`, `<ul>`, `<li>`, `<code>`, `<strong>`, `<em>`. `test_no_external_assets` and the other drift tests pass. |
| **UI: Responsiveness at target viewports** | ☑ pass | Method: `google-chrome --headless=new` rendering `site/index.html` in an `<iframe width=375>` (headless Chrome cannot go below ~485px window width), page script posts metrics. Result: `DOC=360 CLIENT=360 OVERFLOWING_ELEMENTS=0 SEC=328/328` -> no horizontal scroll, no code/li/p overflow in `#tracks`. Direct 1280px window: `SECOVER=0`. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (docs change: verbatim prior content, captured 2026-10-27 before any change; `README.md` is 75 lines):

`README.md` lines 1-9:

```markdown
# Easy Kit

**v2.1.0** — a general-purpose multi-agent supervisor framework for Claude Code, Codex, and Cursor.
Install once, deploy into any project: agent definitions, skills, hooks, and templates that drive a
5-stage agentic pipeline
(clarify → brainstorm → plan → parallel execution in worktrees → review → verify/ship), enforced by
pipeline hooks rather than prompt reminders — e.g. `pre_agent_step_limit.py` blocks runaway tool-call
loops (default 90 calls), and `post_agent_move_to_review.py` is a deliberately inert reminder-only
hook since T044 (it does not move any KANBAN row or reset any counter — see its docstring).
```

`site/index.html` lines 356-364 (end of `#what-you-get` and the start of the next section; there is no `#tracks` and no `href="#tracks"` in the file):

```html
    <rect x="10" y="506" width="300" height="50" rx="8"/>
    <text class="node-title" x="160" y="527" text-anchor="middle">Stage 5 · Integrate</text>
    <text class="node-out" x="160" y="545" text-anchor="middle">verify, merge, release plan</text>
  </g>
</svg>
</section>

<section id="install">
<h2>Install</h2>
```

**AFTER**: `site/index.html` has `<section id="tracks">` (h2 "Minimal and extended tracks", h3 "Auto mode") between `#what-you-get` and `#install`, nav `<li>` `href="#tracks"`, and the diagram `<desc>` says "These stages are the extended track." `README.md` lines 7-8 now read: "Two tracks: small work runs the **minimal track** ... Reply `full` or `minimal` to override." / "Add `[auto]` and either track runs to Ready for Review with a final report of every decision. Merge stays with you." (75 lines).

**DELTA**: A reader of the README or the site now learns the two tracks, the override, `[auto]`, the Debate and the auto-verify hook, and that merge stays with the user.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
