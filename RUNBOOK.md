# RUNBOOK — Personal Agentic Claude (Supervisor harness)
**Last updated**: 2026-09-05

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
   curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh
   ```
   The installer takes no options. It shows a menu (`1) Install  2) Cancel`), the CLI menu
   (`1) Claude Code  2) Codex`), the project-type menu (`1) New project  2) Existing / legacy
   project`), then a plan ending `Proceed? [Y/n]`: in a terminal, press Enter at every prompt to accept
   the defaults (Install, the CLIs found on `PATH` — Claude Code if none — New project, Proceed).
   There is no packs question: every pack ships inactive in `packs/` (T116). To run the check with no terminal instead — it then prints and takes the same defaults —
   wrap the same line: `setsid -w sh -c '<the line above>' </dev/null`.
   **Pass condition**: installer exits 0 and prints `Setup complete`; then
   ```sh
   test -f .claude/harness-lock.json && \
   test ! -d .claude/hooks/tests && \
   grep -q "Complexity matrix in your role guide" templates/TASK_GUIDE_template.md && \
   grep -c '^| \*\*C[0-3]' .claude/agents/backend.md          # must print 4
   ```
   all succeed (the `test ! -d` line fails the check if a release ships the kit's own test suite again). Then `rm -rf "$T"`.

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

### v2.0.0 — additional rollback exposure (canon relocation)

v2.0.0 moves canon from `.claude/agents/` and `.claude/skills/` to plain root and leaves committed
**relative symlinks** behind. That changes what a rollback has to restore in a downstream repo:

- A v2 install replaced two real directories with symlinks. Rolling `main` back to `v1.1.0` and
  running an update (the one install command, action **Update**) does **not** automatically turn
  those symlinks back into directories — Update compares hashes per MANIFEST path, and a symlink is
  not a MANIFEST path.
- Recovery in an affected downstream repo is manual and must be done before re-running the v1
  installer: `rm .claude/agents .claude/skills` (they are symlinks — this removes the links, not
  the canon), then run the install command from the restored `main` inside the repo. If it shows the
  action menu, choose **Reinstall**; v1's `setup.sh` has no menu and reinstalls directly.
- **Check before you rollback**: `ls -l .claude/agents` in the downstream repo. A `->` in the
  output means the repo is on v2 layout and needs the manual step above.

> **Downstream repos already updated are NOT rolled back by any of this.** They hold real copied
> files. Recovery there is the one install command against the restored `main`, run inside the repo
> in a terminal, choosing **Update** — per-file, with the conflict prompt.

---

## Deploying the landing site

**Deployed URL**: [`https://personal-agentic-claude.vercel.app/`](https://personal-agentic-claude.vercel.app/)
(verified live 2026-09-06 — HTTP 200, served HTML byte-identical to this repo's `site/index.html`).

**A push to `main` on GitHub deploys production automatically** (Vercel Git integration).
Observed 2026-09-25: `git push github tokenization-refactor:main` moved `main` `be1b10a..4639ea3`,
and seconds later the live URL served a page byte-identical to `main`'s `site/index.html` — with no
Vercel CLI involved (it is not installed on the pushing machine). Anything merged to `main` is
therefore public at once. **That path has no preview step**: nothing is staged before production.
To get a preview, push a non-`main` branch — Vercel builds a preview per branch *if* the
integration's defaults are on (confirm in the Vercel dashboard; not verified here).

Separate from the harness's own release above: this deploys `site/index.html` (the public marketing
page) to Vercel. Config lives in `vercel.json` at the repo root; it declares `site` as the
**output directory only** and sets no build/install/framework command — this is a static-file
deploy, not a framework build.

**Scope of what gets published**: only the contents of `site/` (currently `site/index.html`) are
served. `vercel.json`'s `outputDirectory` is the one thing standing between this deploy and
publishing the whole repo root — `memory/`, `tasks/`, `PROJECT_KANBAN*.md` and every other
project-management file stay off the public URL because they are outside `site/`, not because
Vercel is trusted to guess correctly.

