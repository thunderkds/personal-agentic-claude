# TASK_GUIDE — T146: An edit or command that touches a sensitive path asks a human first
**Date**: 2026-10-16
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

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

From the user's improvement list, area 9: *"Explicit 'dangerous boundary' detection (secrets, production configs, destructive git commands) with mandatory human confirmation."* Grilled 2026-10-16: the user picked the **sensitive-path confirm hook**. Destructive git is already covered by `git-guardrails-claude-code`.

**Restated intent**:
> Before Edit, Write or Bash touches a path on a sensitive list (`.env*`, secrets, production configs, infra), the harness asks the human — unless the active task's guide predicted that exact path.

**Out of scope**:
- Destructive git (already `git-guardrails-claude-code`)
- Detecting secrets *inside* file content
- Read access (Read tool) — writes and commands only; reads are the T147 sandbox's concern

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (9).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent) — Supervisor 2026-10-17, user approved running T146+T147
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `.claude/hooks/pre_tool_sensitive_path.py`, registered in `.claude/settings.json` `PreToolUse` with matcher `Edit|Write|Bash`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Patterns live in `.claude/sensitive-paths.txt`, one glob per line, `#` comments, `!` negations (default ships `.env`, `.env.*`, `!.env.example`, `**/secrets/**`, `**/*.pem`, `**/*.key`, `**/prod*.{yml,yaml,json,tf}`, `infra/**`, `terraform/**`) | "secrets, production configs" |
| 2 | Edit/Write on a matching `file_path` returns the PreToolUse `ask` decision with a reason naming the pattern | "mandatory human confirmation" |
| 3 | Bash: tokens of the command **after** `strip_heredoc_bodies` and `strip_quoted_spans` (`lib/shell_data.py`) that match a pattern → `ask`; quoted spans that T099 classes as executable are **kept**, so `bash -c "cat > .env"` still asks | T099's direction rule |
| 4 | If the active task (`CLAUDE_ACTIVE_TASK` / `task_context.resolve_task_id`) predicts the exact path in `## Files to Change (Predicted)`, the decision is `allow` with no prompt | "unless the guide predicted it" |
| 5 | Unreadable pattern file, malformed stdin or import failure → `ask` (fail toward the human), never a silent allow | fail closed |
| 6 | Hook ships via `MANIFEST` and is merged by the settings merge (T111) | reaches consumer projects |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Write `{"file_path": ".env"}` | `ask` JSON, reason names `.env` | automated, real stdin protocol |
| 2 | Write `.env.example` | no output, exit 0 | automated |
| 3 | Bash `echo "edit .env later"` | allow (quoted data) | automated |
| 4 | Bash `bash -c "echo x > .env"` | ask | automated |
| 5 | Bash `cat <<EOF > notes.md` with `.env` only in the heredoc body | allow | automated |
| 6 | Edit `infra/main.tf` with active task predicting `infra/main.tf` | allow | automated |
| 7 | Pattern file missing | ask | automated |
| 8 | **Mutation controls**: (a) drop the quoted-span keep rule → SC4 RED; (b) make failure path allow → SC7 RED | | Supervisor re-runs |
| 9 | Live: inside a real Claude Code session, Write to `.env` | the permission prompt appears | manual, at `/verify` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T146.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T146.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/pre_bash_block_unsafe_merge.py` — guarded import that turns an unavailable resolver into the safe decision; `lib/shell_data.py` — the only sanctioned way to separate command text from data (three fail-opens in T099 came from fresh regexes).

**Vital slice**: Edit/Write path match → ask; Bash via shell_data.
**Cut list**:
- Per-project override UI — editing the text file is the override
- Detecting paths built from variables (`$F`) — recorded limitation, not handled
- Read-tool gating (T147)

**Assumption to verify before coding**: the PreToolUse output shape for asking — `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "..."}}`. Check it against the installed Claude Code's hook docs and record the source in TASK_REVIEW. If `ask` is unavailable, STOP and report — do not fall back to `block`.

---

## Edge Case Checklist

- [ ] Absolute vs relative `file_path` — normalise against `$CLAUDE_PROJECT_DIR`
- [ ] Symlinked paths (`.claude/skills` is a symlink) — match the path as given and its resolved form
- [ ] Spawned agents run with `acceptEdits`; `ask` must still prompt there — confirm in SC9
- [ ] Windows-style separators in a pattern file — normalise
- [ ] A Bash command that only *reads* `.env` (`grep KEY .env`) still asks — reads via Bash are not distinguishable cheaply; record as intended

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_tool_sensitive_path.py` | new |
| `.claude/sensitive-paths.txt` | new default list |
| `.claude/hooks/tests/test_pre_tool_sensitive_path.py` | new |
| `.claude/settings.json` | register the hook |
| `MANIFEST` | ship the hook and the list |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/lib/shell_data.py` | consume only; changing it re-opens T099 |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | separate gate |
| `.env*` anywhere | obviously |

---

## Test Plan

Drive the hook through its real stdin/stdout protocol (subprocess with JSON payload), as T093/T099's `/verify` did. SC9 live at Stage 5.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium — mandatory; scope to `main..<branch>`)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T146.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
