# TASK_REVIEW — T110: Update delivers `CLAUDE.md`, through the same edit-safe rule as every other file

> Sibling of `tasks/TASK_GUIDE_T110.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | edited-file conflict, unknown heading, M1 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1 RUNBOOK.md, D2 site #update-flow |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | shell installer; no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Upstream clone
changed `CLAUDE.md`, `.claude/settings.json` and `skills/tdd/SKILL.md`; installed project then ran
`update.sh </dev/null`:

```
exit=0
skill: UPDATED
CLAUDE.md: NOT updated
settings.json: NOT updated
```

**BEFORE (Common-Infrastructure-Agent re-probe, 2026-09-12T15:13:22Z, `main` `992e293`, before any
implementation commit)**. Two independent scratch-repo runs, each against its own local
`SUPERVISOR_REPO=file://...` clone of this repo, upstream mutated (skill + both `CLAUDE.md` +
`CLAUDE_LEGACY.md`) and committed, then `update.sh </dev/null`:

Greenfield (new-project, plain pipe, no pty needed — mode defaults to `1`):
```
$ SUPERVISOR_REPO="file://.../upstream" bash setup.sh </dev/null   # install, unedited
[info] CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
$ # upstream: append MARKER-GREEN-BEFORE to CLAUDE.md, MARKER-LEGACY-BEFORE to CLAUDE_LEGACY.md,
$ #           append to skills/tdd/SKILL.md; git commit
$ SUPERVISOR_REPO="file://.../upstream" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
exit=0
$ grep -c MARKER-GREEN-BEFORE CLAUDE.md            → 0   (CLAUDE.md: NOT updated)
$ grep -c '# marker' skills/tdd/SKILL.md           → 1   (skill: UPDATED)
```

Brownfield (existing/legacy project, real prompt driven through a pty, `script -qec` with answers
`2` then Enter — the mode menu, then the packs menu):
```
$ printf '2\n\n' | script -qec "SUPERVISOR_REPO=file://.../upstream2 bash setup.sh" typescript
[info] CLAUDE source: CLAUDE_LEGACY.md | lock: .claude/harness-lock.json
$ head -1 CLAUDE.md
# CLAUDE LEGACY SUPERVISOR - Operating Protocol
$ # upstream2 (fresh clone, mutated AFTER this install so it measures a real update):
$ #           append MARKER-GREEN-B2 to CLAUDE.md, MARKER-LEGACY-B2 to CLAUDE_LEGACY.md,
$ #           append to skills/tdd/SKILL.md; git commit
$ SUPERVISOR_REPO="file://.../upstream2" bash update.sh </dev/null
[info] Update complete. Re-recorded ./.claude/harness-lock.json
exit=0
$ grep -c MARKER-LEGACY-B2 CLAUDE.md               → 0   (CLAUDE.md: NOT updated — legacy marker)
$ grep -c '# marker' skills/tdd/SKILL.md           → 1   (skill: UPDATED)
```

Both runs confirm the guide's restated defect: `update.sh` never touches `CLAUDE.md` for either
install source, while MANIFEST-listed files (the skill) update normally. Matches the Supervisor's
2026-09-12 `8115bc9` probe recorded above — reproduced independently on `992e293` immediately before
the first implementation commit.

**AFTER**: [same probe post-change — `CLAUDE.md: UPDATED`, plus the brownfield case]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
