---
name: git-guardrails-claude-code
description: Set up a Claude Code PreToolUse hook that blocks dangerous git commands (push, reset --hard, clean -f, branch -D, checkout/restore .) before they execute. Use during Stage 1 one-time setup to protect worktrees from destructive git operations.
---

## Role: Git Safety Hook Installer

Installs a `PreToolUse` hook that intercepts and blocks destructive git commands before Claude runs them — a guardrail for the isolated worktrees sub-agents work in (Stage 3). Complements `update-config` and `fewer-permission-prompts` in the Stage 1 one-time setup checklist.

### What gets blocked
`git push` (all variants incl. `--force`), `git reset --hard`, `git clean -f` / `-fd`, `git branch -D`, `git checkout .` / `git restore .`. When blocked, Claude is told it does not have authority to run the command.

### Steps

#### 1. Ask scope
Install for **this project only** (`.claude/settings.json`) or **all projects** (`~/.claude/settings.json`)?

#### 2. Place the hook script
The bundled script lives at `.claude/skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh`. Copy it to:
- **Project**: `.claude/hooks/block-dangerous-git.sh`
- **Global**: `~/.claude/hooks/block-dangerous-git.sh`

Then `chmod +x` it.

#### 3. Register the hook (via the `update-config` skill)
Add to the chosen settings file, merging into any existing `hooks.PreToolUse` array — never overwrite other settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh" }
        ]
      }
    ]
  }
}
```
(Global scope: use `~/.claude/hooks/block-dangerous-git.sh` as the command.)

#### 4. Ask about customization
Ask whether to add/remove patterns from the blocked list; edit the copied script accordingly.

#### 5. Verify
```bash
echo '{"tool_input":{"command":"git push origin main"}}' | .claude/hooks/block-dangerous-git.sh
```
Should exit code 2 and print a BLOCKED message to stderr.

### Note for this framework
The Supervisor commits/pushes only when the user explicitly asks. This hook enforces that boundary mechanically — if the user later authorizes a push, they run it themselves (or temporarily disable the hook), keeping destructive git an explicit human decision.

### Communication Protocol
- **Default Notification**: "Git guardrails installed (scope: project/global). Blocked patterns: [list]. Verified: exit 2 on `git push`."
