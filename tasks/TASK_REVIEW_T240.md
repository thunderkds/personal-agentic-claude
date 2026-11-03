# TASK_REVIEW — T240: Rename the repo from personal-agentic-claude to easy-kit

> Sibling of `tasks/TASK_GUIDE_T240.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Implementer results (common-infrastructure, 2026-11-03)

### AC 1 — D1 redirect results

Probed on the real rename, not a throwaway; user chose this. The user renamed `thunderkds/personal-agentic-claude`
to `thunderkds/easy-kit` on github.com on 2026-11-03. Probes run by the Supervisor at 2026-11-03T07:44:53Z:

```
== https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh
HTTP/2 200
== https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/update.sh
HTTP/2 200
== https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh
HTTP/2 200
== https://github.com/thunderkds/personal-agentic-claude
HTTP/2 301
location: https://github.com/thunderkds/easy-kit
HTTP/2 200
== git https clone (old name)
1d9669d board+memory: T235 Done
== ssh ls-remote (old name)
1d9669dfa53ccbf81bbe6dd849746734f826881b	HEAD
```

Re-checked by common-infrastructure at 2026-11-03T07:54:16Z: `curl -sIL https://github.com/thunderkds/personal-agentic-claude`
→ `HTTP/2 301`, `location: https://github.com/thunderkds/easy-kit`, `HTTP/2 200`.

**User warning (Edge Case):** the redirect lasts only while no repo exists at `thunderkds/personal-agentic-claude`.
If anyone (the user included) creates a new repo with that name, or forks into that name, GitHub ends the
redirect. Then every old install line, every old `update.sh`, and every old checkout's fetch URL break.
Do not reuse the old name.

### AC 3 — an old install reaches the renamed repo (real network, published `main`)

Old kit scripts = `setup.sh`, `update.sh`, `lib/` from `1dd90fe9` (before this task), extracted with `git archive`.
No terminal (`setsid -w … </dev/null`), so every prompt takes its safe default.

```
2026-11-03T07:49:53Z
56:  BOOTSTRAP_REPO="${SUPERVISOR_REPO:-https://github.com/${GITHUB_USERNAME:-thunderkds}/personal-agentic-claude.git}"
87:    SUPERVISOR_REPO="https://github.com/${GITHUB_USERNAME}/personal-agentic-claude.git"
--- old setup.sh install
[info]  Using repo: https://github.com/thunderkds/personal-agentic-claude.git
[info]  Setup complete. Easy Kit copied into …/scratchpad/ac3-proj
lock-present
--- old update.sh
exit=0
[info]  Using repo: https://github.com/thunderkds/personal-agentic-claude.git
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
kit_commit 1d9669d
```

`kit_commit 1d9669d` is the head of `thunderkds/easy-kit` `main`: the old URL reached the renamed repo.

The old public install line, then this branch's `update.sh` on that install:

```
2026-11-03T07:51:55Z
--- old install line (piped, old raw URL)
exit=0
[info]  Using repo: https://github.com/thunderkds/personal-agentic-claude.git
[info]  Setup complete. Easy Kit copied into …/scratchpad/ac3-new
--- new update.sh (branch) on that install
exit=0
[info]  Using repo: https://github.com/thunderkds/easy-kit.git
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
--- new fork path, user without an easy-kit fork
https://github.com/octocat/personal-agentic-claude.git
--- canonical
https://github.com/thunderkds/easy-kit.git
```

Fork path (Edge Case `SUPERVISOR_REPO` / `GITHUB_USERNAME`): `SUPERVISOR_REPO` still wins unchanged.
A `GITHUB_USERNAME` fork is tried as `<user>/easy-kit.git` first (`git ls-remote`, `GIT_TERMINAL_PROMPT=0`,
so a missing repo fails fast and never asks for a password). If that fails, `kit_repo_url` falls back to
`<user>/personal-agentic-claude.git`, because a fork made before the rename keeps the old name. The
canonical `thunderkds` repo needs no probe. The `octocat` line above is a real probe: no `octocat/easy-kit`
exists, so it fell back.

### AC 4 — D4: what must change for Vercel and the family sites (nothing changed here)

1. **The new subdomain is taken.** `https://easy-kit.vercel.app/` answers `HTTP/2 200` with
   `<title>EasyKit - Free Online Developer Tools</title>` (probed 2026-11-03T07:54:16Z): it is another
   party's project. Renaming the Vercel project to `easy-kit` cannot get that URL. The user chooses:
   keep `personal-agentic-claude.vercel.app`, pick another free `*.vercel.app` name, or add a custom domain.
2. **The Vercel project** (dashboard, user only): if renamed, keep the old URL answering. A renamed
   Vercel project does not keep its old `*.vercel.app` alias by default; add the old one as a domain
   alias that redirects, or old links break.
