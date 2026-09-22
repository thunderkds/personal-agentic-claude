# TASK_REVIEW — T114: One command — it detects the project, shows a menu, and asks before acting

> Sibling of `tasks/TASK_GUIDE_T114.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | cancel = zero changes, invalid input, no-TTY never reinstalls, M1/M2 |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☐ pass / ☐ fail | D1 site #update-flow, D2–D3 RUNBOOK.md, D4 PROJECT_SPEC.md |
| HITL: user reviewed menu transcripts (SC1, SC3, SC6) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | terminal text menu, no visual design surface; wording is reviewed through the HITL row above |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no design system applies to plain terminal output |
| **UI: Responsiveness at target viewports** | ☐ N/A | terminal output; no viewports |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9` — to be re-captured by the implementer on the
integration branch tip after T110–T113 merge, before this task's first commit):

```
===== update.sh as a user would run it (from their project) =====
ls: cannot access 'update.sh': No such file or directory
sh: 0: cannot open ./update.sh: No such file

===== re-running setup.sh on an existing, customized project =====
exit=0
local edit SILENTLY OVERWRITTEN
```

**BEFORE (implementer re-capture, 2026-09-22, branch tip `3612edc` = `main` after T110–T113 + T114 guide docs, before any T114 code commit):**

```
BEFORE captured 2026-09-22T06:27:32Z on 3612edc (feat/t114-one-command-menu tip = main + T114 guide docs)
$ SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null   # first install
exit=0
===== update.sh as a user would run it (from their project) =====
$ ls update.sh; sh ./update.sh
ls: cannot access 'update.sh': No such file or directory
sh: 0: cannot open ./update.sh: No such file
exit=2
===== re-running setup.sh on an installed, edited project =====
$ echo "# local edit" >> skills/tdd/SKILL.md; SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null
[info]  Setup complete. Harness copied into /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-wt-t114/b9cd955c-e534-4d9e-896d-f060fee5cbda/scratchpad/before.AxWu
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
exit=0
local edit gone from skills/tdd/SKILL.md
SKILL.md
$ git status --porcelain
?? skills.bak/

===== second re-run, edit again, full output (same project, 2026-09-22) =====
$ echo '# edit2' >> skills/tdd/SKILL.md; SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null
[info]  Non-interactive mode detected. Defaulting to greenfield (CLAUDE.md). Re-run interactively to choose brownfield.
[info]  Non-interactive mode: no packs installed. Re-run with --pack=<name> to add packs.
[info]  Fetching (shallow clone): file:///home/hungnguyenhuu/workspace/pets/wt-t114
[warn]  Backed up your existing './skills' to './skills.bak.1' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  Setup complete. ...
exit=0
?? skills.bak.1/
```

> Correction to the guide's BEFORE wording, measured: since T112 the edit is no longer *lost* — but it
> is still overwritten in place **without asking**, with no plan and no choice of action, and the
> backup is the whole `skills/` directory (every skill), not the one edited file. `update.sh` is still
> not runnable from a project (exit 2, "cannot open").

**AFTER**: [menu transcripts]

**DELTA**: [one sentence]

**WITNESS**: [who ran it and when]
