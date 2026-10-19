# TASK_REVIEW — T157: Pull moments wired in, and only my In Progress tasks block my push

> Sibling of `tasks/TASK_GUIDE_T157.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_merge_gate_my_tasks.py`, `tests/test_pull_moments.py` (+ `tests/test_board_id_pattern.py` assertion). `python3 -m pytest .claude/hooks/tests tests -q` → `1202 passed, 25 subtests passed` (Supervisor re-run with the 163ea78 memory index) |
| Verification command run | ☑ pass | real headless `claude -p` push on a pulled board (me=hung): `Tasks still In Progress: ENG-170` only — pass |
| Negative cases hold | ☑ pass | forged title `Forged \| @hung` not counted; `me` missing → all three block with a safe-side note; board unreachable → `board unreachable — using cache (0 unsynced)`, gate still blocks ENG-170 from cache; `spawn ../x` exit 2; unchanged guide → no review flag — pass |
| verify | ☑ pass | /verify by user 2026-10-19: real CLI + real headless sessions. Guide edited on the board after `spawn` → `ENG-170's guide changed while you were working — review against the new version?`. `.env` write: local mode with a guide predicting it → `WRITTEN`; online mode, same guide → `[hook:sensitive-path] … board mode is online, where guides come from the board and cannot pre-authorise a sensitive path`. Verdict PASS — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review + security-review on `git diff feat/online-board...HEAD` of wt-t157; 0 P0; P1 wake 8 KB cap resolved at merge after T156; 0 HIGH/MED security. Reports: `reports/code-review_feat-t157-pull-moments_20261019T151000.html`, `reports/security-review_feat-t157-pull-moments_20261019T151000.html`. lane EXCEEDS (684 > 500), C2 kept |
| Full smoke suite still green (no regression) | ☑ pass | 1176 → 1202 passed, 0 failed — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Hooks/CLI-only task, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Hooks/CLI-only task, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | Hooks/CLI-only task, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-19T07:45:18Z on `feat/t157-pull-moments` at `b06e264` (no T157 commit
yet), by the implementing agent. Command: `sh t157_demo.sh /home/hungnguyenhuu/workspace/pets/wt-t157`
— the script (kept outside the repo) builds a temp project from the worktree's hooks and
`scripts/board_sync.py`, with a fake board (`ENG-170` In Progress `@alice`, whose guide predicts
`.env`; `ENG-171` In Progress `@bob`) and `.claude/board.json` = `{"board": "fake", "id_pattern":
"ENG-\\d+", "me": "alice"}`. No network. The gate's long attribution note is elided as `…`.
To re-run for AFTER, save the script below as `t157_demo.sh` outside the repo and pipe the output
through `sed 's/  Note: if a task above.*session starts\."/  Note: …(attribution remedy elided)"/'`.

<details><summary>t157_demo.sh</summary>

