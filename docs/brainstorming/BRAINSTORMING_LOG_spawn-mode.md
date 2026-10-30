# BRAINSTORMING_LOG_spawn-mode.md
**Generated**: 2026-10-17
**Task / Context**: Which spawn mode Stage 3 sub-agents use by default — background `Agent()`, an unsandboxed CLI in a new pane, or the T147 sandboxed CLI in a new pane. Triggered by T144/T145/T148/T149 going to background `Agent()` when the user expected panes.
**Skill**: `Skill({ skill: "brainstorming" })` — tier: Standard

---

## The Problem Space

No written rule picks the spawn mode, so the Supervisor defaults to whatever is built in (`Agent()`).
The user wants a deliberate default. Facts this rests on (verified 2026-10-17):

- Previous session (`09eec774…`) spawned T144/T145/T148/T149 as `Agent({ subagent_type: "common-infrastructure", run_in_background: true })`, no stated reason.
- T148's worktree (`wt-t148`) holds uncommitted `post_tool_trace.py` changes plus untracked `trace_chain.py` / `verify_trace.py` after that session ended at 12:12 — consistent with a background agent dying with its session (not proven).
- CLI pane spawns have a working recipe (`setsid ghostty -e bash -c $SP/launch_Txxx.sh … & disown`, trap-written `.pid/.exit/.done` markers) and a history of plumbing failures: SIGHUP exit 129, missing marker, idle-not-exited for 3h20m (T109) — `memory/learnings.md`.
- `herdr` is installed (`~/.local/bin/herdr`) and was the pane used for T146/T147 verify.
- T147 sandboxed CLI (`claude -p --settings templates/subagent-sandbox.settings.json`) **FAILs on this machine**: Bash cannot run under `kernel.apparmor_restrict_unprivileged_userns=1` (nested userns refused) — `tasks/TASK_REVIEW_T147.md:181`, `memory/learnings.md:2716`.
- `Agent()` spawns are not sandboxed (`memory/decisions.md`, T147).

Non-negotiable: the agent must be able to run tests (Bash), commit in its worktree, and the Supervisor must know reliably when it is done.

---

## Questions for the User

1. Do you need to watch sub-agents work live, or is the final report + commits enough?
2. Should a spawn survive the Supervisor session ending (e.g. you close the terminal mid-task)?
3. Is changing the AppArmor sysctl (system-wide, needs sudo) acceptable to make the sandbox work?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Background `Agent()` | Built-in in-process sub-agent, harness notifies on finish | Low | 0 lines | Low | For C0–C1 |
| B | Unsandboxed CLI pane | `claude -p` (or Codex/Gemini) in a herdr/Ghostty pane, setsid + markers | Medium | ~0 new (launcher exists) | Medium | ✅ For C2+ / watch / non-Claude |
| C | Sandboxed CLI pane | B plus `--settings templates/subagent-sandbox.settings.json` | Medium | 0 new | High here (Bash dead) | Later, once sandbox works |

### Option A — Background `Agent()`
**Approach**: keep the built-in tool; `subagent_type` auto-loads the role guide.
**Pros**: completion notification is reliable (no markers, no wait-loop); no window/SIGHUP plumbing; cheapest in Supervisor tokens.
**Cons**: not watchable; dies with the Supervisor session; not sandboxed; `PostToolUse/Agent` fires at issuance; `isolation:"worktree"` forks from `main`.
**Why it might fail**: a long C2/C3 task outlives the session and is lost half-done (T148 shape); the user cannot see a stuck agent.

### Option B — Unsandboxed CLI in a pane
**Approach**: Supervisor writes `launch_Txxx.sh`, runs it detached with `setsid`, watches markers in a background Bash loop.
**Pros**: watchable; survives the Supervisor session; works for any CLI (multi-provider); own transcript for the token meter.
**Cons**: plumbing is fragile (3 recorded failure shapes); `acceptEdits` doesn't cover Bash, so a headless run needs a permission mode that won't stall; no sandbox.
**Why it might fail**: agent finishes but stays at its prompt and looks "still working"; a prompt appears headless and blocks forever; a forgotten `setsid` kills it at ~2–5 min.

### Option C — Sandboxed CLI in a pane (T147)
**Approach**: B with the generated `dontAsk` sandbox profile.
**Pros**: least privilege — no network, no edits outside the worktree, sensitive paths denied.
**Cons**: on this machine Bash is dead inside it, so agents can't run tests or git.
**Why it might fail**: it already did (T147 /verify FAIL). Works only after `sysctl kernel.apparmor_restrict_unprivileged_userns=0` or an AppArmor profile — a system-wide security change.

---

## 50% Rule Check

No new code needed for any option. The goal ("the spawn mode is chosen on purpose, not by default") is met by one rule paragraph in `docs/claude-md/pipeline-stages.md` Stage 3 plus a "spawn mode" line in `craft-spawn-prompt`'s output — ~10 lines total.

---

## Recommended Path

**User decision 2026-10-17: Option A for every spawn.** The user does not need to watch sub-agents
work — the final report and commits are enough. A's one real gap (a session ending kills the agent)
is covered by a `wake` check for uncommitted work in task worktrees. B stays available on explicit
request or for a non-Claude CLI; C stays deferred.

*Original proposal (superseded by the decision above):* **A + B by rule, C deferred.**
- **Background `Agent()`**: C0–C1 tasks expected to finish within the session.
- **CLI pane (B)**: C2–C3 tasks, any non-Claude CLI, or whenever the user asks to watch.
- **Sandboxed pane (C)**: replaces B once a nested-userns check passes on the machine; until then B.

Justification: A has the most reliable completion signal and costs nothing; B fixes A's two real gaps (visibility, surviving the session) exactly where they bite — long tasks; C is the safest but cannot run Bash here.

---

## Surgical Scope

Files that **should** be touched:
- `docs/claude-md/pipeline-stages.md` — Stage 3 spawn-mode rule
- `skills/craft-spawn-prompt/SKILL.md` — output names the chosen mode and its command

Files that **must not** be touched:
- `templates/subagent-sandbox.settings.json`, `scripts/gen_sandbox_profile.py` — T147 scope, already decided
- `.claude/settings.json` — Supervisor's own permissions

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Background agent outlives nothing: Supervisor session ends → agent's uncommitted work is left in the worktree (check `git status` in every worktree on `wake`)
- [ ] Pane agent done but idle at prompt → watcher shows flat CPU; check `git log` in the worktree before waiting
- [ ] Pane launched without `setsid` → exit 129 at ~2–5 min
- [ ] Headless pane hits a permission prompt (`acceptEdits` ≠ Bash) → stalls or is denied
- [ ] Sandbox check must test *nested* userns, not a bare `bwrap`
