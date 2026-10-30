# BRAINSTORMING_LOG.md — Harness hardening (improvement list, 2026-10-16)
**Generated**: 2026-10-16
**Task / Context**: Pasted 11-area improvement list, scope locked by `grill-with-docs` (mode=requirement) — see the last entry of `memory/decisions.md`. #5 claims deferred to T142.
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Deep — five areas, several of them change gates every future task passes through.

---

## The Problem Space

Five gaps, one shared root: **the pipeline's guarantees rest on text the Supervisor or an agent writes, and nothing machine-checks most of it after the fact.**

| Area | Locked shape (from grilling) | What is genuinely missing today (verified) |
|---|---|---|
| (1) Lanes | Scale depth, never stages; diff-vs-claimed-Complexity check | Complexity is a self-declared label; nothing compares it with the diff |
| (2) Verify recheck | CI re-runs a machine-readable verify block | `templates/TASK_GUIDE_template.md:94` already has `### Verification Command (exact, runnable)` — but `.github/workflows/ci.yml` never runs it |
| (6) Prod gate | Human-approval checkpoint in `ship`; smoke/rollback conventions; no deploys | `ship` already has pre-deploy checks and a rollback plan (`SKILL.md:33,37`); there is no approval checkpoint |
| (4) Inheritance | `touches:` paths, overlap-injected at spawn; compound leads with the general lesson | `TASK_GUIDE` has `## Files to Change (Predicted)` (`:167`); memory and solution entries carry no paths |
| (9) Security | Sensitive-path confirm, sub-agent sandbox profile, hash-chained trace | `.claude/settings.json` has `hooks` only — no `permissions`, no `sandbox`; `memory/event-trace/` is **gitignored** (`.gitignore:53`), so a trace has no copy the agent can't rewrite |

Non-negotiables: every stage and Hard-Stop Gate still runs (Gate 1, LR-0002); no new runtime dependency; `ship` never deploys; `verify` stays user-only.

---

## Questions for the User

**Answered 2026-10-16:** (1) anchor outside the repo — accepted; (2) lane check **warns at Stage 4**, does not block; (3) approval: **the Supervisor asks via a question prompt and records the answer** (not a user-only command) — the record must still name the exact version/commit approved.

1. **Trace anchor.** A hash chain inside a file the agent can write only catches *careless* edits — a rewriting agent just recomputes the chain. Real tamper evidence needs the chain head stored where agents can't write. Recommended: the hook appends each head to `~/.claude/harness-anchors/<repo>/<task>` and a `permissions.deny` rule blocks agent `Edit/Write/Bash` there. Accept, or settle for "careless-edit detection" only?
2. **Lane check strictness.** When the diff exceeds what the claimed Complexity allows: **warn at Stage 4** (recommended — the thresholds are guesses until measured over ~10 tasks), or **block the merge** from day one?
3. **Prod approval record.** Who can write "approved"? Recommended: a user-only command (like `/verify`), so the Supervisor can't approve its own release.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Five mechanisms | One new format + hook/skill per area, built independently | High | ~1,200 lines | Medium | |
| B | One task manifest | The TASK_GUIDE sections that already exist become the single machine-readable source; one shared parser feeds every check | Medium | ~600 lines | Medium | ✅ Yes |
| C | Conventions only | Lanes, approval, compound shape and sensitive paths as written rules; only the CI recheck is code | Low | ~150 lines | Low | |

### Option A — Five mechanisms
**Approach**: new `lane:` frontmatter, a new `### Verify` YAML block, a `touches:` frontmatter on every memory entry, a sensitive-paths config, and a trace-chain lib — each with its own parser and tests.
**Pros**: Each area ships and reverts alone; parallelisable across sub-agents.
**Cons**: Three of the five re-declare data the guide already holds (Complexity label, Verification Command, Files to Change). Duplicated declarations drift.
**Why it might fail**: The `lane:` value and the Complexity label disagree on the first rushed task, and nothing says which wins.

### Option B — One task manifest (recommended)
**Approach**: a `lib/task_guide.py` parser reads three sections every guide already has:
- **Complexity label** → lane depth (which review personas, whether a brainstorm log is required).
- **`## Files to Change (Predicted)`** → (a) the diff check: actual changed files vs. predicted plus the C-level budget; (b) `touches:` for inheritance — memory/solution entries gain a `touches:` line, and spawn injects the entries whose paths overlap; (c) sensitive-path pre-clearance — a predicted `.env` edit is *expected*, an unpredicted one triggers "ask".
- **`### Verification Command`** → fenced `bash` block that CI extracts and runs for each task the PR moves to Done.

