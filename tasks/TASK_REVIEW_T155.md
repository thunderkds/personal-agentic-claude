# TASK_REVIEW — T155: Init asks the four board questions and writes `.claude/board.json`

> Sibling of `tasks/TASK_GUIDE_T155.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_board_init.py` (19 tests; AC1-AC5 + setup.sh question) |
| Verification command run | pass | `pytest tests/test_board_init.py`: 19 passed; shell: ----- summary: 18 passed, 0 failed ----- / ----- summary: 22 passed, 0 failed ----- |
| Negative cases hold | ☑ pass | Real tmux terminal: existing config + `n` → `unchanged`; no `LINEAR_API_KEY` → export instruction, EXIT=1, no file; wrong key on the REAL Linear endpoint → `[board] init failed: Linear rejected the API key (HTTP 401/403); check LINEAR_API_KEY; nothing written`; Ctrl-D → EXIT=0, no file; no controlling terminal (`setsid`) → rc=0, no file; team name with `\x1b[31m` shown with the ESC stripped; written board.json has 0 `lin_api` matches — pass |
| verify | ☑ pass | /verify by user 2026-10-19. Round 1 FAIL: `open("/dev/tty","r+")` → `UnsupportedOperation: File or stream is not seekable.`; setup.sh `y` → `offer rc=0`, no board.json. Fixed 9b5c55b. Round 2 at the real surface (tmux, stub Linear GraphQL via URL shim): full flow → `[board] wrote .claude/board.json (board mode online)`, `status_map {"Code Review": "Ready for Review"}`, `me "HungN"`, `id_pattern "ENG-\\d+"`; that config then drives `board_sync.py pull` (`pulled 2 tasks`) and the merge gate (ENG-171 rendered under Ready for Review); setup.sh `y`+no key → `[WARN] Board setup did not finish; the project stays in local mode.`; `n` → nothing; existing config → not asked — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t155 (+ callers: merge gate, pull_moment); 0 P0/P1 code findings; P1 process (Startup reads incomplete, still partial after round 2); P2 MCP-only sync → T163; lane EXCEEDS 523>500 (warn) — pass |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest -q`: 409 passed in 12.92s |
| /verify FAIL fix: real-terminal prompt (T155 round 2) | pass | `tests/test_board_init.py::test_init_prompts_on_a_real_pty` (pty as controlling terminal). RED before fix (tty_ask opened /dev/tty "r+" -> UnsupportedOperation -> silent exit 0): `FAILED ...test_init_prompts_on_a_real_pty - AssertionError ... 1 failed in 10.06s`. GREEN after (separate write/read handles): `1 passed`. Also `test_setup_warns_when_init_writes_no_config`. |
| Full suite, both folders | pass | `python3 -m pytest -q tests .claude/hooks/tests`: 1276 passed, 25 subtests passed in 38.35s; test_setup.sh 18/0, test_one_command_menu.sh 22/0, test_update.sh 38/0, test_shellcheck_clean.sh PASS |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | CLI/hooks-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | CLI/hooks-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | CLI/hooks-only task, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-10-19T08:31:06Z, `python3 scripts/board_sync.py init`, before any implementation commit):
```
usage: board_sync.py [-h] {pull,flush,status,push} ...
board_sync.py: error: argument command: invalid choice: 'init' (choose from pull, flush, status, push)
exit=2
ls: cannot access '.claude/board.json': No such file or directory
```

**AFTER**:
```
2026-10-19T08:38:22Z
exit=0 (no terminal: silent)
...................                                                      [100%]
19 passed in 0.18s
[board] wrote .claude/board.json (board mode online). Your API key is not stored; keep LINEAR_API_KEY in your shell profile.
{
  "board": "linear",
  "connection": "api",
  "team": "t-1",
  "project": "p-1",
  "me": "HngNguyn.h",
  "status_map": {
    "Code Review": "Ready for Review"
  },
  "id_pattern": "ENG-\\d+",
  "git_auto_status": false
}
```

**DELTA**: `setup.sh` (and `board_sync.py init`) now offers online board mode and writes a secret-free `.claude/board.json`; with no terminal or "no", nothing changes.

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T155 via the active-task state file.
