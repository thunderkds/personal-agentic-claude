# TASK_GUIDE — T147: Spawned sub-agents run under a tighter sandbox profile than the Supervisor
**Date**: 2026-10-16
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Type**: HITL — one decision point (see Approach) before implementation

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2)

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 9: *"Stronger sandboxing or permission boundaries for sub-agents (especially when they can run Bash or touch infrastructure)."* Grilled 2026-10-16: the user picked the **sub-agent sandbox profile**.

**Verified state (2026-10-16)**: `.claude/settings.json` has only `hooks` — no `permissions`, no `sandbox`. The installed `claude` CLI accepts `--settings <file-or-json>`. Sub-agents reach work two ways: in-process `Agent()` (inherits the session's permissions) and CLI spawns (`claude --model … "<prompt>"` in a worktree), which can take `--settings`.

**Restated intent**:
> A spawned sub-agent can write only inside its own worktree, cannot touch sensitive paths at all, and has no network — while the Supervisor session keeps today's permissions.

**Out of scope**:
- Changing the Supervisor session's own permissions
- OS-level containers / VMs
- Per-role profiles (one profile for all roles)

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (9).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent) — Supervisor 2026-10-17, user approved running T146+T147
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] **Decision point resolved** (Approach § Decision) — by the user 2026-10-17: **(b)**, recorded in Approach § Decision

---

## Dependencies & Reachability

**Depends on**: T146 — `.claude/sensitive-paths.txt` must exist; the profile denies the same patterns
**Entry point**: `templates/subagent-sandbox.settings.json` (new), referenced by `skills/craft-spawn-prompt/SKILL.md`'s spawn command

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | A profile file denies Edit/Write outside the worktree, denies every `.claude/sensitive-paths.txt` pattern (generated, not hand-copied), and disables network for Bash | "write only inside its worktree… no network" |
| 2 | `craft-spawn-prompt`'s CLI spawn command includes `--settings <profile>`; the Agent() path is handled per the Decision below | sub-agents get it |
| 3 | A drift test fails if `sensitive-paths.txt` gains a pattern the profile doesn't deny | one list, two consumers |
| 4 | The Supervisor session's `.claude/settings.json` permissions are unchanged | "Supervisor keeps today's permissions" |
| 5 | Bash inside the profile does **not** prompt on every call (memory: `acceptEdits` covers edits only, never Bash) — the profile's allow rules cover the test runners the role guides use | usable, not just safe |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Generated profile vs `sensitive-paths.txt` | every pattern has a deny rule | automated drift test |
| 2 | Real `claude --settings <profile>` spawn in a scratch worktree asked to write `../outside.txt` | refused | manual, pasted transcript |
| 3 | Same spawn asked to `curl https://example.com` | refused / no network | manual, pasted |
| 4 | Same spawn runs `python3 -m pytest -q` | runs without a prompt | manual, pasted |
| 5 | `git diff main -- .claude/settings.json` permissions block | empty | automated |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_subagent_sandbox_profile.py -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T147.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T147.md`.

---

## Approach

**Pattern reference**: `tests/test_settings_merge.sh` (T111) — how settings JSON is generated and checked; `scripts/validate.sh` for drift-style checks.

**Decision (HITL — resolve before coding)**: in-process `Agent()` sub-agents cannot take a separate `--settings`. First **verify** (record the source) whether PreToolUse hook input identifies a sub-agent (e.g. an `agent_id` / `agent_type` field). Then the user picks:
- (a) if it does: extend T146's hook to apply the profile's deny rules when the call comes from a sub-agent;
- (b) if it doesn't: the profile applies to CLI spawns only, and the docs say plainly that `Agent()` spawns are **not** sandboxed.
Never claim (a)'s coverage on (b)'s evidence.

**Resolved 2026-10-17 by the user — (b).** Verification (Supervisor, source: https://code.claude.com/docs/en/hooks, "Common input fields"): hook input *does* carry `agent_id`/`agent_type` for subagent tool calls, so (a) was feasible; the user chose (b) anyway: *"just want to spawn an sub-agent, or parallel agent into new sandboxing terminal and readonly will be fine."* Meaning: the profile applies to CLI spawns in their own terminal (`claude --settings <profile>`); reads outside the worktree stay allowed (sensitive patterns excepted); writes only inside the worktree. `Agent()` in-process spawns are **not** sandboxed — `craft-spawn-prompt` must say so plainly. Do not extend T146's hook.

**Vital slice**: the generated profile + CLI spawn flag + drift test.
**Cut list**:
- Per-role profiles
- Read-path denial beyond sensitive patterns

**Assumption to verify before coding**: the current `permissions` rule syntax (`Edit(<glob>)`, `Bash(<pattern>)`) and the `sandbox` settings keys for network — check the installed Claude Code docs and cite them in TASK_REVIEW. If the network control doesn't exist, STOP and report.

---

## Edge Case Checklist

- [ ] Worktree path differs per spawn — the profile uses a path relative to the session's project dir, not a hard-coded absolute
- [ ] `memory/` writes: sub-agents must not write memory (Supervisor-only per Memory Write Protocol) — deny there too
- [ ] Profile generation must be re-run when `sensitive-paths.txt` changes — the drift test is what forces it

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/subagent-sandbox.settings.json` | new, generated |
| `scripts/gen_sandbox_profile.py` | new generator from `sensitive-paths.txt` |
| `tests/test_subagent_sandbox_profile.py` | new drift + shape tests |
| `skills/craft-spawn-prompt/SKILL.md` | `--settings` on the CLI spawn command; Agent() note per Decision |
| `MANIFEST` | ship profile + generator |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/settings.json` | Supervisor's permissions unchanged (AC4) |
| `.claude/sensitive-paths.txt` | owned by T146 — read only |

---

## Test Plan

Automated drift/shape tests; SC2–SC4 as a recorded live run at `/verify`.

---

## Completion Checklist

- [x] Decision point resolved and recorded
- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium — mandatory)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T147.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
