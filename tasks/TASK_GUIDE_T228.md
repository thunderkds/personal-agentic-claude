# TASK_GUIDE — T228: dotfiles skill keeps agent config in one source
**Date**: 2026-11-01
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-01, verbatim: "hey, I want to apply dotfiles to this kit, let investigate, brainstorming, and start to implement". Examples given: https://trungngo.github.io/dot-cli/, https://mcpmarket.com/tools/skills/dotfiles-manager-1, https://github.com/ryoppippi/dotfiles/tree/main. Path chosen: "A, yes, let go and check about that" (Option A, its 50% form, in `docs/brainstorming/BRAINSTORMING_LOG_dotfiles.md`).

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A user keeps shared agent config in one folder of their own git repo. An optional kit skill shows what would change in each chosen CLI config folder, applies it only when asked, and reports drift. It adds rules and links, and never removes or weakens anything.

**Out of scope** (what this task explicitly does NOT do):
- `remove`, `adopt`, per-folder profiles (cut list of the 50% form)
- General dotfiles: shell, git, editor config
- Installing dot-cli, Stow, Nix or any other tool
- Any change to `setup.sh`, `.claude/settings.json` or `.claude/hooks/`
- Running `apply` on this machine's real home folder: the user does that
- Copying `permissions.allow`, `hooks`, `env`, `defaultMode` or any other settings key

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):
- None in `PRD.md`: stand-in Requirements (`PROJECT_SPEC.md` `## Readiness`). Direct user request above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user picked Option A)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above (no refs: direct request)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `dotfiles`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `skills/dotfiles/scripts/dotfiles.py` is stdlib only, with subcommands `plan`, `apply`, `status`. Flags: `--source <dir>` (default `~/.dotfiles/agents`), repeatable `--claude-dir <dir>`, repeatable `--codex-dir <dir>`. With no target folder it changes nothing, lists the folders it found (`~/.claude*` with a `settings.json`, `~/.codex`), and exits 0 | "apply dotfiles" |
| 2 | Source layout: `settings.base.json`, `AGENTS.md`, `skills/<name>/`. Each part is optional. A missing source folder prints the expected layout and exits 0, with no write | one source, ryoppippi example |
| 3 | `plan` prints every change per target folder and writes nothing | dot-cli `plan` |
| 4 | Settings: from `settings.base.json` only `permissions.deny` and `permissions.ask` are read. They are added to the target's lists, target order first, no duplicates. Every other key in source is reported as ignored. Every target key is kept, byte order of keys preserved by `json` load/dump. `permissions.allow` is never copied, following `lib/merge-settings.py` T148 "an allow would widen it" | "never weakens" |
| 5 | `apply` writes a timestamped backup beside `settings.json` before a change, writes through a temp file in the same folder and renames, and keeps the file mode. With nothing to change it writes nothing, and a second run reports no change | safety |
| 6 | Skills: each `skills/<name>` gets a symlink at `<target>/skills/<name>`. `AGENTS.md` gets a symlink at `<claude-dir>/CLAUDE.md` and `<codex-dir>/AGENTS.md`. A real file, or a link to somewhere else, at the target is reported as a conflict and left unchanged. An empty `CLAUDE.md` of 0 bytes also counts as a conflict | ryoppippi example |
| 7 | `--codex-dir` targets get skills and instructions only, never settings. A missing target folder gets one skipped line | Codex projection |
| 8 | Invalid JSON in a target `settings.json` is refused for that folder with nothing written there, the other folders go on, and the exit code is non-zero. `status` exits 0 when in sync and 1 on drift | safety |
| 9 | The script reads no file in a target folder except `settings.json`, and never touches `.credentials.json`, `history.jsonl`, `projects/`, `sessions/`. It makes no network call and starts no process | "never read credentials" |
| 10 | `skills/dotfiles/SKILL.md`: says it is optional, runs `plan` first, shows the output, asks which folders, runs `apply` only after the user approves that plan, and never picks a folder alone. Auto mode: `plan` only, one `Not done:` line | "optional" |
| 11 | README names the skill within its line cap; `CLAUDE_LEGACY.md` skill list; the site's skill count is right | docs |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Target with 0 deny; source with 7 deny, 2 allow, `env` | `apply` adds 7 deny; allow and env stay out; other target keys equal | automated test |
| 2 | Run `apply` twice | second run writes no file, adds no backup | automated test |
| 3 | `plan` on any state | hash of the whole temp home is the same before and after | automated test |
| 4 | Target `settings.json` invalid; second target valid | first untouched, second applied, exit non-zero | automated test |
| 5 | Real file at `CLAUDE.md`; link to elsewhere at `skills/x` | both reported as conflict, both unchanged | automated test |
| 6 | Secret-looking `.credentials.json` in target | its content never appears in output; the source of the script has no such read | automated test |
| 7 | Script source | imports no network module and no `subprocess` | automated test |
| 8 | File mode 600 on target settings | stays 600 after `apply` | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_dotfiles.py tests/test_site_content.py tests/test_readme_slim.py -q
python3 skills/dotfiles/scripts/dotfiles.py plan --source /nonexistent
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T228.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T228.md`.

---

## Approach

**Pattern reference**: `skills/companion-setup/` on branch `feat/t226-companion-setup` is not on `main`, so use `skills/settings-setup/SKILL.md` + its `### Auto mode` for the skill shape. `lib/merge-settings.py` for add-only list union. Do not import it: it holds hook logic for project files.

