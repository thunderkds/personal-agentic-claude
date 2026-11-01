# BRAINSTORMING_LOG_dotfiles.md
**Generated**: 2026-11-01
**Task / Context**: User request "apply dotfiles to this kit". No task ID yet. Tier: Standard (3 viable directions).
**Skill**: `Skill({ skill: "brainstorming" })`

---

## The Problem Space

The user named three examples. All three keep home-folder config in one git repo and apply it to a machine:

| Example | Engine | What to learn from it |
|---|---|---|
| dot-cli (`trungngo/dot-cli`) | Rust binary, YAML bundles | The command set: `plan`, `apply`, `status`, `diff`, `remove`, `adopt`. A real file in the way is backed up. |
| Dotfiles Manager skill (`trevors/dot-claude`) | GNU Stow | A skill drives the tool, dry run first. `--adopt` moves an existing file into the repo. |
| `ryoppippi/dotfiles` | Nix flake, Home Manager | `agents/AGENTS.md` and `agents/skills/` are one source for Claude Code and Codex. `registry/sources/` pins outside skill repos. |

The kit is per project today: `setup.sh` writes into a project and nothing into the home folder. It has no dotfiles support (`git grep` finds no mention).

This machine shows the real problem. No dotfiles repo or manager exists. Five Claude config folders are selected by `CLAUDE_CONFIG_DIR` aliases in `~/.zshrc`, and all five `settings.json` files differ:

| Folder | defaultMode | allow | ask | deny | hook events | plugins |
|---|---|---|---|---|---|---|
| `~/.claude` | auto | 5 | 4 | 7 | 11 | 2 |
| `~/.claude-personal` | auto | 6 | 0 | 0 | 7 | 2 |
| `~/.claude-work` | none | 5 | 0 | 0 | 7 | 3 |
| `~/.claude-wife` | none | 0 | 0 | 0 | 0 | 0 |
| `~/.claude-hung2` | auto | 6 | 4 | 7 | 7 | 2 |

The deny rules in `~/.claude` protect `~/.ssh`, `~/.aws`, `.env` and keys. Only 2 of 5 folders have 7 deny rules, and `-personal`, used by this session, has none.

Non-negotiable:
- Optional. A project that ignores it behaves as it does today.
- The kit never installs a third-party tool (T226 rule: `skills/score/SKILL.md` "You never install, start or upgrade the verifier").
- `setup.sh` gains no new question (user: keep setup simple).
- Never read, copy or commit credentials, history or session data.

---

## Questions for the User

1. Which path? (See Recommended Path.)

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Kit `dotfiles` skill | A kit skill and a stdlib script with `plan`, `apply`, `status`, `remove`, driven by one source folder in the user's git repo | Low: new skill only | ~300 lines + tests | Low for projects; Medium for home config | ✅ Yes |
| B | Guide on dot-cli | The kit ships an example bundle and a guide; dot-cli does the work | Low | ~60 lines | Low | |
| C | Read-only drift report | A script that shows how the config folders differ, and nothing more | Very low | ~80 lines | Very low | |

Rejected without a full write-up: Nix and Home Manager (needs a large install; against "keep it simple"); moving `agents/`, `skills/` etc. to user level (breaks the per-project model and every hook path).

### Option A — Kit `dotfiles` skill
**Approach**: The user keeps a folder, by default `~/.dotfiles/agents/`, in their own git repo: `settings.base.json` (shared keys), `AGENTS.md`, `skills/`, and `profiles/<name>.json` (only what differs per config folder). `plan` prints each change and writes nothing. `apply` backs up, then merges settings and links skills and instructions into each chosen config folder, and into `~/.codex`. `status` shows drift. `remove` restores from the record.
**Pros**: Fixes the found drift. Works with no new install, because `python3` is already a kit prerequisite. Takes `plan` and `status` from dot-cli and the one source for several CLIs from ryoppippi.
**Cons**: A new surface that writes to the home folder, so it needs careful tests. It overlaps a general dotfiles tool, on purpose only for agent config.
**Why it might fail**: Claude Code may rewrite `settings.json` itself, so a symlink would break or drift (not tested). That is why settings are merged, not linked. Scope can creep into general dotfiles (zsh, git); the cut list must hold.

