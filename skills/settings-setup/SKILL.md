---
name: settings-setup
description: "Stage 1 step: offer settings profiles (High security, Legacy, Solo engineer, Team project, Empty) for the project's .claude/settings.json, ask up to 3 setup questions, and use High security when the user skips. Shows the exact keys it will add, writes only after the user approves, and never removes or changes an existing key, hook or rule. In [auto] mode it writes nothing and puts the recommendation in the final report. Invoke at Stage 1 checklist item 1, or via /settings-setup."
---

## Role: Settings Setup

You are the Supervisor. You give the project a safe start for `.claude/settings.json`. You use the
profiles in `profiles.json` and the script `scripts/apply_profile.py`. You never edit the settings
file by hand: the script does every write, so the add-only rules hold.

### Rules

- Write only the project file `.claude/settings.json`. Never write `~/.claude/settings.json` or
  `.claude/settings.local.json`.
- The script only adds. It keeps every existing key, hook and rule. A scalar the user already set
  stays as it is (the script prints `= kept <key>: <theirs>`).
- Show the dry run before any write. Write only after the user says yes.
- No profile sets `permissions.allow`, `permissions.defaultMode`, `bypassPermissions` or a sandbox
  key. Do not add them here; send such requests to the user's own settings work.
- Needs only `python3`. Run every command from the project root.

### The profiles

Read `profiles.json`. Each profile has an `id`, a `label`, a `for` line (who it is for) and `values`.

| id | Use when |
|---|---|
| `high-security` | The default. The user skips, or does not answer. |
| `legacy` | The user wants to keep today's kit behavior. |
| `solo-engineer` | One person works on the project. |
| `team-project` | Several people share the repo. |
| `empty` | The user wants no change. |

### Step 1 — Detect

Run a dry run for each profile:

```
python3 skills/settings-setup/scripts/apply_profile.py <id> --dry-run
```

- Exit 2: the script cannot read the file safely (for example JSONC comments). It changed
  nothing. Tell the user the reason it printed, and stop. Do not fix the file yourself.
- `high-security`, `solo-engineer` or `team-project` prints `no change`: say
  "This project already has profile <label>." and stop.
- Only `legacy` prints `no change`: the project has the kit's 2 anchor rules (Legacy). Say so,
  and go on to Step 2. Legacy is today's kit default, not a choice the user made.

### Step 2 — Offer the profiles

Show each profile as `<label> — <for>`, from `profiles.json`. Say that High security is the
default. The user can pick one profile by name. Then go to Step 4.

### Step 3 — Ask (only if the user does not pick)

Ask at most 3 questions, one at a time. Each one may be skipped.

1. "Do you want to keep today's kit behavior, with no new rules?" Yes: use `legacy` only. Stop
   asking.
2. "Do you work alone on this project, or with a team?" Alone: `solo-engineer`. Team:
   `team-project`. Skip: none.
3. "Does the repo or your machine hold secret files (`.env`, keys, cloud credentials)?" Yes or
   skip: add `high-security`. No: do not add it, unless question 2 gave no profile.

The result is the list of profiles to apply, in this order: the question 2 profile, then
`high-security`. If the list is empty, use `high-security`. Skip or no answer at any point means
`high-security`.

### Step 4 — Show the change

For each chosen profile, run the dry run and show its output unchanged:

```
python3 skills/settings-setup/scripts/apply_profile.py <id> --dry-run
```

- `+ <key>: <value>` is a rule or key the script will add.
- `= kept <key>: <theirs>` is a key the user already set to another value. The script keeps it.
- `no change` means the profile adds nothing.

Ask: "Write these changes to `.claude/settings.json`?"

### Step 5 — Write on approval

Only after the user says yes, run each chosen profile without `--dry-run`:

```
python3 skills/settings-setup/scripts/apply_profile.py <id>
```

It prints the lines it added and `wrote .claude/settings.json`. A second run prints `no change`.
If the user says no, write nothing and say that the file did not change.

The script writes 2-space JSON with a trailing newline. Tell the user that it may change the
file's indentation, and that no value is removed.

### Auto mode (`[auto]`)

Ask no question. Run only Step 1 and the dry run of `high-security`. Write nothing. In the final
report, under `Not done:`, put: `settings-setup: recommend high-security (dry run below), not
written — yours to approve`, then the dry-run lines.

### Done when

- The user approved and the script printed `wrote ...` or `no change`, or
- The user said no, or the step stopped at Step 1, and you told the user why, or
- In auto mode, the recommendation is in the final report.
