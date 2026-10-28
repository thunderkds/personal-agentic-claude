# PROJECT_SPEC.md
**Last updated**: 2026-06-10
**Version**: 1.0

> **Scope of this document**: *How* to build it safely — architecture, agent config, constraints, risk areas, task state, and accumulated learnings.
> Product intent (personas, user stories, FR/NFR, success metrics) lives in `PRD.md`.

---

## Project Identity

- **Name**: Easy Kit
- **Repo**: per-agentic-claude (local)
- **Primary tech**: POSIX shell (`bash` / `sh`)
- **Type**: CLI deployment scripts
- **Deployment target**: Local developer machine (macOS, Linux, WSL)
- **Key stakeholders**: hungnh1110@gmail.com

---

## Architecture Summary

The supervisor repo (`per-agentic-claude`) is a general framework. A `MANIFEST` file lists all resource paths to deploy. `setup.sh` is the one Easy Kit command (ADR-0002): run inside a git repository, it fetches the kit into a temp clone, detects whether Easy Kit is already installed (`.claude/harness-lock.json`), and offers a numbered action menu — `Install / Cancel`, or `Update (keeps your edits) / Reinstall (backs up your edits) / Cancel` — then a plan screen of what it will copy, back up and remove, and acts only after `Proceed? [Y/n]`. Every prompt reads `/dev/tty`; with no terminal it prints and takes the safe default (Install, or Update keeping every edit — never Reinstall). Install copies each MANIFEST path in as real files and records content hashes in the lock; Update (`lib/harness-update.sh`) refreshes unedited files, asks per edited file, and removes unedited files upstream stopped shipping. `update.sh` is a thin alias for the Update action. Scripts are POSIX sh and emit colored output.

---

## Glossary

