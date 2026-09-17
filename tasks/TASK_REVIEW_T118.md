# TASK_REVIEW — T118: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T118.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | No new test file (correct per guide's Hard-Stop Gate 5 note): `tests/test_t098_harness_presence.sh` (7→0 fail) and `tests/test_harness_projection.sh` (3→0 fail) went red→green, plus the AC4 mutation (below) proves the fix is load-bearing in both directions. |
| Verification command run | pass | Full 7-command sweep run 2026-09-17T08:46:38Z — all exit 0: t098=0 projection=0 smoke=0 settings_merge=0 setup=0 update=0 ci_wires=0. |
| Negative cases hold | pass | AC4 mutation: deleting the provisioned `lib/merge-settings.py` from each fixture builder (in-place edit, byte-identical restore verified via `diff`) reproduces the exact original failure by name (`the fetched Easy Kit has no lib/merge-settings.py`) — t098 back to 8 passed/7 failed, projection back to 35 passed/3 failed. AC4 grep: `settings_merge_refused` count unchanged at 4/4 in `setup.sh`/`update.sh` — hard-fail contract untouched. |
| verify | ☐ N/A | user-invoked only per `memory/MEMORY.md` (`project_verify_skill_is_user_only`) — Supervisor/user to run `/verify`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Touched only the two fixture builders' provisioning block (mkdir + cp, ~2 lines each) in `tests/test_t098_harness_presence.sh` and `tests/test_harness_projection.sh`. `setup.sh`, `update.sh`, `lib/merge-settings.py`, `MANIFEST`, `ci.yml` untouched per guide's Files Must NOT Touch. |
| Full smoke suite still green (no regression) | pass | AC5 sweep (verification command above) — all 7 suites green, including `test_install_update_smoke.sh` which clones the real repo. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Pure-infrastructure task, no UI component. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Pure-infrastructure task, no UI component. |
| **UI: Responsiveness at target viewports** | ☐ N/A | Pure-infrastructure task, no UI component. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-09-17T08:45:20Z–08:45:24Z on branch `fix/t118-fixture-merge-settings`
(pre-implementation), worktree `/home/hungnguyenhuu/workspace/pets/wt-t118`:

```
$ bash tests/test_t098_harness_presence.sh
[... every AC1/AC2/AC3/AC4/AC9/AC10 failure: ...]
[error] Could not merge Easy Kit hooks into ./.claude/settings.json: the fetched Easy Kit has no lib/merge-settings.py
[error] Update finished, but Easy Kit hooks were NOT merged (see the message above).
8 passed, 7 failed
EXIT:1

$ bash tests/test_harness_projection.sh
[... AC7/AC9(x2) failures, same "no lib/merge-settings.py" root cause ...]
test_harness_projection.sh: 35 passed, 3 failed
EXIT:1
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**AFTER**: Captured 2026-09-17T08:45:53Z–08:45:58Z, same branch/worktree, post-fix:

```
$ bash tests/test_t098_harness_presence.sh
[... all PASS ...]
20 passed, 0 failed
EXIT:0

$ bash tests/test_harness_projection.sh
[... all PASS ...]
test_harness_projection.sh: 41 passed, 0 failed
EXIT:0
```

**DELTA**: `main`'s CI is green again — both fixture-repo-dependent suites now build a believable Easy
Kit (carrying `lib/merge-settings.py`) and exercise the real hook-merge path instead of aborting at
`setup.sh:421`/`update.sh:109` before any of their actual assertions run.

**WITNESS**: Common-Infrastructure-Agent (T118), ran all commands directly in
`/home/hungnguyenhuu/workspace/pets/wt-t118` on `fix/t118-fixture-merge-settings`, 2026-09-17
08:45–08:46 UTC.