**Vital slice**: settings union, skill and instruction links, `plan`/`apply`/`status`.
**Cut list**: `remove`, `adopt`, profiles, restore command (the backup is one `cp`), templates, secrets, general dotfiles.

Settings are merged, not linked: the five folders differ, and Claude Code may rewrite `settings.json`.

---

## Edge Case Checklist

- [ ] Only allow-listed paths are read in a target
- [ ] The merge only adds; lists have no duplicates
- [ ] No folder is applied by default: `~/.claude-wife` looks like another person's account
- [ ] Invalid JSON, or `permissions` / `deny` of the wrong type, refuses that folder
- [ ] A crash leaves the old file: temp file in the same folder, then `os.replace`
- [ ] `settings.json` missing in a chosen target: created with only the added rules
- [ ] A link already correct counts as no change
- [ ] A symlinked `settings.json` is reported, not replaced: `os.replace` would break the link
- [ ] Skill folder names that start with `.` are ignored
- [ ] Tests use a temp home only; never the real one. `HOME` is set in each test
- [ ] `README.md` is at its 75-line cap: replace or merge a line, never raise the cap
- [ ] `tests/test_site_content.py` compares the site's skill count with `skills/`. T226 also raises it, so the second merge needs one rebase

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/dotfiles/SKILL.md` | new skill |
| `skills/dotfiles/scripts/dotfiles.py` | new script |
| `tests/test_dotfiles.py` | new tests |
| `CLAUDE_LEGACY.md` | skill list |
| `README.md` | one line, within the cap |
| `site/index.html` | skill count |
| `tests/test_agents_md_primary.py`, `tests/test_agent_guide_dedup.py` | only if a pin on skill lists fails |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | no new question |
| `.claude/settings.json`, `.claude/hooks/` | no project behaviour change |
| `AGENTS.md` | Stage index edit is the Supervisor's after review |
| `memory/` | Supervisor-only |
| `~/.claude*`, `~/.codex` | the user applies to real folders |

---

## Test Plan

New `tests/test_dotfiles.py` covers the Success Criteria in temp folders. Then the full suite: `python3 -m pytest tests/ .claude/hooks/tests/ -q`, and `bash scripts/validate.sh`.

---

## Questions Log

- 2026-11-01 RULE Copy `permissions.allow`? → No. `lib/merge-settings.py` T148: an allow would widen what an agent may do.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T228.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
