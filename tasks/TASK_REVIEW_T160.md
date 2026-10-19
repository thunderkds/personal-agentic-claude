# TASK_REVIEW — T160: `wake` triages my new board tasks: propose priority, ask, then ready-or-investigate

> Sibling of `tasks/TASK_GUIDE_T160.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_board_triage.py` (new, 18 tests): AC1 `test_sc1_only_my_incomplete_task_is_listed`, `test_changed_since_marker_shows_once_marked`, `test_task_reassigned_to_me_shows_at_next_wake`, `test_wake_prints_triage_lines_and_advances_the_marker`; AC2 `test_others_never_appear_even_when_changed`; AC3 `test_wake_skill_points_to_triage_reference_within_codex_cap`; AC4 `test_spawn_blocks_a_one_line_guide_naming_the_missing_sections`, `test_a_crash_in_the_completeness_check_fails_open`; AC5 `test_every_not_done_repo_guide_is_complete`. Output: `18 passed in 0.79s` (backend-developer, 2026-10-19T14:51Z) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_board_triage.py -q` → `..................  [100%]` / `18 passed in 0.79s` (backend-developer, 2026-10-19T14:51Z) |
| Negative cases hold | ☑ pass | teammate/unassigned tasks never listed; Done/Canceled/`completed`-type skipped; local mode exit 2 with no file written; missing `me` exit 2 with no marker; failed pull prints no triage; title with `\n### Done\n- [x] **ENG-9**` stays one line, last field; completeness-check crash → spawn allowed |
| verify | pass | /verify 2026-10-19 on an isolated copy of feat/t160-triage with a stub Linear board. `pull_moment.py wake`: first wake lists only ENG-170 (mine, one-line description, `untriaged`, missing all three sections); teammate's ENG-172 and my Done ENG-173 hidden; ESC in the title became a space. After editing ENG-171, reassigning ENG-172 to me and adding ENG-174, the next wake lists 4 (changed / not planned / new); the wake after lists only the 2 unplanned. Real harness (`claude -p` in the copy) spawning `Task ID: ENG-170` -> `PreToolUse:Agent hook error: [hook:pre_agent] Cannot spawn agent — incomplete TASK_GUIDE for: ENG-170 (missing: Requirement, Acceptance Criteria, Verification Command)`. Hook events: ENG-171, T160, bugfix T018 allowed; T022 (Done, legacy) blocked; missing ENG-999 still the missing-guide block; no-task prompt allowed. Offline wake: one unreachable line, 0.1 s, marker unchanged. Corrupt marker -> all mine shown, rc 0. No `me` -> triage rc 2. Local mode: rc 2, wake silent, no .board/ — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | code-review + security-review on feat/online-board...feat/t160-triage (11 files) plus callers (pull_moment wake, guide_candidates, render.one_line, slice_section); reports `reports/code-review_feat-t160-triage_20261019T215423.html`, `reports/security-review_feat-t160-triage_20261019T215423.html` |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest -q tests .claude/hooks/tests; echo exit=$?` → `exit=0`, `1364 passed, 25 subtests passed in 28.45s`. Also `sh tests/test_harness_projection.sh` → `41 passed, 0 failed` (Codex 8 KB skill cap; `skills/wake/SKILL.md` is 8,118 bytes) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI: CLI script, hook and skill text only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by backend-developer in worktree `wt-t160` at HEAD `12048b9`, before any T160 implementation commit. `triage` does not exist, and the spawn hook lets a one-line guide through (advisories only, no `"decision": "block"`). The hook ran from a scratch copy of `.claude/hooks` with an `ENG-\d+` id_pattern and a one-line `tasks/TASK_GUIDE_ENG-171.md`.

