# TASK_REVIEW — T116: Every pack ships as a dormant catalog; the broken install-time pack installer is removed

> Sibling of `tasks/TASK_GUIDE_T116.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | no CLI sees pack skills, M1/M2 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1–D2 site #packs/#options, D3 PROJECT_SPEC.md, D4 README, D5 docs-agreement test extended + mutation control |
| `tests/test_pack_choice_parsing.sh` retired — reason | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | installer + MANIFEST; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Common-Infrastructure-Agent, 2026-09-23T06:17:46Z–06:18:02Z, branch head `e893453`,
before any implementation commit). Kit = `git archive HEAD` committed into a scratch repo, served as
`SUPERVISOR_REPO=file://…/kit`; target = empty scratch git repo; interactive path driven through a
pty (`run_in_pty` from `tests/lib/pty.sh` = `script -qec`), answers `1` Install, `1` Claude Code,
`1` New project, `1, 5` packs, Enter to Proceed. `--pack=mobile` is not reproduced: since T115 every
argument exits 1 before anything is written (guide, *Drift* §1).

**B1 — interactive menu, machine with no central clone** (`SUPERVISOR_PATH=<nonexistent>`, the case
every post-ADR-0001 user is in), rc=0:
```
        Enter numbers separated by spaces, or press Enter to skip:
Plan: Install Easy Kit into …/scratchpad/before/clean
  - CLIs: Claude Code
  - Project type: New project (CLAUDE.md)
  - Copies in: agents, skills, .claude/hooks, templates, docs/claude-md, AGENTS.md, .cursor/rules, CLAUDE.md
  …
Proceed? [Y/n] [info]  Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.
[info]  Wrote ./.claude/harness-lock.json (74 file hashes).
[warn]  Pack 'mobile' not found in central clone (…/before/no-clone/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/before/no-clone/packs/api) — skipping.
[info]  Setup complete. Easy Kit copied into …/scratchpad/before/clean
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  CLIs: Claude Code
[info]  Packs requested: mobile api
$ ls agents | grep -cE 'mobile|api-'   → 0
$ ls -d packs                          → No such file or directory
```

**B2 — same answers, default `SUPERVISOR_PATH` on this machine, where a v1 `~/.supervisor` clone
still exists.** Worse than "installs nothing": the pack path writes **absolute symlinks out of the
project** into the canon, through the `.claude/agents -> ../agents` link, none of them in the lock:
```
[info]  Pack 'mobile' installed.
[info]  Pack 'api' installed.
[info]  Packs requested: mobile api
agents/api-designer.md     -> /home/hungnguyenhuu/.supervisor/packs/api/agents/api-designer.md
agents/mobile-developer.md -> /home/hungnguyenhuu/.supervisor/packs/mobile/agents/mobile-developer.md
skills/auth-checklist      -> /home/hungnguyenhuu/.supervisor/packs/api/skills/auth-checklist/
skills/contract-review     -> /home/hungnguyenhuu/.supervisor/packs/api/skills/contract-review/
skills/platform-compatibility -> /home/hungnguyenhuu/.supervisor/packs/mobile/skills/platform-compatibility/
skills/ui-accessibility    -> /home/hungnguyenhuu/.supervisor/packs/mobile/skills/ui-accessibility/
```

**B3 — no terminal** (`setsid -w sh setup.sh </dev/null`), rc=0:
```
[info]  No terminal — no packs installed. Re-run in a terminal to pick packs from the menu.
…
[info]  Setup complete. Easy Kit copied into …/scratchpad/before/notty
$ ls -d packs → No such file or directory
```

In every BEFORE run the project receives **no `packs/` directory**: no catalog exists.

*Historical, not reproducible since T115* — Supervisor probe, 2026-09-12, `main` `8115bc9`:

`--pack=mobile`:
```
[warn]  Pack 'mobile' not found in central clone (…/home/.supervisor/packs/mobile) — skipping.
[info]  Packs requested: mobile
NO mobile agent installed
```

Interactive menu via pty, answer `1, 5`:
```
[warn]  Pack 'mobile' not found in central clone (…/.supervisor/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/.supervisor/packs/api) — skipping.
[info]  Packs requested: mobile api
```

**AFTER**: [install output with catalog line; `packs/` present; no pack names under CLI dirs]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
