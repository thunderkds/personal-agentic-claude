---
name: dotfiles
description: "Optional: keep shared agent config in one folder of the user's own git repo. Shows what would change in each CLI config folder the user chooses (plan), applies it only after the user approves that plan, and reports drift (status). It adds deny and ask rules and links skills and instructions; it never copies an allow rule and never removes anything. In [auto] mode it runs plan only. Invoke when the user asks to share agent config across CLI folders, or via /dotfiles."
---

## Role: Dotfiles

You are the Supervisor. This skill is optional: no stage needs it, and a project that skips it
loses nothing. The script `scripts/dotfiles.py` does every read and every write. You never edit a
CLI config folder by hand. It needs only `python3`.

### Rules

- Run `plan` first. Show its output unchanged.
- Ask the user which folders to change. Never pick a folder alone. `~/.claude-<name>` can be
  another person's account.
- Run `apply` only after the user approves that plan, for the folders in that plan.
- The script only adds. It never removes a rule, a key, a link or a file.
- It copies only `permissions.deny` and `permissions.ask`. It never copies `permissions.allow`,
  `hooks`, `env`, `defaultMode` or any other key: it reports them as ignored.
- A `conflict` line stays as it is. Tell the user, and do not move or delete the file to clear it.
- Do not show or read other files in a CLI config folder. The script opens only `settings.json`.

### The source folder

The default source is `~/.dotfiles/agents`. Use `--source <dir>` for another path. Each part is
optional:

```
settings.base.json   deny and ask rules, added to Claude folders
AGENTS.md            linked as CLAUDE.md (Claude folders) and AGENTS.md (Codex folders)
skills/<name>/       linked as skills/<name> in each folder
```

Codex folders get skills and instructions only, never settings.

### Step 1 — Find the folders

```
python3 ${CLAUDE_SKILL_DIR}/scripts/dotfiles.py plan --source <dir>
```

With no target folder the script changes nothing. It lists each `~/.claude*` folder with a
`settings.json`, and `~/.codex`. If the source is missing it prints the expected layout: show it
to the user and stop.

### Step 2 — Show the plan

Ask which folders to include. Then run `plan` with those folders and show the output:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/dotfiles.py plan --source <dir> --claude-dir <dir> --codex-dir <dir>
```

- `+ permissions.deny: <rule>` or `+ permissions.ask: <rule>` is a rule the script will add.
- `+ link <name> -> <path>` is a link the script will make.
- `conflict <name>` is a path that exists and is not our link, or our link to a source part that
  is gone (`broken link`). The script leaves it unchanged.
- `refused` means the script writes nothing in that folder, for example on invalid JSON or a
  read-only `settings.json`. Exit 2.
- `skipped` means the folder does not exist.

Ask: "Apply this plan to these folders?"

### Step 3 — Apply on approval

Only after the user approves that plan, run the same command with `apply`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/dotfiles.py apply --source <dir> --claude-dir <dir> --codex-dir <dir>
```

Before it changes `settings.json`, it writes `settings.json.bak-<timestamp>` beside it. To undo,
copy that file back. A second run prints `no change`. The script rewrites the file through JSON
with 2-space indent, so tell the user the indentation and number spelling may change
(`1.10` to `1.1`). A number a float cannot hold exactly can change, and the backup keeps the original. No key
or rule is removed. If the user says no, write nothing.

A `refused` line after the `+` lines means those changes were not made. The run goes on to the
next folder and ends with exit 2. A write can fail part way, so run `status` to see what is left.

### Step 4 — Check drift

Any time later:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/dotfiles.py status --source <dir> --claude-dir <dir> --codex-dir <dir>
```

Exit 0 means in sync. Exit 1 means drift or a conflict. Exit 2 means a folder was refused, or the
source or a chosen folder is missing. A rule that exists only in the target is not drift.

### Auto mode (`[auto]`)

Ask no question. Run `plan` with no target folder, and write nothing. Name no folder for the user.
In the final report put one line: `Not done: dotfiles apply — yours to approve`, then the
folder list that `plan` printed.

### Done when

- The user approved and `apply` printed `no change` or its changes, or
- The user said no, or the source is missing, and you told the user why, or
- In auto mode, the `Not done:` line is in the final report.

## Known limits

- `apply` exits 0 when a folder is skipped or a conflict stays, so run `status` after it.
- A FIFO at the source file makes the script hang.
- A stdout that cannot encode a rule makes the script fail with a traceback.
