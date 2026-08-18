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
- 2026-07-19 — **A failed `/compact` (login expired mid-compaction) does not mean lost work is gone — it means it's sitting uncommitted in a worktree you don't remember creating, or worse, silently reverted from your working tree with no trace.** Discovered live across three separate tasks in one recovery session, each requiring a *different* response: (1) an approved skill-file prune was fully lost — files back at original line counts, no commit, no worktree copy found anywhere — required a full redo; (2) a QA smoke-test task had a complete, correct, independently-verifiable implementation sitting uncommitted in a pre-existing worktree that `git worktree list` revealed but a fresh session start would never think to check for — required discover-and-reuse-with-independent-reverification; (3) a documentation task had an uncommitted working-tree edit whose Evidence table claimed the work was done and verified, but a live `grep` against the real file proved the claim false — required discard-the-false-claim-and-redo. You cannot tell which case you're in without checking `git worktree list`, `git status --short` in every worktree, AND independently re-verifying any claimed-passing Evidence against actual current file content before trusting it. A checkmark in an Evidence table is a claim, not a fact, especially after any session discontinuity. (source: this session, post-/compact recovery across three tasks)
- 2026-07-19 — `reports/` was fully gitignored (`reports/`) for "local-only HTML reports," but a tracked/shared artifact placed there (the DDR-0001 Token Audit Log, a `.md` file meant to accumulate across sessions and worktrees) silently failed to propagate: each Stage-3 spawn runs in its own isolated worktree, so a gitignored file written there never appears anywhere else, including after a clean merge. Discovered live when a freshly-merged worktree's own test suite failed on `main` immediately after merge — the source `.py` test file merged fine (it was git-tracked), but the `.md` data file it validated did not exist because it had only ever lived on-disk, ungit-tracked, inside the now-orphaned worktree directory. Fix required two parts: (1) change `.gitignore` from `reports/` to `reports/*` + `!reports/token-audit_*.md` — a directory-level ignore blocks git from ever evaluating negation patterns on that directory's contents, so the exception must exclude *contents*, not the directory itself; (2) manually copy the file forward from the old worktree path once, to seed history, since the file was never a git object before this fix. General lesson: before declaring any spawn-produced artifact "gitignored, local-only" as a design choice, check whether that artifact is meant to be read by a *different* worktree or session later — if so, gitignoring it silently breaks cross-worktree continuity with no error until something downstream fails to find it. (source: T0-two-eight review, `.gitignore`, `memory/decisions.md` 2026-06-18 entry amended 2026-07-19)
- 2026-07-17 — Shell footgun in ad-hoc test/verify commands: `VAR=val cmd1 | cmd2` only exports `VAR` into the environment of `cmd1`, NOT `cmd2` on the other side of the pipe — `SUPERVISOR_REPO="file://$FIXTURE" printf 'v\no\n' | bash update.sh` silently left `update.sh` with no override and it fell through to the real GitHub network default. Fix: `export VAR=val` (or wrap in a subshell) before the whole pipeline, not inline before just the first command. Caught mid-`verify` on T033 by noticing the log line showed the real `https://github.com/...` URL instead of the intended `file://` fixture. (source: T033 verify pass)
- 2026-07-17 — Reusable shell pattern for a script that must be BOTH interactively promptable and drivable by piped test input: read the interactive prompt from fd 0 (stdin) as normal, but loop over a generated file list via a *different* fd (e.g. `done 3< "$list"` / `read -r line <&3`) so the main loop's `read` never consumes the piped answers meant for the prompt. On stdin EOF, don't guess a default — treat it as "no input available," skip/preserve, and exit non-zero instructing an interactive re-run. (source: T033, update.sh's `process_files`/`prompt_conflict`)
- 2026-07-19 — `$0` is not a real file path when a shell script is invoked via `curl | sh` — `SCRIPT_DIR=$(dirname -- "$0")` silently resolves to the caller's cwd instead of failing loudly, so any script that sources a co-located file relative to `$SCRIPT_DIR` breaks in a piped context with no obvious error pointing at the real cause (T038: `setup.sh` broke the moment T031 split fetch logic into a separately-sourced `lib/harness-fetch.sh` — the primary documented `curl|sh` install command was silently broken from 2026-07-17 until a real user hit it 2 days later). **Any change that splits a monolithic script into a script + sourced-library pair must explicitly test the piped invocation path** (`cat script.sh | sh`, or the real `curl -fsSL <url> | sh`), not just checkout-based paths — the two have fundamentally different `$0` semantics, and only piped testing exposes the gap. (source: T038)
- 2026-07-21 — **Stage 2 artifacts must be committed before any Stage 3 spawn.** A git worktree branches from HEAD and therefore sees only *committed* state — a `tasks/TASK_GUIDE_Txxx.md` still sitting as an untracked working-tree file on the Supervisor's branch is invisible to the agent, which correctly halts under Hard-Stop Gate 1 ("no TASK_GUIDE = no work"). Cost a full 52k-token spawn to discover, and the failure looks like a missing guide rather than an uncommitted one, so it misdirects. Nothing in `CLAUDE.md` or `general-agent-template.md` states this. Best fix: a pre-flight check in `craft-spawn-prompt` (it already reads the guide path) asserting the guide is tracked AND has no uncommitted changes, before it emits the prompt. (source: T042 first spawn attempt)
- 2026-08-04 (T049) — **Committing the guide first isn't sufficient by itself.** `TASK_GUIDE_T049.md` was committed to `main` (`f39a1ec`) *before* the `Agent({ isolation: "worktree" })` spawn — yet the worktree still forked one commit behind, from `74e61f2`. The guide's content had also been pasted verbatim into the spawn prompt (per the mandatory element-2 requirement), so the agent worked around it by reading the file directly and no work was lost — but a task whose guide is only referenced by path, not pasted, would have hit Hard-Stop Gate 1 despite the Supervisor having done everything the existing 2026-07-21 learning recommends. The isolation mechanism's worktree-creation timing relative to the Supervisor's own commit is not fully synchronous. Treat "I committed it" as necessary, not sufficient — the guide's orienting content should still be pasted into the spawn prompt (already standard practice) as the actual belt-and-suspenders fix, independent of commit timing.
- 2026-07-21 — **`git diff --stat` reads clean for untracked files, so it cannot verify a sub-agent's completion claim.** T042's agent reported "implementation and verification complete"; the hook change was uncommitted and the entire new 311-line test file was untracked, so `git diff <base> --stat` showed only the hook and the test file appeared nowhere at all. Merging on that report would have brought across nothing. Always use `git status --short` (which shows `??` untracked) **and** `git log --oneline` to confirm the agent's commit exists — not `git diff --stat` alone. Third occurrence of the uncommitted-work pattern (T027 near-miss, T028 Ghostty marker, T042). (source: T042 Stage 4)
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

## A Bash command is never attributed by task-ID inference (2026-07-23 T043, resolved 2026-07-31 T047)

Since T043 both always-on hooks attribute structurally, so prose mentioning a Task ID in an Edit, a
Bash command, or a file you merely read no longer counts a step or files a trace record. The
retired workaround — bracket-globbing the ID (`T0[4]3.jsonl`) to dodge a literal-string match — is
no longer needed.

**Consequence, and the fix that took two tasks to find**: structural attribution means a `Bash`
command carries no task identity of its own, yet `pre_bash_block_unsafe_merge.py` requires a
non-error trace record in `memory/event-trace/<task>.jsonl`. The first prescribed fix — export
`CLAUDE_ACTIVE_TASK=Txxx` in the spawn wrapper — **does not work and was never possible**: hooks are
spawned by the harness as siblings of the tool call and inherit the harness env, not the command's
subshell. T047 replaced it with the `.claude/hooks/.state/active_task` file. Write that pointer
immediately before the command and clear it immediately after.

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

**Amendment (2026-07-31, T044) — "it runs now" is not "it applies now".** The built-in diffs *the
checked-out branch* against `origin/HEAD`. T044's work lived on `feat/hook-lifecycle-evidence` while
the repo sat on `main`, so invoking it would have diffed main-vs-main, found nothing, and reported a
clean result — a **false PASS on a mandatory gate**, which is strictly worse than the old failure
mode: the `origin/HEAD` breakage at least errored loudly, this one succeeds quietly. This is the
third distinct way this gate has failed to actually gate (never ran → ran → ran against nothing).

Rule: before invoking the built-in `security-review`, confirm `git branch --show-current` is the
branch under review. If it is not — the normal case when the Supervisor reviews from `main` while
work sits in a worktree — either check the branch out, or review the real `main...<branch>` diff by
hand and label it manual with the reason. Same discipline as "an assertion never observed failing is
not evidence": a gate that reports PASS over an empty diff has not been observed rejecting anything.

## A defect can reproduce itself during its own Stage 2 write-up (2026-07-23, T045)

Writing `tasks/TASK_GUIDE_T045.md` — the guide that documents the unanchored `(?=###|\Z)` Kanban
lookahead — auto-registered a board row whose *title* contained a literal `###`, which truncated the
Todo section and made T044, T040 and T041 resolve to `None`. The bug bit while being documented, via
the auto-registration hook, roughly two minutes after being written down.

**How to apply**: when a defect is about how text is parsed, assume the artifact describing it is
also parsed by the same code. After any Stage 2 write-up that quotes a delimiter, re-run the parser
over the live board/file before committing. More generally: a mitigation that depends on humans
avoiding a character in prose is not a fix — it is a trap with a note attached.

---

## A guard is only as strong as the layer that feeds it (2026-07-30, T044 Stage 4)

T044's `invokes_test_runner` was correct: anchored at a command head, quoted spans stripped,
separators split. Stage 4 review still found the gate accepting a claim — because the *bug was one
layer below the guard*. `extract_command` handed it a string that was never a command: on any record
past `post_tool_trace.py`'s 300-char truncation the summary stops being valid JSON, and the regex
fallback took everything after `"command": "` without stopping at the value's closing quote. The
`description` field — agent-authored prose — leaked in, a `;` inside it created a command boundary,
and `pytest` in that prose became a command head. Defect C, reinstated through a side door.

**How to apply**: when reviewing a validator, do not stop at whether the matching logic is right.
Ask what constructs its input, and whether that construction can ever be wrong. A hardened matcher
fed a corrupted string is a hardened matcher that passes garbage. Concretely: any hand-rolled
`field": "` extraction over possibly-truncated JSON must bound itself to that field's value —
`(?:[^"\\]|\\.)*` — or it silently concatenates siblings. This is the 4th time this project shipped
a guard whose *unexercised path* was the hole (T036/T042/T039 were vacuous assertions; this one was
a real assertion over a wrongly-built input).

## Reverting a mutation with `git checkout` also reverts your fix (2026-07-30, T044)

Mutation-testing a Stage-4 fix means editing the file you just fixed. `git checkout <file>` to undo
the mutation restores the *committed* state — which does not contain the uncommitted fix. The suite
went green again and looked correct, but the fix was gone. Caught only because the diff was
re-checked before commit.

**How to apply**: commit the fix *before* mutating it, and revert the mutation with `git checkout`
against that commit — or save/restore a copy (`cp file /tmp/x.bak`) instead of using git. Always
re-run the full suite AND re-read the diff after a mutation cycle; "tests pass" is exactly what a
silently-reverted fix looks like.

## The merge gate blocks on prose, not just commands (2026-07-30, hit live)

`pre_bash_block_unsafe_merge.py` tests `BLOCKED_PATTERNS` against the *entire* `command` string. A
heredoc that writes documentation is still one Bash command, so appending a memory entry whose prose
contained the literal words "before `git merge`" was blocked by the pipeline gate — while T044 was
legitimately In Progress. The gate was working exactly as written; the input was never a merge.

This is the same family as "never quote a `###` heading inside a KANBAN row": a tool that pattern-
matches text will match the text that *describes* it. Documentation about a guarded operation trips
the guard.

**How to apply**: write file content with the Write tool, or stage it to a scratchpad file and
`cat tmp >> target` — the command string then contains only paths. Do not reword the documentation to
dodge the pattern; the prose should stay accurate and the writing method should change. Worth
considering whether `BLOCKED_PATTERNS` should ignore text inside a heredoc body, but that means shell
parsing — the same complexity T044 deliberately refused, and fail-closed here costs only a retry.

## An env var set inside a Bash tool call is invisible to hooks (2026-07-31, T044 → T047)

Claude Code spawns hook processes as **siblings** of the tool call, so a hook inherits the *harness's*
environment — not the environment the Bash tool builds for the command it runs. Both documented forms
therefore do nothing for attribution:

    CLAUDE_ACTIVE_TASK=T044 python3 -m pytest -q     # scoped to pytest's process
    export CLAUDE_ACTIVE_TASK=T044                   # scoped to that tool call's subshell

`task_context.py:resolve_task_id` reads `os.environ` in the hook process, sees nothing, and every
`Bash` record lands in `_untagged.jsonl`. Observed 2026-07-31 running T044's own verification command
from main at `de120da`: `T044.jsonl` mtime unchanged, the command visible in `_untagged.jsonl`,
`trace_shows_verification('T044') = False`.

Consequence: T044 tightened the merge gate *and* shipped the mechanism meant to keep it from failing
closed on honest work — but that mechanism is inert, so the gate now blocks every honest local merge.
T044 itself merged only via the GitHub UI, which never invokes the local PreToolUse hook, so the
tightened gate went unexercised on a real merge for a week. **Update 2026-07-31**: it finally ran, on
the local `git merge docs/stage2-t047` that consolidated T047's branches — and **allowed** it, having
found T047 closed on the Kanban plus a qualifying trace record. First real exercise of the T044 gate
in either direction. Note it ran from the worktree, so it read the *worktree's* `memory/event-trace/`;
a merge run from the main checkout reads a different trace dir. → T047 (C1/Medium/**P0**). T040
re-blocked on it: it would otherwise build a token-audit window on records that are all untagged.

The general rule: **an agent cannot set environment state for a hook from inside a tool call.** Any
per-task signal a hook must read has to travel through a channel the agent can actually write —
a file, or harness configuration — not process environment.

## Patching a channel in a test does not prove the channel works (2026-07-31, T047)

T044's 42 tests are green and its mutation controls were all observed RED, yet AC7 shipped inert. The
tests exercise `resolve_task_id` with a **patched `os.environ`**, which validates the precedence
logic but never crosses the real harness→hook *process* boundary — and the boundary is exactly where
the defect lives. Every layer of the project's evidence discipline held; none of it was pointed at
the failing seam.

Rule: when a mechanism spans two processes, a unit test that patches the channel proves the logic,
not the plumbing. At least one acceptance check must be a **real end-to-end run** through the actual
path an agent uses. Same family as "a guard is only as strong as the layer that feeds it" — and note
this is the second consecutive T044-related defect found *below* the logic under review, not in it.

## A test that shares a root cannot detect a root-split defect (2026-07-31, T047 Stage 4)

T047 fixed trace attribution with a state file at `.claude/hooks/.state/active_task`, and shipped an
instruction telling agents to write it with a **cwd-relative** redirect. But `ACTIVE_TASK_FILE` is
absolute, resolved off `__file__` of the copy that executes, and the harness runs hooks from
`$CLAUDE_PROJECT_DIR` — the **main checkout**. A Stage 3 sub-agent's cwd is its **worktree**. So the
agent writes one file and the live hook reads another, and every honest task still lands in
`_untagged.jsonl`.

It survived implementation *and* the implementer's own end-to-end check because both ran **inside the
worktree**, where the two paths collapse to the same root. The check was real — it just could not
distinguish the passing case from the failing one, because the split it needed to exercise was
flattened by where it ran.

Rule: when a mechanism spans two roots (worktree vs main checkout, container vs host, test tmpdir vs
real path), a test executed inside one root proves nothing about the split. The regression test must
straddle the boundary. This is the vacuous-assertion family again (T036/T042/T039) and the third
consecutive defect in this subsystem found *below* the logic under review — after T044's
`extract_command` and T044's own AC7. **The feeding layer keeps being the defect, and the reviewer's
own test setup can itself be the feeding layer.**

Corollary for the Supervisor, learned the hard way in this same review: verifying a not-yet-merged
fix by running the **main checkout's** hook tests the OLD code and proves nothing. Run the worktree's
copy, or state plainly that the check was inconclusive. Two of my own "confirmed" results in this
review were invalid for exactly that reason, and a third was contaminated by a pre-existing trace
file I assumed I had created.

## $CLAUDE_PROJECT_DIR exists for hooks but is EMPTY in an agent's Bash tool call (2026-07-31, T047)

Two different environments, easily conflated. `settings.json` invokes every hook as
`python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/x.py`, and the harness expands it there — so a hook
process reliably sees it. An agent's own `Bash` tool call does **not**: `echo $CLAUDE_PROJECT_DIR`
prints empty. Confirmed independently by the Supervisor and the implementing agent.

Consequence for any read/write pair spanning that boundary: the **hook** side can resolve paths from
the variable, but the **agent** side cannot. Instructing an agent to write to
`$CLAUDE_PROJECT_DIR/...` verbatim ships a defect symmetric to the one being fixed. The working shape
is: hook resolves via the env var; the Supervisor embeds a **literal absolute path** into the spawn
prompt at assembly time (its own session already runs from the main checkout).

## A "never raises" contract does not cover module import (2026-07-31, T047 Stage 4)

`task_context.py` documents that `resolve_task_id` never raises — and it doesn't. But
`ACTIVE_TASK_MAX_AGE_S = int(os.environ.get(...))` ran at **import**, one layer below the contract.
A value of `6h` raised `ValueError` before any function was reached, and because both callers wrap
`from task_context import ...` in `except Exception` (correct fail-open), attribution silently died
**repo-wide** — including the path-field precedence that has nothing to do with that setting. A
narrow, opt-in env var could disable a whole subsystem, silently, with a green test suite.

Rule: when a module advertises a never-raises contract, the module-level statements are part of that
contract's surface. Parse env vars and other external input defensively at import, or move the work
into the function the contract actually covers. Corollary: a caller's fail-open `except Exception`
around an import converts a loud crash into a silent capability loss — good for stability, bad for
detection, so the thing being imported must not rely on it.

**Fourth consecutive defect in this subsystem found one layer below the logic under review**
(T044 `extract_command`'s input → T044 AC7's channel → T047's channel path → T047's import-time
parse). Every fix was correct; the feeding layer was wrong each time. Worth a task that exercises the
guardrail chain end-to-end through the real harness path rather than patching one seam at a time.

## A feature whose test suite only passes while the feature is unused (2026-07-31, T047 → T048)

T047's state-file channel works — verified end-to-end on `main`: a real `Bash` tool call was
attributed to `T047.jsonl` and `trace_shows_verification('T047')` returned True, the first correct
attribution of a Bash tool call in this project's history. But arming the channel *as the shipped
instruction requires* turns the hook suite red:

    no state file   -> 121 passed
    armed           ->   9 failed, 112 passed
    removed again   -> 121 passed

Cause: T047 added a `StateFileOverride` isolation helper and used it **only in its own new tests**.
Nine pre-existing T043-era tests read the real `ACTIVE_TASK_FILE` and assert what the *lower*
precedence slots resolve to; once slot 2 has a real file it short-circuits them all. Production logic
is correct — slot 2 winning is the design. The damage is to the workflow: `pytest .claude/hooks/tests/`
is the verification command in the TASK_GUIDE template, what Hard-Stop Gate 5 needs pasted output
from, and part of what the merge gate looks for. So T047's two halves conflict for every future task.
→ T048 (C1/Medium/**P0**).

Rules this yields:
1. **When a change adds global/ambient state, the suite must be run in both states before calling it
   green.** A suite proven only in the state where the new feature is *off* has not been proven.
2. **An isolation helper added for new tests is a signal that existing tests need it too.** Adding
   `StateFileOverride` and applying it to only the new cases is the tell — if the new code needs
   isolating from ambient state, everything sharing that module does.
3. Ambient repo state is not a clean-machine assumption any more: the workflow now *instructs* agents
   to create this file, so tests must assume it exists.

Fifth consecutive defect in this subsystem sitting one layer below the logic under review, and the
first found only because Stage 5 verify was run in the real post-merge environment rather than
re-trusting the worktree's green run.

## An importlib-loaded module is a different object from the imported one (2026-07-31, T048)

`test_task_context.py` loads the module under test via
`importlib.util.spec_from_file_location(...)` rather than a plain `import`, so the resulting module
object is **not** the one a plain `import task_context` elsewhere would produce and is not shared via
`sys.modules`. Consequence for test isolation: a `conftest.py` fixture that imports the module
normally and mutates a module-level constant (`ACTIVE_TASK_FILE`) would be patching a *different
copy* — the fixture runs, reports success, and the test still reads the real value. Silently inert,
and it would look like the isolation worked.

This is why T048 put its autouse fixture in the test module itself rather than `conftest.py`. Rule:
when patching module-level state for a module loaded by `spec_from_file_location`, the patch must
target the same object the test holds. Check module identity before trusting a fixture that appears
to do nothing wrong.

## Nest isolation at the test-function level, not inside the shared helper (2026-07-31, T048)

The tempting fix for ambient state is to wrap the shared `resolve()` helper so every call is
isolated. That breaks the tests that *want* the state armed: their explicitly-armed override would be
clobbered by the helper's internal default, and every real slot-2 assertion would silently start
reading nothing — coverage deleted while the suite goes green. Wrapping each **test function**
instead makes isolation the default for anything written tomorrow (the goal) while letting a test's
own explicit `with` block nest inside and win for its duration.

Generalizes: default isolation belongs at the outermost boundary of a test, where an explicit opt-in
can still override it — never inside a helper the tests share, where it competes with their intent.

## Two single-line MANIFEST additions will conflict even with zero real overlap (2026-08-04, T051)

T049 added `docs/claude-md` to `MANIFEST`; T051 (spawned from a worktree forked before T049 merged)
independently added `AGENTS.md`. Both inserted their line right after the same `templates` line —
git's merge sees two different additions at the identical position and conflicts, even though the
two lines don't touch each other's content at all. Not a defect in either task, not something
`craft-spawn-prompt`'s pre-flight check would catch (both guides were valid, both diffs were
correctly scoped) — it's the structural shape of append-only files edited by concurrent
worktree-isolated tasks. Resolution is trivial (keep both lines) but expect it whenever two Stage-3
tasks in flight at once both touch `MANIFEST`, `PROJECT_KANBAN.md`'s own section boundaries, or any
other single shared append point.

## A guard can lock out the only role able to release it (T053/T055, 2026-08-06)

`pre_agent_step_limit` keys its counter off the shared `.claude/hooks/.state/active_task`. When the
T055 agent exhausted its 40-call budget, every session that inherited the stale ID was killed —
including the Supervisor's. The hook's own message says "Supervisor: reset
`.state/step_count_T055.txt`", but the Supervisor could not: `Bash` and `Read` were both blocked, and
the reset needs a tool call. Recovery required the user to intervene manually.

Two lessons:
- A kill-switch must exempt the role its own remediation message addresses, or it is a deadlock.
- **The `Write` tool was never gated while `Bash` and `Read` were.** Overwriting the counter with `0`
  released the block. When a hook appears to have blocked everything, probe other tool families
  before escalating — the gate is rarely as total as it looks.

## A worktree agent structurally cannot write the main-checkout state path (T053, 2026-08-06)

`craft-spawn-prompt` element 6 instructs the agent to write an absolute main-checkout path. A
worktree-isolated agent's sandbox **refuses** it and redirects to the worktree copy, which the hooks
never read. So the mandated attribution instruction is unfollowable by exactly the agents it targets;
the agent then inherits whatever ID another agent left in the shared file. This is the root of the
T056 race — not merely concurrent writes, but that the correct write is impossible. Do not "fix" this
by rewording the instruction; the channel itself needs to be per-worktree.

## `isolation: "worktree"` forks from **main**, not the current branch (2026-08-06)

Confirmed by three spawns: every Agent-tool worktree came up at `main` (`8f19a45`) while the working
branch was many commits ahead. So a guide committed on a feature branch is **invisible** to the agent
you spawn for it — T053, T055 and T056's first two spawns all landed in trees without their own
TASK_GUIDE. My first read of this was "forked one commit behind"; that was wrong and made it look
like a timing problem. It is not timing — it is a fixed base, and no amount of committing earlier
fixes it.

Two things that work:
- Put a `ls tasks/TASK_GUIDE_Txxx.md` self-check at the top of every spawn prompt with an explicit
  STOP instruction. T056's third spawn halted correctly instead of inventing the task from the
  prompt's orienting content.
- For branch-based work, create the worktree yourself off the branch tip
  (`git worktree add -b <name> <path> HEAD`) and spawn **without** `isolation` — the Agent tool would
  otherwise create a second worktree and orphan yours (already recorded).

## Parallel spawns onto a known-open race are the Supervisor's error, not the agents' (2026-08-06)

Memory had carried the shared-`.state` race as open since T047. Spawning T053 and T055 concurrently
turned a documented risk into a session-halting failure that cost both runs. When memory flags a
concurrency risk as open, serialize until it is closed — the parallelism saved nothing here and cost
two full agent runs plus a manual recovery.

## The Kanban is test-covered — editing it after the last test run pushes red (2026-08-06)

`test_find_kanban_section_on_real_current_board` reads the **live** `PROJECT_KANBAN.md` and asserts
every `- [x]` row resolves to Done. Marking T053/T055 `[x]` while placing them in Ready for Review
turned the suite red at 158/159 — and it shipped, because the final board edits came after the last
`pytest` run and the commit went out unverified. `[x]` means Done on this board; Ready for Review
uses `[ ]`.

The board is not an inert document — it is an input to the hook suite. Any Kanban edit is a code
change for testing purposes: re-run `pytest` after it, not before. Third recorded instance of
evidence that named a commit without being re-run at that commit (T035, T039).

## A counter with no reset path is a landmine with a fuse, not a guard (T056, 2026-08-06)

`post_agent_move_to_review.py` was made inert in T044 for a correct reason (no completion event
carries task identity) — but nothing replaced it as the resetter, so every step counter grew forever.
The failure did not look like "counter never resets"; it looked like three unrelated random
lockouts, one of them caused by a task that had been Done for hours. When a guard's state has no
automatic path back to its safe value, the guard's real behaviour is "eventually blocks everything",
and the delay before that hides the cause.

Whenever a component is deliberately disabled, ask what it was the *only* thing doing. T044 answered
"it can't write the Kanban correctly" and stopped there; the counter reset it also owned went
unnoticed for weeks.

## Clean up your own attribution pointer after a verification run (2026-08-06)

Twice this session the poisoning `active_task` pointer was one the *Supervisor* wrote for its own
verification run and left armed. Counters accrue against whatever it names, and the next session
inherits it. Write it immediately before a verification command, clear it immediately after — the
6h staleness window is far too long to rely on when several tasks run in one session.

Caught the third instance at **39 of 40** calls, one away from another lockout.

## A sub-agent inherits its parent's `session_id` (T054, 2026-08-06)

T056 keyed step counters by `session_id` to stop one task's exhausted budget blocking other sessions.
It works for unrelated sessions — but a spawned agent runs under the **parent's** `session_id`, so the
counter `step_count_<parent-session>_T054.txt` blocked the Supervisor as well when the agent spent its
42 calls. Agent-vs-parent is the pairing that actually occurs in this pipeline; agent-vs-unrelated is
the rare one. A fix keyed on session identity must include something that distinguishes agent from
spawner. → **T057**.

Corollary on sizing: 40 calls was demonstrably too low for a ~7-file C2 task. The agent made concrete
forward progress on every call and still died before its first commit. Either raise the limit for
multi-file tasks or split them — "commit early and often" does not help an agent that runs out before
commit #1.

## An AC can be written against a file's older shape (T054, 2026-08-06)

T054's AC9 required `MANIFEST` to gain the new skill and template paths. But MANIFEST lists
*directories* copied with `cp -r`, so both already deployed; adding the paths would have been
redundant and inconsistent with every other line in the file. Satisfying the AC literally would have
made the repo worse. Check the file the AC describes before treating the AC as ground truth — and
record the deviation in the Evidence, don't silently skip it.

## A guard's value is measured against its actual record, not its intent (T057, 2026-08-06)

The step-limit hook's lifetime record: 4 hard lockouts of the Supervisor, ~an hour of manual
recovery, 2 lost agent runs, 0 runaways caught. Kept at full strength it would have kept costing that.
The right move was to deliberately weaken it and say so in the guide, not to keep hardening a guard
whose failure mode was more expensive than the thing it guarded against. When a safety mechanism has
a measurable history, weigh the change against that history rather than against the hazard it was
imagined to prevent.

## An agent that stops on failing tests is doing the most valuable thing it can (T057, 2026-08-06)

T057's agent found 8 pre-existing failures and halted with a written reason instead of editing them
green — exactly what AC9 asked. That single decision is what made the outcome trustworthy: had it
"fixed" them, the suite would have gone green while quietly deleting SC2's coverage. Two follow-ons:
- Put an explicit "do not modify existing tests, STOP and report" instruction in every spawn prompt.
  It cost one round-trip and bought a real review.
- **Verify the agent's reasoning anyway.** "These tests contradict the new design" is exactly the
  claim that launders a regression. Each of the 8 was checked individually before being touched.

## Stale Evidence is false Evidence once the blocker is resolved (T057, 2026-08-06)

The agent honestly filled the Evidence table with `verify | fail | 8 failed, 180 passed` while the
test conflict was open. After the Supervisor resolved it, that row was no longer honest — it recorded
a state that no longer existed, and the merge gate scans that exact cell. Evidence written mid-blocker
must be re-written when the blocker clears, not left as a historical note. 4th Evidence-integrity
incident (T035 false claims, T039 unre-run command, T053 weak-advisory, now this).

## A test that writes to a tracked repo file is invisible where you run it and destructive where you don't (T059, 2026-08-06)

`.claude/hooks/tests/test_token_audit_generator.py:235` requests the `tmp_path` fixture and then
ignores it, calling `token_audit.generate_report()` with `ROOT / "reports" / "token-audit_2026-07-21.md"`
— the real tracked file. In the **main checkout** `memory/event-trace/` is populated, so regeneration
only ever appends and the damage shows up as nothing worse than a permanently dirty working tree
(this is why it survived undetected; it was already dirty in this session's opening `git status`).
In a **worktree** the trace dir is gitignored and therefore empty, so the identical call writes an
empty Entries block over all 106 derived entries. A sub-agent's commit swept up the clobbered file and
did not report it. The lesson is not "the agent was careless" — re-running the suite reproduced it
deterministically, which is what proved the cause was the suite, not the agent. **Check whether a
test writes anywhere outside `tmp_path` before trusting a clean-looking suite, and diff every file in
an agent's commit against the guide's predicted file list.** Registered as T059.

## Prior art can reframe a task after Stage 2 has already locked it (T058, 2026-08-06)

The user pointed at `github.com/millionco/debug-agent` *after* the guide was written, committed, and
about to be spawned. Reading it turned a text edit into a design change and moved the task C1 → C2.
Nothing was wasted — the guide was rewritten and re-committed before the spawn — but the cheaper
order is to search for an existing implementation of the idea during Stage 0.5, not after Stage 2.
The general-agent-template's Search-Before-You-Build ladder covers this for *implementers*; it does
not currently fire for the Supervisor writing a guide.

## Retiring a convention touches more places than the AC table enumerates (T058, 2026-08-06)

T058's AC11 named Phase 6's cleanup checkbox as the one place referencing the retired `[DEBUG-xxxx]`
prefix. It also lived in the Karpathy Surgical-Changes override on line 13 — outside the predicted
diff and outside every "Files Must NOT Touch" entry. The implementing agent found it, changed it, and
flagged it rather than burying it. **When retiring a token or convention, grep the whole file for it;
do not trust the predicted diff.** The test that caught it (`"[DEBUG-" not in text`, asserted
file-wide because it is a *negative*) is the rare case where a file-wide substring assertion is the
correct instrument.

## A section-body checksum needs a length floor beside it (T058, 2026-08-06)

Pairing `sha256(body)` with a minimum-length assertion and a non-empty guard inside the extraction
helper closes T039's vacuity mode, where both sides extracted empty and empties compared equal.
Strictly the hash alone suffices when the expectation is a hardcoded digest (an empty body hashes to
something else), but the floor makes the failure message say *truncated* rather than *changed*.
Fourth recorded instance of the vacuous-assertion family.

---

## Two T046 process gotchas, both re-confirmations (2026-07-24, T046)

> Recovered 2026-08-07 from `stash@{0}`, uncommitted since T046 merged.

**The Ghostty spawn marker silently failed again.** The sub-agent finished correct work (2 commits)
but the `.done` marker was never written and the wait-loop reported nothing. Verifying the worktree
with `git status --short` + `git log --oneline` directly is the only trustworthy signal. Third
occurrence after T027 and T028.

**`git checkout -- <file>` is blocked by the git-guardrails hook**, not just `checkout .`. An
attempt to discard an uncommitted `PROJECT_KANBAN.md` scratch edit was silently refused, leaving the
task showing In Progress, and the merge gate correctly rejected the merge. To revert an uncommitted
tracked file while the guardrail is active, re-edit it back by hand with the Edit tool rather than
`git checkout`.

## Kanban merge hygiene when both sides touch the board (2026-07-24, T046)

The Supervisor's live board edits (move task to In Progress) and the branch's board edits (move to
Ready for Review) both change the same rows relative to the merge base, which conflicts on
`--no-ff`. Clean path: before merging, restore the Supervisor-side `PROJECT_KANBAN.md` to match the
merge base so only the branch changed it, merge, THEN move the task to Done on the merged result and
commit. Do NOT pre-move to Done on the Supervisor side before merging — that reintroduces the
same-row conflict.

## The register hook stubs a Kanban row you are about to write by hand (2026-08-07, T059/T060)

`post_write_register_task.py` fires on the Write of a `tasks/TASK_GUIDE_Txxx.md` and auto-registers a
minimal Todo row. If the Supervisor has already written a detailed row for that task, the board ends
up with **two** rows for one task — a bare stub (`title | agent | C2 | Risk | P1`) and the real one.
Both landed committed in T060's Stage 2 commit and were only caught later by eyeballing the board
structure. The stub sorts *above* the detailed row, so a casual read sees the uninformative one.

After writing any TASK_GUIDE, re-read the Kanban section before committing. The Kanban is
test-covered, but the covering test asserts section parsing, not row uniqueness — nothing catches a
duplicate ID.

## A memory pass is uncommitted work like any other, and stashes hide it (2026-08-07, T046)

T046 shipped on 2026-07-24 (`bf23413`, feature live in the template, Kanban row under Done) but
`grep T046 memory/` returned **zero hits** two weeks later. Its entire memory pass — a 44-line
decision entry and two learnings — had been stashed and forgotten. The task looked complete by every
signal that normally gets checked: merged commit, passing tests, closed board row.

The three recorded uncommitted-work gotchas all concern *implementation* left in a worktree. This is
the same failure applied to the audit trail, and it is harder to notice because nothing downstream
fails when memory is missing. Audit `git stash list` during any recovery pass, and treat a memory
write as part of the task, not as bookkeeping that can trail it.

## A review fix can be as unpinned as the defect it fixes (2026-08-07, T060 Stage 4)

The P2 fix scoping `traceparent` out of the empty-inventory case passed the entire suite while
asserting nothing — mutating the new sentence to its opposite stayed **GREEN**. The reviewer had
reproduced, at the moment of fixing, the exact gap the review had just found: T058's own Stage 4 P2
was three constraints the guide called load-bearing with no assertion pinning them.

Mutation-test the *fix*, not only the original implementation. A Stage 4 fix ships with no test of
its own unless someone writes one, and the suite going green after a review fix means nothing about
whether the fix is guarded. Fifth instance of the vacuous-assertion family.

## When a test pins prose, fix the prose around it, not the test (2026-08-07, T060 Stage 4)

The first attempt at the P2 fix reworded the NDJSON payload field list and broke a test asserting
that exact comma-separated string. The tempting move — loosen the regex — would have deleted the
coverage that made the list stable in the first place. The right move was to leave the pinned string
byte-identical and add the scoping as a following sentence.

A failing assertion after a review fix is a question about the fix, not a defect in the test. Same
family as "don't reword the docs to dodge the merge gate."

## A fixture can claim provenance it does not have (2026-08-07, T061 Stage 4)

`test_post_tool_trace_spawn.py`'s docstring said its Agent payload was "pinned to the 2026-08-07
probe capture". Its nested keys were invented: `ephemeral_5m` where the real harness sends
`ephemeral_5m_input_tokens`. Every test passed, because the implementation had been written against
the same wrong names — the fixture and the code agreed with each other and neither agreed with
reality.

It surfaced only because the Supervisor still had the raw probe dump and drove the hook with the
*actual* payload. A field written against that fixture would have silently never populated in
production, with a green suite the whole time.

**Rule**: when a test claims to be pinned to a captured payload, keep the capture and diff against it
— a provenance claim in a docstring is not provenance. Related to "patching a channel in a test
doesn't prove the channel works", but distinct: here the channel was real and the *fixture* was
counterfeit.

## Volume is not cost when nearly everything is a cache read (2026-08-07, T061 investigation)

Two probe arms, same trivial work, varying only the unique prompt size: arm A 29 unique tokens →
15,669 total / 15,259 cache_read / 405 cache_creation; arm B 1,144 unique tokens → 16,981 / 16,572 /
404. Adding 1,115 tokens of novel prompt text moved `cache_creation` by **−1**.

Unique per-task content is *not* paid at creation rates — the spawn prompt is already inside the
Supervisor's cached context before the agent starts. So trimming injected context (MEMORY.md, guides,
CLAUDE.md) is worth roughly a tenth of its nominal token count.

What survives is the floor: **every spawn costs ~15.7k tokens before doing any work** (15,669 for a
single `echo`), against 48,401 for T059's real three-line fix and 81,220 for T060. The lever is spawn
*count*, not spawn *content*. Recorded from n=3 synthetic spawns — directional, not established.

## Measure before optimizing, but check the measurement is not already arriving (2026-08-07)

DDR-0001 spent two measurement windows failing to capture cost-per-task by hand from `/cost`, and
DDR-0002 retired the effort. The `Agent` tool had been returning `totalTokens`, `totalToolUseCount`,
a full cache-split `usage` and a `toolStats` block on every spawn the whole time, and
`post_tool_trace.py` had been receiving and discarding it across 42 spawns.

Before building an instrument, dump one raw payload of whatever the harness already hands you. The
cheapest instrument is the one you are already being given and throwing away.


## An empty Todo column can mean "never registered", not "nothing left" (2026-08-07)

After T061 merged, `PROJECT_KANBAN.md` read 0 Todo / 0 In Progress / 59 Done, and the user reasonably
read that as the harness refactor being finished. It was not: T061 shipped *measurement only* and is
scoped in its own guide as "this task captures; it concludes nothing". The five directions that would
actually change performance existed solely as prose in `BRAINSTORMING_LOG.md`.

Hard-Stop Gate 3 covers the opposite failure — work that is done but still shows Todo. It says
nothing about a direction that has been decided, prioritised and recorded but never turned into a
row, and that gap makes the board silently overstate completeness.

**Rule**: when an ideation or planning session ends with a selected direction, register its items on
the board in the same session, even when every one of them is blocked or gated. A blocked row is
information; an absent row is a false all-clear.

## An assertion can be non-vacuous against one mutation and vacuous against another (2026-08-07, T067 Stage 4)

T067's line-cap assertion computed `read_skill().rstrip("\n").split("\n")`, which strips **all**
trailing newlines. The implementer mutation-controlled it by appending 20 *non-blank* padding lines —
RED, control passes, assertion looks sound. The Supervisor appended 12 *blank* lines, taking the file
to 167 by `grep -c ''`, and the suite stayed **green**: the padding was stripped before counting,
while the docstring claimed the whole file was counted.

A single mutation proves an assertion is not *entirely* vacuous. It does not prove the assertion
measures what it says. Choose mutations that attack the *stated* metric from more than one direction,
especially for cheap guards like counts and substring checks — and this is a concrete reason the
implementer must not be its own sole oracle, since it will naturally pick the mutation its own mental
model suggests. Sixth entry in the vacuous-assertion family.

## The merge gate evaluates the whole Bash command string before any of it runs (2026-08-07)

Closing the Kanban and merging were chained in one `Bash` call (`python3 ... && git add && git commit
&& git merge`). `pre_bash_block_unsafe_merge.py` inspects the command string *before* execution, so
it saw the board as it still was on disk — T067 In Progress — and blocked the entire call. Nothing
ran, including the board edit that would have satisfied it.

The recorded rule "close the task on the Kanban BEFORE `git merge`" means **in a separate tool call**,
not merely earlier in the same command. Same family as the gate blocking on prose in a heredoc: the
guard reads the string, not the intent.

## Two errors that cancel look more convincing than the truth (2026-08-07, T063)

Reconciling T067's agent-reported tool mix against the trace, T063's first cut produced a perfect
`33 == 33` across all four rows. It was wrong: the unwindowed bucket still held the Supervisor's
pre-spawn guide `Write`, which exactly compensated for one missing agent edit. The windowed — correct —
reconciliation leaves a 1-call residual that is still unexplained.

A *perfect* agreement between two independently-derived numbers deserves more suspicion than a close
one, especially when both sides were assembled by the same person. Ask what could be wrong on both
sides at once before accepting it.

## A mutation that does not take effect proves nothing (2026-08-07, T063 Stage 4)

The Supervisor's AC9 control appended a file write to the end of `memory_usage_report.py` and the suite
stayed **GREEN**, which looked like a real gap in a load-bearing guard. The mutation was inert: the
write sat *after* `if __name__ == "__main__": sys.exit(main())`, so it never executed. Re-inserted
inside `main()`, it turned both guards RED immediately.

Before trusting a GREEN result from a mutation control, confirm the mutation actually changed
behaviour — here, that the file was really created. This is the mirror of the vacuous-assertion family:
there the assertion is empty, here the *stimulus* is. A false "the test is weak" finding is as costly
as a missed one.

## A naive metric can measure your own process instead of the thing (2026-08-07, T063)

"5 of 49 tasks show a `MEMORY.md` read" read like strong evidence that agents ignore injected memory.
It was measuring *when the active-task pointer gets armed*: `craft-spawn-prompt` element 6 arms it
before the first verification command, which is after the mandatory startup reads, so every agent's
memory read lands in `_untagged` (30 of them) rather than under its task.

When a metric derived from instrumentation gives a striking answer, first ask which of *your own*
process steps it could be measuring instead. Third instrument-validity failure in this repo after
DDR-0001 and DDR-0002.

## A hook that blocks via stdout JSON fails OPEN when it raises (T064, 2026-08-09)

`pre_bash_block_unsafe_merge.py` signals a block by printing a `decision: block` object on **stdout**
and exiting **0**. So an uncaught exception — an `ImportError` at module level, say — exits 1 with
*empty* stdout, which the harness reads as a non-blocking hook error, and the guarded command
**proceeds**. T064 shipped the new resolver as an unguarded import carrying a comment stating the
absence of a `try/except` was what made the gate fail closed. It made it fail open, in the one place
the task's own AC7 designated as must-fail-closed. Reproduced directly: hide the lib file, feed the
hook a merge payload → `exit=1`, `stdout=[]`.

The general rule: **for a hook, "fail closed" is a thing you must actively emit, never something you
get by declining to catch.** If the block channel is stdout, an exception silences the block. Catch
it and print the block explicitly.

Also note the failure exists **only at module-import time**, so an in-process `import` of the hook
cannot exercise it — the test has to run the hook as a subprocess. Same family as "patching a channel
in a test doesn't prove the channel works". 4th distinct way this gate has failed to gate.

## A test can pin a section's *location*, and a move-shaped task cannot pass it (T064, 2026-08-09)

Two pre-existing tests asserted the `verify` Evidence row was present in
`templates/TASK_GUIDE_template.md` and in `bugfix/SKILL.md` — the exact files T064's ACs vacate. No
amount of correct implementation satisfies both the AC and the test; only a test edit resolves it.
This is **distinct** from the recorded "when a test pins prose, fix the prose around it, not the
test": there is no prose to fix, only a file path.

Resolution that keeps the coverage: repoint the assertion to the new location with the asserted
string **byte-identical**, and add a negative assertion that the old location no longer carries it,
so the move cannot silently revert. Do not delete the test.

**Stage 2 pre-flight for any move-shaped task**: grep the suite for the file paths the task will
vacate, and list the hits in the guide as expected escalations. T064's guide did not, so the agent
found them at implementation time — it escalated correctly rather than editing them green, which is
the behaviour to keep asking for.

## A percentage claim needs more than one sample (T064, 2026-08-09)

T064's AC15 asked for "≥25% smaller for a guide of T060's shape". Measured across five real guides,
four cleared 25% (30.5–33.6%) and one came in at **16.3%** on an unusually large `## Approach`. A
single-guide measurement would have supported a stronger claim than the data does. State the range
and name the outlier; a control (one-line sections) measuring −0.4% is what shows the metric
discriminates at all.

## A test helper can re-implement the logic it is meant to test (T068, 2026-08-09)

T068's new test file defined `row_is_filled()` which walked `VERIFY_ROW_PATTERN` and applied
`UNCHECKED_PASS_PATTERN` itself, instead of calling the shipped `has_filled_verify_row()`. It even
degraded defensively — `match.group("result") if "result" in match.groupdict() else match.group(0)`,
`getattr(merge_gate, "UNCHECKED_PASS_PATTERN", None)`. All 8 assertions therefore tested a **copy of
the logic living in the test file**, and the copy was correct, so everything looked green and the
mutation controls even went RED.

Proof it was vacuous: mutate the **real** function to ignore `UNCHECKED_PASS_PATTERN` — restoring the
exact defect the task exists to fix — and the full suite stayed at `326 passed`. After rewiring the
helper to write a real review file to a temp dir and call `has_filled_verify_row`, the identical
mutation turned AC1 RED.

**The tell is a test helper that reaches for a module's constants rather than its functions.** If a
helper imports `SOME_PATTERN` and applies it, ask what calls that pattern in production and test
*that* instead. Defensive `getattr`/`groupdict()` fallbacks in a test are a second tell: they exist so
the helper survives the mutation you are about to make, which is the opposite of what a control needs.

7th entry in the vacuous-assertion family, and the first where the vacuity was in the *harness around*
the assertions rather than in an assertion itself.

Contributing cause worth noting: `pre_bash_block_unsafe_merge.py` ends in a bare `main()` with no
`if __name__ == "__main__"` guard, so importing it executes `main()` and blocks on `json.load(sys.stdin)`.
Tests must load it through an `exec`-with-`main()`-stripped helper, and that friction is part of why a
re-implementation looked like the easier path.

## A guide's own factual error propagates into the implementation (T068, 2026-08-09)

The Stage 2 guide's AC table attributed the `☑ pass / ☐ N/A` Result-cell shape to T050. It was wrong:
T050's real row is `☑ pass` with no unchecked glyph, and the shape actually occurs in
`TASK_GUIDE_T063.md`. The agent copied the attribution straight into a test constant named
`T050_TRAP_ROW` — a fixture claiming a provenance it did not have (the recorded T061 failure,
repeating, this time seeded by the Supervisor rather than the implementer).

Both real rows omit "pass" from the Notes column and are therefore *correctly* rejected by the old
and new patterns alike, so the fixture had to be synthetic anyway.

**When a guide pins a corpus as the oracle, spot-check the corpus against the real files before
writing it down.** A wrong example in a guide does not stay in the guide — it becomes a constant name,
a docstring, and a code comment.

## A cap on a proxy metric decays silently (T065, 2026-08-09)

The hot-tier cap counted **lines** while the cost was **characters**. Across 12 commits it was green
while the file grew 15.5%, and twice the line count went *down* while the character count went *up* —
the Supervisor consolidated old entries to satisfy the cap and spent the room on longer new ones. A
gate whose units are not the thing you pay for teaches people to game the units, and it does so
without ever failing.

What makes the replacement stick is **not the new number** but the sentence next to it declaring it a
**ratchet** and naming the only tool allowed to move it, downward. A budget with no such rule is a
budget that gets raised the first time it is inconvenient.

Corollary for the gate's message: `assert x <= y` gives the next person nothing. Report current value,
budget, overage, and the sanctioned remedy.

## The harmful copy of a retired contract is usually the one you did not predict (T065, 2026-08-09)

The guide named `docs/claude-md/pipeline-stages.md` as the home of "do not re-read memory". A second,
**more load-bearing** copy lived in `.claude/agents/general-agent-template.md` — the file sub-agents
actually read — and a third in `compact-memory/SKILL.md` was found only by running the negative test.
The guide predicted 8 locations; the sweep found 11, and the file-wide negative grep found 3 of them.

A file-wide negative grep is not a formality on this kind of task. Second instance after T058.

## A negative-grep test is vacuous if its file list is wrong (T065, 2026-08-09)

A test asserting "this string appears nowhere in these files" passes for free if a path is mistyped or
the list is short. Two guards, both needed: assert every enumerated file **exists**, and assert that
lines you deliberately *content-excluded* (here `CLAUDE.md`'s unrelated "If 200 lines can be 50") are
**still present** — otherwise deleting them is an equally green way to pass.

Also: exclude a known-good hit by **matching its content**, never by allowing "one hit". A count-based
allowance silently absorbs the next real regression.

## A sub-agent has no `Skill` tool (T065, 2026-08-09)

`TASK_GUIDE_template.md`'s Completion Checklist instructs the implementer to run
`Skill({ skill: "code-review" })`, `security-review` and `verify`. A sub-agent's toolset is
Read/Write/Edit/Bash/Glob/Grep — **`Skill` is not in it**, so those three lines are structurally
unfollowable by the role they are addressed to. T065's agent reported this rather than silently
claiming the runs; earlier tasks have quietly recorded "security-review PASS" in exactly this spot.
The Supervisor must run all three at Stage 4. The template should say so.

## A scope guard committed as an invariant blocks the thing it was guarding (T065, 2026-08-09)

T065's AC12 said "this task must not touch `memory/MEMORY.md`'s index entries". The test that enforced
it asserted `len(entry_lengths) == 146` — the exact count at review time. That question ("did T065
touch the index?") is only meaningful *while T065 is in review*. Committed as a standing assertion it
forbade the harness from **ever recording a new memory entry**, and it failed on the first legitimate
memory pass after the merge — minutes later, on the very next commit.

Neither the implementer nor the Supervisor caught it at Stage 4, and no amount of mutation testing
would have: nothing added an entry while the test existed, so it could only manifest in use.

**The tell is an assertion pinning a count, hash, or line number captured "as of this task".** Ask
whether it will still be true after the next unrelated change. If not, it is a scope guard — verify it
at review time by diffing directly, and either drop it or pin it to an explicit baseline ref. Keep the
genuinely invariant half (here: the header still states the budget and the path channel).

Second instance of the recorded "working-tree-vs-HEAD is a scope guard, not a repeatable test", and
the first where the guard blocked a routine harness operation rather than just failing noisily.

## Dedupe toward the channel that is guaranteed, not the one that is tidy (T066, 2026-08-09)

The harness auto-loads `.claude/agents/<name>.md` as an agent's system prompt, so a **role guide
always arrives**. `general-agent-template.md` arrives only if the agent chooses to read it. The
instinct on any dedup task is to make the shared template the single source and thin the leaves —
that reads better and is what "de-duplicate" normally means. Here it would move content *out* of a
guaranteed channel *into* an optional one, which is the "already covered must mean
reaches-the-context" error with extra steps.

Before consolidating anything, ask which file is **structurally guaranteed** to be in the reader's
context and which merely *ought* to be. Do not go hunting for a read-rate to justify a bolder cut —
guaranteed-vs-not is a structural fact; a measured rate is not the same claim.

Corollary that nearly bit: the smallest leaf may be *missing* the shared section entirely.
`common-infrastructure.md` had zero Communication Protocol and zero Complexity content, so the first
deletion from the template would have silently stripped both from the most-used agent type.

## A comparison whose two sides came from different readers (T066, 2026-08-09)

T066's AC7 test passed **while the files were still untouched**: the baseline came from `git show`
(bytes) and the current value from `read_text` (characters), and these guides are dense with `—` and
`≤`, so bytes ran ~4% above chars and manufactured a saving out of UTF-8.

New shape in the vacuous-assertion family, and the tell is specific: **a comparison whose two sides
were produced by different readers** — `read_bytes` vs `read_text`, `git show` vs working tree, one
side stripped and the other not. Normalise both sides through the same function before comparing.

## `cmd | tail && git commit` commits a red suite (T066, 2026-08-09)

`pytest -q 2>&1 | tail -2 && git commit ...` committed a failing suite, because `tail` always exits 0
and `&&` gates on the **last command of the pipeline**, not on `pytest`. This repo chains commits
behind `&&` routinely, so the footgun is live. Redirect to a file and check `$?`, or use
`set -o pipefail`. Never read a pipeline's success from the tail of its output.

## Verify a docs change where it is *distributed*, not where it is written (T070, 2026-08-15)

T070 edited three markdown prose lines, which reads like a SKIP — no runtime surface. But this repo's
"app" is its installer, and `templates/` ships downstream via `MANIFEST`, so the claim "an agent
following this pointer now arrives somewhere real" is directly observable: `SUPERVISOR_REPO=<local
worktree> bash setup.sh` into a throwaway `git init` repo, then read the installed files back. That
capture showed all three pointers landing fixed downstream, and following them landed on 4 C0–C3 rows
in each role guide against **0** in `general-agent-template.md` — the defect and its fix, both visible
at the surface a real reader meets. A prose change with a distribution mechanism has a runtime surface;
look for the mechanism before reporting SKIP.

## A fix outside MANIFEST reaches new installs only (T070, 2026-08-15)

Driving the upgrade path — install pre-T070, then `update.sh` — showed `templates/TASK_GUIDE_template.md`
silently updating while `CLAUDE.md` kept the stale pointer. `CLAUDE.md` is absent from `MANIFEST`;
`setup.sh` copies it once as a project-owned file and `update.sh:276` names it as *the* example of a
lock entry carried over untouched. So an edit to `CLAUDE.md` propagates to fresh installs and never to
existing ones. Arguably correct (projects customize their own `CLAUDE.md`), but it means "I fixed it in
`CLAUDE.md`" and "downstream repos have the fix" are different claims. `docs/claude-md/` **is** in
MANIFEST, so the split runs right through what looks like one document.

## The noun a pointer teaches should exist in the file it points to (T070, 2026-08-15)

All three repointed lines say "the Complexity matrix", but the literal phrase occurs **0 times** in the
role guides — the heading is `## Complexity & escalation`. A reader who greps the term the pointer gave
them still lands nowhere. Same defect class T070 was written to fix, one notch smaller, and it survived
the fix because the sweep matched the retired *path*, not the retired *noun*. Recorded, not folded in
(Surgical Changes).

## A scope guard committed as an invariant — occurrences 4, 5 and 6, in one task (T071, 2026-08-16)

T071 was blocked three separate times by the same shape, which is now frequent enough to state as a
rule: **an assertion anchored to "the state as of my review" is a scope guard, and it becomes a wall
the moment anyone legitimately touches that file again.**

1. `test_ac5_ac10_…byte_identical` pinned `CLAUDE.md` to `9f3f2e9`, so *any* edit was RED.
2. `test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline` asserts the role guides stay
   *strictly smaller forever* — a question that only meant something during T066's review. It left
   **222 chars** of headroom on `common-infrastructure.md`.
3. `test_ac3_reasoning_prose_sections_are_byte_identical_to_the_baseline` pinned the template's
   `## Approach` section — the section T046 and T071 both show is *designed* to gain advisory fields.

**The file already knew.** `test_t069_ac9`, sitting directly below (2), carries a comment refusing
that exact shape: *"deliberately not `after <= before`: that would be a scope guard committed as an
invariant (T065 AC12) — correct today, and a blocker on the first legitimate sentence anyone adds
afterwards."* The lesson was written down and then violated twice in the same file.

**Repointing is the fix, not deletion** — T070's precedent. But two refinements came out of T071:

- **Repointing does not always help.** Repointing `BASELINE_REF` for (2) makes `before == after`, so
  a strict `after < before` fails *by construction*. The agent tried it, measured 4 immediate
  failures, and kept the old ref — correctly refusing a Supervisor instruction that was wrong.
  **Check what the assertion's shape does at the new ref before repointing.**
- **Check whether the constant is shared before moving it.** (3)'s `BASELINE_REF` fed **four**
  assertions including the no-backfill guard. A wholesale repoint would have silently reset that
  guard's baseline. The fix was to **split** the constant — new `APPROACH_BASELINE_REF` for the one
  heading, old ref for the rest — so both pins keep discriminating. Verify a split with a mutation on
  **each side**: a split is the easiest place to disarm a pin while the suite stays green.

**Stage 2 pre-flight, amended**: grepping the suite for pinned *strings* is not enough. Also grep for
**size invariants** — line caps, char budgets, `<`/`<=` comparisons against a baseline ref. T071's
approved +8-lines-per-guide budget was unreachable for all four roles and nobody noticed until an
agent measured it.

---

## An instruction inside a hook is code, and a false one is a silent repo-wide defect
**From T073, 2026-08-17.**

`post_bash_memory_update.py` had no logic bug — `main()` and its trigger patterns were correct and
stayed byte-unchanged through the fix. The defect was a **sentence** in the prompt it injects, which
told every session for months not to commit files that are git-tracked. It produced a real loss
(T046's memory pass sat in a forgotten stash; `grep T046 memory/` was empty two weeks after a green,
merged, closed task) and nothing anywhere failed, because a missing memory entry has no test.

Three things generalise:

- **Prose a hook injects is executable by the model.** Review it with the same suspicion as a
  conditional. "It's only a NOTE" is how it survived.
- **Assert prose against ground truth, never against itself.** A test asserting the NOTE *exists*
  would have passed just as happily while `.gitignore` drifted underneath it — which is exactly how
  this survived. T073's test cross-checks `git ls-files --error-unmatch` and the absence of tracked
  files under `memory/event-trace/`, so the assertion breaks when *reality* moves, not when the
  wording does.
- **`git check-ignore` cannot detect an ignore-rule mutation on a tracked path.** It never reports a
  tracked file as ignored, so `check-ignore`-based assertions about tracked files are vacuous by
  construction. The implementer's mutation control correctly stayed GREEN and was misread as a git
  curiosity rather than as the defect — **8th vacuous-assertion instance, first one where the control
  fired properly and the reading failed.** Assert tracked-ness with `ls-files`, not `check-ignore`.

## The merge gate reads `tasks/` from `__file__`, so worktree-branch evidence is invisible to it
**From T073 Stage 5, 2026-08-17.** `pre_bash_block_unsafe_merge.has_filled_verify_row` resolves
`TASKS_DIR` off `ROOT = dirname(dirname(dirname(__file__)))` — the **main checkout**. The filled
`verify` row lived on the worktree branch where the work was done, so the gate blocked the push with
`T073 (no evidence row)` while the evidence was complete and correct. Probed directly:
main-checkout `False` / worktree `True` / `trace_shows_verification('T073')` `True`.

This is the **same `__file__`-vs-`$CLAUDE_PROJECT_DIR` root split flagged open since T056**, surfacing
in a second subsystem. It is not a gate failure in the "failed to gate" family — it fails *closed*,
which is right — but it is circular in practice: the fix is to get the branch into the checked-out
tree, and the command that does that is itself gated. **The escape is the documented order, not a
bypass: close the Kanban row before merging.** The row was legitimately closeable (tests green,
evidence filled, verify PASS), and the gate scans only In Progress / Ready for Review.

## A guard that scans the whole command string fires on a command that merely *mentions* the verb
**From T073 Stage 5, 2026-08-17. Recorded before for the merge gate; now confirmed for
`post_bash_memory_update` too.** `GIT_MEMORY_PATTERNS` matches anywhere in the command, so
`echo 'do not git push yet'` triggers a spurious memory-update prompt — and a heredoc *documenting*
the operation trips it as well. Both fired during this very verification: the driver command was
blocked until the git verb was split in the harness source, and the memory-pass heredoc re-fired the
hook while writing up the hook's own defect. Harmless here (worst case a no-op pass), and deliberately
left untouched as out of scope — but the shape is now attested in two hooks, so treat "whole-string
scan" as a known false-positive source whenever writing a new one. Write files with the Write tool
rather than heredocs when the content quotes a guarded operation.

## A conformance suite's real failure mode is its discovery layer, not its rules (T078, 2026-08-18)

`test_skill_spec_conformance.py` parametrizes six checks over filesystem-discovered skill dirs. If
discovery returns `[]`, pytest reports zero failures — a green suite that asserted nothing. Same
defect already recorded as "a negative-grep test is free-passing if its file list is wrong", and why
the task's mutation controls attack **discovery** (SC5/SC6) as well as the rules (SC3/SC4). SC6 is
the one that matters: delete the non-empty + known-skill guards, point the root at an empty dir, and
the suite goes **GREEN over zero skills**. That proves the guard is load-bearing; SC5 passing alone
does not, because it never shows what caused the RED.

Generalisable: **when a suite is parametrized over a discovered collection, the collection itself
needs an assertion.** Two, ideally — non-empty, and a known member pinned by name (a mis-rooted glob
can still be non-empty). The Supervisor's independent control confirmed the pairing works: a mutant
hardcoding a 3-skill list was caught, but only by the *second* assertion (nonexistent root -> `[]`);
the first, `discover_skill_dirs(SKILLS_DIR) == SKILL_DIRS`, compares the function against its own
cached result and cannot fail for any implementation. 8th sighting of the vacuous-assertion family,
this time inside a guard written specifically to prevent it.

## An Evidence row can contain "pass" while meaning the opposite (T078, 2026-08-18)

The implementing agent's draft verify row read: *"`Skill()` is not available to this agent's tool
set, so `/verify` could not be invoked here — pass."* The merge gate scans that column for a runner
or a verdict; this sentence would have satisfied a naive substring scan while stating the gate was
never run. The agent was being honest — the trailing "pass" belonged to a different clause — but the
cell as written is indistinguishable from a real PASS to the thing that reads it.

**When reviewing Evidence, read the sentence, not the token.** 6th incident in the
evidence-integrity family, and the first where the misleading text came from an agent truthfully
reporting a limitation rather than overclaiming.

## The `Depends on` extractor reads the whole line, so prose after `None` becomes a dependency (2026-08-18)

`pre_agent_validate_guide.py:87` uses `re.search(r"\*\*Depends on\*\*:\s*(.+)", guide)` — it captures
the entire rest of the line. A guide line reading ``**Depends on**: `None` — branched off `main`,
independent of T074/T075`` produced the advisory *"T078 declares 'Depends on: T074' but T074 was not
found anywhere on PROJECT_KANBAN.md"*. The explicit `None` was ignored and a `Txxx` from the
explanatory clause was read as the declared dependency.

Non-blocking (advisory only), so it cost nothing here — but it is the same shape as the other
defects in this hook family: **structural attribution done by free-text scan instead of by parsing
the declared value.** Fix is to parse the field's value and stop at `None`, mirroring what
`resolve_task_id` already does. Not yet filed as a task.

## A gate that cannot see the form its own documentation teaches (T079, 2026-08-18)

`test_skill_reference_pointers.py` resolves **Markdown links** only. `write-better-skill/SKILL.md`
line 91 — the canonical example teaching what a context pointer *is* — was written as a path in
plain backticks: ``Read `references/api-errors.md` if the API returns a non-200 status code``. So an
author following the documented example produced a pointer the gate could not see, which could rot
to a missing file with the suite staying green.

Found at Stage 5 by **driving** the gate, not reading it: the same broken target gave `1 failed` in
link form and `7 passed` in the taught form, the only difference being syntax. Reading the test
would not have surfaced it — the test is correct; the *documentation* pointed somewhere the test
does not look.

Two generalisations worth keeping:
1. **When you ship a rule and a checker for it, check that the rule's own examples are in the form
   the checker reads.** Taught form and enforced form drifting apart is invisible to both.
2. The naive fix was wrong: converting the illustrative `references/api-errors.md` into a link would
   have made the gate **RED on its own documentation**, since that path does not exist. The fix was
   to require link syntax, name the enforcing test, and use the file's own two real pointers as the
   worked examples. **When a doc example is illustrative-but-fake, making it checkable means making
   it real, not making it look real.**

Also note the blind spot did not even register as a skipped test: `write-better-skill`'s two genuine
link-form pointers satisfied the non-empty guard, so the suite looked fully exercised.

## `git stash` is not a safe way to prove a fix mattered (T079, 2026-08-18)

The implementing agent tried to demonstrate that its fence-handling fix was load-bearing by stashing
it and re-running — but the stash took the **new test** along with the fix, so the run passed
vacuously and appeared to prove the fix unnecessary. Same family as the recorded "reverting a
mutation with `git checkout` also reverts your fix", one tool over.

The agent recognised it and redid the control properly: old logic restored against the **new** test,
which went RED. Correct method — when proving a fix matters, revert **only** the fix, never the
evidence that detects it. Safest form is old-implementation + new-test, held apart explicitly.

## Documentation that describes a gate in terms the gate does not use (T079 + T080, 2026-08-18)

**Two instances in one session, same family, both found by driving the gate rather than reading the
diff.** A checker and its documentation drift apart in a way neither side can detect: the checker is
correct, the docs are correct-sounding, and only running one against the other exposes the gap.

1. **T079 — taught form vs. enforced form.** `test_skill_reference_pointers.py` resolves Markdown
   links only, but `write-better-skill`'s canonical example of a context pointer was a path in plain
   backticks. Same broken target: `1 failed` in link form, `7 passed` in the taught form.
2. **T080 — the noun the budget measures.** Both `README.md` and `write-better-skill` said the
   500-line budget applied to the `SKILL.md` **body**; `count_lines(read_skill_md(...))` counts the
   **whole file, frontmatter included**. A live probe with a 498-line body went RED at `is 502
   lines, spec budget is 500`. An author trimming to a 500-line body fails while the document
   explaining the rule says they should pass. T080 had faithfully copied the wording from
   `write-better-skill` — **byte-identical to the cited authority, and the authority was wrong**, so
   the "numbers must match" AC actively propagated the defect.

**The general rule: when you ship a rule plus a checker for it, verify the rule's own prose and
examples against what the checker actually reads.** Matching the authority is not the same as being
right; if the authority is imprecise, an AC demanding byte-identity spreads the imprecision. The
cheap test is to construct the boundary case the prose describes and watch which way the gate goes.

Corollary from T079's fix: **when a doc example is illustrative-but-fake, making it checkable means
making it real, not making it look real.** Converting the invented `references/api-errors.md` path
into a link would have turned the gate RED on its own documentation; the fix was to use the file's
own two genuine pointers as the worked examples.

## A shipped stub can contradict itself where no in-repo file shows it (T075, 2026-08-18)

T075 lowered `HOT_TIER_CHAR_BUDGET` 50,000 -> 45,000 and updated `setup.sh`'s seeded `MEMORY.md`
stub. It updated **one** of the two places the stub states the number. The shipped file said
`Max 45,000 characters — a ratchet` on line 3 and `The enforced gate is the 50,000-character
whole-file budget above` on line 22 — contradicting itself about the one number the task exists to
change, in every downstream repo `setup.sh` scaffolds.

**Why nobody caught it earlier**: the live `memory/MEMORY.md` carries no such comment block, so the
defect is invisible in-repo. It only appears if you **execute the heredoc**. Reading the diff shows
a correct one-line change; running the scaffold shows a self-contradicting file. Stage 3 and Stage 4
both passed it; Stage 5 caught it only because the shipping surface was driven rather than read.

**The guard that should have caught it**: `test_ac8` asserted the new figure was *present*, and
carried negative assertions for two other stale strings (`"200 lines"`, `"Injected in full"`) — but
none for the old budget. The one negative assertion that mattered was the only one missing. 9th
sighting of the vacuous-assertion family, and the sharpest yet: **the defect T075 exists to prevent,
reintroduced inside T075.**

Fixed as "every `\d{1,3},\d{3}` figure in the stub must equal `HOT_TIER_CHAR_BUDGET`" rather than
`"50,000" not in stub`, so the next ratchet cannot reintroduce the same decay under a new number.
Generalisable: **when a constant appears in shipped prose, assert agreement across all its
occurrences, not the presence of the current value.** Pinning the old value only guards one step.

## Clear `__pycache__` after a mutation control, before trusting the restore (2026-08-18)

Mutating `test_token_audit_format.py`, running a control, then `git checkout`-ing it left the suite
reporting **7 failed** while `git status` was clean and the constant was correct on disk. Stale
bytecode: the module is imported through a `sys.path` insert by sibling test modules, so the `.pyc`
outlived the restore.

Harmless in that direction — a spurious RED. **The dangerous direction is the mirror**: a stale
`.pyc` showing GREEN while the file on disk is broken, which is a false PASS on a mutation control.
After any control that edits an imported module, `find -name __pycache__ -exec rm -rf {} +` before
believing the restore run. Related to the recorded "an importlib-loaded module is a different object
from the imported one" — same root, different mechanism.
