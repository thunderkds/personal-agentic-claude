#!/bin/bash
MARK=/home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/markers/T115
echo $$ > "$MARK.pid"
trap 'rc=$?; printf "%s" "$rc" > "$MARK.exit"; touch "$MARK.done"' EXIT INT TERM HUP
cd /home/hungnguyenhuu/workspace/pets/wt-t115 || exit 1
claude --model opus --permission-mode acceptEdits "$(cat /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/markers/prompt_T115.txt)"
