# RUNBOOK — Personal Agentic Claude (Supervisor harness)
**Last updated**: 2026-08-15

> Operational runbook: how to deploy, verify, and recover this service. Written/appended by the `ship` skill after Stage 5 verification, and kept current by whoever last touched the deploy path. This is the document an operator opens at 3am — every command must be copy-pasteable and every check must have a pass condition.

---

## Service Identity

- **Name**: Personal Agentic Claude — Supervisor agent harness (agents, skills, hooks, templates)
- **Repo**: `git@github.com:thunderkds/personal-agentic-claude.git` (remotes `github` and `origin` both point here)
- **Deployment target**: Local developer machine (macOS, Linux, WSL) — per `PROJECT_SPEC.md:16`
- **Tech**: POSIX sh installer (`setup.sh`, `update.sh`, `lib/harness-fetch.sh`), Python 3 hooks under `.claude/hooks/`, Markdown agent/skill definitions
- **Owner / on-call**: hungnh1110@gmail.com

> **Distribution model (ADR-0001)**: there is no server and nothing to "deploy" in the usual sense.
> A release is **the state of `main` on GitHub**. Downstream repos consume it by cloning it into a
> temp dir and copying every `MANIFEST` path in (`setup.sh`), or by hash-comparing and selectively
> overwriting (`update.sh`). **Pushing `main` IS the deploy.** The tag is the rollback anchor.

---

## Deploy Procedure

Ordered steps to ship a release. Commands copy-pasteable.

1. **Pre-deploy checks**
   ```sh
   git branch --show-current                 # must print: main
   git status --short                        # must be empty (see note below)
   python -m pytest .claude/hooks/tests/ -q  # must print "N passed", exit 0
   bash scripts/smoke-install.sh             # must print "smoke-install.sh: PASS", exit 0
   ```
   Check exit codes **without a pipe** — `cmd | tail` always exits 0 and will hide a red suite.
   Confirm every in-scope task shows `- [x]` in the Done section of `PROJECT_KANBAN.md` and has a
   filled `verify` row in its `tasks/TASK_REVIEW_Txxx.md`.

2. **Tag the release** (the rollback anchor — do this *before* pushing)
   ```sh
   git tag -a vX.Y.Z -m "release vX.Y.Z — <task IDs>"
   ```

3. **Publish** — this is the deploy; downstream installs see the change the moment it lands
   ```sh
   git push github main
   git push github vX.Y.Z
   ```

4. **Post-deploy health check** — install from the *published remote*, not a local path
   ```sh
   T=$(mktemp -d) && cd "$T" && git init -q . && git commit -q --allow-empty -m init
   bash <(curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh)
   ```
   **Pass condition**: installer exits 0 and prints `Setup complete`; then
   ```sh
   test -f .claude/harness-lock.json && \
   grep -q "Complexity matrix in your role guide" templates/TASK_GUIDE_template.md && \
   grep -c '^| \*\*C[0-3]' .claude/agents/backend.md          # must print 4
   ```
   all succeed. Then `rm -rf "$T"`.

---

## Rollback Procedure

- **Trigger conditions**
  - The health-check install exits non-zero, or `Setup complete` never prints.
  - A fresh install produces a tree missing MANIFEST paths, or `harness-lock.json` is absent.
  - The hook suite fails from a clean clone of the published `main`.
  - Any downstream repo reports `update.sh` overwriting a file it should have prompted about.
- **Reverse steps** (in order)
  1. Move `main` back to the previous release tag and republish:
     ```sh
     git push github +<previous-tag>:main      # force-update main to the last good tag
     ```
     (A force push is the rollback here precisely because the "deployed artifact" is the branch tip.
     Prefer `git revert <merge-sha>` + a normal push if anyone else has already pulled.)
  2. Delete the bad tag so it cannot be installed by pin:
     ```sh
     git push github :refs/tags/vX.Y.Z && git tag -d vX.Y.Z
     ```
  3. Nothing to un-migrate: there is no database, no service, no state outside the consumer's repo.
- **Verify rollback**: re-run the §Deploy step-4 health check. Pass condition is the same, except
  the `templates/TASK_GUIDE_template.md` grep should match the **previous** release's content.

> **Downstream repos already updated are NOT rolled back by any of this.** They hold real copied
> files. Recovery there is `bash update.sh` against the restored `main`, per-file, with the conflict
> prompt.

---

## Health Checks & Dashboards

| Check | Command / URL | Pass condition |
|-------|---------------|----------------|
| Suite green | `python -m pytest .claude/hooks/tests/ -q` | `N passed`, exit 0, no pipe |
| Install smoke | `bash scripts/smoke-install.sh` | `smoke-install.sh: PASS`, exit 0 |
| Fresh install from remote | §Deploy step 4 | exits 0, `Setup complete`, lock file written |
| Pointer integrity | `grep -rn 'matrix in \`.claude/agents/general-agent-template.md\`' <install>` | only hit is `RETIRED_CLAUSE` in the test file |

- **Dashboards**: none — no runtime service exists.

---

## Common Failure Modes & Remediation

| Symptom | Likely cause | Remediation |
|---------|-------------|-------------|
| `curl \| sh` install prints "No local checkout detected" then works | Expected — `setup.sh` bootstraps a full clone because `$0` has no file location under a pipe (T038) | None; informational |
| Install fails at clone | Network, or `SUPERVISOR_REPO` points at a bad URL | Re-run with an explicit `SUPERVISOR_REPO=<url>` |
| `update.sh` exits non-zero with "conflict(s) could not be resolved" | Ran non-interactively over locally-customized files | Re-run `bash update.sh` in a real terminal and resolve per file |
| A fix to `CLAUDE.md` never appears downstream | **By design** — `CLAUDE.md` is outside `MANIFEST`; `setup.sh` copies it once and `update.sh:276` carries its lock entry over untouched | Downstream must merge the change into their own `CLAUDE.md` by hand |
| Merge blocked: "Tasks still In Progress" | The pipeline gate reads `PROJECT_KANBAN.md` in the **current checkout** before the merge runs | Close the row to Done in a **separate** tool call, on the branch being merged, then merge |

---

## On-Call / Escalation

1. **First responder**: hungnh1110@gmail.com (single-maintainer project)
2. **Escalate to**: n/a — if the harness is broken, downstream repos keep working on their installed copies; there is no outage
3. **Comms**: commit message + `memory/decisions.md` entry

---

## Release Log

| Version / Tag | Date | Scope (Task IDs) | Deployer | Outcome |
|---------------|------|------------------|----------|---------|
| v1.0.0 | 2026-08-15 | T070 (first tagged release; codifies the state of `main` at `238421c`) | hungnh1110@gmail.com | _pending operator execution_ |
