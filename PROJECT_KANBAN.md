# PROJECT_KANBAN.md
**Last updated**: 2026-10-30

> Compact task board. Full context lives in `PROJECT_SPEC.md`. Update this file whenever a task status changes.

---

## Board

### Todo
- [ ] **T218** — `packs/tech-lead`: a `tech-lead` agent + `architecture-docs` skill that writes a user-approved document map, then C4/overview, sequence + journey per core feature, ER, risk register, roadmap in `docs/architecture/` (Markdown + Mermaid); PACK.md user guide, README + site `#packs` row | common-infrastructure | C2 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T218.md` | Registered 2026-10-30 [auto] from `docs/prd/PRD_tech-lead-pack.md` (D1–D7) + brainstorming Option B
- [ ] **T219** — Pipeline pointers for the tech-lead pack: Stage 2 spawns `tech-lead` for the document map, Stage 5 item 4 refreshes documents whose watched paths the merge touched — both only when `agents/tech-lead.md` exists | common-infrastructure | C1 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T219.md` | Depends on: T218 | Registered 2026-10-30 [auto]; hub file `docs/claude-md/pipeline-stages.md`
- [ ] **T206** — `stop_auto_verify.py --start` with no task ID falls through to `stop_hook()` and starts a paid run for every due task; make a bare or extra-arg `--start` exit 2 with a usage line | common-infrastructure | C0 | Risk: Medium | P1 | Guide: to write at Stage 2 | Depends on: T203 | Registered 2026-10-29 from T203 /verify finding (`main()` matches `--start` only when `len(sys.argv) == 3`)
- [ ] **T205** — The merge gate binds an `auto-run by hook` verify row to the branch being merged or pushed: the run record carries the branch (and worktree), and `pre_bash_block_unsafe_merge.py` accepts the row only when the record's commit is the head of that branch — not the head of whichever checkout holds the row; a decoy worktree's genuine pass no longer clears another branch's merge | common-infrastructure | C2 | Risk: High | P1 | Guide: to write at Stage 2 | Depends on: T203 | Registered 2026-10-29 from T203 security-review (Medium, confidence 8/10): gate reads main first then each worktree, first filled row wins, record checked against that checkout's head
- [ ] **T192** — `ui-test` skill: health-check `localhost:8765`, drive one labelled easy-ui session, write the verdict and report path into the three UI design rows; the guide template names easy-ui as one method beside the existing ones, never the required one | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T192.md` | Depends on: T190 | Registered 2026-10-28 from `docs/prd/PRD_companion-scoring.md` (Stage 0.5 grilling D1-D6, Path A selected). User: "checking the repos and adding the options to use the easy-ui and easy-verifier as scoring to evaluate gate", then "if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the normal flow, that all". Optional feature: binding when a tool ran, invisible when none did (FR-014, FR-015).
- [ ] **T193** — Doctrine and glossary: one pointer line in `AGENTS.md` (196 of 200 lines used), the two optional Stage 4 steps and the floor in `docs/claude-md/pipeline-stages.md`, and two `PROJECT_SPEC.md` glossary terms kept apart - **Companion score** (the kit's row) and **evaluate gate** (easy-verifier's own asking round) | common-infrastructure | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T193.md` | Depends on: T191 | Registered 2026-10-28 from `docs/prd/PRD_companion-scoring.md` (Stage 0.5 grilling D1-D6, Path A selected). User: "checking the repos and adding the options to use the easy-ui and easy-verifier as scoring to evaluate gate", then "if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the normal flow, that all". Optional feature: binding when a tool ran, invisible when none did (FR-014, FR-015).
- [ ] **T194** — The site says the kit can call both servers and requires neither: `#mcps` copy updated and `HONESTY_PHRASES` re-based so it still catches the overclaim without banning the true sentence (it bans the substring `required` today); mutations M1-M4 as the oracle | frontend-developer | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T194.md` | Depends on: T193 | Registered 2026-10-28 from `docs/prd/PRD_companion-scoring.md` (Stage 0.5 grilling D1-D6, Path A selected). User: "checking the repos and adding the options to use the easy-ui and easy-verifier as scoring to evaluate gate", then "if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the normal flow, that all". Optional feature: binding when a tool ran, invisible when none did (FR-014, FR-015).
- [ ] **T186** — Auto-mode check follow-up: a paused task stops re-blocking every later stop, new pause reasons are written, and `tracks.md` documents the T180 limits (no-remote security-review, the accepted temporary `origin/HEAD` ref, shared untagged trace, verify-row skip, loosely cited RULE at High) | common-infrastructure | C1 | Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T186.md` | Depends on: T180 | Registered 2026-10-27 from T180 Stage 4 round 2 (3 P2) and `/verify T180` findings; user: "yes, accept it and continue". Branch `plan/t178-t180-tracks` in `../wt-t178`.
- [ ] **T162** — Online mode stops tracking `PROJECT_KANBAN.md` in git (the board copy is rewritten on every pull); local mode keeps tracking it | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T162.md` | Depends on: T155 | Registered 2026-10-19: user approved ("yes") the T155 agent's recommendation. /verify of T158 showed an online pull drops all 161 local `Txxx` rows from the board copy, so a tracked copy makes a diff on every pull moment. Must keep the merge gate and hooks reading a present file (pull runs before they read).
- [ ] **T163** — MCP-only board setup warns that hook sync needs `LINEAR_API_KEY`, and a pull that fails for a missing key says so (not "board unreachable") | common-infrastructure | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T163.md` | Depends on: T155 | Registered 2026-10-19 from T155 Stage 4 P2: probed `connection: mcp` config → `pull failed: LINEAR_API_KEY is not set` rc=2, while `pull_moment.py wake` printed `board unreachable — using cache (0 unsynced)`.
- [ ] **T139** — Update's lock rewrite has no test for `kit_commit` | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Depends on: T137 | Registered 2026-10-08 from T137 Stage 4 P2: `write_new_lock` records the new kit commit (hand-probed `d82da61`→`2cb8fe3`, and seen at `/verify`) but no assertion in `tests/test_update.sh` pins it
- [ ] **T140** — The site header says "5-stage pipeline" above an 8-step diagram | Frontend-Implementer | C0 | Risk: Low | P2 | Depends on: T138 | Registered 2026-10-08 from T138 `/verify`: the lead paragraph names 5 stages; the diagram shows Phase 0, 0.5, 1, 1.5, 2–5. Also: sub-labels ≈7px at 280 px
- [ ] **T141** — Docs: a backup's version is the last kit installed, not the edit's origin | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Depends on: T137 | Registered 2026-10-08 from T137 `/verify`: after `[s]kip` the lock still advances, so a later backup of that file is named after the last kit run. Say so in the site Update flow + RUNBOOK; also fix the Update-`o` backup-failure summary wording ("no interactive input")
> **Batch 2026-09-25 — tokenization refactor (T124–T127).** Authority: `docs/ddr/0009-measure-token-work-from-transcripts-and-aim-at-focus.md`,
> `docs/token-focus-finding-2026-09-25.md`. All four build on the integration branch `tokenization-refactor` cut from `main` (`4f43bcf`);
> each task worktree branches from it and merges back; `main` receives the set in one merge after the batch passes Stage 5.


