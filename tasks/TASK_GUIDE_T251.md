# TASK_GUIDE — T251: Agents cannot write session transcripts (deny rule)
**Date**: 2026-11-04
**Complexity Level**: C1
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

---

## Requirement (Pillar 1 — Adapt the requirement)

From T250's Stage 4 Debate, finding (b): the merge gate accepts a minimal-track line `- verify: ☑ pass — /verify by the user, session <sid>, commit <sha>` when `<sid>.jsonl` in the merging session's transcripts folder holds a human `/verify <ID>` entry (`.claude/hooks/pre_bash_block_unsafe_merge.py` `user_line_confirmed`, `.claude/hooks/lib/session_work.py` `verify_typed`). No permission rule protects that folder, so an agent running as the same OS user can forge a transcript. The T250 review reproduced this with a Bash heredoc that writes `fake-sid.jsonl`. The run records already have deny rules in `.claude/settings.json` (`permissions.deny`: one `Edit(...)` rule and one `Bash(*...*)` rule on their folder). The user approved adding the same kind of rule for transcripts on 2026-11-04 ("approve all you do all").

**Restated intent**:
> An agent in a kit project cannot write or create a session transcript file with the Edit/Write tools or with a Bash command that names the transcripts folder, so the user-`/verify` proof gets the same trust level as the run records. What the rule does not cover is written down.

**Out of scope**:
- Changing the merge gate or `session_work.py` logic.
- A cryptographic or OS-level proof (none exists for the run records either).
- Editing the user's own `~/.claude*/settings.json` — the kit ships project settings only.

**Requirement Refs**: no `PRD.md` IDs (`PROJECT_SPEC.md` `## Readiness`: `README.md` stand-in). Traces to T250 Debate (b), `tasks/TASK_REVIEW_T250.md` `## Auto decisions` item 2 and item 5.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user 2026-11-04 (AskUserQuestion): "Edit + Bash (Recommended)"
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered (none in `PRD.md`)

> An agent must NOT start implementing until this gate is checked.

---

## Dependencies & Reachability

**Depends on**: T250 — `user_line_confirmed` / `verify_typed` read `<sid>.jsonl` (merged `04418364`)

**Entry point**: `permissions.deny` in `.claude/settings.json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `.claude/settings.json` `permissions.deny` gains an `Edit(...)` rule covering `*.jsonl` under the default transcripts folder `~/.claude/projects/`; the two existing rules stay, in order | Restated intent: Edit/Write tools |
| 2 | It also gains a `Bash(...)` rule for a command that names the transcripts folder, (user decision D1: Edit + Bash) | Restated intent: Bash command |
| 3 | A real headless Claude Code run with the kit's settings is refused: a `Write` of `~/.claude/projects/<x>/fake.jsonl` and (if D1 adds it) a Bash `printf … > ~/.claude/projects/<x>/fake.jsonl`; the denial text is pasted. The same run can still `Read` a transcript file | AC 1–2 observed, not assumed |
| 4 | Install paths ship the new rules: `setup.sh` settings merge (`tests/test_settings_merge.sh` T148 block) and `plugin_init` (`tests/test_plugin_init.py`) add them, add-only, to a project that lacks them | Restated intent: "in a kit project" |
| 5 | `docs/claude-md/tracks.md` `### Known limits` (the T250 bullet on the forgeable transcript) says the deny rules now cover the default `~/.claude/projects/` only: a custom `CLAUDE_CONFIG_DIR` (e.g. `~/.claude-<name>/`) is not covered unless the pattern does (D2), and the Bash rule matches command text, so a command that builds the path at run time is not stopped | Restated intent: "what the rule does not cover is written down" |
| 6 | Negative: no deny rule blocks the hooks themselves (hooks read transcripts in Python, not through a tool call) — the full suite stays green, including `.claude/hooks/tests/test_t250_session_ownership.py` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Kit `.claude/settings.json` | deny list = old two rules + new rules | automated test |
| 2 | Headless `claude -p` in a scratch kit project asked to write a fake transcript | tool call denied, file absent | real run (pasted) |
| 3 | Fresh `setup.sh` install / `plugin_init` into a project with its own deny list | own rules kept first, kit rules appended once | automated test |
| 4 | Headless run asked to read a transcript | read allowed | real run (pasted) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_plugin_init.py -q
bash tests/test_settings_merge.sh
python3 -m pytest .claude/hooks/tests/ tests/ -q
# ci: skip for the real run — needs a logged-in claude CLI; paste its output in the review file
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T251.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T251.md`.

---

## Approach

**Pattern reference**: `.claude/settings.json` `permissions.deny` — the two existing run-record rules; `tests/test_settings_merge.sh` T148 block and `tests/test_plugin_init.py` (deny union, add-only).

**Vital slice**: the deny entries plus one real headless denial.
**Cut list**: per-user config-dir rules in the user's own settings (the kit does not write user settings; the Known-limits text tells the user how).

Decisions for the Fidelity Gate:
- **D1 — Bash rule. DECIDED by the user 2026-11-04: Edit + Bash.** Was recommended: add a Bash rule like the run-record one, matching a command that names `.claude/projects/` (the T250 forgery used a Bash heredoc, so an Edit-only rule does not stop it). Cost: an agent's Bash `ls`/`grep`/`cat` on that folder is refused too; agents read transcripts with the Read tool instead. Alternative: Edit rule only (the Advocates' proposal), which leaves the reproduced Bash path open.
- **D2 — config dir.** Try a pattern that also matches `~/.claude-<name>/projects/` (e.g. `~/.claude*/projects/**/*.jsonl`) and prove with the headless run whether Claude Code honours it. If it does not, keep `~/.claude/projects/` and record the gap (AC 5).

Write the test for AC 1 first and see it fail; then the settings change; then AC 4 tests; then the real run (AC 3).

---

## Edge Case Checklist

- [ ] A project that already has its own `permissions.deny` keeps its rules first (T148 order)
- [ ] The Bash pattern must not match the kit's own normal commands (e.g. `git`, `pytest`, `python3 .claude/hooks/...`) — check the suite and a few hook commands
- [ ] `plugin/` copies: if any file under `plugin/` mirrors `.claude/settings.json`, copy it too (`RUNBOOK.md` plugin file copies)
- [ ] The Bash rule's text must not itself trip the run-record rule when an agent edits `settings.json` through Bash (use the Edit tool)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/settings.json` | new deny entries |
| `tests/test_settings_merge.sh` or `tests/test_plugin_init.py` | assert the new entries ship |
| `tests/` (new `test_t251_transcript_deny.py`) | AC 1 shape test |
| `docs/claude-md/tracks.md` | `### Known limits` text (AC 5) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py`, `.claude/hooks/lib/session_work.py` | out of scope |
| `~/.claude*/settings.json` | user settings, not the kit's |

---

## Test Plan

Shape test on the settings file; install-path tests (setup merge, plugin_init); one real headless `claude -p` run in a `mktemp -d` scratch project with the kit's settings, showing a denied write and an allowed read; full suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T251.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — via the auto verify run
- [ ] Supervisor notified: task ready for Stage 4 review