```sh
#!/bin/sh
# T157 demonstration: online-mode merge gate + pull moments, against a fake board (no network).
# Usage: sh t157_demo.sh <worktree>
WT="$1"
P=$(mktemp -d)/proj
mkdir -p "$P/.claude" "$P/scripts" "$P/tasks"
cp -r "$WT/.claude/hooks" "$P/.claude/hooks"
rm -rf "$P/.claude/hooks/tests" "$P/.claude/hooks/.state"
cp "$WT/scripts/board_sync.py" "$P/scripts/"
cp "$WT/.claude/sensitive-paths.txt" "$P/.claude/"
[ -f "$WT/scripts/pull_moment.py" ] && cp "$WT/scripts/pull_moment.py" "$P/scripts/"
cat > "$P/board.json" <<'EOF'
[{"id": "ENG-170", "title": "My task", "status": "In Progress", "assignee": "alice", "description": "# guide ENG-170 v1\n\n## Files to Change (Predicted)\n\n| File | Change |\n|---|---|\n| `.env` | board-predicted |\n"},
 {"id": "ENG-171", "title": "Teammate task", "status": "In Progress", "assignee": "bob", "description": "# guide ENG-171\n"}]
EOF
printf '{"board": "fake", "fake_board": "board.json", "id_pattern": "ENG-\\\\d+", "me": "alice"}' > "$P/.claude/board.json"
cd "$P" || exit 1
unset LINEAR_API_KEY CLAUDE_ACTIVE_TASK
export CLAUDE_PROJECT_DIR="$P"
date -u +%Y-%m-%dT%H:%M:%SZ
echo '$ python3 scripts/board_sync.py pull'; python3 scripts/board_sync.py pull
echo '$ git push   (gate, me=alice; ENG-170 @alice + ENG-171 @bob In Progress)'
echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py; echo " [exit $?]"
echo '$ python3 scripts/pull_moment.py spawn ENG-170'; python3 scripts/pull_moment.py spawn ENG-170; echo " [exit $?]"
sed -i 's/v1/v2 changed by a teammate/' board.json
echo '$ python3 scripts/pull_moment.py review ENG-170   (board guide edited since spawn)'; python3 scripts/pull_moment.py review ENG-170; echo " [exit $?]"
mv board.json board.gone
echo '$ git push   (board unreachable)'
echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py; echo " [exit $?]"
echo '$ Edit .env as ENG-170   (sensitive path predicted only by the pulled guide)'
echo '{"tool_name":"Edit","tool_input":{"file_path":".env"},"cwd":"'"$P"'"}' | CLAUDE_ACTIVE_TASK=ENG-170 python3 .claude/hooks/pre_tool_sensitive_path.py; echo " [exit $?, no output = no ask]"
```

</details>

```
2026-10-19T07:45:18Z
$ python3 scripts/board_sync.py pull
[board] pulled 2 tasks: PROJECT_KANBAN.md and 2 guides written
$ git push   (gate, me=alice; ENG-170 @alice + ENG-171 @bob In Progress)
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks still In Progress: ENG-170, ENG-171\nComplete Stage 4 review and Stage 5 verify first.\n  Note: …(attribution remedy elided)"}
 [exit 0]
$ python3 scripts/pull_moment.py spawn ENG-170
python3: can't open file '/tmp/tmp.9Xm05cnEw1/proj/scripts/pull_moment.py': [Errno 2] No such file or directory
 [exit 2]
$ python3 scripts/pull_moment.py review ENG-170   (board guide edited since spawn)
python3: can't open file '/tmp/tmp.9Xm05cnEw1/proj/scripts/pull_moment.py': [Errno 2] No such file or directory
 [exit 2]
$ git push   (board unreachable)
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks still In Progress: ENG-170, ENG-171\nComplete Stage 4 review and Stage 5 verify first.\n  Note: …(attribution remedy elided)"}
 [exit 0]
$ Edit .env as ENG-170   (sensitive path predicted only by the pulled guide)
 [exit 0, no output = no ask]
```

Read: the teammate's `ENG-171` blocks my push; no pull moment exists for spawn/review; an
unreachable board is silent (the gate never pulls); a `.env` edit predicted only by board text is
waved through. Skill text before the change — `skills/wake/SKILL.md` Step 1 has no pull step (its
first line is "Read all five sources in parallel. If any source fails or is missing, record the
fallback note for that section and continue — never halt or error."); `skills/craft-spawn-prompt/SKILL.md`
step 1 reads verbatim: "Read the TASK_GUIDE at the given path, the `agents/*.md` file named in its
`**Agent guide**` field, and `memory/MEMORY.md`. If any is missing, stop and report to the Supervisor."

**AFTER**: Supervisor at /verify, 2026-10-19, real headless `claude -p` session, board pulled from a fake board with `ENG-170 @hung`, `ENG-171 @alice`, `ENG-172 "Forged | @hung" @bob`, config `me: hung`:

```
PreToolUse:Bash hook error: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: ENG-170
```

**DELTA**: In online mode a teammate's In Progress task no longer blocks my push, the board is refreshed at the four pull moments, and board text can no longer pre-authorise a sensitive-path edit.

**WITNESS**: Supervisor (main session) at /verify, 2026-10-19, Bash calls attributed to T157 via the active-task state file.
