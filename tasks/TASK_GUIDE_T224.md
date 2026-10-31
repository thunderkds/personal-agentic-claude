# TASK_GUIDE_T224 — Landing page lists all five Easy Kit family members

**Board:** `PROJECT_KANBAN_SITE.md` | Role: Frontend-Implementer (done by the Supervisor, see Deviation) | C1 | Risk: Low | P1
**Branch / worktree:** `feat/t224-family-members` / `../wt-t224` | Track: extended (UI component)

## Requirement (user, 2026-10-31, verbatim)
"let check and update the index page for list of member
1. the heart: personal-agentic-claude 2. easy-verifier 3. easy-ui 4. easy-memory 5. easy-personal"

Found: the header and drawer family nav listed 3 sites (Kit, Memory, Verifier); `#mcps` had 3 cards
(no easy-personal-mcp). Live URLs checked by HTTP GET on 2026-10-31: `easy-ui-mcp.vercel.app` 200
(title "easy-ui-mcp docs", matches `easy-ui-mcp/site/index.html`), `easy-personal.vercel.app` 200
(title matches `easy-personal-mcp/site/index.html`). `easy-ui.vercel.app` is an unrelated site; not used.

## Acceptance Criteria
| # | Criterion | Test |
|---|---|---|
| 1 | Header family nav = Easy Kit, Easy Verifier, Easy UI, Easy Memory, Easy Personal, GitHub (user's order); Easy Kit is `aria-current` | `test_family_nav_lists_the_five_sites_then_github_with_the_current_page_marked` |
| 2 | Drawer family nav lists the same five sites | `test_drawer_family_nav_lists_the_same_five_sites_as_the_header` |
| 3 | `#mcps` lead says four companion tools; 4th card `easy-personal-mcp` (separate, companion, optional; 4–5 one-line highlights; cost stated as API-equivalent, not the subscription bill; repo + site links with `noopener noreferrer`) — facts only from `easy-personal-mcp/README.md` v0.2.0 | `test_personal_mcp_card_*`, `test_mcps_section_lead_counts_four_companions`, card-count tests |
| 4 | Five links do not overlap the brand: header family nav moves into the drawer below 900px | `test_five_site_family_nav_moves_to_the_drawer_below_900px` (mutation: 899→719 turns it RED) |

Cut list: no site link added to the easy-ui-mcp / easy-memory-mcp cards (existing tests pin "repo link only"); other members' own family navs not changed (separate repos).

## Evidence
| Row | Result | Notes |
|---|---|---|
| New test(s) cover ACs | ☑ pass | RED first: 8 failed / 145 passed before the page edit; after: `154 passed in 0.51s` (site tests); full `tests/` + `.claude/hooks/tests` green (`1320 passed, 25 subtests passed`) |
| Visual regression | ☑ pass | headless Chrome screenshots at 1440, 1280, 1024, 900, 720, 375 px: header fits at ≥900; at 720 before the CSS fix the links overlapped "Easy Kit" — fixed, re-shot clean |
| Design-system compliance | ☑ pass | reused `.family-nav`/`.dot`/`.card agent-card` markup; no new colours; token tests green |
| Responsiveness | ☑ pass | <900px links in the Menu drawer; 375px unchanged |
| code-review | ☐ not run | `code-review` skill not available in this session |
| verify | ☐ user | site board is not read by `stop_auto_verify.py`; user runs `/verify T224` or reviews the screenshots |

## Deviation
No `frontend-developer` agent and no project skills were available in this session, so the
Supervisor wrote the change itself (Hard-Stop Gate 1 deviation, recorded here).