3. **The Vercel Git connection**: confirm in the dashboard (Project → Settings → Git) that it shows
   `thunderkds/easy-kit` and that a push to `main` still deploys. Not verified here.
4. **This repo**, once a new URL exists (not before — the old URL is live, so it stays now):
   `README.md:21,59,75`, `RUNBOOK.md:140` (twice), `site/index.html:50,212`, `site/docs.html:200,216`,
   `tests/test_site_content.py:1886`; then drop `VERCEL_HOST` from `tests/test_repo_name.py`.
5. **Family sites linking `https://personal-agentic-claude.vercel.app/`** (live files, read-only grep
   2026-11-03, `~/workspace/pets/hungnguyen111/`):
   - `easy-ui-mcp`: `site/index.html:177,192`, `test/site.test.ts:222`
   - `easy-memory-mcp`: `site/index.html:263,278`, `tests/test_site_page.py:35`
   - `easy-personal-mcp`: `site/index.html:211,422`, `web/src/App.jsx:52`, `web/src/App.test.jsx:400`,
     `scripts/check_static.py:31`, `tests/test_site_content.py:32,39,477`, `tests/test_web_toolchain.py:119`,
     `PROJECT_SPEC_SITE.md:31`
   - `easy-verifier-mcp`: `site/index.html:25,37`, `tests/test_site_content.py:31`, `tests/test_site_theme.py:109`,
     `PROJECT_SPEC_SITE.md:96`
6. **Family links to the GitHub repo** (they redirect today, so they work; update for one name):
   `easy-personal-mcp/README.md:348` (`github.com/thunderkds/personal-agentic-claude`, link text too),
   `easy-personal-mcp/tests/test_readme.py:222` (pins the text `personal-agentic-claude`),
   `easy-memory-mcp/PROJECT_SPEC.md:14`, `easy-verifier-mcp/REQUIREMENT.md:75`.

### Notes