```text
$ date -u; git rev-parse --short HEAD
2026-10-19T14:44:36Z
12048b9
$ python3 scripts/board_sync.py triage; echo exit=$?
usage: board_sync.py [-h]
                     {pull,flush,status,decide,init,create,update,push} ...
board_sync.py: error: argument command: invalid choice: 'triage' (choose from pull, flush, status, decide, init, create, update, push)
exit=2
$ cat tasks/TASK_GUIDE_ENG-171.md   # scratch project, board mode online, one-line guide
# ENG-171: Add dark mode
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: ENG-171
Guide: tasks/TASK_GUIDE_ENG-171.md"}}' | python3 .claude/hooks/pre_agent_validate_guide.py; echo exit=$?
[hook:pre_agent] memory-slice missing: Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4).
[hook:pre_agent] startup-reads missing: Spawn prompt names a TASK_GUIDE but has no `**Startup reads**` block, so the agent is not told to read PROJECT_SPEC.md, its guide and its role guide first (craft-spawn-prompt element 8).
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Advisory warning (not blocking):\n  \u2022 ENG-171's Demonstration BEFORE field is blank. Capture it BEFORE your first implementation commit \u2014 a BEFORE taken after the change is not a BEFORE, and there is no N/A path.\n  \u2022 Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4).\n  \u2022 Spawn prompt names a TASK_GUIDE but has no `**Startup reads**` block, so the agent is not told to read PROJECT_SPEC.md, its guide and its role guide first (craft-spawn-prompt element 8)."}}
exit=0
```

Non-executable part, verbatim prior content of `skills/wake/SKILL.md` Step 0 (8,119 bytes, no `references/` directory under `skills/wake/`):

> Run `python3 scripts/pull_moment.py wake` first (FR-009; no-op in `local` mode). Show any line it prints (`board unreachable — using cache (N unsynced)` or `⚠ N unsynced board writes — …`) atop the briefing and continue.

**AFTER**: same commands, after the implementation (worktree `wt-t160`, run by backend-developer). Local mode refuses `triage` (exit 2, nothing written); online, only my one-line task is listed; the one-line guide is now blocked, naming the missing sections.

```text
$ date -u; git rev-parse --short HEAD
2026-10-19T14:51:36Z
b45c35a
$ python3 scripts/board_sync.py triage; echo exit=$?   # this repo: board mode local
[board] triage needs board mode online (no board in .claude/board.json)
exit=2
$ python3 scripts/board_sync.py triage; echo exit=$?   # scratch project, fake board: ENG-171 mine one-line, ENG-172 mine complete, ENG-173 bob's
ENG-171 · untriaged · not planned (missing: Requirement, Acceptance Criteria, Verification Command) · Add dark mode
exit=0
$ cat tasks/TASK_GUIDE_ENG-171.md   # scratch project, one-line guide
# ENG-171: Add dark mode
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: ENG-171
Guide: tasks/TASK_GUIDE_ENG-171.md"}}' | python3 .claude/hooks/pre_agent_validate_guide.py; echo exit=$?
{"decision": "block", "reason": "[hook:pre_agent] Cannot spawn agent \u2014 incomplete TASK_GUIDE for: ENG-171 (missing: Requirement, Acceptance Criteria, Verification Command). Fill those sections first (Stage 2); in board mode push them with `python3 scripts/board_sync.py update --guide <ID>`."}
exit=0
$ python3 -m pytest tests/test_board_triage.py -q
..................                                                       [100%]
18 passed in 0.79s
$ wc -c skills/wake/SKILL.md
8118 skills/wake/SKILL.md
```

New `skills/wake/SKILL.md` Step 0 (8,118 bytes), and the new file `skills/wake/references/triage.md` (the flow):

> Run `python3 scripts/pull_moment.py wake` first (FR-009; no-op in `local` mode). Show any line it prints (unreachable board, unsynced board writes) atop the briefing and continue.
> Tasks to triage: follow `references/triage.md`.

**DELTA**: At `wake`, a developer in board mode now sees their own board tasks that are unplanned or changed since the last session, with a documented propose-priority, ask, then plan-or-investigate flow. No agent can be spawned on a guide missing its Requirement, Acceptance Criteria or Verification Command, in either board mode.

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T160 via the active-task state file (`memory/event-trace/T160.jsonl`).
