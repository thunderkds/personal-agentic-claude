# TASK_GUIDE — T132: The RUNBOOK says a push to `main` deploys the site
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — documentation plus one drift test; no deploy config change
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `RUNBOOK.md` § "Deploying the landing site", `vercel.json`, `.vercelignore`, `tests/test_vercel_config.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: *"yes"* — to filing the correction below.

**Observed defect (Supervisor, 2026-09-25):** `git push github tokenization-refactor:main` moved `main`
`be1b10a..4639ea3`; seconds later `https://personal-agentic-claude.vercel.app/` served a page
byte-identical to `main`'s `site/index.html` (`diff -q` → `live page == main`). No one ran the Vercel
CLI (it is not installed on this machine). So the Vercel project is connected to the GitHub repo and
deploys `main` automatically. The docs say the opposite:
- `RUNBOOK.md`: *"**This deploy is operator-run.** No agent, hook, or CI workflow triggers any of the commands below."*
- `PROJECT_SPEC_SITE.md:32`: *"No automated deploy from CI. The operator runs the deploy."*

It matters beyond wording: (a) anything pushed to `main` is public at once — the preview-before-`--prod`
step the RUNBOOK relies on does not exist on this path; (b) `.vercelignore` limits what the **CLI
uploads**, but a Git-connected build clones the whole repository on Vercel's side, so `memory/`,
`tasks/` etc. already reach Vercel's build infrastructure (still not served — only `site/` is output).

**Restated intent:**
> The RUNBOOK and site spec describe the deploy that actually happens — a push to `main` deploys
> production — state what `.vercelignore` does and does not protect on that path, and keep the CLI
> steps as the manual/rollback route. A drift test fails if the RUNBOOK goes back to calling the deploy
> operator-only.

**Out of scope:** disconnecting the Git integration or changing Vercel settings (operator's call, in the
Vercel dashboard); `vercel.json`/`.vercelignore` changes; any harness file.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-25)
- [x] Domain terms align: *production deploy*, *preview*, *Git integration*, *CLI upload*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `RUNBOOK.md` § "Deploying the landing site"

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | RUNBOOK § "Deploying the landing site" opens with: a push to `main` on GitHub deploys production automatically (Vercel Git integration), observed 2026-09-25 with the evidence above; the "operator-run … No agent, hook, or CI workflow triggers" sentence is removed | defect |
| 2 | It says what the automatic path skips — no preview before production — and how to get one (push a non-`main` branch: Vercel builds a preview per branch **if** the integration's defaults are on; mark this "confirm in the Vercel dashboard" rather than asserting it) | (a) |
| 3 | It states `.vercelignore` governs CLI uploads only; on the Git path Vercel clones the full repo, so repo contents reach Vercel's build side while only `site/` is served. Name the operator's option to change that (disconnect Git integration, or accept) without choosing for them | (b) |
| 4 | The existing CLI steps stay, relabelled as the manual/rollback route; the step-4 verify command stays | no regression |
| 5 | `PROJECT_SPEC_SITE.md:32` corrected to match | defect |
| 6 | New test in `tests/test_vercel_config.py`: the RUNBOOK section mentions that a push to `main` deploys, and does not contain "operator-run" | drift |

**Mutation controls:** **M1** — restore the "operator-run" sentence → AC6 test RED. **M2** — delete the push-to-`main` sentence → RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_vercel_config.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T132.md`. BEFORE: the two quoted sentences above, verbatim from the files.

---

## Approach

**Pattern reference**: existing assertions in `tests/test_vercel_config.py`.

**Vital slice**: AC1, AC3, AC6. **Cut list**: Vercel API checks; dashboard screenshots.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `RUNBOOK.md` | § Deploying the landing site |
| `PROJECT_SPEC_SITE.md` | Constraint line 32 |
| `tests/test_vercel_config.py` | AC6 test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `vercel.json` | Config unchanged |
| `.vercelignore` | Config unchanged |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Completion Checklist

- [ ] Implementation done; AC6 test observed RED first
- [ ] M1–M2 pasted in `tasks/TASK_REVIEW_T132.md`
- [ ] UI Evidence rows: ☐ N/A — no UI change
- [ ] `/verify` — user-run
