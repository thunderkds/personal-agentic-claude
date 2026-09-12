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

**Still to capture by the implementer, before the first commit**: the directory case (`templates/mine.md`
pre-existing) — asserted from `lib/harness-fetch.sh:152` by reading only, not yet run.

**AFTER**: [same probes — `.bak` present and named in output]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
