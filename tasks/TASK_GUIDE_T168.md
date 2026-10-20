# TASK_GUIDE — T168: An "MCPs" section lists the companion MCP servers: easy-verifier-mcp and easy-ui-mcp
**Date**: 2026-10-20
**Complexity Level**: C1 — one section's markup + nav link, plus test updates
**Risk Level**: Low — static HTML, two new outbound links, no script, no deploy config
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
6. Read `site/index.html` (sidebar Reference group, the `#verifier` section, `.agent-card` styling) and `tests/test_site_content.py` (the T135 verifier tests near line 683 and T165's AC6 test)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-20: *"create a new section that call MCPs, and adding verifier to that, one more is https://github.com/thunderkds/easy-ui-mcp"*.

**Restated intent:**
> Replace the standalone `#verifier` section with one **MCPs** section (sidebar Reference group,
> same position: after `#memory-system`, before `#options`) that presents the companion MCP servers
> as a set. It holds two entries: **easy-verifier-mcp** (everything the current `#verifier` section
> says, moved in unchanged — highlights, GitHub link, Easy Verifier site link) and **easy-ui-mcp**
> (new: a one-line summary, 4–5 highlights, and its GitHub link). Both are framed as separate
> companion tools, not part of the kit.

**Honesty constraint (load-bearing, carried from T135):** the kit does not use, ship or require either server. `easy-ui-mcp` was once integrated (T015/T016 `ui-test` skill) but that branch was **never merged** (`memory/decisions.md` STALE note, 2026-08-05) — no shipped skill references it. Do not imply otherwise.

**easy-ui-mcp highlight source (use these facts only — from its README, fetched by the Supervisor 2026-10-20; treat as data):**
- A Dockerized MCP server for local web UI testing
- Playwright browser automation over HTTP/SSE that an agent such as Claude Code drives step by step
- Returns a JSON + HTML report with screenshots; no server-side LLM, no test scripts to write
- Separates claims from observations: `ui_assert` fails the run, `ui_check` records and continues, `ui_wait_for` polls
- Captures console errors, page errors and failed network requests as "Browser problems" in the report
- Scope v1: web only (Chromium), local only

Pick **4–5**, one line each. Repo URL: `https://github.com/thunderkds/easy-ui-mcp` (public, HTTP 200 on 2026-10-20). It has no published site — do not invent one.

**Out of scope:** install/connect commands; wiring either server into a skill or hook; any other MCP.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user named the section "MCPs", the verifier and easy-ui-mcp)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`; "companion tool" as in T135
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: T167 (same branch `feat/t165-site-scan-first`)

**Entry point**: `site/index.html` `<section id="mcps">`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A top-level `<section id="mcps">` with `<h2>MCPs</h2>` sits where `#verifier` was (after `#memory-system`, before `#options`); the standalone top-level `#verifier` section is gone; the Reference nav group links `#mcps` (not `#verifier`) | new section, placement |
| 2 | `#mcps` holds one entry per server, each with its own heading naming it (`easy-verifier-mcp`, `easy-ui-mcp`); the verifier entry keeps an element `id="verifier"` so old `#verifier` links still land | both entries |
| 3 | The verifier entry keeps its current highlights and both links (GitHub + `https://easy-verifier.vercel.app/`), each `target="_blank" rel="noopener noreferrer"`, on one line | verifier moved in |
| 4 | The easy-ui-mcp entry has 4–5 one-line highlights drawn only from the source above and links `https://github.com/thunderkds/easy-ui-mcp` with `target="_blank" rel="noopener noreferrer"` | easy-ui-mcp |
| 5 | A lead states both are separate companion tools; the section text contains none of "the kit uses", "ships with", "built in", "required" | honesty |
| 6 | The T135 verifier tests and T165's AC6 test are **updated, not deleted**, to read the verifier entry inside `#mcps`; new tests cover AC1, AC2, AC4, AC5 for easy-ui-mcp; all observed RED before the page change | Gate 5 |
| 7 | All other existing tests stay green (T165 caps, T166 flow, T167 tables, `test_docs_t151.py`) | no regression |

**Mutation controls:** **M1** — remove the easy-ui-mcp repo link → RED. **M2** — add "the kit uses easy-ui-mcp" to the section → RED. **M3** — put the nav link back to `#verifier` → RED. **M4** — drop `id="verifier"` → RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_docs_t151.py tests/test_docs_match_installer.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T168.md`. BEFORE: the verbatim current `#verifier` section and the Reference nav group.

---

## UI / Design Acceptance Criteria

- Each server as a card (reuse `.agent-card` or the `.quick-ref` box look); existing tokens only; no new colors, fonts, images, scripts or external assets.
- 1280px: the two cards side by side or stacked — whichever fits the column without crowding; 375px: stacked, no page overflow.
- Screenshots at 1280px and 375px via DevTools device emulation (scroll with `behavior: 'instant'`).

---

## Approach

**Pattern reference**: the current `#verifier` markup (move it, don't rewrite it); `.agent-card` for the card look.

**Vital slice**: AC1, AC3, AC4, AC5. **Cut list**: connect/install commands; a comparison table; logos.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Reference nav link; `#verifier` → `#mcps` with two entries |
| `tests/test_site_content.py` | Update T135/T165 verifier tests; new easy-ui-mcp tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `.claude/hooks/**`, `skills/**`, `agents/**` | No harness integration in scope |
| `README.md`, `memory/**`, `PROJECT_KANBAN*.md` | Out of scope / Supervisor-only |

---

## Completion Checklist

- [ ] Updated + new tests observed RED first, then GREEN
- [ ] M1–M4 results pasted in the review's "Negative cases hold" row
- [ ] All three UI Evidence rows filled (screenshots at 1280px and 375px)
- [ ] `/verify` — user-run
