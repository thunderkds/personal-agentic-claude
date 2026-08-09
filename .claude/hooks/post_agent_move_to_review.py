#!/usr/bin/env python3
"""
PostToolUse hook — fires after every Agent tool call.

**This hook does not move any row on PROJECT_KANBAN.md, and does not touch any
step counter. It only prints a reminder.** It is deliberately inert as a writer;
what follows is why, so the next reader does not "fix" it back.

Two defects made the automatic move actively harmful (T044):

1. **Wrong task.** The Task ID came from `re.findall(r"\\bT(\\d{3})\\b", prompt)`
   over the *whole* spawn prompt. Stage 3 at the time mandated pasting
   `memory/MEMORY.md` verbatim into every spawn prompt (T065 replaced that with
   a path reference), and that file is full of prose task IDs, so one spawn
   moved every mentioned task — observed emptying `### In Progress`
   entirely and deleting three unrelated step counters. Attribution now comes
   from `lib/task_context.py:resolve_task_id` (structural signals only, T043).

2. **Wrong time.** `PostToolUse` fires when the tool call *returns*. Sub-agents
   in this harness run in the background by default, so the call returns at
   spawn *issuance* — the board announced "Ready for Review" while the agent was
   still writing its first test (observed live on T039).

Fixing (1) does not fix (2), and there is no reliable completion signal to move
the row on. The harness does expose `SubagentStop` (and `TaskCompleted`), which
fire on genuine completion, but their payloads carry only `session_id` /
`transcript_path` / `agent_id` / `agent_type` — no `tool_input`, no spawn
prompt, no task identifier. `SubagentStop` matchers filter on *agent type*, and
one agent type (e.g. `common-infrastructure`) serves many tasks, so the event
cannot say *which* task finished. `resolve_task_id` has nothing structural to
work from, and guessing is the defect being removed.

So the row is moved by the Supervisor, by hand, as the pipeline already
requires (Hard-Stop Gate 3). A board that is confidently wrong is worse than one
a human keeps current. Reinstating the automatic move requires a completion
event that carries the task's identity — not a heuristic over a transcript.

Consequence worth knowing: the step-limit counter is no longer reset when a task
reaches a gate. Reset it manually if a rework cycle needs a fresh budget:
`rm .claude/hooks/.state/step_count_Txxx.txt`.
"""
import json
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

# Hooks run as standalone scripts from an arbitrary cwd, so the shared lib is
# imported off __file__, not off the import path. Fail open: a broken import
# must degrade to "unattributed", never crash a tool call.
sys.path.insert(0, os.path.join(HOOKS_DIR, "lib"))
try:
    from task_context import resolve_task_id
except Exception:
    def resolve_task_id(event):
        return None


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if not isinstance(event, dict) or event.get("tool_name") != "Agent":
        sys.exit(0)

    task_id = resolve_task_id(event)
    if not task_id:
        sys.exit(0)

    print(
        f"[hook:post_agent] Agent call returned for {task_id}. This fires at spawn "
        f"issuance for a background agent, not on completion — the board is NOT "
        f"updated. Verify the worktree, then move {task_id} on PROJECT_KANBAN.md "
        f"by hand.",
        file=sys.stderr,
    )


main()
