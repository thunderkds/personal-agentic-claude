# TASK_GUIDE — T135: The landing page references easy-verifier-mcp in a short "Verifier" section
**Date**: 2026-09-26
**Complexity Level**: C1
**Risk Level**: Low — one static HTML section plus drift tests; no harness file, no deploy config
**Priority**: P2
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `site/index.html` (sidebar nav + the `#repository-layout` / `#memory-system` sections for markup style) and `tests/test_site_content.py` (nav-link and external-asset tests)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-26: *"create a new sections that using verifier in the index page, https://personal-agentic-claude.vercel.app/, and refer to this repos with some strong highlight points https://github.com/thunderkds/easy-verifier-mcp.git"* — then, on scope: *"keep this small, just enough information to reference in mostly"*; placement: *"In the reference section maybe"*.

**Restated intent:**
> Add one short section to `site/index.html`, listed in the sidebar's **Reference** group, that
> introduces easy-verifier-mcp as a **companion tool** (a separate repo, not part of the kit), gives
> a few strong highlight points, and links to https://github.com/thunderkds/easy-verifier-mcp.
> It is mostly a reference: a lead paragraph, a short highlight list, the link. No setup guide.

**Honesty constraint (load-bearing):** the kit does **not** call easy-verifier-mcp anywhere today
(`grep -rli easy-verifier` over the repo → 0 hits). The section must not say or imply the kit uses,
ships, or requires it. Phrase it as something that pairs with the kit's Stage 4 review — e.g. "a
separate, no-LLM evidence engine you can run alongside Stage 4 review".

**Highlight source (use these facts only — from the easy-verifier-mcp README, 2026-09-26):**
- No LLM, no model API key — ratings are deterministic rules over cited metrics
- Seven independently callable dimensions: architecture, solution-fit, requirement-fidelity, code-quality, security, test-strategy, blast-radius
- Auditable coverage — a "found 4/6" is always shown with the sources it did not find
- Read-only and local — never executes the target repo's code, no outbound network, secrets redacted to a fingerprint
- Kit-aware mode — treats this kit's artifacts (`PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_*.md`, `memory/`) as ground truth; standalone mode elsewhere
- One core, three ways to run: CLI, MCP server (stdio), hardened Docker container

Pick **4–6** of these; keep each to one line.

**Out of scope:** wiring the verifier into any skill/hook; install/config instructions or code blocks
beyond at most one command; any other section; any image or external asset.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-26: "keep this small", "In the reference section")
- [x] Domain terms align: *companion tool*, *Reference nav group*, *Stage 4 review*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `site/index.html` — sidebar Reference group + a new `<section id="verifier">`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `site/index.html` has `<section id="verifier">` with an `<h2>` naming easy-verifier-mcp, placed with the other Reference sections (after `#memory-system`, before `#options`) | placement |
| 2 | The sidebar Reference group has a link `href="#verifier"` (existing nav tests stay green) | placement |
| 3 | The section links to `https://github.com/thunderkds/easy-verifier-mcp` with `target="_blank" rel="noopener noreferrer"`, matching the existing repo link | refer to repo |
| 4 | The section has 4–6 one-line highlights drawn only from the highlight source above; the whole section stays short (≤ ~20 lines of HTML) | strong highlights, keep small |
| 5 | The section states it is a separate tool and does not claim the kit uses/ships/requires it | honesty constraint |
| 6 | New tests in `tests/test_site_content.py`: section + nav link exist; repo URL present inside the section; the section text contains none of "the kit uses", "ships with", "built in", "required" | drift |

**Mutation controls:** **M1** — delete the nav `<li>` → AC2/AC6 test RED. **M2** — remove the repo link → RED. **M3** — insert "the kit uses easy-verifier" into the section → RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T135.md`. BEFORE: the verbatim sidebar Reference group and the `#memory-system` → `#options` boundary from `site/index.html` as it is now. Paste M1–M3 results in its "Negative cases hold" row.

---

## UI / Design Acceptance Criteria

- Reuse the page's existing markup patterns (`<p class="lead">`, plain `<ul>`); no new CSS, fonts, images or scripts.
- Long words (e.g. `requirement-fidelity`) must wrap at 375px width.

---

## Approach

**Pattern reference**: the header's existing GitHub link (`site/index.html` ~line 222) and the `#memory-system` section.

**Vital slice**: AC1–AC3, AC5. **Cut list**: comparison table of the seven dimensions; install/MCP config snippets; badges or screenshots.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | New Reference nav `<li>` + `<section id="verifier">` |
| `tests/test_site_content.py` | AC6 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json`, `.vercelignore` | Deploy config unchanged |
| `.claude/hooks/**`, `skills/**`, `agents/**` | No harness integration in scope |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Completion Checklist

- [ ] Implementation done; AC6 tests observed RED first
- [ ] M1–M3 pasted in the Evidence table
- [ ] All three UI Evidence rows filled
- [ ] `/verify` — user-run
