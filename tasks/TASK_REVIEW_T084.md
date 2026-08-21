# TASK_REVIEW — T084: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T084.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☑ pass | User-run `/verify` 2026-08-21 — **pass**, driven by the Supervisor. **The deploy itself was NOT exercised**: no Vercel CLI on the machine, none installed or authenticated, because deploying is outward-facing and the operator's call. Two surfaces were drivable and were driven. (1) `.vercelignore` uses gitignore syntax, so the real matcher ran via `git check-ignore` against a scratch tree mirroring this repo — exactly two files survive upload, `site/index.html` and `vercel.json`; `memory/decisions.md`, `memory/event-trace/`, `tasks/`, `docs/`, `PROJECT_KANBAN.md`, `README.md`, `.claude/hooks/` all EXCLUDED. Probed under growth: new files inside `site/` (incl. a new nested dir) are admitted automatically, while a brand-new top-level dir and `.env` are excluded with no edit to the file — fail-closed in both directions. (2) The runbook's step-4 verification command ran verbatim against a served copy (`MATCH`) and against a deliberately wrong page (`NO MATCH`) — it discriminates rather than printing MATCH regardless. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: (captured 2026-08-21T08:51:21Z, before any implementation commit)

`vercel.json` does not exist:
```
$ ls vercel.json
ls: cannot access 'vercel.json': No such file or directory
```

`RUNBOOK.md` current end (no "Deploying the landing site" section exists yet — file ends with the
Release Log table):
```
## Release Log

| Version / Tag | Date | Scope (Task IDs) | Deployer | Outcome |
|---------------|------|------------------|----------|---------|
| v1.0.0 | 2026-08-15 | T070 (first tagged release; codifies the state of `main` at `238421c`) | hungnh1110@gmail.com | _pending operator execution_ |
```

Full-suite regression baseline:
```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
688 passed in 9.41s
```

**AFTER**:

`vercel.json` exists and parses:
```
$ cat vercel.json
{
  "outputDirectory": "site"
}
```

`RUNBOOK.md` gains a "Deploying the landing site" section (link/preview/production/verify/rollback,
operator-run) between the harness's own Deploy Procedure/Rollback Procedure and
"## Health Checks & Dashboards".

Full-suite regression run, post-change:
```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
693 passed in 8.45s
```
(688 baseline + 5 new `tests/test_vercel_config.py` tests = 693; 0 regressions.)

**DELTA**: An operator can now run `vercel link` / `vercel` / `vercel --prod` from the repo root and
have Vercel publish only `site/` (not the project's memory/task files), with a written rollback
(`vercel promote <previous-deployment-url>`) instead of improvising one at incident time.

**WITNESS**: common-infrastructure sub-agent (T084), 2026-08-21 — commands run directly in the
`wt-t084` worktree; not yet independently re-run by the Supervisor/reviewer.


---

## Stage 5 `/verify` findings (2026-08-21, user-run)

1. **⚠️ The deploy is unverified and unverifiable from here.** Whether Vercel honours
   `outputDirectory` for a build-less static project is a property of the platform, not of this repo.
   Everything around it is verified: valid JSON, names a directory that exists and contains
   `index.html`, declares no build/install/framework key, upload scope resolves as documented. **The
   operator must run the preview deploy (`vercel`) before `vercel --prod`** — the runbook orders it
   that way for exactly this reason, and it is the first real test of the one claim verification
   could not reach.
2. **The gitignore re-inclusion trap did not bite, and the reason is load-bearing.** `*` excludes the
   `site` directory itself, and git cannot re-include a file whose parent directory is excluded — so a
   lone `!site/**` would have been **silently inert** and the deploy would have uploaded nothing. The
   file re-admits `!site/` *before* `!site/**`, which is what makes it work. Recorded because the two
   lines look redundant and someone will eventually delete one.
3. Probe that held: `.env` at repo root is excluded. Not present today; covered by the deny-all rather
   than by anyone having thought of it.
4. `vercel ls` in the rollback step lists deployments across the whole Vercel account, not filtered to
   this project. Fine with one project, mildly noisy later.

## Stage 4 note — the P1, and why the agent's reasoning was right but landed short

The implementer reported that `memory/`, `tasks/` and `PROJECT_KANBAN*.md` are "never in the published
output." **That was true and still left the hole**: `outputDirectory` scopes what Vercel *serves*, not
what the CLI *uploads*. The Vercel CLI transmits the project source tree to Vercel's build
infrastructure on every deploy, so this repo's project memory — decisions, learnings, event traces —
would have left the machine on every `vercel` invocation and been retained by a third party. Never at
a public URL, which is precisely why neither the config nor the original runbook paragraph surfaced it.

Fixed with `.vercelignore` as an **allowlist** (bare `*`, then re-admit `site/` and `vercel.json`
only). A denylist was the obvious shape and was rejected: it fails open the first time anyone adds a
directory — the same failure mode as the documentation drift this whole release exists to fix.
