# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 200 lines. One-line summaries + links to cold files.
> Injected in full into every sub-agent spawn prompt.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

> **token-audit**: DDR-0001 baseline window is open — log a `reports/token-audit_2026-07-17.md` entry at cold-start, each Stage transition, and each spawn; paste `/cost` at session end.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary (≤150 chars) -->

### Decisions
- [CLAUDE_LEGACY.md sync policy](decisions.md) — mirror new skills + session-startup gates + Hard-Stop Gates from CLAUDE.md into CLAUDE_LEGACY.md on each addition; bump version
- [Hard-stop gates in Permanent Rules](decisions.md) — 4 Supervisor self-checks: no TASK_GUIDE=no work; refactor/QA floors at C2/Medium; KANBAN current before session ends; one project per KANBAN
- [Codebase Map](codebase-map.md) — structural snapshot (tree, entry points, hotspots) in memory/codebase-map.md; cold-tier; C2/C3 agents read it; refresh via /map-codebase
- [LLM-as-Renderer for HTML reports](decisions.md) — html-report skill renders Stage 4 output inline; no shell post-processor; built-ins (code-review, security-review) can't be modified
- [reports/ is local-only](decisions.md) — generated HTML reports excluded from git; local browser viewing only; **amended 2026-07-19**: `reports/token-audit_*.md` is a tracked exception (must survive across worktrees)
- [thinking-report is separate from html-report](decisions.md) — Stage 0.5–2 decision reasoning vs Stage 4 review findings; different templates, different triggers
- [thinking-report MVP: matrix only, no flowchart](decisions.md) — CSS flowchart deferred; matrix answers "why this option?" reliably with less implementation risk
- [Dark neon theme on HTML report templates](decisions.md) — both templates use #0a0a12 bg + cyan/green/purple/amber neon palette with glow effects; matches user's dashboard aesthetic preference
- [learn skill: Learning Record System](decisions.md) — LR files in memory/learning-records/; supersession archive; skill promotion on ≥2 LRs with user approval; closes passive-memory gap
- [teach + write-better-skill: two-skill craft system](decisions.md) — teach auto-fires on skill-writing requests → emits draft SKILL.md; write-better-skill is the consulted craft reference (mattpocock port)
- [wake skill: mandatory cold-start briefing](decisions.md) — reads git/KANBAN/MEMORY/LRs live; ≤50-line output; hard gate before first Supervisor response each session
- [Code Naming Conventions in CLAUDE.md](decisions.md) — code-level only (funcs=verbs, classes=nouns, tests, DB, env vars, etc.); enforced at Stage 4 code-review; branch docs/code-naming-conventions
- [Deterministic guardrail hooks](decisions.md) — step-limit + event-trace + trace-verified merge gate; context-compaction/auth ideas rejected as N/A; branch feat/deterministic-guardrails-hooks
- [T017: Depends on / Entry point advisory tracking](decisions.md) — TASK_GUIDE dependency+reachability fields; non-blocking warnings at spawn (hook) and review (code-review P2); not a Hard-Stop Gate; merged via feat/task-dependency-tracking
- [T018/T019/T020: Kanban regex + reconciliation + live-instance gitignore](decisions.md) — extract() needed re.MULTILINE, not just wider char class (caught by code-review, not by unit tests); Kanban T005-T012 re-synced, task 013/task 014 removed; .gitignore stops ignoring tracked live-instance files
- [T021/T022/T023: craft-spawn-prompt skill + hardened spawn-hook](decisions.md) — new skill assembles spawn prompts (standard vs bugfix-flavored); pre_agent_validate_guide.py now matches structural Txxx refs only, not bare prose; closes MEMORY.md-paste landmine at the root; T024 follow-up flagged (post_write_register_task.py agent-field regex)
- [T025: craft-agent skill (optional, supplemental)](decisions.md) — teach-style drafter for .claude/agents/*.md, whole-team mode, draft-only; base team stays unconditional, craft-agent fires only for uncovered roles (user correction mid-session); glossary gained Base team/Agent Draft; T026 follow-up flagged (template verify-row gate mismatch)
- [T027: DDR (Design Decision Record)](decisions.md) — new default decision artifact (2-of-3 gate, docs/ddr/NNNN-title.md), ADR now the rare 3-of-3 escalation; grill-with-docs checks DDR first, flags ADR-eligible rather than auto-upgrading; glossary gained DDR/ADR/decisions.md-entry; near-miss merging an incomplete worktree — see gotcha below
- [Token refactor: measure first → DDR-0001](decisions.md) — baseline Token Audit Log (reports/, NOT memory/) over 7-session/14-day window before any trim; slim-skills runs parallel; CLAUDE.md trim deferred until data; ≥20% success / <5% rollback; first DDR ever written
- [T028 done: Token Audit Log scaffold + test](decisions.md) — reports/token-audit_2026-07-17.md live, window now open; branch feat/token-audit-log pushed, Stage 4 review pending; T029/T030 still Todo
- [T029 done: slim-skills run](decisions.md) — learn 182→128, map-codebase 165→130, bugfix skipped (already floor), code-review 157→146; checksums verified; line count ≠ bloat signal for template/table-heavy skills
- [Fidelity Gate: hallucination check in write-better-skill](decisions.md) — teach/craft-agent each gain a pre-Emit step: traceability to PRD/PROJECT_SPEC/user words, Skill()/Agent() ref resolution (unresolved → flagged inline, not blocked), no Permanent-Rules overreach; DDR gate 1-of-3, decisions.md-only
- [Direct-to-repo install, no central clone → ADR-0001](decisions.md) — temp-clone-copy-discard replaces ~/.supervisor symlink model; setup.sh=full overwrite, new update.sh=hash-lock (.claude/harness-lock.json) + per-file conflict prompt; packs/migration deferred; first ADR ever written
- [T031 merged: lib/harness-fetch.sh](decisions.md) — shared fetch/copy library for setup.sh(T032)/update.sh(T033); 0 P0/P1 review findings; T033 must enumerate files itself (not harness_copy_manifest) for per-file conflict detection
- [T032 merged: setup.sh rewritten](decisions.md) — direct-copy install, git-repo check, per-file harness-lock.json; 0 P0/P1; stale-symlink-at-MANIFEST-path correctly overwritten (setup always-overwrite ≠ update's refuse-on-symlink, not a conflict)
- [T033 merged: update.sh rewritten](decisions.md) — hash-lock compare, per-file conflict prompt (fd0/fd3 split), symlink-refusal all-or-nothing; 0 P0/P1; 3 independent verify scenarios pass incl. two-conflicts-in-one-run
- [T028 merged: Token Audit Log scaffold](decisions.md) — reports/token-audit_2026-07-17.md + format test; rebased past T031-T033 drift after a failed /compact; reports/ gitignore amended (see below) since worktree-isolated spawns need the file to survive merge
- [T024/T026 merged: two merge-gate regex fixes](decisions.md) — agent-field extraction (matched wrong line); template's example verify row (2 compounding bugs: check-column text, AND "pass" must be in the Notes column not Result column — undocumented until now)
- [T034 merged: independent QA install/update smoke suite](decisions.md) — recovered real work from a pre-existing worktree post-/compact, independently re-verified (9/9 + 55/55 across all 4 suites), fixed a stale pre-T026-fix verify row before merging
- [T035 merged: README rewritten for direct-repo model](decisions.md) — a prior uncommitted edit FALSELY claimed this was done (Evidence checkmarks, no real changes) — discarded, redone for real; 2 gaps found beyond original scope (packs need pre-existing ~/.supervisor, obsolete submodule note removed)
- [T036 merged: fixed scripts/smoke-install.sh — CI was broken since T031-T033](decisions.md) — silently red for 3 days across 5+ merged PRs, never caught; ADR-0001 migration didn't update every CI entry point; 1 P1 self-review fix (vacuous assertion)
- [T037 merged: fixed CI shellcheck SC1091](decisions.md) — missing -x flag, not a missing source= directive (that was already correct since T031); shellcheck exits non-zero on info-level findings with no severity filter
- [Full Todo audit + reprioritization, 2026-07-19](decisions.md) — T003/T004 deduped (already Done), T005-T007 closed as superseded (dead Typer-CLI scope), T008-T012 closed as already-built-but-mislabeled; T024/T026 raised to P0

### Patterns & Gotchas
- [Agent files must not tell sub-agents to write memory](learnings.md) — backend/frontend/qa.md + CLAUDE_LEGACY.md had "Update MEMORY.md" — fixed to "flag to Supervisor"; watch for this on every sync
- [html-report findings use `<pre>`](learnings.md) — never manually HTML-escape finding text; wrap in `<pre>` to handle `<`, `>`, `&` safely
- [Report filename: skill_branch_timestamp.html](learnings.md) — `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html`; sortable, collision-free
- [html-report scoring rubric](learnings.md) — Risk 0–30=green, 31–65=yellow, 66–100=red; all dimension slots are bare integers (no `%`)
- [{{RISK_SCORE}} must be bare integer](learnings.md) — no `%` in slot value; `%` is hardcoded in template HTML and CSS width attribute
- [verify Evidence-row gate regex](learnings.md) — Check cell must be exactly `verify` immediately before the `|`; TASK_GUIDE_template.md's own example text doesn't match (T026 follow-up flagged); gate also cross-checks memory/event-trace/<task>.jsonl for a real non-error command, not just a text claim
- [Sub-agent "changed" ≠ committed](learnings.md) — always `git status --short` the worktree and check `git diff <base> --stat` against the TASK_GUIDE's predicted files before trusting a merge; a merge command succeeding is not proof it merged everything (T027 near-miss)
- [Ghostty spawn marker can silently fail](learnings.md) — T028: sub-agent finished correct work but never committed/marked done; wait-loop itself reported `stopped` with no notification; always check worktree `git status` directly before trusting "done" — 2nd occurrence of the T027 uncommitted-work pattern
- [Temp-dir cleanup: expose via variable, not stdout](learnings.md) — `$(fn)` capture runs trap registration in a subshell, EXIT trap fires in the wrong shell; set a var instead (T031 gotcha)
- [No shellcheck in this env](learnings.md) — shell tasks substitute `sh -n` + bash/dash test runs, noted explicitly rather than silently skipped (T031)
- [Don't combine isolation:"worktree" with a pre-made worktree](learnings.md) — Agent tool creates its own second worktree/branch, orphaning the manually-created one; omit isolation when a worktree already exists (T032 gotcha)
- [Check Evidence table is actually filled](learnings.md) — not every implementer fills it (T031 did, T032 didn't); reviewer fills it with own reproduced output if blank
- [step_limit hook false-positive, now scans ALL tool inputs not just Bash](learnings.md) — 25+ stale counter files never reset on completion; blocks even Edit calls whose *text* mentions an old task ID; escape valve = bracket-glob the ID; fix is overdue, no longer occasional
- [Worktree-isolated files silently die if gitignored](learnings.md) — a Stage-3 spawn's gitignored output never leaves its worktree, even after merge; before gitignoring any spawn-produced artifact, check whether a future worktree/session needs to read it (T028 gotcha, reports/token-audit exception)
- [Post-/compact recovery: a checkmark is a claim, not a fact](learnings.md) — 3 different failure modes hit in one session (fully lost work / real work sitting in a forgotten worktree / FALSE Evidence claims with no real changes) — always `git worktree list` + independently re-verify claimed-passing Evidence against real file content before trusting it
- [VAR=val|pipe only scopes to first command](learnings.md) — use export or a subshell before the whole pipeline, not inline before cmd1 (T033 verify footgun)
- [fd0-prompt / fd3-filelist shell pattern](learnings.md) — lets a script be both interactively promptable and piped-test-drivable without stdin collision (T033)

### Patterns & Gotchas (thinking-report)
- [col-chosen on both th and td](learnings.md) — must apply to header AND body cells in chosen column; omitting on td leaves body unstyled
- [thinking-report trigger](learnings.md) — auto after Stage 0.5b direction approval and Stage 2 confirmation; args: session=<type> task=<ID> branch=<branch>
- [Assumptions tag classes](learnings.md) — tag-resolved (green) / tag-assumption (amber) / tag-deferred (purple); min 2 items required

### Decisions (Packs)
- [Packs are additive-only, core unchanged](decisions.md) — pack agents/skills symlink alongside core; never replace core resources
- [Pack install: --pack=<name> flag or interactive prompt](decisions.md) — no packs in non-interactive mode by default; users opt in explicitly
- [Pack structure: agents/ + skills/ + PACK.md](decisions.md) — pack agents use namespaced names (e.g. mobile-developer) to avoid core collisions

### Patterns (Packs)
- [Pack mandatory gates by domain](learnings.md) — mobile→ui-accessibility; data→pipeline-safety; devops→infra-safety; ai-agent→eval-design; api→contract-review
- [Pack agent boundary from core](learnings.md) — mobile≠frontend (lifecycle/app-store); data≠backend (pipeline idempotency); api≠backend (contract-first)
- [install_pack() in setup.sh](learnings.md) — iterates agents/*.md and skills/*/ from pack dir; symlinks into .claude/agents/ and .claude/skills/

