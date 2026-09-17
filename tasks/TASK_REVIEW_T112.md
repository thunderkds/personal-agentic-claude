# TASK_REVIEW — T112: First install never destroys a project's own files — they are backed up and named

> Sibling of `tasks/TASK_GUIDE_T112.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | identical content (no .bak), existing .bak, non-git, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1–D2 PROJECT_SPEC.md, D3 site #install, D4 RUNBOOK.md |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Repo pre-seeded with
`CLAUDE.md` = `# my project rules`, `AGENTS.md` = `# my agents`, then `setup.sh </dev/null`:

```
CLAUDE.md now: # Claude Project Supervisor Guidelines
AGENTS.md now: # AGENTS.md
```

Exit 0, no warning, no backup.

**BEFORE — directory case** (Common-Infrastructure-Agent, 2026-09-17, kit HEAD `d1f91de` = `main` + guide
retarget only, before any implementation commit). Scratch git repo under `mktemp -d`, pre-seeded with
`templates/mine.md` and `docs/claude-md/my-notes.md`, then `SUPERVISOR_REPO=file://<worktree> bash setup.sh </dev/null`:

```
== 2026-09-17T11:27:59Z BEFORE install (kit HEAD d1f91de)
docs/claude-md:
-rw-rw-r-- 1 hungnguyenhuu hungnguyenhuu   21 Sep 17 18:27 my-notes.md
templates:
-rw-rw-r-- 1 hungnguyenhuu hungnguyenhuu   16 Sep 17 18:27 mine.md
== running setup.sh </dev/null
exit=0
[info]  Wrote ./.claude/harness-lock.json (110 file hashes).
[info]  Setup complete. Harness copied into .../before.tIwuSI/proj
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
== 2026-09-17T11:27:59Z AFTER install
docs/claude-md:
code-naming-conventions.md  folder-structure.md  memory-write-protocol.md
phase0-project-initiation.md  pipeline-stages.md  untrusted-content-boundary.md
templates:
ADR_template.md ... TASK_GUIDE_template.md TASK_REVIEW_template.md thinking_report_template.html
ls: cannot access 'templates/mine.md': No such file or directory
ls: cannot access 'docs/claude-md/my-notes.md': No such file or directory
bak count: 0
```

Premise confirmed by running: both project directories are replaced wholesale by `rm -rf` at
`lib/harness-fetch.sh:152`, exit 0, no warning, no backup.

**AFTER**: [same probes — `.bak` present and named in output]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