- **T107 guard reconciled.** T107's "guard held at 9 occurrences" was a one-off `grep -rn "personal-agentic-claude"
  setup.sh update.sh README.md | wc -l` in `tasks/TASK_REVIEW_T107.md:48,58`, never a test file. No test
  pins that count. `tests/test_repo_name.py` supersedes it and says so in its docstring.
- **Allow list** (`tests/test_repo_name.py` `ALLOWED`): the `setup.sh` fork fallback line; `scripts/memory_usage_report.py`
  (the local checkout folder's name in recorded traces, not the GitHub repo); two hook-test fixtures copied
  from recorded traces; the test itself. History paths: `tasks/`, `memory/`, `docs/archive|brainstorming|prd|adr|ddr/`,
  `reports/`, `PROJECT_KANBAN*`, `BRAINSTORMING_LOG.md`, `docs/memory-usage-finding-2026-08-07.md`. Any
  `personal-agentic-claude.vercel.app` is allowed (D4).
- **Not changed, outside D3's search term** (a product name, out of scope): `RUNBOOK.md:1,10` say
  "Personal Agentic Claude"; `PROJECT_SPEC.md:13,23` say `per-agentic-claude`.
- `RUNBOOK.md:11` now names `git@github.com:thunderkds/easy-kit.git`; the local remotes still use the old
  URL until the Supervisor changes them (they work through the redirect).

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Supervisor confirmed 2026-11-03T08:45:07Z: `python3 -m pytest tests/test_repo_name.py -q` → `8 passed in 0.07s`. Implementer output, for the reviewer to confirm: `tests/test_repo_name.py` (new, 8 tests: AC 2 sweep + anti-vacuity + stale-allow check; AC 3 default URL, fork named easy-kit, fork made before the rename falls back, `SUPERVISOR_REPO` wins, both error messages print the new install line). Red at 07:48:10Z: `5 failed, 3 passed`. Green at 08:14:43Z, HEAD `b976d0be`: `python3 -m pytest tests/test_repo_name.py -q` → `8 passed in 0.07s`; `sh scripts/smoke-install.sh` → `smoke-install.sh: PASS`. AC 5 full suites: `python3 -m pytest tests -q` (08:06:35Z, `b976d0be`) → `1665 passed in 485.98s (0:08:05)`; `python3 -m pytest .claude/hooks/tests -q` (07:54:35Z run, tree of `ab513797`; `b976d0be` changes only `tests/test_site_story.py`) → `1389 passed, 25 subtests passed in 138.91s (0:02:18)`; `sh scripts/smoke-install.sh` (07:57:56Z, `ab513797`) → `smoke-install.sh: PASS`, again at 08:14:43Z on `b976d0be` → `smoke-install.sh: PASS`. First full `tests` run failed 1: `test_site_story.py::test_every_paragraph_item_cell_and_definition_of_the_old_page_is_on_docs` (install line hash `93af67c788f6305e` changed); fixed in `b976d0be` with `CHANGED_BY_T240`, same pattern as T239. `shellcheck -x setup.sh update.sh` clean. |
| Verification command run | ☑ pass | 2026-11-03T08:45:07Z, `feat/t240-repo-name` @ `2809c654`: `python3 -m pytest tests/test_repo_name.py -q` → `8 passed in 0.07s`; `sh scripts/smoke-install.sh` → `smoke-install.sh: PASS` |
| Negative cases hold | ☑ pass | The new test copied onto a detached `main` (`1dd90fe9`) tree: `5 failed, 3 passed in 0.09s` — the sweep, installer URL and error-message tests fail on the old name; the 3 that pass (fork fallback, `SUPERVISOR_REPO` wins, anti-vacuity) do not depend on the rename. Implementer red run 07:48:10Z: `5 failed, 3 passed`. |
| verify | ☑ pass | auto-run by hook, session 066934d0-1c33-4230-869c-52f913065447, commit 1ce2c44b1232c08cd5f83cba6b9b896d7720e37e, log .claude/verify-runs/T240-1ce2c44b1232.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review over `main...HEAD` (12 files) + callers of `kit_repo_url`/`resolve_repo_url` (`setup.sh:69,99,820`); lane: `lane: C2, 11 files, 233 lines, FITS; unpredicted: tests/test_docs_match_installer.py, tests/test_readme_slim.py, tests/test_site_content.py, tests/test_site_story.py` (test pins, predicted as "pins follow"). Findings: P0 0, P1 0, P2 0, P3 1 (fork `curl` line in `site/docs.html` fails for a fork made before the rename; optional). security-review on the same diff: no findings ≥ 8 — pass. Startup reads complete. |
| Full smoke suite still green (no regression) | ☑ pass | Implementer: `python3 -m pytest tests -q` → `1665 passed in 485.98s` (@ `b976d0be`); `python3 -m pytest .claude/hooks/tests -q` → `1389 passed, 25 subtests passed in 138.91s`; Supervisor re-run 08:45:07Z `smoke-install.sh: PASS` |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional; no scoring requested for this rename |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | `site/*.html` changes are URL text inside existing links and code boxes only; no layout, class or style change |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | `site/*.html` changes are URL text inside existing links and code boxes only; no layout, class or style change |
| **UI: Responsiveness at target viewports** | ☑ N/A | `site/*.html` changes are URL text inside existing links and code boxes only; no layout, class or style change |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure in `../wt-t240` at `1dd90fe9`, before any implementation
commit. The installer's own messages and URLs still name the old repo:

```
$ date -u +%Y-%m-%dT%H:%M:%SZ; git rev-parse --short HEAD; sh setup.sh --harness codex; echo "exit=$?"; d=$(mktemp -d); cp update.sh "$d/"; sh "$d/update.sh"; echo "exit=$?"; rm -rf "$d"; git grep -n 'personal-agentic-claude' -- setup.sh update.sh
2026-11-03T07:46:28Z
1dd90fe9
[error] Easy Kit takes no options (got: --harness codex). Run it and choose from the menus:
[error]   curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh
exit=1
[error] update.sh is now part of the one Easy Kit command. Run this inside your project and choose Update:
  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh
exit=1
setup.sh:41:  log_error "  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
setup.sh:56:  BOOTSTRAP_REPO="${SUPERVISOR_REPO:-https://github.com/${GITHUB_USERNAME:-thunderkds}/personal-agentic-claude.git}"
setup.sh:87:    SUPERVISOR_REPO="https://github.com/${GITHUB_USERNAME}/personal-agentic-claude.git"
update.sh:10:  printf '  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh\n' >&2
```

Red test, written first (`tests/test_repo_name.py`, uncommitted):

```
$ python3 -m pytest tests/test_repo_name.py -q   # 2026-11-03T07:48:10Z
FAILED tests/test_repo_name.py::test_no_live_file_names_the_old_repo - Assert...
FAILED tests/test_repo_name.py::test_every_allow_entry_still_matches_a_line
FAILED tests/test_repo_name.py::test_default_repo_is_easy_kit - AssertionErro...
FAILED tests/test_repo_name.py::test_fork_named_easy_kit_is_used - AssertionE...
FAILED tests/test_repo_name.py::test_error_messages_print_the_new_install_line
5 failed, 3 passed in 0.77s
```

**AFTER**: same command, HEAD `b976d0be` (implementer capture; the reviewer re-runs it):

```
2026-11-03T08:14:54Z
b976d0be
[error] Easy Kit takes no options (got: --harness codex). Run it and choose from the menus:
[error]   curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh
exit=1
[error] update.sh is now part of the one Easy Kit command. Run this inside your project and choose Update:
  curl -fsSL https://raw.githubusercontent.com/thunderkds/easy-kit/main/setup.sh | sh
exit=1
setup.sh:53:    _url="https://github.com/${_user}/personal-agentic-claude.git"
```

The one line left is the fork fallback (allow-listed in `tests/test_repo_name.py`).

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
