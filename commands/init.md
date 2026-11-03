---
description: "Set up this project for the Easy Kit plugin, once: writes CLAUDE.md, AGENTS.md, the board, tasks/, memory/ and the kit docs, add-only (an existing file is never changed). Then shows the kit's settings rules and writes them only after you approve."
---

# /easy-kit:init

You set up the current project for the Easy Kit plugin. A plugin cannot carry project files or
permissions, so this command adds them. It only adds: it never changes or deletes a file that
exists. Run every command from the project root (the folder Claude Code was started in).

## Step 1 — Add the project files

Run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plugin_init.py"
```

Show its whole output to the user, unchanged. It prints one line per path: `+ created <path>` or
`= kept <path>` (already there, not changed), then notes.

- Exit 2: it wrote nothing (for example, the folder is not in a git repository). Tell the user the
  reason it printed, and stop.
- Do not edit any file it kept. If a note says `CLAUDE.md` does not import `@AGENTS.md`, tell the
  user to add that line; do not add it yourself.

## Step 2 — Settings: show first, write only after approval

The plugin cannot set permissions. Follow the `settings-setup` flow (Steps 4 and 5 of
`${CLAUDE_PLUGIN_ROOT}/skills/settings-setup/SKILL.md`) for two profiles: `legacy` (the kit's 2 deny
rules that protect the trace anchors) and `high-security` (the default profile).

Show the change first. Run both dry runs and show their output unchanged:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/settings-setup/scripts/apply_profile.py" legacy --dry-run
python3 "${CLAUDE_PLUGIN_ROOT}/skills/settings-setup/scripts/apply_profile.py" high-security --dry-run
```

- Exit 2 (for example, `.claude/settings.json` is not valid JSON): it changed nothing. Tell the
  user the reason, write nothing, and go to Step 3. Never fix or overwrite the file yourself.
- Both print `no change`: say the settings already hold these rules, and go to Step 3.

Ask: "Write these changes to `.claude/settings.json`?" Only if the user says yes and approves, run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/settings-setup/scripts/apply_profile.py" legacy
python3 "${CLAUDE_PLUGIN_ROOT}/skills/settings-setup/scripts/apply_profile.py" high-security
```

The script only adds: every existing key, hook and rule stays as it is. If the user says no, write
nothing and say that the file did not change. In auto mode (`[auto]`), ask nothing and write
nothing: put the dry-run lines in the final report as yours to approve.

## Step 3 — Report

End with a short report: what was created, what was kept, and the settings result. Repeat these two
notes from Step 1's output:

- The copies of `templates/`, `docs/claude-md/`, `agents/` and the scripts go stale after a plugin
  update. Running `/easy-kit:init` again adds new files and never replaces one that is there.
- The gates are plugin hooks. Each teammate must install the easy-kit plugin; a teammate without it
  has no gates.
