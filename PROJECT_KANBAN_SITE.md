# PROJECT_KANBAN — Kit Landing Site (v1)

> Separate board per Hard-Stop Gate 4: the static site deploys to Vercel, a different target from
> the harness itself. Harness tasks live on `PROJECT_KANBAN.md` and are never mixed in here.
> Spec: `PROJECT_SPEC_SITE.md`.
>
> Task IDs stay in the `Txxx` namespace (shared, monotonic across both boards) because
> `pre_agent_validate_guide.py` and `lib/task_context.py:resolve_task_id` both parse that exact
> pattern. A `S001`-style ID would silently defeat spawn validation.

## Todo

- [ ] **T084** — **Vercel deploy configuration + runbook.** `vercel.json` pinning the static output to `site/`, no build command, plus a runbook section giving the operator the exact deploy commands. The Supervisor plans and de-risks this; **the operator executes the deploy** — no agent pushes to an external host. Depends on T083 (nothing to deploy until the page exists) | Common-Infrastructure-Agent | C1 | Risk: Low | P0 | Registered 2026-08-21

## In Progress

- [ ] **T083** — **Static landing page for the kit (`site/index.html`).** One page, plain HTML/CSS, no build step, no JS framework. Sections: what the kit is, the 5-stage pipeline, agent roster (4 spawnable roles + the shared base template), skill roster (30, grouped by pipeline stage), enforcement hook table (8 hooks with their real wiring and whether each blocks or advises), install + update commands, prerequisites. Content must be derived from source files, never from `README.md` prose — the README is known to carry two false hook claims (T081). Gate 5 test is `tests/test_site_content.py`, which asserts every `.claude/skills/` dir, every agent `name:`, and every hook in `.claude/settings.json` appears on the page, and that the step-limit default quoted on the page equals `pre_agent_step_limit.py`'s `STEP_LIMIT` literal — so a future skill addition fails CI instead of shipping a stale page | Frontend-Implementer | C2 | Risk: Low | P0 | Registered 2026-08-21 | **In Progress** — Stage 3 started 2026-08-21, worktree `wt-t083` on `feat/t083-site`

## Ready for Review

## Done

## Blocked

| Task | Blocked by | Since |
|------|-----------|-------|