| Term | Definition |
|------|-----------|
| Central clone | **Superseded by ADR-0001** — the single copy of this repo formerly kept at `~/.supervisor` (or `$SUPERVISOR_PATH`) that every project symlinked against. No longer used by the base install path; see Temp-clone-copy-discard. |
| Lane | The depth profile a task's Complexity label (C0-C3) selects from the role guides' Complexity matrices. Lanes scale depth, never stages: every stage and Hard-Stop Gate still runs. `scripts/lane_check.py` compares the branch diff against the declared lane at Stage 4 (warn-only). |
| Minimal track | The track for small, low-risk implementation work: C0 or C1, Risk Low, no Gate-2 word, no change to user data, one session, one agent, no UI component (`docs/claude-md/tracks.md`). The Supervisor writes the code itself on a new branch — test first, change, real run — with no task guide and no process stop, and ends with a Decision record. Announced in one line as `Track: minimal — <reasons>`. **Not a Lane**: a Lane scales depth inside the extended track and keeps every stage; the minimal track runs none of the 5 stages. |
| Extended track | The track for big, risky or multi-session work: any of C2 or above, Risk Medium or High, a Gate-2 word or *migrate*, a change that deletes, moves, renames or converts user data or its storage format, more than one session or agent, a UI component. It is the full 5-stage pipeline, unchanged, with every Hard-Stop Gate. Announced in one line as `Track: extended — <reasons>`. **Not a Lane**: the Lanes (C0–C3 depth profiles) apply inside it. |
| Decision record | The record that ends a minimal-track task: ID, title, track, `Asked:`, `Decisions:` (an assumption starts with `Assumed:`), `Checked:`, `Files:`, `Not done:` (always the merge). Appended newest first to `tasks/MINIMAL_LOG.md`, created on first use from `templates/MINIMAL_LOG_template.md`; the same block is the Supervisor's final chat message. **Not the Decision Log** of board mode `online` (the shared "Project Decisions" board document), and not a DDR (one file per design decision in `docs/ddr/`). Not Evidence either: the merge gate does not read it. |
| Vital Slice | The subset of a requested feature's **implementation surface** that carries most of its value — what actually gets built. Named, never numbered: the 80/20 framing is a heuristic recorded once in `CLAUDE.md` and deliberately absent from every file an agent acts from, because nothing measures it (see DDR-0005). Extends Simplicity First from *reject the unrequested* to *rank the requested*. **Bounded by the AC-immunity rule**: a Vital Slice narrows implementation surface only — never an Acceptance Criterion, never a pipeline stage, never a Hard-Stop Gate. |
| Cut List | The recorded set of implementation surface deliberately **not** built when a Vital Slice is chosen, one reason per entry. An advisory `## Approach` field in `TASK_GUIDE_template.md`. Load-bearing because an unrecorded cut is indistinguishable from an oversight after the fact. Reviewed at Stage 4: a Cut List consisting mainly of error handling, validation or boundary conditions signals an **inverted ranking** — that is where correctness lives, not where the disposable 80% lives. |
| Target project | The user's project where supervisor resources are deployed |
| Easy Kit | The product this repo ships — the name users see in every menu and message. Internal identifiers keep the older word "harness" for the kit (`harness-lock.json`, `lib/harness-fetch.sh`) and are deliberately not renamed: renaming the lock would break every existing install. Do not show "harness" to users. |
| CLI | User-facing word for a supported agent runtime (Claude Code, Codex), chosen from a numbered menu at install. Internally the same concept is called **Harness** (`memory/glossary.md`); the two words must never appear side by side in user-facing text. |
| Manifest | `MANIFEST` file — one resource path per line, drives what the installer copies in |
| General resources | `agents/`, `skills/`, `templates/` — **as of ADR-0001**, copied as real files into each project (not symlinked). **As of ADR-0002 (proposed)**, `packs/` is copied too, as a Pack catalog. |
| Pack catalog | All of `packs/` copied into a project **inactive**: present on disk, invisible to every CLI, because nothing under `packs/` is linked or projected. The raw material the Supervisor analyzes against the project's business domain. See ADR-0002 (proposed). |
| Activated pack | A pack from the catalog whose `agents/*.md` and `skills/*/` have been copied into the plain-root canon (`agents/`, `skills/`) after the client approved the Supervisor's recommendation. Only activation makes a pack visible to a CLI. Distinct from "installed" — packs are never chosen at install time. |
| Temp-clone-copy-discard | ADR-0001's install mechanism: `setup.sh`/`update.sh` `git clone --depth 1` the harness into a `mktemp -d` (EXIT-trap cleaned up), copy `MANIFEST` paths + `CLAUDE.md` into the working repo as real files, then discard the temp clone. No central clone persists anywhere. |
| harness-lock.json | `.claude/harness-lock.json` — git-tracked lockfile recording the content hash of each installed `MANIFEST` path at install/update time. `update.sh` compares current file hash against the recorded one to distinguish "untouched since install" (safe to overwrite) from "user customized" (prompt per-file). See ADR-0001. |
| Project-specific files | `tasks/`, `memory/`, `PRD.md`, `PROJECT_SPEC.md` — never symlinked, created fresh |
| Greenfield | New project — uses `CLAUDE.md` as supervisor rules |
| Brownfield | Existing/legacy project — uses `CLAUDE_LEGACY.md` as supervisor rules |
| Report | A self-contained `.html` file generated by a Stage 4 skill, containing scored dimensions and a findings table |
| Report Slot | A `{{PLACEHOLDER}}` in `templates/report_template.html` that the LLM fills during rendering |
| Scoring Dimension | One axis of evaluation shown as a 0–100% progress bar (Risk, Code Quality, Adaptation Effort) |
| Report Session | One invocation of a Stage 4 skill; produces one report file named `reports/<skill>_<branch>_<ISO-timestamp>.html` |
| Delivery Report | A self-contained `.html` file generated by the `delivery-report` skill, rendering a task's **Demonstration** block (BEFORE / AFTER / DELTA / WITNESS) plus its Evidence table as a completion count. Conforms to the canonical `Report` definition — HTML, self-contained, `reports/`-hosted — but carries **no scored dimensions and no findings table**; it demonstrates what a task delivered, it does not assess it. Distinct from `Report` (Stage 4 review findings) and `Thinking Report` (Stage 0.5–2 direction lock). Renders `templates/delivery_report_template.html`. |
| Demonstration | The TASK_GUIDE block that anchors a task's delivered outcome to an observable before/after pair, present in **both** guide flavors (implementation and bugfix). Four fields: **BEFORE** (command showing the thing absent/failing — the bugfix flavor's is its Phase 1 repro loop), **AFTER** (same command post-change), **DELTA** (one sentence: what a user can now do), **WITNESS** (who ran it and when — never the implementing agent alone). Canonical term — do not use "before/after section" or "demo block" as synonyms. |
| BEFORE capture | The RED-state observation recorded in a Demonstration block **before any implementation commit exists**. The one field in the system that cannot be back-filled from a finished branch, and therefore the load-bearing element of the whole mechanism — every other checklist row in either guide flavor is satisfiable by assertion alone. |
| Depends on | A TASK_GUIDE field declaring a task-to-task precondition (`Depends on: Txxx — [artifact]`). Verified automatically at spawn time by `pre_agent_validate_guide.py` (warns if the referenced task isn't Done). Distinct from `## Blocked` on `PROJECT_KANBAN.md`, which stays a manual escape hatch for non-task blockers (external people/APIs/decisions) the hook cannot verify. |
| Entry point | A TASK_GUIDE field declaring the literal, grep-able identifier (route path, button label, function/consumer name) that reaches a task's output (`Entry point: [identifier]` or `Standalone — N/A` with a one-line reason). Checked at Stage 4 review to catch unreachable/dead-code features. Canonical term — do not use "Reachable via" as a synonym. |
| Base team | The 4 agents every project starts with unconditionally: Common-Infrastructure-Agent, Backend-Implementer, Frontend-Implementer, QA-Automation-Agent (`.claude/agents/*.md`). Canonical term — supersedes CLAUDE.md Stage 1.5's prior "default core team" wording (same concept, renamed for consistency). |
| Agent Draft | The fenced `.claude/agents/<name>.md` block emitted by `craft-agent` for a role beyond the base team. Not written to disk automatically — user/Supervisor saves it, then follows a Registration checklist (mirrors the `teach` skill's SKILL.md draft lifecycle: drafted → saved → registered). |
| craft-agent | Optional, supplemental skill — invoked only when a project's requirement implies a role the base team doesn't cover. Never a required Stage 1.5 step; the base team is always the starting point. |
| DDR (Design Decision Record) | The **default** decision-record artifact for real design decisions: one file per decision at `docs/ddr/NNNN-title.md`, referenced in cross-links as `DDR-NNNN`. Write-gated at **2-of-3** of the ADR criteria (hard to reverse / surprising without context / genuine trade-off) — looser than ADR's 3-of-3, so it captures the design decisions this project actually produces (e.g. T017's Depends-on/Entry-point field shape, T025's craft-agent scope), which rarely clear ADR's architecture-level bar. |
| ADR (Architecture Decision Record) | The **optional, rare escalation** above DDR — write-gated at **3-of-3** (all of: hard to reverse, surprising without context, genuine trade-off). One file per decision at `docs/adr/NNNN-title.md`, referenced as `ADR-NNNN`. `grill-with-docs` checks the DDR gate first; if a decision also clears all 3 ADR criteria, it is flagged ADR-eligible and the user is asked whether to escalate — DDR is not automatically upgraded. |
| decisions.md entry | The lowest tier: a one-liner (or short paragraph) appended to `memory/decisions.md`'s rolling log for every decision, regardless of DDR/ADR eligibility. When a decision also gets a DDR or ADR file, the `decisions.md` entry adds a `→ see DDR-NNNN` / `→ see ADR-NNNN` pointer — mirrors the existing `MEMORY.md → decisions.md` link pattern. |
| Token Audit Log | The measurement artifact at `reports/token-audit_<window>.md` (lives in `reports/`, **not** `memory/` — it is a generated, window-scoped artifact, not curated memory). One-line entries at session cold-start, each stage transition, and each `Agent()` spawn; every entry tagged with a Task ID (or `overhead`), cache-hit vs. cache-miss, and model tier. Session `/cost` output appended at session end as ground truth. See DDR-0001. |
| Measurement Window | The bounded data-collection period for the Token Audit Log: closes at **7 logged sessions or 14 calendar days, whichever comes first**. A *session* = one conversation that ran `wake`. The identical rule governs both the baseline window (before refactor) and the validation window (after). See DDR-0001. |
| Cold-start cost | The uncached prompt cost paid on the first turn of a new session — chiefly `CLAUDE.md` + `memory/MEMORY.md` + system prompt, billed at full price before the 1hr prompt cache warms. Distinct from within-session turns (cache hits ≈ 10% price) and from sub-agent spawns, which never inherit the parent session's cache. |
| $ per completed task | The bottom-line evaluation metric: a session's `/cost` spend split proportionally across that session's Task-ID-tagged audit entries, grouped by Complexity level (C0–C3) so like compares with like. Success criterion: ≥20% reduction at the same C-level; rollback trigger: <5%. See DDR-0001. |
| Fidelity Gate | The hallucination check `teach`/`craft-agent` must clear before emitting a SKILL.md or agent draft, defined once in `write-better-skill` (single source of truth, both drafting skills reference it). Checks: (1) every claimed capability traces to `PRD.md`, `PROJECT_SPEC.md`, or the user's literal words this session — untraceable claims are cut; (2) every `Skill()`/`Agent()` reference inside the draft either resolves to an existing file or is flagged inline as an unresolved companion-draft dependency (draft still emits); (3) no claimed authority the Permanent Rules reserve elsewhere (e.g. direct `memory/` writes). Result stated as "Fidelity gate: PASS" or a list of cuts/flags, appended before the Registration checklist. |
| Anchor | The out-of-repo copy of a task's event-trace chain heads (T148): after each trace append, `post_tool_trace.py` appends `<task> <line-no> <hash>` to `~/.claude/harness-anchors/<repo-slug>/<task>.anchors` (base overridable by `CLAUDE_TRACE_ANCHOR_DIR`). Each line of `memory/event-trace/<task>.jsonl` carries `prev` and `hash`, so an edit breaks the in-file chain; the anchor catches the rewrite that recomputes the chain, because `.claude/settings.json` denies agents write access to it: `Edit(~/.claude/harness-anchors/**)` and `Bash(*harness-anchors*)`, its only permissions rules (user decision 2026-10-17). `scripts/verify_trace.py <task>` reports `INTACT`, `BROKEN at line N`, `ANCHOR MISMATCH at line N`, `UNVERIFIED at line N` (a line written with `"anchor": "failed"`, exit 1) or `UNANCHORED`. `lib/merge-settings.py` unions the kit's `permissions.deny` into an installed project's settings, add-only. Raises the bar, not a proof: the human operator can edit it, and a Bash deny rule is pattern-based. |
| Board | The online task tracker a project in board mode `online` uses as its source of truth for tasks, guides, logs and decisions — Linear first; GitHub board / Jira later. **Not "provider"**: provider means the agent runtime (Claude Code, Codex, Cursor — DDR-0006). (`PRD_online-board.md`) |
| Board adapter | The one file that talks to a board (`lib/board/<board>.py`), implementing the fixed 7-operation interface. Only it knows which board is used; the task-ID pattern and `git_auto_status` live in config. |
| Board mode | Per-project setting chosen at init: `online` (a board is the source of truth) or `local` (today's behavior, byte-identical, `Txxx` IDs). |
| Board cache | The local files pulled from the board — `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_<ID>.md`, `memory/decisions.md` — that hooks read. Never edited by hand in online mode; the board wins. |
| Outbox | Local queue of writes (status, milestone comments, decisions) that could not reach the board; replayed idempotently when it is reachable. |
| Pull moment | One of the four times the board cache refreshes: session start (`wake`), before spawning an agent, before Ready for Review, before merge. |
| Decision Log | The single shared "Project Decisions" document on the board: dated, attributed entries, each linked to the task it came from. `memory/decisions.md` is its board cache. |
| Update log | `.claude/update-log.md` in an installed project: one dated entry per **Update** run, newest on top, listing each edited file's outcome and how it was decided (asked per file, auto-approve, no terminal) (T174). Project-owned, never a kit file. Not the Decision Log. |
| My task | A board task assigned to the current user. Only my tasks are triaged (FR-011) and only my In Progress tasks block my push/merge. |
| Citation | A `file:line` plus the quoted text at that line that answers a question in `resolve-question` (T170). The Supervisor or a scanner supplies it. **Not "evidence"**: Evidence is the TASK_GUIDE Evidence table filled at Stage 4/5. |
| Fact question | A question the repo can answer with a Citation (where a rule lives, what a script does). `resolve-question` answers it from a Citation or from scanners (T170). |
| Choice question | A question only the user can decide (scope, trade-off, preference). `resolve-question` sends it to the user at once, never to scanners (T170). **Not "intent"**: intent is the requirement restated at Stage 2 / the Requirement Fidelity Gate. |
| Scanner | A read-only `Explore` agent that `resolve-question` starts to search one assigned area of the repo (code, docs/memory, or git history) for a Fact question. It returns an answer with Citations, or "not found" (T170). |
| Debate | In auto mode, the `resolve-question` step that settles a Choice question (or a Fact question the Scanners could not settle): 2-3 Advocates each argue one option, the Supervisor decides by fixed rules, logs it and flags it for the user's review. At most 3 per task (T179). |
| Advocate | A read-only `Explore` agent that a Debate starts to argue for one option with Citations and the option's risk. It cannot change files (T179). |
| Safer option | The option the Supervisor picks in a Debate when no Citation makes one option necessary: it can be undone > it keeps all data > it is the smaller change > it matches the request's literal words (T179). |
| Auto mode | The mode the user turns on with the literal tag `[auto]` in a request; a bare word *auto* is not the tag (T180, `docs/claude-md/tracks.md` `## Auto mode`). Either track then runs to its end with no question to the user: each stop follows its auto rule (a rule, a Citation or a Debate), and every decision goes in the Final report. The task is marked by the line `Mode: auto`, which T182's hook reads. Some stops stay (a safety-hook block, a 4th Debate, a paid action outside the task, …). Never in auto mode: merge, push, Done, the Supervisor running `/verify`. **Not the installer's Update auto-approve** (T174, `.claude/update-log.md`), which answers per-file update prompts. Not a track or a Lane: it runs on either track. |
| Final report | The record an auto-mode task ends with: the `## Auto decisions` section of `tasks/TASK_REVIEW_<ID>.md` (extended track) or the Decision record itself (minimal track). `Mode: auto`, one numbered line per decision with how it was made (`RULE`, `FACT`, `DEBATED`, `SAFER OPTION`) and `⚠ decided for you — please review` on every Debate, safer-option and taste decision, then `Checks:` and `Not done:` with the `/verify` state. The same block is the Supervisor's final chat message (T180). **Not the Delivery Report** (the `delivery-report` HTML page), and not Evidence: the merge gate does not read it. |
| Auto verify | The step that runs the real built-in `/verify` for an auto-mode task on **both tracks** (T182, widened to the minimal track by T188; `docs/claude-md/tracks.md` `### Auto verify (Stop hook)`). When a `Mode: auto` task is in Ready for Review and its result is empty for the head commit, the Stop hook `.claude/hooks/stop_auto_verify.py` starts one detached, new headless session (`claude -p "/verify <ID>" --max-budget-usd 2`, the user's own permission settings) in the task's checkout, once per task and commit. `.claude/hooks/lib/auto_mode.py` is the one reader of which tasks are in auto mode, their track and their report file, shared with `stop_auto_mode_check.py`. When the run ends, the hook, never the Supervisor, writes a run record in the trace anchors' directory (which agents are denied write access to), the result where that track keeps its evidence — the `verify` Evidence row (extended: `☑ pass` / `☑ fail` / `☐ blocked`, Notes starting `auto-run by hook`) or a `verify:` line under the Decision record's `Checked:` field in `tasks/MINIMAL_LOG.md` (minimal) — and the report's `Not done:` auto verify slot, so the report stops saying `auto verify: running (T182)`. The merge gate accepts either an `auto-run by hook` row or a minimal-track `verify:` line only with a record for that task and head commit that says pass. The merge stays the user's. **Not the Supervisor's `auto-checked` real-run check (T180)**, which goes under `Checks:` and never fills the `verify` row. |

---

## Critical Constraints

- Never symlink `tasks/`, `memory/`, `PRD.md`, or `PROJECT_SPEC.md` — these are project-specific
- Never commit project-specific files to this repo
- Scripts must be POSIX-compatible (no bash 4+ features unavailable on macOS default shell)
- `setup.sh` must never destroy a project's own files — before replacing any pre-existing path (`CLAUDE.md` or a MANIFEST path, file or directory) whose content differs from the kit's, install moves it to `<name>.bak-<id>` — `<id>` is the kit commit being replaced (`kit_commit` in the lock), or today's `YYYYMMDD` when none is recorded — (or the next free `<name>.bak-<id>.N`; an existing backup is never overwritten; Update's `[o]verwrite` backs up the same way, T137) and names the backup in its output. Identical content is left alone with no backup (T112, ADR-0002)

---

## Known Risk Areas

| Area | Risk Level | Reason | Files |
|------|-----------|--------|-------|
| Copy install over existing paths | Medium | Install copies kit files over paths the project may already own; a silent replace would destroy project data. Mitigated by `harness_backup_path`, which moves a differing path to `<name>.bak-<id>[.N]` (T137) and names it — see `docs/adr/0002-one-confirmed-menu-driven-installer.md` ("No silent loss") | `setup.sh`, `lib/harness-fetch.sh` |
| Pack activation name collision | Medium | An activated pack's agent or skill name could collide with a core one in `agents/` or `skills/`; ADR-0002 requires activation to refuse, never overwrite. The shipped catalog itself is inert (T116: `packs` carries no MANIFEST destination pair) — activation is owned by T117 | `packs/`, `agents/`, `skills/` |
| WSL symlink behavior | Low | Linux symlinks in WSL filesystems behave correctly; Windows NTFS symlinks may not | `setup.sh` |

---

## Sub-Agent Team

| Agent | Role | CLI Spawn Command |
|---|---|---|
| Common-Infrastructure-Agent | Worktree setup | `Agent({ subagent_type: "common-infrastructure", prompt: "Create worktree for T001" })` |
| Backend-Implementer | Write setup.sh, update.sh, MANIFEST, README | `Agent({ subagent_type: "backend-developer", prompt: "T001: tasks/TASK_GUIDE_T001.md" })` |
| QA-Automation-Agent | Smoke-test scripts, verify idempotency | `Agent({ subagent_type: "qa-expert", prompt: "T004: tasks/TASK_GUIDE_T004.md" })` |

---

## CLI Model Table

> Filled at Stage 1. One row per authenticated CLI, one column per Complexity level. At spawn
> time, `craft-spawn-prompt` looks the task's Complexity Level up in the row for the CLI that will
> run it and reports `<cli> · <Cn> → <model>`. No row for the CLI, or an empty cell → STOP and ask
> the user; never fall back to another CLI's model, never invent one.

| CLI | Run command | C0 | C1 | C2 | C3 |
|---|---|---|---|---|---|
| claude | `claude` | haiku | sonnet | sonnet or opus | opus |
| codex | `codex` | | | | |

---

## Tasks

| ID | Title | Status | Assigned Agent | Complexity | Risk | Priority |
|----|-------|--------|---------------|-----------|------|----------|
| T001 | setup.sh + MANIFEST | Done | backend-developer | C1 | Medium | P0 |
| T002 | update.sh | Done | backend-developer | C1 | Low | P0 |
| T003 | README.md | Done | backend-developer | C0 | Low | P1 |
| T004 | .gitignore + repo hygiene | Done | backend-developer | C0 | Low | P2 |
| T005 | CLI Wiring — Typer Entrypoint | Done (superseded — no code ever existed, original scope closed 2026-07-19) | Backend-Implementer | C1 | Low | P0 |
| T006 | Mermaid Export (Stretch Goal) | Done (superseded — closed 2026-07-19) | Backend-Implementer | C1 | Low | P1 |
| T007 | QA — Unit Tests + Sample Traces + Smoke Suite | Done (superseded — closed 2026-07-19) | QA-Automation-Agent | C2 | Low | P0 |
| T008 | Infrastructure — memory/learning-records/ folder + LR format template | Done | common-infrastructure | C0 | Low | P0 |
| T009 | Core learn SKILL.md — detection, LR writing, supersession, skill promotion | Done | backend-developer | C2 | Low | P0 |
| T010 | Registration — CLAUDE.md + MEMORY.md + README + setup.sh | Done | common-infrastructure | C0 | Low | P1 |
| T011 | Core wake SKILL.md — live 4-section cold-start briefing | Done | backend-developer | C2 | Low | P0 |
| T012 | Registration — CLAUDE.md + MEMORY.md + README | Done | common-infrastructure | C0 | Low | P1 |
| T024 | Fix post_write_register_task.py agent-field regex | Done | backend-developer | C0 | Low | P0 |
| T026 | Fix TASK_GUIDE_template.md example verify Evidence row | Done | backend-developer | C0 | Low | P0 |
| T028 | Token Audit Log — scaffold + entry convention + format test (DDR-0001) | Done | backend-developer | C1 | Low | P0 |
| T029 | Prune the 4 oversized SKILL.md files via /slim-skills (HITL) | Done | Supervisor + user | C1 | Low | P1 |
| T030 | Post-baseline analysis — pick token refactor from real data (blocked by T028 window close) | Todo | Supervisor + user | C1 | Low | P1 |
| T031 | lib/harness-fetch.sh — shared temp-clone-copy-discard + MANIFEST parsing (ADR-0001) | Done | backend-developer | C2 | Medium | P0 |
| T032 | Rewrite setup.sh — direct-copy install, git-repo prerequisite check, write .claude/harness-lock.json (ADR-0001) | Done | backend-developer | C2 | Medium | P0 |
| T033 | New update.sh — hash-lock compare, per-file conflict prompt, symlink-refusal, git-repo check (ADR-0001) | Done | backend-developer | C2 | Medium | P0 |
| T034 | QA — smoke tests: fresh install, untouched-update, conflict-prompt, non-git-dir rejection (ADR-0001) | Done | qa-expert | C1 | Low | P0 |
| T035 | README.md — update install/update instructions for direct-repo model (ADR-0001) | Done | backend-developer | C0 | Low | P1 |
| T036 | Fix scripts/smoke-install.sh for direct-repo install model (CI was broken since T031-T033) | Done | backend-developer | C1 | Low | P1 |
| T037 | Fix CI shellcheck SC1091 — missing -x flag for lib/harness-fetch.sh source | Done | backend-developer | C0 | Low | P0 |
| T038 | Fix setup.sh piped curl\|sh install (primary Quick Start command broken since T031) | Done | backend-developer | C2 | Medium | P0 |

---

## Memory / Insights

| Date | Insight | Source Task |
|------|---------|------------|
| 2026-06-10 | MANIFEST-driven deployment chosen over hardcoded path list — allows framework growth without script edits | Brainstorming |
| 2026-06-10 | Symlinks default; `--copy` flag for per-project customization — document in README, not just help text | Grill session |
| 2026-06-10 | `tasks/` and `memory/` always created fresh — never symlinked. Prevents project context bleed. | Grill session |
| 2026-06-18 | HTML reports use LLM-as-Renderer (Option B): skill appends a render prompt suffix; LLM outputs complete HTML with inline CSS. No shell post-processor needed. | Brainstorming + Grill |
| 2026-06-18 | Report filename: `reports/<skill>_<branch>_<ISO-timestamp>.html` — identifies skill, branch, and time; sortable, collision-free. | Grill session |
| 2026-06-18 | All Stage 4 skills (code-review, security-review, blast-radius) get HTML reports in pilot scope. | Grill session |