### Patterns (learn skill)
- [learn materiality gate](learnings.md) — write LR only for corrections, preference disclosures, confirmed patterns, corrected misconceptions; never for greetings or activity logs
- [LR numbering at write time](learnings.md) — scan directory for highest LR-NNNN immediately before each Write call; prevents collision in multi-LR invocations
- [user type → LR only](learnings.md) — user-preference insights never route to cold files; scope-creep guard in routing table
- [skill promotion: code block only](learnings.md) — never auto-save SKILL.md stub; output fenced block and stop; user saves + registers manually

### Decisions (bugfix skill — 2026-06-29)
- [bugfix skill](decisions.md) — intake → orient (read code + confirm mental model with user, hard gate) → TASK_GUIDE → diagnose → review → integrate; wrong model = wrong path with no way back; P0 floors at Medium Risk

### Decisions (slim-skills — 2026-06-24)
- [slim-skills skill](decisions.md) — on-demand prune of bloated SKILL.md files (>150 lines); behavioral checksum extraction preserves hard constraints + output assertions; human approval gate before any write

### Decisions (New Skills — 2026-06-24 batch)
- [strategy skill](decisions.md) — STRATEGY.md north star (problem/approach/audience/metrics); grounds ideate + brainstorming; distinct from PRD
- [ideate skill](decisions.md) — pre-brainstorm divergent filter; 25–50 raw ideas → adversarial filter → 5–7 survivors; prevents deep brainstorm on weak direction
- [resolve-pr-feedback skill](decisions.md) — post-Stage-4 PR thread resolution; triage validity → fix → commit → reply; full-PR or single-thread mode
- [compound skill](decisions.md) — post-Stage-5 problem→solution capture to docs/solutions/; complements learn (LRs) with searchable structured artifacts
- [compound-refresh skill](decisions.md) — on-demand audit of docs/solutions/; Keep/Update/Consolidate/Replace/Delete classification; fixes documentation drift
- [optimize skill](decisions.md) — optional metric-driven iteration loop; baseline → hypothesis backlog → experiments → converge; hard + judge metrics
- [code-review project override](decisions.md) — .claude/skills/code-review/SKILL.md overrides built-in; adds P0–P3 severity, confidence anchors, dedup+promotion, conditional personas, model tiering
- [brainstorming upgrade](decisions.md) — added scope tiers (lightweight/standard/deep), one-question-per-turn gate, visual probe gate, claim verification before doc-write

### Learning Records
<!-- One-liner per active LR: - [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — summary -->
<!-- Superseded LRs: ~~old text~~ → see LR-NNNN -->

### Glossary
- [Report / Report Slot / Scoring Dimension / Report Session](glossary.md) — canonical terms for the html-report skill and Stage 4 reporting system
- [Thinking Report / Trade-Off Matrix / Thinking Session](glossary.md) — canonical terms for the thinking-report skill and Stage 0.5–2 decision system
- [Pack / Core framework / Pack agent](glossary.md) — canonical terms for the optional pack system

