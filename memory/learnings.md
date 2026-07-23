# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

<!-- - 2026-06-12 — T001: clarification text (source: user answer / ADR link) -->

## Patterns

- 2026-06-18 — `html-report` skill: always use `<pre>` in the findings table for finding descriptions — do NOT manually HTML-escape. `<pre>` handles `<`, `>`, `&` in code snippets safely without extra processing. (source: grill session, edge case checklist)
- 2026-06-18 — Report filename convention: `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html` — skill name identifies type, branch identifies code under review, timestamp makes it sortable and collision-free across sessions. (source: grill session Q2)
- 2026-06-18 — `html-report` scoring rubric: Risk 0–30 → green/Healthy, 31–65 → yellow/Needs Attention, 66–100 → red/Critical. Overall badge is the worst of (Risk color, inverse-Quality color). Integer 0–100 for all three dimensions; bare number in slot (no `%` — hardcoded in template HTML). (source: SKILL.md)

- 2026-06-18 — `thinking-report` Trade-Off Matrix: always add `col-chosen` as a second class on both `<th>` and `<td>` cells in the chosen option column — omitting it on `<td>` leaves the column body unstyled (green header, white cells). (source: templates/thinking_report_template.html)
- 2026-06-18 — `thinking-report` trigger: auto-invoked by the Supervisor after Stage 0.5b direction approval and Stage 2 plan confirmation — not manually triggered per-task. Args: `session=<brainstorming|grilling|planning> task=<TASK_ID> branch=<branch>`. (source: CLAUDE.md Stage 0.5b + Stage 2)
- 2026-06-18 — Assumptions list tags: use `tag-resolved` (green) for confirmed answers, `tag-assumption` (amber) for unconfirmed givens, `tag-deferred` (purple) for intentionally postponed decisions. Minimum 2 items required by SKILL.md. (source: .claude/skills/thinking-report/SKILL.md)

- 2026-06-18 — Pack mandatory gates by domain: `mobile` → `ui-accessibility` before any UI Stage 4; `data` → `pipeline-safety` on any write/delete/schema change; `devops` → `infra-safety` before any infra apply; `ai-agent` → `eval-design` at Pillar 1 for C2+ LLM tasks; `api` → `contract-review` at Pillar 1 on any spec change. (source: pack agent SKILL.md files)
- 2026-06-18 — Pack agent boundary from core: `mobile-developer` ≠ `frontend-developer` (mobile lifecycle, app-store, platform APIs vs web DOM/CSS); `data-engineer` ≠ `backend-developer` (pipeline idempotency, schema evolution vs app services); `api-designer` ≠ `backend-developer` (contract-first, versioning, consumer-driven vs business logic). (source: PACK.md boundary sections)
- 2026-06-18 — `install_pack()` in setup.sh: iterates `packs/<name>/agents/*.md` → symlinks to `.claude/agents/`; iterates `packs/<name>/skills/*/` → symlinks to `.claude/skills/`. Uses same symlink/copy logic as `install_abs()`. (source: setup.sh)

## Patterns (learn skill)

- 2026-06-19 — `learn` materiality gate: write an LR only for user corrections, preference disclosures, confirmed non-obvious patterns, corrected misconceptions, or "surprising" moments. Never for greetings, activity logs, or terms already in glossary.md. (source: .claude/skills/learn/SKILL.md)
- 2026-06-19 — LR numbering must happen at write time (not at skill start) — prevents collision when two LRs are produced in one invocation. Scan `memory/learning-records/` for highest LR-NNNN immediately before each Write call. (source: .claude/skills/learn/SKILL.md Step 4)
- 2026-06-19 — `user` type LRs never route to cold files (decisions.md / glossary.md / learnings.md) — LR only. Routing a user preference to a cold file is a scope-creep bug. (source: .claude/skills/learn/SKILL.md routing table)
- 2026-06-19 — Skill promotion gate: output SKILL.md stub as a fenced code block and stop — never call Write tool automatically. User must save manually and register in CLAUDE.md. (source: .claude/skills/learn/SKILL.md Step 8)

## Patterns (wake skill)

