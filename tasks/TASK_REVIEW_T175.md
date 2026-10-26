# TASK_REVIEW — T175: Kit-arms experiment, part 1 — fixture, 6 graded tasks, runner, pre-registered rule (no paid runs)

> Sibling of `tasks/TASK_GUIDE_T175.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass (agent-filled; reviewer to confirm) | `experiments/kit-arms/tests/test_kit_arms.py` — 48 tests: SC1-3 oracle discrimination (untouched fixture fails code oracles 1,2,3,6; references pass all; task3 bad = fail; task5 bad = unsafe; task4 guess-a/guess-b classified), SC4 dry run 36 cells with a fail-loud PATH stub `claude`, SC5 cap stop, SC6 no-terminal exit 2, SC7 work dir inside main checkout refused, SC8 arm shapes, Q1/Q2 rule functions, real-agent path vs PATH stubs (result/void/timeout kills process group). Written RED first: commit `57c5e97` (`3 failed, 30 errors`). Output: `48 passed in 114.55s (0:01:54)` |
| Verification command run | ☑ pass (agent-filled at `ce3e86a`; reviewer to re-run) | Full guide command, exit 0, tail: `48 passed in 114.55s` · `Report: .../experiments/kit-arms/results/dry-run/report.md  (36 runs, spend $0.00, rule complete: True)` · `1447 passed, 25 subtests passed in 35.88s` · `validate.sh: PASS` · total 3:27.84 |
| Negative cases hold | ☑ pass (agent-filled) | Mutants, each run then reverted: `killpg`→`proc.kill()` → timeout test `1 failed` (after tightening it to <15 s; it first survived); cwd guard removed → SC7 `1 failed`; both cap checks removed → SC5 `1 failed`. The cwd-guard mutant created `kit-arms-work-should-not-exist/` in the main checkout (empty; removed with `rmdir`; main `git status --porcelain` identical to before) |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: CLI scripts, Markdown report only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure before the first implementation commit (worktree `/home/hungnguyenhuu/workspace/pets/wt-t175`):

```
2026-10-26T07:52:26Z
$ ls experiments
ls: cannot access 'experiments': No such file or directory
$ git log --oneline -1
ac257ad plan(T175,T176): kit-arms experiment — fixture + graders + pre-registered rule (T175), 36 paid runs under $60 (T176); D1 3 arms, D2 fixture, D3 cap, D4 split
```

**AFTER**: same command, after the last commit:

```
2026-10-26T08:16:13Z
$ ls experiments
kit-arms
$ git log --oneline -1
ce3e86a fix(T175): runner removes only its own work dir; a run timeout kills the agent's whole process group
```

and `python3 experiments/kit-arms/run_arms.py --dry-run --runs 2` → `Report: .../results/dry-run/report.md  (36 runs, spend $0.00, rule complete: True)`.

**DELTA**: The user can read the 6 task prompts, the hidden graders and a pre-registered keep/cut rule, and run a free dry run that builds all 3 arms and grades 36 cells, before any money is spent in T176.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
