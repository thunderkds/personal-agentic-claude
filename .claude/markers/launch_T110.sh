#!/bin/bash
MARK=/home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/markers/T110
echo $$ > "$MARK.pid"
trap 'rc=$?; printf "%s" "$rc" > "$MARK.exit"; touch "$MARK.done"' EXIT INT TERM HUP
cd /home/hungnguyenhuu/workspace/pets/wt-t110 || exit 1
claude --model sonnet --permission-mode acceptEdits "$(cat /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/markers/prompt_T110.txt)"