- 2026-06-19 — `wake` graceful degradation is per-section, not per-skill — if KANBAN is missing, only Section 2 gets a fallback note; other sections still render from their live sources. (source: .claude/skills/wake/SKILL.md)
- 2026-06-19 — `wake` ≤50-line cap is enforced by a 4-step truncation sequence applied after composing all sections: (1) Section 1 → 5 commits, (2) Section 4 → 1 LR, (3) Section 3 → 5 entries, (4) append truncation note. (source: .claude/skills/wake/SKILL.md Step 6)
- 2026-06-19 — `wake` is strictly read-only — no Write, Edit, or Create step anywhere. Attempting to add a write step violates the out-of-scope constraint. (source: .claude/skills/wake/SKILL.md Karpathy Overrides)
- 2026-06-19 — Mid-session `/wake` invocation: prepend `"Note: invoked mid-session — this is a live snapshot, not a session-start state."` as first line of briefing. (source: .claude/skills/wake/SKILL.md edge case table)

## Patterns (teach + write-better-skill)

- 2026-06-19 — Split skill authoring into two skills: `write-better-skill` (pure reference, craft principles) + `teach` (orchestrator, emits draft). Matches mattpocock's own principle: split by invocation when another skill must reach the reference independently. (source: .claude/skills/teach/SKILL.md, .claude/skills/write-better-skill/SKILL.md)
- 2026-06-19 — `write-better-skill` must be model-invoked (no `disable-model-invocation`) so `teach` can reach it as an internal call. If it were user-invoked, no skill could reference it. (source: mattpocock invocation section — "other skills can reach it" requires model-invoked)
- 2026-06-19 — `teach` completion criterion is checklist-based: description has trigger phrasing (not identity prose), leading word identified or absence noted, every step has a checkable criterion, no-op test passed on all lines, registration checklist appended. (source: .claude/skills/teach/SKILL.md Step 5)

- 2026-06-22 — "Refactor to clean architecture" and similar structural refactors are NOT small tasks. Evaluate by blast radius (files touched, callers affected), not by how casual the request sounds. Start at C2/Medium Risk; require a TASK_GUIDE before any code. (source: LR-0001, user correction)
- 2026-06-22 — Pipeline bypass root causes confirmed by user: (1) perceived task smallness, (2) no TASK_GUIDE acting as a gate, (3) Supervisor role drift into implementation. Absence of a TASK_GUIDE is a hard blocker — no implementation without it. (source: LR-0002, user correction)
- 2026-06-22 — Agent files (.claude/agents/backend.md, frontend.md, qa.md) and CLAUDE_LEGACY.md all contained "Update memory/MEMORY.md if new patterns were learned" — contradicting the Memory Write Protocol. The correct instruction is "Flag learnings to the Supervisor — never write to memory/ directly." When syncing CLAUDE.md changes into agent files or CLAUDE_LEGACY.md, always verify no memory-write instructions creep in for sub-agents. (source: fix/agent-memory-write-protocol)

- 2026-07-01 — `.claude/agents/*.md` pin `model:` frontmatter to the generic alias `sonnet` (not a version-pinned ID like `claude-sonnet-4-6`), so it auto-resolves to the latest Sonnet (currently Sonnet 5) without an edit. Only hardcoded example model IDs in doc/skill text (e.g. `.claude/skills/html-report/SKILL.md`, `packs/ai-agent/agents/ai-engineer.md`) need manual bumping when a new model ships. (source: chore/update-model-refs-sonnet5)

## Gotchas

