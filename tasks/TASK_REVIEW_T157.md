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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T157.jsonl`, never the
implementing agent alone]