The separate pieces stay separate: the approval command in `ship`, the sandbox profile (`--settings` on the spawn line — the flag exists in the installed `claude`), and the trace anchor.
**Pros**: No new declaration for the Supervisor to fill; one parser and one test fixture set; predictions become checkable, which also exposes careless Stage 2 planning.
**Cons**: All 128 existing guides predate it — old guides with vague "Files to Change" must be exempt (apply only to guides created after the change). The parser becomes a single point of failure for three gates.
**Why it might fail**: The parser fails *open* (an unreadable section is treated as "nothing to check"). This repo has hit that shape three times (T099). It must fail closed with a named error, and be mutation-tested.

### Option C — Conventions only
**Approach**: a lane table in each role guide, an approval line in `ship`'s checklist, compound's template reordered, a sensitive-path list in `CLAUDE.md`; CI recheck is the only code.
**Pros**: Smallest; nothing new to break.
**Cons**: Repeats exactly the failure LR-0002 records — rules that are written but not enforced get bypassed when work feels small. Delivers no security piece.
**Why it might fail**: It already has, for written rules in this repo.

---

## 50% Rule Check

Option B is already the 50% cut of A — it reuses three existing sections instead of adding three formats. A further cut: **drop the sandbox profile into the sensitive-path hook's config** (one deny/ask list serves both: the hook asks the Supervisor session, `--settings` denies spawned agents), and **ship the lane check as a Stage 4 report line, not a hook**, until question 2 says block. That's about 400 lines.

---

## Edge Case Checklist (for TASK_GUIDEs)

- **Lanes**: Hard-Stop Gate 2 words (*refactor*, *test coverage*…) floor at C2 regardless of the diff; renames count as two paths; generated/lock files are excluded from the budget.
- **CI verify**: run only guides the PR moves to Done (an old guide's command can reference deleted files); commands needing a worktree, network or a human (`/verify`) must be declared non-CI and skipped by name, not silently; a fork PR runs guide-authored commands — `pull_request` without secrets only.
- **Inheritance**: a moved file orphans its `touches:` entry — `compound-refresh` must flag it; directory globs can match half the repo — cap the injected lines at T125's slice budget; compound's "general lesson" must state *when it applies*, or it becomes a platitude.
- **Sensitive paths**: Bash path detection repeats T099's quoted-span trap — reuse `lib/shell_data.py`, never a fresh regex; `.env.example` is not a secret; reads vs writes are separate decisions.
- **Sandbox**: memory says spawns use `acceptEdits` and that covers edits only, never Bash — check the profile doesn't make every Bash call prompt inside the spawned terminal.
- **Trace**: concurrent appends from two agents on one task break a naive chain — lock the file or chain per agent.
- **Prod gate**: the approval must name the version or commit, so approving v2.1 doesn't approve v2.2.

---

## Surgical Scope

**Should touch**: `templates/TASK_GUIDE_template.md` (verify block fence convention), new `.claude/hooks/lib/task_guide.py`, `.github/workflows/ci.yml`, `.claude/skills/ship/SKILL.md`, `.claude/skills/compound/SKILL.md`, `.claude/skills/craft-spawn-prompt/SKILL.md` (overlap injection, `--settings`), `.claude/hooks/post_tool_trace.py`, new sensitive-path hook, `.claude/settings.json`.
**Must not touch**: `pre_bash_block_unsafe_merge.py`'s push/merge matcher (T099 just closed it); `post_agent_move_to_review.py` (inert by design, T044); the 128 existing TASK_GUIDEs; `setup.sh`/`update.sh` beyond shipping new files through MANIFEST.

---

## Recommended Path

> **Stage 2 correction (2026-10-16), verified in code:** no new parser — `.claude/hooks/lib/guide_sections.py` already slices guide sections; inheritance extends `skills/craft-spawn-prompt/scripts/memory_slice.py` (T125) to `decisions.md`'s existing `**Files**:` lines instead of adding `touches:`; `ship` § 7 already has a GO gate, so approval is a fifth condition. "Task manifest" renamed **guide fields** (`MANIFEST` is the install file). Result: seven independent tasks T143–T149, only T147 depends on T146.

**Option B — One task manifest**, cut per the 50% check, split into five tasks: (1) `task_guide.py` parser + CI verify recheck; (2) lane depth table + Stage 4 diff report line; (3) `touches:` inheritance + compound general-lesson-first; (4) sensitive-path ask hook + spawn sandbox profile; (5) anchored trace chain; plus (6) `ship` approval checkpoint, independent. Task 1 goes first — 2, 3 and 4 read its parser.

## Next Actions (Stage 2)

1. ~~User answers the three questions above.~~ Done — see answers at top.
2. `grill-with-docs` (terminology mode) on "lane", "touches", "anchor" before `to-issues`.
3. Register T143–T148 after a full-board ID scan; Hard-Stop Gate 2 does not apply by wording, but tasks 1, 4 and 5 are hook/gate changes → C2 / Medium, `security-review` mandatory.
