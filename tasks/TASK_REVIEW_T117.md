# TASK_REVIEW — T117: `select-packs` — the Supervisor recommends packs from the business domain and activates the ones the client approves

> Sibling of `tasks/TASK_GUIDE_T117.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | collision refusal, no lock entries, hardcoded-name + `--pack` mutation controls |
| verify | ☐ pass / ☐ fail / ☐ N/A | agent run on sample PRD vs control tree |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| HITL: user reviewed the recommendation run | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | skill + doc text; no UI surface |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** — non-executable change (a new skill + doctrine text), so the verbatim prior content:

`docs/claude-md/folder-structure.md:41` (2026-09-12):
```
   *(Each pack contains agents/ + skills/ + PACK.md. Installed via `setup.sh --pack=<name>`.)*
```

`CLAUDE.md:66-67` (2026-09-12):
```
> `general-agent-template` is shared base rules, not a directly spawned sub-agent. Pack skills
> symlink into `skills/` alongside these when a pack is installed.
```

No `skills/select-packs/` exists.

**AFTER**: [new wording + the SC5/SC6 run]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