### Option B — Guide on dot-cli
**Approach**: A doc and an example bundle. The user installs `dot` themselves.
**Pros**: Least code. Full engine, including secrets and remote hosts.
**Cons**: dot-cli is v0.1.0, created 2026-10-12, with 1 star and 10 open issues. It has no merge for JSON settings in the page or design notes I read, and the five folders differ, so a link or a template replaces what each folder has.
**Why it might fail**: The kit's guide depends on a tool that may change its config format ("before 1.0, a minor version may change the config format").

### Option C — Read-only drift report
**Approach**: `/dotfiles status`-style script with a report. The user fixes each folder by hand.
**Pros**: Smallest and no write risk.
**Cons**: It does not give the user what the three examples do: one repo that applies itself.
**Why it might fail**: The report is read once, and the drift stays.

---

## 50% Rule Check

Cut Option A to `plan`, `apply`, `status`. Drop `remove`, because `apply` keeps a timestamped backup and restoring is one `cp`. Drop profiles at first: the base file applies to each chosen folder, and existing keys stay. Drop `adopt`: the first `plan` prints what to copy. That is about 150 lines, and it still fixes the deny-rule gap.

---

## Recommended Path

**Option A — Kit `dotfiles` skill, in its 50% form.** It fixes the problem found on this machine, adds nothing to `setup.sh`, and depends on nothing new. `remove`, profiles and `adopt` wait until the first version has been used.

---

## Surgical Scope

Files that **should** be touched:
- `skills/dotfiles/SKILL.md`, `skills/dotfiles/scripts/dotfiles.py` — new
- `tests/test_dotfiles.py` — new, uses temp folders as the home folder only
- `docs/claude-md/pipeline-stages.md`, `CLAUDE_LEGACY.md`, `README.md`, `site/index.html`, `AGENTS.md` stage index — one line each; count pins as needed

Files that **must not** be touched:
- `setup.sh` — no new question
- `.claude/settings.json`, `.claude/hooks/` — no project behaviour change
- Any real home-folder file during tests

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Only allow-listed keys and paths are read: never `.credentials.json`, `history.jsonl`, `projects/`, `sessions/`, or a settings `env` key that may hold tokens
- [ ] The merge only adds: never removes a key, a rule or a hook; lists have no duplicates
- [ ] Each folder is chosen by the user: `~/.claude-wife` looks like another person's account, so no folder is applied by default
- [ ] `apply` refuses a folder whose `settings.json` is invalid JSON, and writes nothing to it
- [ ] Write through a temp file and rename, so a crash leaves the old file; keep the file mode
- [ ] A running Claude Code session may hold the file open or write it during `apply`
- [ ] A broad `allow` in the base file must not silently weaken a stricter folder: `plan` prints added allow rules separately
- [ ] `~/.claude/settings.json` hook commands with absolute paths stay as they are per machine
- [ ] A symlink already in place at a target is shown, not replaced
- [ ] A missing `~/.codex` is skipped with one line, and Codex gets only skills and instructions

---

## Next Actions

1. User picks a path.
2. Stage 2: register the task, write the guide with this checklist.
3. Stage 3: test first, in a worktree.
4. Applying to this machine's real folders is a separate step the user runs after `plan`.

---

## User Selection

> **Approved direction**: Option A — Kit `dotfiles` skill, 50% form. Task T228.
> Approved by user on 2026-11-01.
>
> Stage 2 narrowed the settings merge: only `permissions.deny` and `permissions.ask` are added. `permissions.allow` is never copied, following `lib/merge-settings.py` (T148).