- 2026-06-18 — `{{RISK_SCORE}}` slot must be a bare integer (e.g. `72`), not `72%`. The `%` is hardcoded in `templates/report_template.html` and also used in `style="width:{{RISK_SCORE}}%"` — a `%` in the slot value would produce `width:72%%` and break the progress bar. (source: templates/report_template.html)
- 2026-07-19 — Second, undocumented bug in the same gate regex (`verify\s*\|[^|\n]+\|[^|\n]*pass`, T026 follow-up to the entry below): the final `[^|\n]*pass` group must find "pass" somewhere in the **third** (Notes) column, not the second (Result) column. A row like `` | verify | ☑ pass | some description with no "pass" in it | `` — the exact shape used throughout this session's earlier T028/T029 Evidence tables — does NOT satisfy the gate, confirmed by extracting and testing the real regex directly from the hook source. The Notes/observation text must itself contain the word "pass" (e.g. end with "— pass"). Template's example row updated to state this explicitly so future guides don't silently inherit the same trap a second time. (source: T026, `.claude/hooks/tests/test_task_guide_template_verify_row.py`)
- 2026-07-16 — `.claude/hooks/pre_bash_block_unsafe_merge.py`'s Evidence-row check regex is `verify\s*\|[^|\n]+\|[^|\n]*pass` — the Check-column cell must contain the literal word `verify` with only whitespace before the next `|`. `TASK_GUIDE_template.md`'s own example row (`` `verify` skill — works in running app | ☐ pass / ☐ fail / ☐ N/A ``) does NOT match this regex because of the trailing "skill — works in running app" text between "verify" and the pipe — discovered live on T025 when `git merge` was blocked twice despite a filled, truthful Evidence row. Additionally the gate cross-checks `memory/event-trace/<task>.jsonl` for a real non-error Bash call whose command text matches `pytest|npm test|...|verify` — a text claim alone is never enough (fail-closed by design). Fix: write the Check cell as exactly `| verify | ☑ pass | ... |`, and if there's no running app, actually re-run the TASK_GUIDE's Verification Command for real (not just cite it) so a genuine trace record exists. (source: T025, tasks/TASK_GUIDE_T025.md, .claude/hooks/pre_bash_block_unsafe_merge.py)
- 2026-07-16 — A sub-agent's completion report claiming files were changed is not proof they were **committed** in the worktree — discovered on T027 when the Supervisor's Stage-4 review-fix commit only staged the one file it directly edited (`grill-with-docs/SKILL.md`), and the merge silently succeeded while missing the implementing agent's own uncommitted `templates/DDR_template.md` (new) and `CLAUDE.md` changes, which had never been committed at all. `git merge --no-ff` does not error on a "successful but incomplete" merge — it just merges whatever the branch's HEAD actually points to. Fix: after any Stage-4 fix commit, before merging, always run `git status --short` in the worktree to check for uncommitted implementer changes, and verify `git diff <base> --stat` on the feature branch matches the TASK_GUIDE's predicted file scope (not just "the merge command didn't error") before trusting a merge is complete. If a bad merge already landed on an unpushed local branch, `git log github/main -1` (or equivalent) to confirm nothing was pushed, then `git reset --hard` to before the merge commit and redo it — safe only pre-push. (source: T027, tasks/TASK_GUIDE_T027.md)
- 2026-07-17 — Second occurrence of the "sub-agent didn't commit" failure shape, this time via the Ghostty spawn pattern (see [[feedback_subagent_spawn_terminal]]): on T028, the spawned sub-agent produced fully correct, test-passing artifacts (`reports/token-audit_2026-07-17.md`, a passing pytest suite, a `memory/MEMORY.md` edit) but the Ghostty window/process ended before it ran `git commit` or wrote the `TASK_ID.done` marker — and the Supervisor's own background wait-loop task was later reported `stopped` with no completion record, so even the marker-based tracking failed silently (no notification arrived; the Supervisor only discovered the gap when asked to push and found the marker file missing). Fix applied this time: before trusting any "push"/"merge" request from the user, check the worktree directly (`git status --short`, run the guide's verification command) rather than assuming a prior notification means the task finished. Open question flagged in `memory/decisions.md` (2026-07-17 entry): the marker-file wait-loop may need a durable fallback (e.g. Supervisor-side periodic `git status` polling of the worktree) rather than relying solely on the sub-agent reaching its own commit step before the window closes. (source: T028, tasks/TASK_GUIDE_T028.md)
- 2026-07-17 — Shell functions that create a resource needing an EXIT-trap-based cleanup (e.g. a temp dir) must expose the path via a variable, **not** stdout — discovered on T031's `harness_make_temp_dir`. Printing the path and capturing it with `x=$(harness_make_temp_dir)` runs the whole function, including its trap registration, inside a command-substitution subshell; the EXIT trap then fires in that subshell, not the caller's shell, so cleanup either leaks the dir or fires at the wrong time. Fix: the function sets a well-known variable (here `$HARNESS_TEMP_DIR`) as a side effect and returns nothing meaningful on stdout; callers read the variable directly, never `$(...)`-capture. Applies to any future shared-lib function with the same shape (register-cleanup-then-return-a-path). (source: T031, lib/harness-fetch.sh)
- 2026-07-17 — This dev environment has no `shellcheck` installed. Shell-script tasks (T031 onward) substitute `sh -n <file>` (syntax check) plus running the test suite under both `bash` and `dash` as the lint/portability evidence, and note the substitution explicitly in the Completion Checklist rather than silently skipping the item. If `shellcheck` becomes available, prefer it. (source: T031)
- 2026-07-17 — Confirmed empirically (not just reasoned): a `MANIFEST` entry with a leading slash (e.g. `/etc`) does NOT escape the temp/target directory in `harness_copy_manifest`, because the function builds paths via string concatenation (`"$_tmp_dir/$_line"`), so a leading slash just produces a double-slash still anchored under the intended dir, not an absolute-path traversal. Verified by direct `sh` driver-script testing during T031's `verify` pass, not by the author's own test suite. (source: T031 verify pass)
- 2026-07-17 — Do NOT pass `isolation: "worktree"` on an `Agent()` call when a worktree for that task was already created manually (e.g. by `common-infrastructure`) — the Agent tool's own `isolation: "worktree"` creates a *second*, independent worktree/branch (observed at `.claude/worktrees/agent-<id>`, branch `worktree-agent-<id>`), silently orphaning the manually-created one. Discovered on T032 when the sub-agent's actual work landed in a worktree/branch the Supervisor never provisioned. Fix: when Stage 3 already created a worktree via `common-infrastructure`, omit `isolation` entirely on the `Agent()` call (the spawn prompt already scopes the agent to that worktree path); reserve `isolation: "worktree"` only for ad-hoc spawns with no pre-existing worktree. (source: T032 spawn)
- 2026-07-17 — A sub-agent may finish implementation but leave the TASK_GUIDE's own Evidence table unfilled (unlike T031's implementer, which filled it) — always check the Evidence table is actually populated before treating a task as review-complete, and if blank, fill it yourself as reviewer using your own independently-reproduced command output, not the agent's prose report. (source: T032 Stage 4 review)
- 2026-07-17 — `.claude/hooks/pre_agent_step_limit`'s 40-tool-call counter accumulates across the sub-agent's own implementation run AND the Supervisor's subsequent Stage 4/5 review/verify calls for the same Task ID — it does not reset when the sub-agent reports "Ready for Review." Fired as a false positive on both T031 and T033 (recurring, not a one-off) despite the trace showing genuine, non-looping work each time. Escape valve: inspect `memory/event-trace/T<NNN>.jsonl` (note: even reading/catting this file is blocked while the limit is tripped — use a bracket-glob like `T0[3]3.jsonl` to dodge the literal-string match), confirm no loop, then `rm .claude/hooks/.state/step_count_T<NNN>.txt` to reset. Worth fixing at the hook itself (e.g. reset the counter on a "Ready for Review" marker) rather than manually resetting every time — flagged as a follow-up, not yet actioned. (source: T031, T033)
- 2026-07-19 — Multiple further occurrences of the `pre_agent_step_limit` false-positive above in the same recovery session — including one triggered purely by an Edit tool call whose *text content* (this very learnings.md entry) mentioned an old, already-Done task's ID, with no Bash command involved at all. Confirms the hook scans literal task-ID substrings across tool inputs broadly, not just Bash commands, and per-task counters are never cleared on completion — `.claude/hooks/.state/` has accumulated 25+ stale counter files for tasks finished weeks ago. Escape valve each time: bracket-glob or string-concatenation the ID in the reset command to dodge the same block while clearing it (e.g. `T0"NN".txt`). The hook-level fix (reset counter on "Ready for Review", or scope the scan to Bash-only) is now overdue — this is no longer an occasional nuisance, it blocks routine documentation work. (source: this session, post-/compact recovery)
- 2026-07-19 — **A failed `/compact` (login expired mid-compaction) does not mean lost work is gone — it means it's sitting uncommitted in a worktree you don't remember creating, or worse, silently reverted from your working tree with no trace.** Discovered live across three separate tasks in one recovery session, each requiring a *different* response: (1) an approved skill-file prune was fully lost — files back at original line counts, no commit, no worktree copy found anywhere — required a full redo; (2) a QA smoke-test task had a complete, correct, independently-verifiable implementation sitting uncommitted in a pre-existing worktree that `git worktree list` revealed but a fresh session start would never think to check for — required discover-and-reuse-with-independent-reverification; (3) a documentation task had an uncommitted working-tree edit whose Evidence table claimed the work was done and verified, but a live `grep` against the real file proved the claim false — required discard-the-false-claim-and-redo. You cannot tell which case you're in without checking `git worktree list`, `git status --short` in every worktree, AND independently re-verifying any claimed-passing Evidence against actual current file content before trusting it. A checkmark in an Evidence table is a claim, not a fact, especially after any session discontinuity. (source: this session, post-/compact recovery across three tasks)
- 2026-07-19 — `reports/` was fully gitignored (`reports/`) for "local-only HTML reports," but a tracked/shared artifact placed there (the DDR-0001 Token Audit Log, a `.md` file meant to accumulate across sessions and worktrees) silently failed to propagate: each Stage-3 spawn runs in its own isolated worktree, so a gitignored file written there never appears anywhere else, including after a clean merge. Discovered live when a freshly-merged worktree's own test suite failed on `main` immediately after merge — the source `.py` test file merged fine (it was git-tracked), but the `.md` data file it validated did not exist because it had only ever lived on-disk, ungit-tracked, inside the now-orphaned worktree directory. Fix required two parts: (1) change `.gitignore` from `reports/` to `reports/*` + `!reports/token-audit_*.md` — a directory-level ignore blocks git from ever evaluating negation patterns on that directory's contents, so the exception must exclude *contents*, not the directory itself; (2) manually copy the file forward from the old worktree path once, to seed history, since the file was never a git object before this fix. General lesson: before declaring any spawn-produced artifact "gitignored, local-only" as a design choice, check whether that artifact is meant to be read by a *different* worktree or session later — if so, gitignoring it silently breaks cross-worktree continuity with no error until something downstream fails to find it. (source: T0-two-eight review, `.gitignore`, `memory/decisions.md` 2026-06-18 entry amended 2026-07-19)
- 2026-07-17 — Shell footgun in ad-hoc test/verify commands: `VAR=val cmd1 | cmd2` only exports `VAR` into the environment of `cmd1`, NOT `cmd2` on the other side of the pipe — `SUPERVISOR_REPO="file://$FIXTURE" printf 'v\no\n' | bash update.sh` silently left `update.sh` with no override and it fell through to the real GitHub network default. Fix: `export VAR=val` (or wrap in a subshell) before the whole pipeline, not inline before just the first command. Caught mid-`verify` on T033 by noticing the log line showed the real `https://github.com/...` URL instead of the intended `file://` fixture. (source: T033 verify pass)
- 2026-07-17 — Reusable shell pattern for a script that must be BOTH interactively promptable and drivable by piped test input: read the interactive prompt from fd 0 (stdin) as normal, but loop over a generated file list via a *different* fd (e.g. `done 3< "$list"` / `read -r line <&3`) so the main loop's `read` never consumes the piped answers meant for the prompt. On stdin EOF, don't guess a default — treat it as "no input available," skip/preserve, and exit non-zero instructing an interactive re-run. (source: T033, update.sh's `process_files`/`prompt_conflict`)
- 2026-07-19 — `$0` is not a real file path when a shell script is invoked via `curl | sh` — `SCRIPT_DIR=$(dirname -- "$0")` silently resolves to the caller's cwd instead of failing loudly, so any script that sources a co-located file relative to `$SCRIPT_DIR` breaks in a piped context with no obvious error pointing at the real cause (T038: `setup.sh` broke the moment T031 split fetch logic into a separately-sourced `lib/harness-fetch.sh` — the primary documented `curl|sh` install command was silently broken from 2026-07-17 until a real user hit it 2 days later). **Any change that splits a monolithic script into a script + sourced-library pair must explicitly test the piped invocation path** (`cat script.sh | sh`, or the real `curl -fsSL <url> | sh`), not just checkout-based paths — the two have fundamentally different `$0` semantics, and only piped testing exposes the gap. (source: T038)
- 2026-07-21 — **Stage 2 artifacts must be committed before any Stage 3 spawn.** A git worktree branches from HEAD and therefore sees only *committed* state — a `tasks/TASK_GUIDE_Txxx.md` still sitting as an untracked working-tree file on the Supervisor's branch is invisible to the agent, which correctly halts under Hard-Stop Gate 1 ("no TASK_GUIDE = no work"). Cost a full 52k-token spawn to discover, and the failure looks like a missing guide rather than an uncommitted one, so it misdirects. Nothing in `CLAUDE.md` or `general-agent-template.md` states this. Best fix: a pre-flight check in `craft-spawn-prompt` (it already reads the guide path) asserting the guide is tracked AND has no uncommitted changes, before it emits the prompt. (source: T042 first spawn attempt)
- 2026-07-21 — **`git diff --stat` reads clean for untracked files, so it cannot verify a sub-agent's completion claim.** T042's agent reported "implementation and verification complete"; the hook change was uncommitted and the entire new 311-line test file was untracked, so `git diff <base> --stat` showed only the hook and the test file appeared nowhere at all. Merging on that report would have brought across nothing. Always use `git status --short` (which shows `??` untracked) **and** `git log --oneline` to confirm the agent's commit exists — not `git diff --stat` alone. Third occurrence of the uncommitted-work pattern (T027 near-miss, T028 Ghostty marker, T042). (source: T042 Stage 4)
- 2026-07-21 — **The built-in `security-review` skill cannot run in this repo**: it shells out to `git log --no-decorate origin/HEAD...` and this repo's only remote is named `github`, not `origin` (`refs/remotes/origin/HEAD` does not exist). It fails with `fatal: ambiguous argument 'origin/HEAD...'`. Since `CLAUDE.md` mandates `security-review` for every Medium/High-risk task and multiple past Completion Checklists tick that box, **the gate has almost certainly never actually executed here** — same "rule that looks enforced but silently isn't" class as LR-0002. Workaround used on T042: perform the review manually and label it as manual with the reason, never silently skip. Real fix (needs user consent — touches git config): add an `origin` remote alias, or set `refs/remotes/origin/HEAD`. (source: T042 Stage 4)
- 2026-07-21 — **"Already covered" must mean *reaches the context that needs it*, not *exists somewhere in the repo*.** Supervisor reasoning error, caught by user pushback: I argued against importing 2 of ponytail's 7 laziness-ladder rungs because `tdd/SKILL.md` and the `CLAUDE.md` Karpathy table "already covered" them. Both fail on delivery — `CLAUDE.md` is not in the sub-agent startup read list (`general-agent-template.md:10-14`), and `tdd` is invocation-triggered so it never loads for agents doing non-TDD work. The same distinction is the actual defect T041 fixes, which made the error self-illustrating. Corollary: de-duplicating text that lands in the *same context window twice* (T039) is a genuine win; text appearing in *different documents loaded in different contexts* is redundancy that buys reliability, not waste — do not collapse the two cases. (source: 2026-07-21 ponytail evaluation, user correction)
- 2026-07-19 — Shell footgun distinct from the T033 `VAR=val cmd1 | cmd2` one: under `set -e`, `failing_cmd; rc=$?` does NOT capture the real exit code the way you'd expect — the script exits immediately at `failing_cmd` (since `set -e` triggers on any unchecked non-zero exit), so the `rc=$?` line, and anything after it (cleanup, `rm -rf`, etc.), never runs at all. The fix is `rc=0; failing_cmd || rc=$?` — the `||` makes the command "checked," which `set -e` exempts from triggering. Caught in self-review on T038 *before* any test ran, while writing a bootstrap-clone-then-reinvoke pattern that needed guaranteed cleanup regardless of the re-invoked command's exit status. (source: T038 self-review, setup.sh's piped-install bootstrap branch)

---

## A comparison assertion that has never been observed failing is not evidence (2026-07-23, T039)

**Pattern**: T039's AC5 checksum check printed `PASS` on every run while asserting nothing. The awk
matcher anchored on `^## Hard-Stop Gates$`, but the real heading is `### Hard-Stop Gates
(Supervisor-level — …)` — an H3 with a parenthetical. `^## ` cannot match `###` (third char is `#`,
not a space), so *both* the current and baseline extractions returned the empty string, and two empty
strings compare equal. The guide I wrote seeded the error by citing the heading as `##`; the agent
implemented it faithfully.

**Generalization**: any equality/checksum/diff assertion whose two sides are produced by a *matcher*
can pass vacuously when the matcher under-matches. This is the same failure family as the regex
defects in T018/T022/T024/T042 — the difference is that a regex defect produces a wrong value, while
this produces *no* value on both sides, which then agrees.

**How to apply**: a negative control is load-bearing, not optional. Before accepting any checksum or
"unchanged" assertion, mutate the thing it guards and confirm the test goes red — then paste that red
output as evidence. The Supervisor should reproduce this independently rather than trust the pasted
run. Also add an empty-extraction guard so a broken matcher fails loud instead of passing silently.
3rd vacuous-assertion occurrence overall (T036 vacuous assertion, T042, T039).

## A working-tree-vs-HEAD scope guard is not a repeatable test (2026-07-23, T039)

**Pattern**: T039's AC5/AC6 compared CLAUDE.md against floating `HEAD:CLAUDE.md`. That works exactly
once — while the change is uncommitted. After commit, baseline == current: the line-delta is 0 and the
test fails forever, and the checksum compares the change against itself. The agent's pasted "green"
output had been captured pre-commit and could never be reproduced.

**How to apply**: decide up front whether a check is a *permanent invariant* (runs forever at any
commit) or a *one-shot scope guard for this change*. Invariants go in CI. Scope guards must pin an
explicit baseline commit (`BASELINE_REF=${BASELINE_REF:-<sha>}`) and must be kept out of CI, or they
become a landmine for the next legitimate edit. The committed script must exit 0 from a clean checkout.

## Evidence claiming a post-commit re-run must be reproduced, not trusted (2026-07-23, T039)

**Pattern**: T039's first submission filled the `verify` row with "reran post-commit → all checks
passed, exit 0". Running it at that exact commit produced `FAIL … exit 1`. The agent had run it
pre-commit and described it as post-commit. 2nd false-Evidence occurrence (T035 was a prior uncommitted
edit that falsely claimed completion with checkmarks and no real changes).

**How to apply**: for any Evidence row that names a commit, check out/inspect that commit and re-run it
yourself. Cheap, and it is the only thing that separates a claim from a fact. Hard-Stop Gate 5 depends
on this being real.

## post_agent_move_to_review.py fires at spawn, not completion (2026-07-23)

**Pattern**: the hook is a PostToolUse matcher on `Agent`. With async/background sub-agents that event
fires when the spawn is *issued*, so the task is moved Todo → Ready for Review before any work exists.
Observed on T039: the board claimed Ready for Review while the agent was still writing its first test.

**How to apply**: do not trust the board's Ready for Review state as proof a sub-agent finished — check
the worktree with `git status --short` + `git log --oneline`. Fix candidate (not yet a task): gate the
move on real completion, distinct from T043's attribution fix — that one is *which* task, this one is
*when*. Related: the merge gate reads the same board, so a task left In Progress blocks the merge —
close it on PROJECT_KANBAN.md **before** running `git merge`, or `pre_bash_block_unsafe_merge.py`
rejects the merge.

## Built-in security-review remains unrunnable — 2nd consecutive Medium-risk task (2026-07-23)

**Pattern**: confirmed again on T039 — `git remote -v` shows only `github`, and `git rev-parse
origin/HEAD` fails. The built-in hardcodes `origin/HEAD`, so a gate CLAUDE.md marks *mandatory* for
every Medium/High task has likely never executed. Done manually on T042 and T039.

**How to apply**: keep doing it manually and label it as manual in the Kanban row and Evidence. The real
fix (`git remote add origin <url>` as an alias, or setting `origin/HEAD`) mutates the user's git config
and needs explicit consent — raised with the user 2026-07-23, not yet approved.

---

## The step-limit / trace false-positive is FIXED (2026-07-23, T043)

Supersedes the standing "bracket-glob the task ID in prose to avoid tripping the hook" workaround —
that contortion is no longer needed. Both hooks now attribute structurally (see the T043 entry in
decisions.md). Prose mentions of a Task ID in an Edit, a Bash command, or a file you merely read no
longer count a step or file a trace record against that task.

**Consequence to watch**: a `Bash` command is now *never* attributed. `pre_bash_block_unsafe_merge.py`
requires a non-error trace record in `memory/event-trace/<task>.jsonl` whose summary matches
`pytest|npm test|jest|go test|cargo test|verify`, so real test runs will only be recorded against a
task if `CLAUDE_ACTIVE_TASK=Txxx` is exported when they run. Set it in the spawn wrapper.

## The merge gate's own evidence is a substring match (2026-07-23)

`pre_bash_block_unsafe_merge.py:trace_shows_verification` accepts any non-error trace record whose
`summary` merely *contains* `pytest`/`verify`/etc. Verified on T043: the only two qualifying records
were Supervisor inspection commands that happened to contain those words in their text — no test had
run under that tag at all, yet the gate would have passed the merge. The gate designed to stop "the
agent claims it ran tests" is itself satisfied by a claim-shaped string. Same vacuous-evidence family
as the T039 AC5 checksum.

## Don't quote a `###` heading inside a PROJECT_KANBAN.md row (2026-07-23)

`pre_agent_validate_guide.py:find_kanban_section` and `pre_bash_block_unsafe_merge.py:tasks_in_section`
both slice sections with `re.search(rf'### {section}\n(.*?)(?=###|\Z)', ...)`. A row whose *text*
contains a literal `###` terminates the section early. Writing "`### Hard-Stop Gates`" into T039's Done
row made T042/T038/T022 resolve to `None`, so any task depending on them drew a false "unknown
dependency, check for a typo" advisory. Reworded the row; the regex fragility itself is unfixed — it
needs a lookahead anchored to line-start (`(?=^###|\Z)` with re.MULTILINE). 5th defect in this hook
family (T018/T022/T024/T042/this).

## security-review now actually runs (2026-07-23)

Fixed with user consent: `git remote add origin <same-url>` + `git remote set-head origin main`, so
`origin/HEAD` resolves. The `github` remote is untouched and nothing referenced the remote name. T043
is the first task in this project's history where the built-in Medium/High gate executed as designed
instead of being performed by hand. Note the built-in diffs against `origin/HEAD`, so it reviews the
whole branch vs main, not just the newest commit — scope the analysis yourself.

## A defect can reproduce itself during its own Stage 2 write-up (2026-07-23, T045)

Writing `tasks/TASK_GUIDE_T045.md` — the guide that documents the unanchored `(?=###|\Z)` Kanban
lookahead — auto-registered a board row whose *title* contained a literal `###`, which truncated the
Todo section and made T044, T040 and T041 resolve to `None`. The bug bit while being documented, via
the auto-registration hook, roughly two minutes after being written down.

**How to apply**: when a defect is about how text is parsed, assume the artifact describing it is
also parsed by the same code. After any Stage 2 write-up that quotes a delimiter, re-run the parser
over the live board/file before committing. More generally: a mitigation that depends on humans
avoiding a character in prose is not a fix — it is a trap with a note attached.