**Scope of what gets uploaded is a separate question, and `outputDirectory` does not answer it.**
**On the automatic Git path, whether `.vercelignore` limits what Vercel keeps is not established.**
Vercel builds from its own clone of the GitHub repository. Its docs say the *built-in* default
exclusions (`.git`, `.env.local`, …) apply only to CLI deployments
([build features](https://vercel.com/docs/builds/build-features#ignored-files-and-folders)); the
[`.vercelignore` page](https://vercel.com/docs/deployments/vercel-ignore) does not say whether it is
applied to Git deployments. Check it on a real deployment: open the deployment in the Vercel
dashboard and append `/_src` to its URL (Source view, team-only) — if `memory/` or `tasks/` appear
there, the repository's full contents are retained by Vercel on every push to `main`. Either way
only `site/` is served. If they appear, the operator may disconnect the Git integration or accept
it — this file does not choose.
For the manual CLI route below, the Vercel CLI transmits the project source tree to Vercel's build infrastructure on every deploy;
`outputDirectory` governs only what is *served* from the result. Without `.vercelignore`, this
repo's `memory/` (project decisions, learnings, event traces), `tasks/`, and `docs/` would be sent
to a third party and retained there on every `vercel` invocation — never at a public URL, but off
this machine all the same. `.vercelignore` is therefore an **allowlist**: it denies everything with
a bare `*` and re-admits only `site/` and `vercel.json`. A denylist was rejected because it fails
open the first time anyone adds a directory. `tests/test_vercel_config.py` asserts the allowlist
form and asserts that `memory/`, `tasks/`, `docs/`, and `PROJECT_KANBAN*` are never re-admitted.

**Manual / rollback route.** The commands below are not the normal path — a push to `main` already
deploys. They are for a deliberate hand-run deploy or a rollback, from a terminal with the Vercel CLI
installed and authenticated.

1. **One-time link** (per machine, per project) — associates this repo with a Vercel project:
   ```sh
   vercel link
   ```

2. **Preview deploy** — ships a throwaway preview URL, does not touch production:
   ```sh
   vercel
   ```
   Open the printed preview URL and confirm it renders the same content as local `site/index.html`.

3. **Production deploy**:
   ```sh
   vercel --prod
   ```

4. **Verify the deploy served the current page**:
   ```sh
   curl -s <production-url> | grep -q "$(grep -m1 '<title>' site/index.html)" && echo "MATCH"
   ```
   `MATCH` means the served page contains the same `<title>` as the local file. For a stronger
   check, diff the full response against `site/index.html` directly.

**Rollback** — promote the previous deployment instead of re-deploying an old commit:
```sh
vercel ls                          # list deployments, newest first
vercel promote <previous-deployment-url>
```
This re-points production at the last known-good deployment without a new build. Re-run the step-4
verification against the production URL afterward.

No Vercel token, project ID, or org ID is stored in this file or in `vercel.json` — the CLI reads
those from its own local auth state (`vercel login` / `.vercel/` created by `vercel link`, which is
gitignored).

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
| An update exits 2 with "conflict(s) could not be resolved" | Ran with no terminal over locally-customized files (no terminal = Update, every edit kept) | Re-run the install command in a real terminal, choose **Update**, and resolve per file |
| A fix to `CLAUDE.md` doesn't reach a project | `update.sh` (T110) delivers `CLAUDE.md` from the same source (`CLAUDE.md` or `CLAUDE_LEGACY.md`) the project was installed with, recorded as `claude_md_source` in `.claude/harness-lock.json`. It overwrites only when the project's `CLAUDE.md` is unedited since install; an edited `CLAUDE.md` goes through the same conflict prompt (`[o]/[s]/[v]`) as any other file | If prompted, `[v]iew` the diff and `[o]verwrite` to take the fix, or `[s]kip` to keep your edits and merge by hand |
| `setup.sh`/`update.sh` exits 2 and prints a `"hooks"` block | `.claude/settings.json` is invalid JSON or a symlink, or `python3` is not on `PATH` (every kit hook runs as `python3 …`) | Fix the JSON / replace the symlink with a real file / install `python3`, then re-run. The file is left byte-identical, so the printed block can also be pasted in by hand |
| `*.bak` files or folders (e.g. `CLAUDE.md.bak`, `templates.bak/`, `.bak.1`) appear after install | The project already had those paths with different content; install moved them aside instead of overwriting them (T112), and named each one in a `[warn]` line | Compare each backup with the kit's copy and merge what you need by hand, then delete the backup. If `.claude/hooks.bak` appears, repoint any of your own hook entries in `.claude/settings.json` at it |
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
| v1.1.0 | 2026-08-21 | T083, T084, T085, T087, T088 — public landing site, Vercel deploy config, README 477→55, site reference content, PACK.md flag fix | hungnh1110@gmail.com | _pending operator execution — site deploy not yet run_ |
| v2.0.0 | 2026-09-05 | **BREAKING.** T086, T089, T090–T104 — canon relocated to plain root (`agents/`, `skills/`) with `.claude/*` kept as committed relative symlinks (T096, DDR-0007); per-harness install projection and `setup.sh --harness codex|claude` (T097/T098); provider adapters `AGENTS.md` + `.cursor/rules/agent-base.mdc` (T090/T091); merge-gate and quoted-span hook fixes (T094/T095/T099); Response Standard inlined into `CLAUDE.md` (T100/T103); docs and baseline reconciliation (T101/T102); site names the shipping version (T104) | hungnh1110@gmail.com | **Deployed 2026-09-05.** `main` fast-forwarded `a586000` → `b6ef559` (0 divergent commits, clean FF — this is the first release to actually reverse the 2026-08-25 v2/main freeze; `main` is now the v2.0.0 codebase). Tagged `v2.0.0`, pushed `main` + tag. Health check PASS: fresh `curl \| sh` install from the published `main` exited 0, printed `Setup complete`, and all three post-install assertions held (`harness-lock.json` present, `TASK_GUIDE_template.md` complexity-matrix reference found, `agents/backend.md` has 4 complexity rows) |
