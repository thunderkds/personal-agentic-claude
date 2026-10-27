# TASK_REVIEW — T178: Two tracks — small tasks run on the minimal track without process stops and end with a Decision record; big or risky tasks run on the extended track

> Sibling of `tasks/TASK_GUIDE_T178.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_tracks.py` (new, 39 tests: AC 1 ×10, AC 2 ×6, AC 3 ×3, AC 4 ×2, AC 5 ×5, AC 6 ×13). RED at `66796a1`: `27 failed, 12 passed` (the 12 pin today's hook behaviour for a guideless task and the unchanged Gates 2–6). GREEN after `fbe55ab`: `tests/test_tracks.py` 39 passed (inside the `54 passed` run below). Amended, not new: `tests/test_agents_md_primary.py` (fidelity check allows exactly the T178 spans + `## Tracks`), `.claude/hooks/tests/test_agent_guide_dedup.py` (byte baseline repointed `8080fdb` → `fbe55ab`). AC 7 / AC 8: AC 8 (paid live run) not run — Supervisor, after the user's go. |
| Verification command run | ☑ pass | 2026-10-27T02:52:05Z, `python3 -m pytest -q tests/test_tracks.py tests/test_agents_md_primary.py tests/test_claude_md_slim.py && python3 -m pytest -q tests` → `54 passed in 17.66s` then `615 passed in 145.42s (0:02:25)`. |
| Negative cases hold | ☑ pass | `pytest -v tests/test_tracks.py -k ac6` → `13 passed`. Merge gate still blocks a guideless minimal task with a full Decision record AND a real `pytest` record in its trace (`…awaiting_the_user[merge]`, `[push]` PASSED; reason `T901 (no evidence row)`); a record line shaped like a filled `verify` row is not read; the `Track: minimal` marker changes nothing (`…does_not_exempt_a_row…` PASSED: marked == unmarked block); In Progress blocks (`…in_progress` PASSED). Controls: an unattributed call is not counted (`…ignores_an_unattributed_call`), a guide write still registers (`…still_registers_a_guide`), the stop reminder output is unchanged with no minimal row (`…unchanged_with_no_minimal_row`). |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 (Supervisor, 2026-10-27): `git diff 8386b17..HEAD` (11 files) — `AGENTS.md` (Tracks, Gate 1, Permanent Rule), `docs/claude-md/tracks.md`, `docs/claude-md/pipeline-stages.md`, `templates/MINIMAL_LOG_template.md`, `PROJECT_SPEC.md` glossary, `.claude/hooks/stop_review_reminder.py`, tests. Callers read: `pre_bash_block_unsafe_merge.py` (unchanged; Done rows not checked), AGENTS.md Gates 2–6 (unchanged by design, AC 4). `lane_check.py`: `lane: C3, 10 files, 698 lines, FITS; unpredicted: tasks/TASK_GUIDE_T178.md, tests/test_agents_md_primary.py`. Supervisor re-run: `54 passed`; `1486 passed, 25 subtests passed`; `validate.sh: PASS`. Not reviewed: files outside the diff. |
| Full smoke suite still green (no regression) | ☑ pass | Baseline before any change: `1447 passed, 25 subtests passed` (`tests` + `.claude/hooks/tests`). After: `python3 -m pytest -q tests` → `615 passed`; `python3 -m pytest -q .claude/hooks/tests` → `871 passed, 25 subtests passed in 179.97s` (1486 = 1447 + 39 new); `sh scripts/validate.sh` → `validate.sh: PASS`. First after-run caught 2 pins on AGENTS.md (`test_vital_slice.py::test_ac11_line_cap[AGENTS.md]` 199 > 196; `test_agent_guide_dedup.py` byte baseline) — fixed by removing 3 post-heading blank lines and repointing the baseline. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI component (doctrine docs, a template, one Stop-hook message) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI component (doctrine docs, a template, one Stop-hook message) |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI component (doctrine docs, a template, one Stop-hook message) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on `feat/t178-tracks` at `8386b17`, before the first implementation commit.

(a) Executable — the real hooks, run by `scratchpad/demo_t178.sh` against a temp project whose board has one
minimal-track row (no guide, only a Decision record) in Ready for Review:

```
captured 2026-10-27T02:35:23Z
$ ls /tmp/tmp.MevxuIg2lo/proj/tasks/ ; ls /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md
MINIMAL_LOG.md
ls: cannot access '/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md': No such file or directory
ls: cannot access '/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md': No such file or directory
$ python3 .claude/hooks/stop_review_reminder.py   (stderr)

============================================================
⚠️  SUPERVISOR: Tasks awaiting Stage 4 Review:
   - [ ] **T901** — Fix the comma bug in amounts | Supervisor | C0 | Risk: Low | P2 | Track: minimal | Record: `tasks/MINIMAL_LOG.md`

Run: Skill({ skill: 'code-review' })
For Medium/High risk: Skill({ skill: 'security-review' })
============================================================

$ echo '{"tool_name":"Bash","tool_input":{"command":"git merge feat/t901"}}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py
block
[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.
```

The stop hook asks for `code-review` on a task that has no Stage 4 (wrong for the minimal track); the merge gate
blocks (right, and must stay).

(b) Non-executable — verbatim prior doctrine, `AGENTS.md` at `8386b17`:

```
## 5-Stage Agentic Pipeline
See [`docs/claude-md/pipeline-stages.md`](docs/claude-md/pipeline-stages.md) for full Stage 0.5–5 detail. Strictly follow this order. Never skip or reorder stages.
```
```
- Stage 4 (code-review) is mandatory for every task. Stage 4 security-review is mandatory for Medium/High risk tasks.
```
```
1. **No TASK_GUIDE = no work.** If the user requests any implementation and no `tasks/TASK_GUIDE_Txxx.md` exists for it, the Supervisor must create one through Stage 2 before any code is written — by the Supervisor *or* any agent. The Supervisor must never write implementation code directly.
```

`docs/claude-md/pipeline-stages.md` at `8386b17`, the head before Stage 0.5:

```
# 5-Stage Agentic Pipeline

> Extracted from `AGENTS.md` — full detail for Stage 0.5 through Stage 5. See `AGENTS.md` for the pointer back to this file and the Mandatory Session Startup / Hard-Stop Gates, which remain inline there.

Strictly follow this order. Never skip or reorder stages.
```

`PROJECT_SPEC.md` glossary: no `Minimal track`, `Extended track` or `Decision record` row (only `Decision Log`,
line 74). `templates/MINIMAL_LOG_template.md` and `docs/claude-md/tracks.md`: absent (see (a)).

**AFTER**: same script, after `fbe55ab`:

```
captured 2026-10-27T02:58:15Z
$ ls /tmp/tmp.e62ZRGfpQp/proj/tasks/ ; ls /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md
MINIMAL_LOG.md
/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md
/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md
$ python3 .claude/hooks/stop_review_reminder.py   (stderr)

============================================================
⚠️  SUPERVISOR: Minimal-track tasks awaiting the user's merge decision
   (Decision record in tasks/MINIMAL_LOG.md; merge only when the user asks):
   - [ ] **T901** — Fix the comma bug in amounts | Supervisor | C0 | Risk: Low | P2 | Track: minimal | Record: `tasks/MINIMAL_LOG.md`
============================================================

$ echo '{"tool_name":"Bash","tool_input":{"command":"git merge feat/t901"}}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py
block
[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.
```

New doctrine, `AGENTS.md` (verbatim):

```
## Tracks
Before any implementation work, sort the request by [`docs/claude-md/tracks.md`](docs/claude-md/tracks.md) and say the track in one line: `Track: minimal — <reasons>` or `Track: extended — <reasons>`. The 5-stage pipeline below is the **extended track**, unchanged. It applies if any of: C2 or above; Risk Medium or High; a Gate 2 word or *migrate*; more than one session or agent; a UI component. Otherwise the **minimal track**: the Supervisor writes the code itself on a new branch (test first, change, real run) with no process stop, and ends with a Decision record in `tasks/MINIMAL_LOG.md`. The user can switch with `full` or `minimal`; the Supervisor moves a task only up.
```
```
- Stage 4 (code-review) is mandatory for every extended-track task. Stage 4 security-review is mandatory for Medium/High risk tasks.
```
```
1. **No TASK_GUIDE = no work.** This gate applies to the extended track. If the user requests any implementation and no `tasks/TASK_GUIDE_Txxx.md` exists for it, the Supervisor must create one through Stage 2 before any code is written — by the Supervisor *or* any agent. The Supervisor must never write implementation code directly. On the minimal track the Supervisor writes the code itself, with no guide, and ends with a Decision record (`docs/claude-md/tracks.md`).
```

`docs/claude-md/pipeline-stages.md` head (new paragraph above the unchanged "Strictly follow this order…"):

```
These 5 stages are the **extended track** (`docs/claude-md/tracks.md`). The track rule sends big, risky or
multi-session work here, and small low-risk work to the minimal track. Hard-Stop Gate 1 applies to the
extended track only. Gates 2–6 still apply to it unchanged. Gate 5 (a new test with its pasted output) also
applies to the minimal track, through the Decision record's `Checked:` field.
```

New files: `docs/claude-md/tracks.md`, `templates/MINIMAL_LOG_template.md`. Glossary: `Minimal track`, `Extended track`,
`Decision record` rows after `Lane` in `PROJECT_SPEC.md`.

**DELTA**: The Supervisor can now run a small, low-risk request straight through itself (one-line track announcement, test first, change, real run, Decision record) instead of stopping at Gate 1 for a task guide, while the merge of that work is still blocked until the user asks.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
