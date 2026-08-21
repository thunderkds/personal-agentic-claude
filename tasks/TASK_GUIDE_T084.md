# TASK_GUIDE — T084: Vercel deploy configuration + runbook
**Date**: 2026-08-21
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC_SITE.md` (this task's spec, not `PROJECT_SPEC.md`)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C1 → apply the C1 row of the Complexity matrix; single known surface, no codebase-map read needed

---

## Requirement (Pillar 1)

> "I think using vercel to deploy a static page will be good to go. This is the release for version 1 of this kit"

**Restated intent**:
> Make `site/` deployable to Vercel with one operator command, with the deploy steps and the rollback
> written down — configuration and runbook only.

**Out of scope**:
- **Running the deploy.** No agent authenticates to, pushes to, or triggers Vercel. The operator executes; this task hands them the exact commands. Deploying is outward-facing and is the user's call.
- Any CI workflow, GitHub Action, or auto-deploy-on-push wiring.
- Custom domain, DNS, environment variables, redirects beyond what a one-page static site needs.
- Editing `site/index.html` — T083 owns it.

**Requirement Refs**: N/A — traces to the user request above, recorded in `PROJECT_SPEC_SITE.md`.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-21)
- [x] Domain terms align with `PROJECT_SPEC_SITE.md`
- [x] Every AC traces to the Requirement
- [x] Requirement Refs recorded N/A with reason

---

## Dependencies & Reachability

**Depends on**: T083 — `site/index.html` must exist; there is nothing to configure a deploy for until it does.

**Entry point**: `vercel.json` — read by the Vercel CLI/platform at the repo root.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `vercel.json` exists at the repo root, is valid JSON, and declares `site` as the output/public directory with **no build command** | "static page", no-build stack decision |
| 2 | The config does not reference any framework preset, install command, or node version — a static-file deploy only | non-goals |
| 3 | `RUNBOOK.md` gains a "Deploying the landing site" section with the exact operator commands: the one-time `vercel link`, the preview deploy, and the production deploy | "guide", operator-executes constraint |
| 4 | That section also gives the **rollback** step (promote the previous deployment) and how to verify a deploy served the current page | `ship`-skill convention: every deploy plan carries a rollback |
| 5 | The runbook states explicitly that the deploy is operator-run and that no agent or hook triggers it | outward-facing-action policy |
| 6 | `tests/test_vercel_config.py` asserts AC1 and AC2 by parsing `vercel.json`, and asserts the output dir it names is a directory that actually exists in the repo | Gate 5 |
| 7 | Full suite passes with 0 regressions against the post-T083 baseline | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | `vercel.json` as committed | parses as JSON; names `site` as output dir; declares no build command | automated test |
| 2 | The output dir named in `vercel.json` | exists on disk and contains `index.html` | automated test |
| 3 | **Mutation control M1** — point `vercel.json` at a non-existent dir (`site-typo`) | the AC6 existence test goes **RED**; revert after observing | Supervisor re-runs manually |
| 4 | **Mutation control M2** — add a `"buildCommand"` key | the no-build assertion goes **RED**; revert after observing | Supervisor re-runs manually |

> M1 and M2 are mandatory. A config test that only checks "the file parses" would pass against a
> config pointing at nothing — which is precisely the failure mode that reaches production silently.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_vercel_config.py -q && python3 -m pytest tests/ -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T084.md`.

---

## UI / Design Acceptance Criteria

**N/A — pure infrastructure task.** No UI component: this task produces a JSON config and a runbook
section. All three Gate 6 evidence rows are ☐ N/A for this reason. (The page's own UI evidence is
T083's, and is not re-verified here.)

---

## Approach

**Pattern reference**: `RUNBOOK.md`'s existing entries — imitate their structure (what/when/exact
commands/rollback). The `ship` skill's output format is the house style for a deploy plan.

**Vital slice**: the config plus the three operator commands. Everything else is prose.

**Cut list**: preview-per-branch wiring, custom domain, deploy notifications — none requested, and each
adds a thing to maintain for a one-page site.

Keep `vercel.json` minimal. For a no-build static site the whole file is a couple of keys; resist adding
`rewrites`/`headers` blocks speculatively. If a `cleanUrls`-style nicety is wanted, note it in the cut
list rather than adding it unrequested.

---

## Edge Case Checklist

- [ ] Vercel's schema has changed across versions (`builds` vs `outputDirectory`); use the current documented static form and name which one you used and why in the report — do not guess between them silently
- [ ] The repo root is not the site root — a config that defaults to root would deploy the whole repo, publishing `memory/`, `tasks/`, and `reports/`. AC1 exists specifically to prevent that; call it out in the runbook
- [ ] `reports/` is gitignored but `memory/` is not — a mis-scoped deploy would publish project memory. Treat scoping as the security-relevant part of this task
- [ ] The runbook must not embed a Vercel token, project ID, or org ID

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `vercel.json` | New — static deploy config |
| `RUNBOOK.md` | New section: deploying the landing site (deploy + verify + rollback) |
| `tests/test_vercel_config.py` | New — AC6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/**` | T083 owns the page |
| `README.md` | T085 owns it |
| `.github/**`, any CI config | Auto-deploy is an explicit non-goal |
| `PROJECT_KANBAN*.md`, `memory/**` | Supervisor-only |

---

## Test Plan

`tests/test_vercel_config.py`: parse `vercel.json`; assert valid JSON; assert the declared output
directory is `site`; assert that directory exists and contains `index.html`; assert no build/install
command key is present. Then the full suite for regressions, then M1/M2.

Manual (operator, at Stage 5 — not this agent): run the preview deploy from the runbook and confirm the
served page matches local `site/index.html`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] M1 and M2 each observed RED with the failing assertion pasted, then reverted
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: **N/A** — Low risk. But the deploy-scope edge case above is security-relevant; state in the report which paths the config would publish
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T084.md` (Gate 5)
- [ ] UI/Design rows: ☐ N/A ×3 with the justification above (Gate 6)
- [ ] **Did not run any deploy** — confirm explicitly
- [ ] Supervisor notified: ready for Stage 4 review