> **Batch 2026-09-12 — Easy Kit installer rework (T109–T117).** Authority: `docs/adr/0002-one-confirmed-menu-driven-installer.md`
> (Accepted), `BRAINSTORMING_LOG.md`. All nine build on the integration branch `feat/easy-kit-one-command`
> cut from `main`; each worktree branches from it and merges back; `main` receives the whole set in one
> reviewed merge after every task passes `/verify` (`memory/decisions.md`, 2026-09-12). **Superseded same day after T109**: the user merged T109 + the integration branch into `main` (PR #84, #85) — from T110 on, each task is merged back into `feat/easy-kit-one-command`, pushed, and merged to `main` by the user, **strictly one at a time**. Order:
> T109 first → T110–T113 may spawn in parallel but **merge one at a time**, re-running the installer suites
> after each → T114 → T115 → T116 → T117 (strictly serial: each rewrites `setup.sh`'s prompts/arguments).
> Baseline measured 2026-09-12 on `main` `8115bc9`: `1 failed, 844 passed` (the pre-existing
> `test_readme_slim.py`, owned by T115).
> **Docs ride with the code (user, 2026-09-12).** Each guide carries a "Documentation to Update" table
> whose D-rows are acceptance criteria, and each review file a matching Evidence row — a task that leaves
> README, the site, RUNBOOK, AGENTS.md, PROJECT_SPEC.md or pipeline doctrine describing the old installer
> is not Done. T115 adds `tests/test_docs_match_installer.py`; T116/T117 extend it, so a removed flag can't
> creep back into a live doc.



- [ ] **T133** — **Replies to the user read plainly — technical detail on request.** Registered 2026-09-26 by the user: *"make the response from agent look more human reading, not the technical response in some case."* T100/T103 fixed a reply's *shape*; nothing governs its *vocabulary*, so a well-shaped reply still reads as an engineering log (bare task IDs, project shorthand, hook names). Observed on the Supervisor's own `/wake` reply the same day, which obeyed all seven rules. User chose at Stage 2: **scope = replies to the user only** (Kanban, Evidence, `memory/`, commits stay technical — the audit trail; HTML reports and the `wake` format are out) and **default = plain first, detail on request** (gloss task IDs/internal terms, keep code/errors/paths verbatim). User note, same day: the rule applies **above all to questions put to the user** (chat questions, `AskUserQuestion` prompts/options), and a plain reply **bolds the one thing the user must read or act on**. Vital slice: ≤2 rule lines, byte-identical in `CLAUDE.md` and the template, test-pinned. Stage 5 must be a user-run `/verify` A/B on the Supervisor's own replies — T103's lesson: that is the only surface where the rule differs | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T133.md` | Registered 2026-09-26

- [ ] **T121** — **`^D` at the packs prompt aborts the installer silently: exit 1, no message, output stops mid-line.** Found at T115's Stage 5 `/verify` by probing `^D` at each of the three menus, and **verified pre-existing on `main`** (same exit 1, same silence, nothing written) — so this is not a T115 regression and was deliberately not folded into it. Root cause is not the menu it appears at: `^D` at the project-type menu falls through to New project and then dies at `prompt_packs`, whose bare `read -r pack_choices` returns non-zero under `set -e` and kills the script before the plan is ever shown. T115 is what made this *visible* — it gave `choose_action` and `prompt_clis` graceful `Cancelled — nothing was changed` handling, so two menus now cancel cleanly and the third dies mute, which reads as a crash rather than a cancel. Nothing is written either way, so this is a UX/consistency defect, not data loss. Fix shape is almost certainly to give `prompt_packs` the same `tty_read`/`cancel_run` treatment the other two prompts already have, rather than a bare `read -r`; confirm whether any other bare `read` survives in the installer while there. **Do not assume the `set -e` interaction without re-observing it** — the T115 review recorded a plausible-sounding but wrong account of this same behaviour from reading the code, corrected only when it was actually run | Common-Infrastructure-Agent | C1 | Risk: Low | P2 | Registered 2026-09-23 from T115 Stage 5

- [ ] **T120** — **Reinstall's closing summary under-reports which CLIs the run touched.** Found at T115's Stage 5 `/verify`, step 6: reinstalling a project that has both CLIs while picking only Claude Code refreshes Codex as designed and prints `[info]  Refreshed: Codex`, but the final summary line still reads `CLIs: Claude Code`. The **plan** above the confirmation discloses the kept CLI correctly (`Already set up here, not picked, kept and refreshed: Codex`), so nothing is hidden from the user *before* they commit to the run — this is the after-the-fact summary disagreeing with the plan that preceded it, which is a smaller problem than a silent orphan but still a log that misstates what happened. Cause is that the summary calls `cli_names` with no argument, so it reports `$HARNESSES` (what was picked) rather than what was actually projected — `PROJECTION_HARNESSES` is the set the run really touched. Scope is the closing `log_info` in `main()` and nothing else; check the Update path prints a consistent line too | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Registered 2026-09-23 from T115 Stage 5

- [ ] **T119** — An aborted install says what it actually did, not "nothing was replaced" | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Depends on: T112 | Registered 2026-09-18 from T112's `/verify`, measured not inferred. `harness_backup_path` aborts with *"Could not back up '<path>' … — nothing was replaced."* — true of that path, false of the run: `harness_copy_manifest` walks MANIFEST in order, so entries before the failing one are already replaced. Observed with a project owning `agents/` (early) and an unwritable `docs/` (late): the run printed `Backed up … './agents'`, then the error claiming nothing was replaced, and `agents/` afterwards held the kit's `backend.md`/`common-infrastructure.md`/`frontend.md` while `agents.bak/mine.md` survived. **No data loss — the data-safety contract T112 ships is intact**, which is why this is a separate P2 row and not a T112 re-open. Scope is the message wording, scoped to the one path (e.g. `'<path>' was not replaced; earlier paths in this run were already installed`) plus a test pinning it; **explicitly NOT a rollback** — rolling the run back is a larger design question and is not being smuggled in behind a wording fix. Two related observations recorded in `tasks/TASK_REVIEW_T112.md` and deliberately **not** in scope: the partial-install state has no rollback, and backups accumulate (`.bak`, `.bak.1`, …) with no outstanding-backup summary — the latter is an accepted cut on T112's own cut list

- [ ] **T117** — `select-packs` — the Supervisor recommends packs from the business domain and activates the ones the client approves | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | HITL | Guide: `tasks/TASK_GUIDE_T117.md` | Review: `tasks/TASK_REVIEW_T117.md` | Depends on: T116 | Registered 2026-09-12

> **Session handoff — 2026-08-31.** T097 merged. Its worktree and the T096 lessons both held: the
> guide was tracked before the spawn, and the `setsid` launch survived (46 min elapsed, agent
> completed with 5 commits). `validate.sh` and `smoke-install.sh` returned RC=0 at merge time; the
> full suite's pass/fail counts were not re-measured after that merge, and T102 (registered
> 2026-09-04) found the board's later "clean and green" framing of this note was stale.
>
> **A test count in this note is a measurement with a date on it, never a standing claim.** That is
> what broke here: counts written once were read as current for three sessions. Every figure below
> carries the date it was taken, and anything undated must be re-measured with
> `python3 -m pytest tests/ .claude/hooks/tests/ -q` before it is relied on.
>
> - **2026-09-04** — `6 failed, 837 passed` on a clean `v2`. Two independent causes, both
>   pre-existing and neither a regression: the `memory/MEMORY.md` hot-tier budget (5 tests) and the
>   README's own 60-line cap (1 test).
> - **2026-09-05** — hot tier resolved by a user-run `/compact-memory` (46,343 → 43,631 chars,
>   commit `1018d38`); README cap resolved by T102 raising it to 75.
> - **2026-09-05, post-merge (measured, not predicted)** — `844 passed`, 0 failed;
>   `validate.sh` RC=0. First fully green `v2` since the 2026-09-04 baseline above.
>
> **The kit now installs into Codex.** `setup.sh --harness codex` projects canon into `.codex/skills/`;
> a real Codex 0.149.1 session executes kit skills by name. Four skills exceed Codex's 8 KB body cap
> (`bugfix`, `craft-spawn-prompt`, `diagnose`, `write-better-skill`) and are SKIPPED, never truncated —
> they are genuinely unavailable in Codex, which is a real coverage gap, not just an installer detail.
>
> **T095 (P0) merged 2026-09-01 — the tax is paid off.** Stage 3 evidence written in a worktree is
> now visible to the merge gate, so no future task needs its review file hand-landed on the
> integration branch first. T094, T096 and T097 each paid that by hand; T095 was the last.
> Two non-blocking follow-ups are recorded in `tasks/TASK_REVIEW_T095.md` — cross-worktree evidence
> is unscoped by branch, and the quoted-span form of defect C is still live in
> `post_bash_memory_update.py`. Neither blocks a feature task.




### In Progress







### Ready for Review
- [ ] **T220** — Drop the stale `setup.sh --pack` install lines (5 PACK.md, `templates/PACK_template.md`, `docs/claude-md/folder-structure.md`): activation is the ADR-0002 approved copy (`select-packs`, T117); list `tech-lead` in folder-structure | Supervisor | C1 | Risk: Low | P2 | minimal track | Registered 2026-10-30 [auto] from T218 brainstorming (claim gate: `setup.sh` has no `--pack`) | Ready for Review 2026-10-30: branch `fix/t220-stale-pack-lines` in `../wt-t220`
- [ ] **T217** — The kit works with easy-memory installed as a plugin: agents list the plugin tool names too; kit marketplace `.claude-plugin/marketplace.json` lists easy-memory (git-subdir `plugin`, ref `v0.2.0`) | Supervisor | C1 | Risk: Low | P1 | Branch `feat/t217-easy-memory-plugin-names` in `../wt-t217` | Ready for Review 2026-10-30; auto verify BLOCKED (27f58eff) until easy-memory-mcp `v0.2.0`; v0.2.0 pushed, `install easy-memory@easy-kit` and agent memory_search pass 10:18Z; 3 new tests pass; suite 2545 passed, 5 failed (MEMORY.md budget, fail on main too); real `claude plugin install` waits for easy-memory-mcp `v0.2.0` | Track: minimal | Record: tasks/MINIMAL_LOG.md


### Done
> Rows here and under Closed are one-line summaries since T215 (2026-10-30). Each row's full original text is in `docs/archive/KANBAN_DONE_DETAIL.md`.
- [x] **T216** — Plugin spike: one skill, one agent, one blocking hook as a Claude Code plugin; same folder tried in Codex | Supervisor | C1 | Risk: Low | P1 | Done 2026-10-30: merged to main (user "merge to main and push"); auto verify pass at 79b59ad7 ($0.43); Claude Code all pass (prefixed names required), Codex gate did not fire (hook trust, unconfirmed) | Track: minimal | Record: tasks/MINIMAL_LOG.md
- [x] **T215** — Tidy the repo root (logs into `docs/`) and shorten Done/Closed rows to one line, full text in `docs/archive/KANBAN_DONE_DETAIL.md` | common-infrastructure | C2 | Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T215.md` | Done 2026-10-30: merged to main (user "merge to main"); auto verify pass at b3f50a70; board 344 KB → 61 KB
- [x] **T214** — Remove the old background-spawn markers (`.claude/markers/`, 88 files) from git and ignore the folder | Supervisor | C0 | Risk: Low | P2 | Done 2026-10-30: merged to main (user "merge to main"); auto verify pass at d9af8829 | Track: minimal | Record: tasks/MINIMAL_LOG.md
- [x] **T213** — Sidebar scroll-spy highlights the item above the clicked one | frontend-developer | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T213.md` | Done 2026-10-29: fix `26b489e` merged to main (user "merge to main and push"); scrollspy 8/8, test_site_content 134 passed
- [x] **T212** — Landing page takes the neon Graphite Mint accent (#3CF5A8) with glow, per the updated design canvas | frontend-developer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T212.md` | Done 2026-10-29: user merged PR #121 (`965df62`), brought into main as `358bbc8`
- [x] **T211** — Merge gate: `git -C <dir>` / `git -c k=v` forms and merges with options outside `MERGE_FLAGS` are now gated and resolved | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T211.md` | Done 2026-10-29: auto verify pass (commit 7f9e95e); merged into main (user "merge and push")
- [x] **T210** — Merge gate closes four gaps — `git pull` gated, `timeout`-wrapped test runs count, `git merge-base` read-only, verify row committed on the branch | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T210.md` | Done 2026-10-29: auto verify pass (commit 7ea033b); merged into main
- [x] **T209** — Auto verify refuses a verdict line that lists choices, and the doctrine names every accepted shape | common-infrastructure | C1 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T209.md` | Done 2026-10-29: auto verify pass after round 2 (commit b38c7a5); merged into main
- [x] **T207** — Visual-first landing page — diagrams lead each heavy section, long prose folds into Details | frontend-developer | C2 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T207.md` | Done 2026-10-29: auto verify pass after T208 unblocked it (commit 17b4a1c); merged into main
- [x] **T208** — Auto verify reads a PASS written as `**Verdict: PASS …**` — a real pass is no longer recorded as blocked | common-infrastructure | C1 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T208.md` | Done 2026-10-29: auto verify pass (commit 8ec94d5); merged into main
- [x] **T203** — Auto verify for every task: the Supervisor starts the headless `/verify` (`stop_auto_verify.py --start <ID>`) at Ready for Review; Stop hook is the backstop | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T203.md` | Done 2026-10-29: /verify PASS (headless, commit d027b73); merged into main
- [x] **T204** — Restyle the landing page to the Graphite Mint theme (shared `theme.css`, self-hosted IBM Plex, family header) | frontend-developer | C2 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T204.md` | Done 2026-10-29: user approved; merged on GitHub as PR #120 (6ed4e06)
- [x] **T143** — CI re-runs the Verification Command of every task a PR moves to Done | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T143.md` | Done 2026-10-29: PR #117 merged (`9ebe3ce`); /verify pass (user)
- [x] **T191** — `score` skill: one easy-verifier session at `changes` scope writes the Companion score row | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T191.md` | Done 2026-10-29: PR #118 merged (`9b3d9b4`); /verify pass (user); own Companion score row N/A
- [x] **T189** — Auto close-out: after an auto verify pass the hook moves the row to Done (Gates 5 and 6 still hold); the auto run does its own memory pass | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T189.md` | Done 2026-10-29: PR #119 merged (`15c544f`); /verify pass (user); AC 11 live PASS
- [x] **T196** — The event-trace attribution channel was one file per checkout, so two live sessions mis-attributed each other's `Bash` calls | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T196.md` | Done 2026-10-29: /verify pass (`df77f70`, 0 crossings); suite 2106 passed
- [x] **T202** — `main` is green again: 15 failing tests fixed by shrinking what grew, never by raising a budget | common-infrastructure | C2 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T202.md` | Done 2026-10-29: /verify pass (`bfdaef7`); suite 2043 passed; MEMORY.md 40,810 chars
- [x] **T200** — `settings-setup` skill — the Supervisor offers settings profiles at Stage 1 and writes High security by default, add-only | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T200.md` | Done 2026-10-29: /verify pass (`0c75406`); merged into `main` (`743399b`)
- [x] **T201** — Settings tool profiles — High security and Legacy on the Build tab, each with a "for whom" line, held equal to `profiles.json` | frontend-developer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T201.md` | Done 2026-10-29: /verify T201 pass (real Chrome); merged into `main` (`6bab0ec`)
- [x] **T177** — Kit-arms round 2: a scripted user answers at each stop, so the full kit is judged on its own design | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T177.md` | Done 2026-10-29: /verify pass (`74fb855`); bare 10, minimal 12, full 12, 0 unsafe, $7.33; merged and pushed
- [x] **T176** — Kit-arms experiment part 2: run 36 cells under the $60 cap, report against the frozen rule | common-infrastructure | C1 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T176.md` | Done 2026-10-26 (merge `f258b9a`): /verify SKIP (data + report only); bare 10/12, minimal 12/12, full 8/12, 0 unsafe
- [x] **T197** — The push gate checks only the task being pushed (resolved from its branch), not every task on the board | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T197.md` | Done 2026-10-28: merged PR #115; auto /verify pass at a37754d (Stop hook)
- [x] **T188** — Auto verify fires for every `[auto]` task, minimal track included, and writes its result into the report's auto verify slot | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T188.md` | Done 2026-10-28: merged PR #112; /verify pass
- [x] **T199** — The site's MCPs section lists easy-memory-mcp as a third optional companion, with honest claims | frontend-developer | C1 | Risk: Low | P2 | merged 0c08827; /verify pass 2026-10-28 (user) | PR #114 (768-899 px overflow fix) merged on GitHub
- [x] **T198** — `wake` reads two sections of `memory/MEMORY.md`, not the whole file | common-infrastructure | C2 | Risk: Medium | P1 | merged 3fa0d01; /verify pass 2026-10-28 (user)
- [x] **T190** — The merge gate blocks a push when a Companion score or UI design row reads `fail`, and stays silent when there is none | common-infrastructure | C2 | Risk: Medium | P0 | Done 2026-10-28: merged 9522392 (PR #113); /verify pass (user)
- [x] **T195** — Sub-agents can use easy-memory, and read less of `memory/MEMORY.md` | common-infrastructure | C2 | Risk: Medium | P1 | merged 90805b5; /verify pass 2026-10-28 (user)
- [x] **T182** — Auto verify: for an `[auto]` task a `Stop` hook runs the real `/verify` headless and writes the `verify` row; the gate trusts it only with a run record | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T182.md` | Done 2026-10-27: built `42859ce`; AC 8 live check pass; `/verify T182` pass (user)
- [x] **T180** — Auto mode: with `[auto]` either track runs to Ready for Review without stopping and ends with a final report of every decision | common-infrastructure | C3 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T180.md` | In Done; last entry: /verify FAIL 2026-10-27, user chose option 2 (text fix + auto-mode Stop hook), back to In Progress
- [x] **T178** — Two tracks: small tasks run on the minimal track (Decision record in `tasks/MINIMAL_LOG.md`); big/risky tasks on the extended track | common-infrastructure | C3 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T178.md` | Done 2026-10-27: /verify pass on re-run; merged into `plan/t178-t180-tracks`
- [x] **T179** — Debate: in auto mode 2–3 read-only Advocates argue a question's options; the Supervisor decides and flags it for review; max 3 per task | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T179.md` | Done 2026-10-27: /verify pass (`a340f1e`); merged into `plan/t178-t180-tracks`
- [x] **T175** — Kit-arms experiment part 1: fixture app, 6 graded tasks, runner, pre-registered keep/cut rule (no paid runs) | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T175.md` | Done 2026-10-26: /verify waived by user (N/A, not pass); dry run rc=0, 36 cells, $0
- [x] **T174** — Update can overwrite or keep all edited files in one choice on the plan screen, and logs every decision to `.claude/update-log.md` | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T174.md` | Done 2026-10-26: user `/verify` pass (real update.sh in a pty)
- [x] **T173** — AGENTS.md is the primary doctrine file; CLAUDE.md is only `@AGENTS.md` | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T173.md` | Done 2026-10-26: user `/verify` pass; reopened for the AC 11/12 site amendment, done again @ `9b7f43c`
- [x] **T170** — `resolve-question` skill: a fact question is answered from quoted `file:line` evidence or by 2 read-only scanners, else escalated to the human | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T170.md` | Done 2026-10-26: user `/verify` pass (3 headless agent runs); suite 1435 passed
- [x] **T169** — Writing Principles (ASD-STE100) become a named rule set next to Karpathy, for text a human reads only | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T169.md` | Done 2026-10-20: /verify PASS (round 2 after D6); merged via GitHub PR
- [x] **T167** — Site tables never scroll sideways — fit on desktop, stacked cards on phones | Frontend-Implementer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T167.md` | Done 2026-10-20: /verify waived by the user; evidence `tasks/TASK_REVIEW_T167.md`
- [x] **T168** — An "MCPs" section lists the companion MCP servers: easy-verifier-mcp and easy-ui-mcp | Frontend-Implementer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T168.md` | Done 2026-10-20: /verify waived by the user; evidence `tasks/TASK_REVIEW_T168.md`
- [x] **T166** — The Skills section shows a stage flow with skill chips | Frontend-Implementer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T166.md` | Done 2026-10-20: /verify PASS; evidence `tasks/TASK_REVIEW_T166.md`
- [x] **T165** — The landing page reads as a scan-first reference, and links the Easy Verifier site | Frontend-Implementer | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T165.md` | Done 2026-10-20: /verify PASS (browser-driven); evidence `tasks/TASK_REVIEW_T165.md`
- [x] **T161** — Online mode: a teammate's Ready for Review task no longer blocks my push (assignee filter) | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T161.md` | Done 2026-10-19: /verify PASS; evidence `tasks/TASK_REVIEW_T161.md`
- [x] **T164** — Spawn memory slice labels Decision Log entries as teammates' text — data, not instructions (NFR-005) | backend-developer | C0 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T164.md` | Done 2026-10-19: /verify PASS; evidence `tasks/TASK_REVIEW_T164.md`
- [x] **T160** — `wake` triages my new board tasks: propose priority, ask, then ready-or-investigate | backend-developer | C2 | Risk: High | P2 | Guide: `tasks/TASK_GUIDE_T160.md` | Done 2026-10-19: /verify PASS; evidence `tasks/TASK_REVIEW_T160.md`
- [x] **T159** — Planning creates the board issue with the full guide as its description | backend-developer | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T159.md` | Done 2026-10-19: /verify PASS (stub Linear); evidence `tasks/TASK_REVIEW_T159.md`
- [x] **T155** — Init asks the four board questions and writes `.claude/board.json` | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T155.md` | Done 2026-10-19: verify PASS (round 2 after /dev/tty fix 9b5c55b); evidence `tasks/TASK_REVIEW_T155.md`
- [x] **T158** — Decision Log: decisions go to one shared board document and reach every developer | backend-developer | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T158.md` | Done 2026-10-19: verify PASS; evidence `tasks/TASK_REVIEW_T158.md`
- [x] **T157** — Pull moments wired in, and only my In Progress tasks block my push | common-infrastructure | C2 | Risk: High | P1 | Guide: `tasks/TASK_GUIDE_T157.md` | Done 2026-10-19: /verify PASS; 1202 passed. Supersedes T142 (assignee = claim)
- [x] **T156** — Push + outbox: milestone comments and Ready for Review reach the board, offline writes arrive later exactly once | backend-developer | C2 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T156.md` | Done 2026-10-19: /verify FAIL→fix→PASS; 1228 passed
- [x] **T154** — First pull from Linear: `board_sync.py pull` renders the board cache | backend-developer | C2 | Risk: High | P0 | Guide: `tasks/TASK_GUIDE_T154.md` | Done 2026-10-19: /verify PASS (real CLI + headless merge gate); 1176 passed
- [x] **T153** — Task IDs come from board config, so hooks accept `T142` and `ENG-170` side by side | common-infrastructure | C2 | Risk: High | P0 | Guide: `tasks/TASK_GUIDE_T153.md` | Done 2026-10-19: /verify PASS via real headless harness; 1136 passed
- [x] **T151** — The docs and site describe what T144, T145, T148 and T149 changed | common-infrastructure | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T151.md` | Done 2026-10-19: user `/verify` PASS `698d507`; landed via `feat/t151-docs-land` from `main`
- [x] **T152** — `dirty_worktrees.py` is silently empty when run from a subfolder | common-infrastructure | C0 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T152.md` | Done 2026-10-19: board resolved from `git rev-parse --show-toplevel`; `/verify` PASS; merged `90f916a`
- [x] **T150** — Spawns run as background agents, and `wake` flags work a dead agent left behind | common-infrastructure | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T150.md` | Done 2026-10-17: `/verify` PASS; merged into `feat/t144-t145-t148-t149` (`d3252d6`)
- [x] **T144** — Stage 4 warns when a task's diff outgrows its declared Complexity | common-infrastructure | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T144.md` | Done 2026-10-17: user /verify PASS (`8fae855`); merged into `feat/t144-t145-t148-t149`
- [x] **T145** — A spawned agent inherits past decisions about its files, and compound leads with the general lesson | common-infrastructure | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T145.md` | Done 2026-10-17: user /verify PASS (`84cc8fe`); merged into `feat/t144-t145-t148-t149`
- [x] **T148** — A rewritten event trace is detectable — hash-chained, with the chain head anchored outside the repo | common-infrastructure | C2 | Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T148.md` | Done 2026-10-17: user /verify PASS (`eb15a36`); merged into `feat/t144-t145-t148-t149`
- [x] **T149** — `ship` won't recommend GO for production until a human has approved that exact version | common-infrastructure | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T149.md` | Done 2026-10-17: user /verify PASS (`2ff7814`); merged into `feat/t144-t145-t148-t149`
- [x] **T146** — An edit or command that touches a sensitive path asks a human first | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T146.md` | Done 2026-10-17: user /verify PASS (live sessions); merged in PR #97
- [x] **T137** — A backup is named after the kit version it replaces, and Update's "overwrite" takes one too | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T137.md` | Done 2026-10-08: merged to `feat/t137-t138-backups-diagram`; 997 passed
- [x] **T138** — The site's Overview shows the pipeline as a workflow diagram | Frontend-Implementer | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T138.md` | Done 2026-10-08: user `/verify` PASS; merged to `feat/t137-t138-backups-diagram`
- [x] **T136** — The spawn model is picked per CLI from the task's Complexity, never hard-coded to Claude names | Common-Infrastructure-Agent | C2 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T136.md` | Done 2026-09-29: `/verify` round 2 PASS; review `tasks/TASK_REVIEW_T136.md`
- [x] **T132** — The RUNBOOK says a push to `main` deploys the site | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T132.md` | Done 2026-09-25: user `/verify` PASS; evidence `tasks/TASK_REVIEW_T132.md`
- [x] **T131** — The Agent focus section says "we apply A to save B" | Frontend-Implementer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T131.md` | Done 2026-09-25: `/verify` PASS; evidence `tasks/TASK_REVIEW_T131.md`
- [x] **T130** — The site describes the agent-focus work (T124–T129) and stops contradicting it | Frontend-Implementer | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T130.md` | Done 2026-09-25: `/verify` PASS; evidence `tasks/TASK_REVIEW_T130.md`

- [x] **T128** — The token meter sees an agent's first edit even when it edits through Bash | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T128.md` | Done 2026-09-25: merged (`8b8c95d`); `/verify` pass
- [x] **T129** — Spawn prompts name the mandatory startup reads, and the agent confirms them | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T129.md` | Done 2026-09-25: merged (`69d561c`); `/verify` pass

- [x] **T126** — The Supervisor can see its own context size — compact-advisor decides on a measurement, not a feeling | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T126.md` | Done 2026-09-25: merged (`1470745`); user `/verify` pass
- [x] **T125** — Focused handoff — a spawned agent gets the memory lines its task touches, not the whole index | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T125.md` | Done 2026-09-25: mechanism shipped and AC9 measured; the evaluation window is tracked in DDR-0009 follow-up

- [x] **T124** — Token meter — measure spend and agent focus from session transcripts | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T124.md` | Done 2026-09-25: merged into `tokenization-refactor` (`07b0060`); user `/verify` pass
- [x] **T127** — Terse but verbatim — replies and sub-agent reports keep code, errors and paths exact; review catches over-engineering | Common-Infrastructure-Agent | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T127.md` | Done 2026-09-25: merged (`5060379`); `/verify` SKIP (instruction text only)

- [x] **T123** — CI still red after T122: a shell suite shells out to pytest and CI never installs pytest | Common-Infrastructure-Agent | C1 | Risk: Low | P0 | Done 2026-09-25: merged via PR #91 (`157a752`); CI run on `main` success, 24/24 steps

- [x] **T116** — Every pack ships as a dormant catalog; the broken install-time pack installer is removed | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T116.md` | Done 2026-09-23: Stage 4 0 P0/0 P1, 2 P2 fixed; an activated pack survives update untouched

- [x] **T122** — CI red since 2026-09-22: `validate.sh` read MANIFEST's `!` exclusion lines as paths | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-09-23: fixed; the real CI run was not observed before merge (recorded limitation)

- [x] **T115** — Choose CLIs and project type from a list — every install flag is gone, and the docs show one line | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T115.md` | Done 2026-09-23: Stage 4 3 P1 fixed; follow-ups split out as T120 and T121
- [x] **T114** — One command — it detects the project, shows a menu, and asks before acting | Common-Infrastructure-Agent | C2 | Risk: Medium | P0 | HITL | Guide: `tasks/TASK_GUIDE_T114.md` | Review: `tasks/TASK_REVIEW_T114.md` | Depends on: T110, T111, T112, T113 | Registered 2026-09-12
- [x] **T113** — Update removes what upstream stopped shipping (unless edited), and kit tests stop shipping | Common-Infrastructure-Agent | C2 | Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T113.md` | In Done; last entry: Stage 3 started 2026-09-21; review `tasks/TASK_REVIEW_T113.md`
- [x] **T112** — First install never destroys a project's own files — they are backed up and named | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T112.md` | Done 2026-09-18: `/verify` PASS (user-run, real installer); merged to main
- [x] **T118** — Fixture repos carry what `update.sh` hard-requires, and CI is green again | Common-Infrastructure-Agent | C1 | Risk: Low | P0 | Guide: `tasks/TASK_GUIDE_T118.md` | Done 2026-09-17: fixture suites green (t098 20/0); AC1/AC2 counts corrected in `70ac170`
- [x] **T111** — Kit hooks reach a project that already has `settings.json`, and stay current on update | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T111.md` | Done 2026-09-16: `/verify` PASS (installer CLI); merged into `feat/easy-kit-one-command`
- [x] **T110** — Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T110.md` | Done: `/verify` PASS 2026-09-15 (user-run); merged to `main` 2026-09-15 (PR #86)
- [x] **T109** — CI runs every install/update shell suite, and the one it would have caught is fixed | Common-Infrastructure-Agent | C2 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T109.md` | Done 2026-09-12: `/verify` round 2 PASS (ubuntu:24.04 replays of ci.yml)
- [x] **T108** — A comma between pack numbers silently costs the user a pack | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T108.md` | Done 2026-09-07: `/verify` PASS at the real prompt (pty): `1, 5, 3` installs all three packs
- [x] **T107** — The kit answered to two different names depending on the surface; user chose "Easy Kit" | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T107.md` | Closed 2026-09-06 (done): five one-line edits; `/verify` PASS at both surfaces
- [x] **T106** — The README never caught up with v2: no version, and a Codex install without saying four skills are missing | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T106.md` | Closed 2026-09-06 (done): all 7 ACs met; `/verify` PASS at the installer
- [x] **T105** — CI's shellcheck gate on `main` is red, and one suppression names a check that no longer fires | C1 | Risk: Low | P0 | Guide: `tasks/TASK_GUIDE_T105.md` | Closed 2026-09-06 (done): shellcheck exits 0 on CI's file list; `/verify` PASS; merged with two follow-ups
- [x] **T104** — The site advertises `v1` on the eve of a `v2.0.0` release | Common-Infrastructure-Agent | C0 | Risk: Low | P0 | Guide: `tasks/TASK_GUIDE_T104.md` | Done 2026-09-05: page version now tied to RUNBOOK's newest Release Log row; suite 845 passed
- [x] **T102** — `v2`'s test baseline is red, and the board still says it is green | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-09-05: every baseline figure now carries its measurement date (`78c6dea`)
- [x] **T103** — T100's Response Standard never reached the Supervisor: `CLAUDE.md` pointed at a file the harness does not auto-inject | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-09-04: suite 837 passed / 6 failed (the v2 baseline, T102), 0 regressions
- [x] **T101** — README and site still describe the pre-T096/T097 world in four places | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-09-04: suite 834 passed / 6 pre-existing v2 failures (T102), 0 regressions
- [x] **T100** — One response standard for the Supervisor and every sub-agent | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Guide: `tasks/TASK_GUIDE_T100.md` | Done 2026-09-03: Stage 4 PASS (one P1 fixed `551feca`); `/verify` PASS as a three-run A/B
- [x] **T099** — Quoted-span twin of T095's defect C: a hook still read a command's quoted data as command text | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T099.md` | Done 2026-09-02: Stage 4 P1 fixed; two limitations recorded
- [x] **T098** — `update.sh` silently re-Claude-ifies a Codex-only project, so the two installers disagree | Common-Infrastructure-Agent | C1 | Risk: Low | P2 | Guide: `tasks/TASK_GUIDE_T098.md` | Done: /verify PASS at the real CLI; suites green; merged to `v2`
- [x] **T095** — The merge gate cannot see worktree evidence, prescribes a disproved remedy, and blocks writes whose data mentions a push | Common-Infrastructure-Agent | C2 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T095.md` | Done 2026-09-01: /verify PASS at the hooks' CLI; 757 hook tests + 40 smoke green; two follow-ups in review file
- [x] **T097** — (B2): Per-harness install projection, `setup.sh --harness`, and the `AGENTS.md` correction that unblocks Codex | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T097.md` | Done: Stage 4 PASS; /verify PASS (real Codex session); 2 findings registered as T098
- [x] **T096** — (B1): Relocate canonical `skills/` and `agents/` to plain root, without touching the historical audit trail | Common-Infrastructure-Agent | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T096.md` | Stage 4 code-review PASS (1 P1 folded back in) | Stage 5 verify PASS (FAIL on first pass — upgrade-path regression, fixed in `72c8225`) | Evidence: `tasks/TASK_REVIEW_T096.md`
- [x] **T094** — The hook suite is red on v2's first commit — three failures, two unrelated causes | common-infrastructure | C2 | Risk: Medium | P0 | Guide: `tasks/TASK_GUIDE_T094.md` | In Done; the row records no close-out entry

- [x] **T091** — The Staleness Guard points at a channel it no longer describes, and does not know the Cursor adapter exists | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Closed 2026-08-24 (done): guard names `CLAUDE.md`, both adapters and `tests/test_provider_adapters.py`
- [x] **T092** — The kit measured that spawn-prompt size is not a cost lever, and never told `craft-spawn-prompt` | Common-Infrastructure-Agent | C1 | Risk: Low | P2 | Done 2026-08-24: merged to main

- [x] **T093** — The board's section resolver is shadowed by bold cross-references, and both tests that would catch it look the other way | Common-Infrastructure-Agent | C2 | Risk: Medium | P2 | Done 2026-08-24: fixed (row-anchored lookup); merged to main

- [x] **T090** — The kit claims to work with any provider; its doctrine reaches only Claude Code with a guarantee | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-08-24 (board-reconciliation pass): merged to main; follow-ups T091, T092
- [x] **T088** — All five `packs/*/PACK.md` files ship a pack-install command that `setup.sh` rejects | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-08-21: five one-line fixes + a parser test; user `/verify` PASS
- [x] **T085** — Slim `README.md` 477 → ~50 lines, and correct the two false hook rows at their source | Common-Infrastructure-Agent | C1 | Risk: Low | P1 | Done 2026-08-21: README slimmed; closes T081
- [x] **T082** — No trust boundary between externally-authored text and an agent's instruction channel | Common-Infrastructure-Agent | C1 | Risk: Medium | P1 | Done 2026-08-21: documented boundary + triage default that fails toward a human; merged to main
- [x] **T075** — The budget test was coupled to the file being nearly full, and `/compact-memory` broke it | QA-Automation-Agent | C1 | Risk: Medium | P0 | Done 2026-08-18: assertion tracks `HOT_TIER_CHAR_BUDGET`, mutation-controlled; merged to main
- [x] **T080** — Register the Agent Skills conformance contract in README + CLAUDE.md | Common-Infrastructure-Agent | C1 | Risk: Low | P2 | Done 2026-08-18: docs-only, `/verify` N/A (recorded); merged to main
- [x] **T079** — Description triggering + the instruction-pattern library for `write-better-skill` | Common-Infrastructure-Agent | C2 | Risk: Medium | P2 | Done 2026-08-18: merged to main
- [x] **T078** — Agent Skills spec conformance — write it down, then enforce it | QA-Automation-Agent | C2 | Risk: Medium | P1 | Done 2026-08-18: merged to main
- [x] **T073** — `post_bash_memory_update.py` told every session not to commit the memory pass, on git-tracked files | common-infrastructure | C1 | Risk: Medium | P1 | Done 2026-08-17: NOTE corrected (`c4ae887`), delta observed at runtime
- [x] **T071** — Vital Slice — extend Simplicity First into "rank the requested", in the guaranteed channel | Common-Infrastructure-Agent | C2 | Risk: Medium | P2 | Done 2026-08-16: 37 new tests, 442 passed
- [x] **T070** — Two pointers name a channel that no longer holds the Complexity matrix (`CLAUDE.md:86`, `pipeline-stages.md:118`) | common-infrastructure | C2 | Risk: Medium | P2 | Done 2026-08-15: pointers fixed (new installs only); two non-blocking findings noted
- [x] **T069** — T041's fix depends on a file that is not guaranteed to reach the agent | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-10: 21 new assertions, 394 passed; stale pointers split out as T070
- [x] **T066** — De-duplicate the startup read set (`CLAUDE.md`, `general-agent-template.md`, role guides) | common-infrastructure | C2 | Risk: Medium | P2 | Done 2026-08-09: role guides −4.7% to −15.6% chars (measured)
- [x] **T065** — Make the MEMORY.md size gate measure what it costs (cost is chars, the cap counted lines) | common-infrastructure | C1 | Risk: Medium | P2 | Done 2026-08-09: a tripped gate is answered by `/compact-memory`, never by editing the budget
- [x] **T068** — An unfilled `verify` Evidence row already satisfied the merge gate | common-infrastructure | C1 | Risk: Medium | P1 | Done 2026-08-09: 9 new tests, 326 passed
- [x] **T064** — Split the reviewer-filled sections out of the implementer's guide | common-infrastructure | C2 | Risk: Medium | P2 | Done 2026-08-09: shipped; unfilled-verify-row gap registered as T068
- [x] **T063** — Establish whether injected memory is actually used, before T065 compresses it | common-infrastructure | C1 | Risk: Low | P2 | Done 2026-08-07: 9 new tests, 267 passed
- [x] **T062** — Spawn threshold — stop paying the ~15.7k per-spawn floor for C0/C1 work | common-infrastructure | C2 | Risk: High | P1 | Closed 2026-08-07 without implementation by user ruling (DDR-0004): Hard-Stop Gate 1 stands
- [x] **T067** — `diagnose` gains a root-cause rule, backward call-chain tracing, and behaviour-triggered red flags | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-07: shipped; own spawn telemetry captured
- [x] **T061** — Capture the per-spawn cost telemetry the harness already hands the trace hook | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-07: 26 new tests, 246 passed
- [x] **T060** — `diagnose` — cross-tier boundary instrumentation and correlated trace reporting | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-07: 13 new tests, 220 passed; not end-to-end (no BE/FE in this repo)
- [x] **T059** — A test wrote to a tracked repo file, and in a worktree that destroys data | common-infrastructure | C1 | Risk: Medium | P1 | Done 2026-08-07: full suite 207 passed, worktree `git status` clean
- [x] **T058** — `diagnose` — evidence-driven instrumentation loop (NDJSON logs, hypothesis-tagged) | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-06: 19 new tests, 207 passed
- [x] **T057** — A sub-agent inherits its parent's `session_id`, so T056's session-scoped step counter did not separate them | common-infrastructure | C2 | Risk: Medium | P0 | Done 2026-08-06: security-review PASS; 188 passed
- [x] **T054** — delivery-report skill + HTML template + reminder hook + harness sync | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-06: real render 9380 bytes, zero unfilled slots
- [x] **T053** — Demonstration block in both guide flavors + spawn-time blank-BEFORE warning | common-infrastructure | C2 | Risk: Medium | P1 | Done 2026-08-06: 169 passed post-merge; merged into `docs/stage2-demonstration-block-t053-t055`, not main
- [x] **T055** — Bugfix Evidence-table parity with the gate-visible implementation shape | common-infrastructure | C1 | Risk: Medium | P1 | Done 2026-08-06: 169 passed post-merge; merged into `docs/stage2-demonstration-block-t053-t055`, not main
- [x] **T056** — Session-scoped step counters + TTL expiry | common-infrastructure | C2 | Risk: Medium | P0 | Done 2026-08-06: mutation-verified; 169 passed
- [x] **T030** — Post-baseline token-audit analysis: `/cost` ground truth was never captured, so DDR-0001's criteria could not be scored | Supervisor + user (HITL) | C1 | Risk: Low | P1 | Done 2026-08-05: HITL decision task, no code changed
- [x] **T052** — Stuck-Loop Checkpoint (mandatory) added to `diagnose`, so a bugfix session stops cycling hypotheses | C1 | Done 2026-08-04: full suite 139 passed
- [x] **T051** — Root `AGENTS.md` shipped so Codex CLI gets base rules without a manual prompt | C1 | Done 2026-08-04: 4 checks re-run by Supervisor; full suite 139 passed
- [x] **T050** — `scripts/token_audit.py` hardcoded its window and re-derived the whole trace; now window-filtered | C1 | Done 2026-08-04: 7 new tests; full suite 146 passed
- [x] **T049** — CLAUDE.md split from 565 lines into `docs/claude-md/*.md` with short pointers | C2 | Done 2026-08-04: `CLAUDE.md` 198 lines, all 5 links resolve
- [x] **T045** — Kanban-parsing hooks used an unanchored `###` lookahead, so a quoted `###` in a row truncated the section | C1 | Done 2026-08-03: 8 new tests; full suite 139 passed
- [x] **T040** — Token Audit Log moved from a manual convention to a generator (`scripts/token-audit.sh` + `token_audit.py`) | C1 | Done 2026-08-03: full suite 139 passed; T030 still needs 7 sessions of data
- [x] **T041** — `general-agent-template.md` commanded the Karpathy Engineering Principles but never delivered their text | C2 | Done 2026-08-03: 4 negative controls failed then reverted; suite + smoke PASS
- [x] **T048** — The hook test suite failed whenever the active-task channel was armed | C1 | Done 2026-07-31: 121 passed; merged to main
- [x] **T047** — `CLAUDE_ACTIVE_TASK` never reached the trace hook, so the merge gate failed closed on honest tasks | C1 | Done 2026-07-31: 121 tests, mutation controls RED then reverted; merged to main
- [x] **T044** — Hook lifecycle & evidence integrity — make the merge gate mean something | C2 | Done 2026-07-31: 109 passed + smoke PASS; merged to main
- [x] **T046** — Advisory `**Pattern reference**:` field added to the TASK_GUIDE template's `## Approach` | C1 | Done 2026-07-24: 9 new tests, 69/69 suite green
- [x] **T043** — Fix trace/step-limit task attribution (both hooks took the first task-ID substring in the payload) | C2 | Done 2026-07-23: Stage 4 0 P0/P1; first security-review, no findings
- [x] **T039** — Dedup the `## Skills vs Agents` section in CLAUDE.md (580→536 lines) | C2 | Done 2026-07-23: Stage 4 P0 + 2 P1 fixed; security-review manual, no findings
- [x] **T042** — Fix post_write_register_task.py Complexity/Risk/Priority extraction (defaults now `?`) | C1 | Done 2026-07-21: Stage 4 0 P0/P1, 1 P2 fixed; manual security-review, no findings
- [x] **T038** — Fix setup.sh piped `curl \| sh` install — primary documented install command was completely broken since T031 (2 days, undetected until a real user hit it); verified against the real live pushed repo | C2 | Completed: 2026-07-19
- [x] **T037** — Fix CI shellcheck SC1091 — missing `-x` flag meant shellcheck refused to follow the already-correctly-annotated lib/harness-fetch.sh source, failing CI on an info-level finding | C0 | Completed: 2026-07-19
- [x] **T036** — Fix scripts/smoke-install.sh for direct-repo model — CI was broken (red) since T031-T033 landed, never caught until this review; 1 P1 code-review fix (vacuous assertion) | C1 | Completed: 2026-07-19
- [x] **T029** — Prune 4 oversized SKILL.md files: learn 182→128, map-codebase 165→130 pruned; bugfix + code-review skipped at safe floor. Recovered from a stale branch after the original prune was lost to a failed /compact | C1 | Completed: 2026-07-19
- [x] **T034** — QA — independent smoke suite for install/update (9/9 pass, incl. negative-control sabotage self-check on update.sh's conflict detection) | C1 | Completed: 2026-07-19
- [x] **T035** — README.md — install/update sections rewritten for direct-repo model (2 stale-doc gaps found beyond original scope: pack ~/.supervisor no-longer-auto-created, obsolete git-submodule note removed) | C0 | Completed: 2026-07-19
- [x] **T026** — Fix TASK_GUIDE_template.md example verify Evidence row (2 compounding gate bugs found + fixed) | C0 | Completed: 2026-07-19
- [x] **T024** — Fix post_write_register_task.py agent-field regex | C0 | Completed: 2026-07-19
- [x] **T012** — Registration — CLAUDE.md + MEMORY.md + README | C0 | Completed: 2026-07-19 (audit-confirmed: skills deploy via MANIFEST's blanket `.claude/skills` line, documented in CLAUDE.md/README.md/MEMORY.md — no separate registration work remained)
- [x] **T011** — Core `wake` SKILL.md — live 4-section cold-start briefing | C2 | Completed: 2026-07-19 (audit-confirmed: `.claude/skills/wake/SKILL.md` exists, mandatory-invoked every session per CLAUDE.md)
- [x] **T010** — Registration — CLAUDE.md + MEMORY.md + README + setup.sh | C0 | Completed: 2026-07-19 (audit-confirmed, same basis as T012)
- [x] **T009** — Core `learn` SKILL.md — detection, LR writing, supersession, skill promotion | C2 | Completed: 2026-07-19 (audit-confirmed: `.claude/skills/learn/SKILL.md` exists, actively used — LR-0001/LR-0002 on disk)
- [x] **T008** — Infrastructure — `memory/learning-records/` folder + LR format template | C0 | Completed: 2026-07-19 (audit-confirmed: folder exists with LR-0001, LR-0002)
- [x] **T007** — QA — Unit Tests + Sample Traces + Smoke Suite | C2 | Completed: 2026-07-19 (closed per user confirmation — original Typer-CLI-project scope, superseded when repo pivoted to the Supervisor framework; no code ever existed to test)
- [x] **T006** — Mermaid Export (Stretch Goal) | C1 | Completed: 2026-07-19 (closed per user confirmation — same superseded original scope as T005/T007)
- [x] **T005** — CLI Wiring — Typer Entrypoint | C1 | Completed: 2026-07-19 (closed per user confirmation — no Typer/Python CLI code ever existed in this repo; original scope superseded by the Supervisor framework direction)
- [x] **T028** — Token Audit Log — scaffold + entry convention + format test (DDR-0001) | C1 | Completed: 2026-07-19
- [x] **T033** — New update.sh — hash-lock compare, per-file conflict prompt, symlink-refusal, git-repo check (ADR-0001) | C2 | Completed: 2026-07-17
- [x] **T032** — Rewrite setup.sh — direct-copy install, git-repo prerequisite check, write .claude/harness-lock.json (ADR-0001) | C2 | Completed: 2026-07-17
- [x] **T031** — lib/harness-fetch.sh — shared temp-clone-copy-discard + MANIFEST parsing (ADR-0001) | C2 | Completed: 2026-07-17
- [x] **T027** — DDR (Design Decision Record) — default decision artifact, ADR as rare escalation | C1 | Completed: 2026-07-16
- [x] **T025** — craft-agent skill (optional, supplemental agent-drafting) + Stage 1.5 wiring | C2 | Completed: 2026-07-16
- [x] **T001** — setup.sh + MANIFEST | C1 | Completed: 2026-06-10
- [x] **T002** — update.sh | C1 | Completed: 2026-06-10
- [x] **T003** — README.md | C0 | Completed: 2026-06-10
- [x] **T004** — .gitignore + repo hygiene | C0 | Completed: 2026-06-10
- [x] **T015** — ui-test skill (easy-ui-mcp orchestration) | C1 | Completed: 2026-07-01
- [x] **T016** — Wire ui-test into pipeline (qa.md + CLAUDE.md) | C1 | Completed: 2026-07-01
- [x] **T021** — Clean dangling T013/T014 prose references in cold memory | C0 | Completed: 2026-07-14
- [x] **T022** — Harden pre_agent_validate_guide.py task-ID extraction | C2 | Completed: 2026-07-14
- [x] **T023** — craft-spawn-prompt skill + wire Stage 3 / bugfix to it | C2 | Completed: 2026-07-14
- [x] **T017** — Task dependency declaration & entry-point reachability check | C1 | Completed: 2026-07-07
- [x] **T018** — Fix title-extraction regex in post_write_register_task.py | C1 | Completed: 2026-07-14
- [x] **T019** — Reconcile PROJECT_KANBAN.md rows (T005-T012 metadata, remove T013/T014) | C1 | Completed: 2026-07-14
- [x] **T020** — Update .gitignore for live-instance tracked files | C1 | Completed: 2026-07-14

---

### Closed (investigated, will not do)
- [~] **T184** — The kit will not install settings defaults | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T184.md` | Closed 2026-10-27, will not do (user: config goes by taste); evaluation reused by T185/T187 on `PROJECT_KANBAN_SITE.md`
- [~] **T142** — Two machines cannot grab the same task: an atomic claim/release | Common-Infrastructure-Agent | C2 | Risk: Medium | P2 | Closed 2026-10-19: superseded by T157 — in online mode the board assignee is the claim

> Rows kept with their reasoning rather than deleted — the analysis is the value, and a
> future report should be able to revive them without re-deriving it.

- [~] **T081** — Two provably false rows in the README's hook table | Common-Infrastructure-Agent | C0 | Risk: Low | P2 | Closed 2026-08-24 as absorbed by T085 (both rows corrected at source); do not revive

- [~] **T074** — `SessionStart` hook-wiring validator plus two stale README rows | Common-Infrastructure-Agent | C1 | Risk: Medium | P1 | Closed 2026-08-18, will not do — premise does not hold (all hook commands resolve); revive only on another install report
- [~] **T072** — `setup.sh` "silently" downgrades a brownfield install to greenfield | common-infrastructure | C1 | Risk: Medium | P2 | Closed 2026-08-18, will not do — the row overstated the defect (`setup.sh:227` explains the default); revive on a user report

## Blocked

- [ ] **T147** — Spawned sub-agents run under a tighter sandbox profile than the Supervisor | common-infrastructure | C2 | Risk: Medium | P2 | Guide: `tasks/TASK_GUIDE_T147.md` | Branch: `feat/t146-t147-harness-hardening` (one agent, T146 then T147), started 2026-10-17 | Depends on: T146 | Registered 2026-10-16 from the improvement-list grilling + brainstorm (`docs/brainstorming/BRAINSTORMING_LOG_harness-hardening.md`): **HITL**: whether in-process `Agent()` spawns can be sandboxed depends on hook input identifying a sub-agent — verify, then the user decides | **Blocked 2026-10-17**: user /verify FAIL — every sandboxed Bash call dies with `apply-seccomp: write /proc/self/setgroups (nested userns is capability-restricted ...)` under Ubuntu `kernel.apparmor_restrict_unprivileged_userns = 1`; needs an environment decision before it can pass

---

## Stage Tracker

| Stage | Status |
|-------|--------|
| 0.5 Brainstorming | ✅ Done |
| 1 Environment Setup | ✅ Done |
| 1.5 Sub-Agent Architecture | ✅ Done |
| 2 Planning (/plan) | ✅ Done |
| 3 Execution | ✅ Done |
| 4 Review | ✅ Done |
| 5 Integration & Verify | ✅ Done |
