# TASK_REVIEW — T124: Token meter — measure spend and agent focus from session transcripts

> Sibling of `tasks/TASK_GUIDE_T124.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass / ☐ fail | `tests/test_token_meter.py` (29 tests, SC1–SC10; SC11 is Stage 5) over `tests/fixtures/transcripts/**` (synthetic). Implementer run 2026-09-25T04:36:34Z @ `a224e1e`: `python3 -m pytest tests/test_token_meter.py -q` → `29 passed in 1.19s`. Mutation controls: see below. |
| Verification command run | ☑ pass / ☐ fail | Implementer run @ `a224e1e`: `pytest tests/test_token_meter.py -q` → `29 passed in 1.19s`; `pytest .claude/hooks/tests tests -q \| tail -1` → `884 passed in 14.73s`; `sh scripts/validate.sh` → `validate.sh: PASS`. The 4th command (real transcripts, AC11) is Stage 5 — pre-check numbers below, not a substitute. |
| Negative cases hold | ☑ pass / ☐ fail | No-usage dir → exit 2 naming `usage` (SC7); empty/missing dir → exit 2; malformed line skipped+counted (SC8); unparsed file listed by basename; symlinked dir outside root not followed; sentinel absent in 8 output modes (SC5); source has no write/mkdir (SC10); fixture tree unchanged after a run. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass / ☐ fail | Implementer run: 884 passed (855 before + 29 new), 0 failed; `validate.sh: PASS`. Reviewer to re-run. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☑ N/A | No UI component — stdout CLI script. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☑ N/A | No UI component — stdout CLI script. |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☑ N/A | No UI component — stdout CLI script. |

### Mutation controls M1–M6 (implementer run 2026-09-25T04:36:20Z @ `a224e1e`)

Each mutant applied to the committed file, target test run, file restored from `git show HEAD:`,
test re-run; `git status` clean afterwards. Runner: scratchpad `mutate.py` (not committed).

| # | Mutation | Mutated → | Reverted → |
|---|----------|-----------|------------|
| M1 | drop `message.id` de-dup (per-file + global) | `test_sc1_…` FAILED `assert 4 == 3` | 1 passed |
| M2 | price 1h cache writes at 1.25× | `test_sc1_…` FAILED `assert 15.9 == 19.65` | 1 passed |
| M3 | count reads after the first Edit as pre-edit | `test_sc2_…` FAILED `assert 1520 == 500` | 1 passed |
| M4 | print one tool-result excerpt in the session view | `test_sc5_…session_mode` FAILED — sentinel in stdout | 2 passed |
| M5 | return exit 0 with zeros when nothing parses | `test_sc7_…` FAILED `assert 0 == 2` | 1 passed |
| M6a | drop the recall window (check every later output) | `test_recall_window_is_three_outputs` FAILED `assert 1 == 0` | 2 passed |
| M6b | drop the recall check entirely | `test_sc4_…` FAILED `assert 0 == 1` | 2 passed |

M6 is read two ways, so both were run: SC4 as written (1 qualifying output, recall 1) cannot detect an
*unbounded* window, so `bash_late` (the only quote lands in the 4th output) was added for that reading.

### AC11 pre-check on real transcripts (implementer, informational — Stage 5 owns the verdict)

`python3 scripts/token_meter.py --projects-dir ~/.claude-personal/projects --bash-lines 200`, 2026-09-25:

| Metric | Finding doc | Meter | Tolerance |
|---|---|---|---|
| Spend | $389 | $388.84 (72 transcripts, 3,343 calls) | ±2% ✓ |
| Bash outputs > 200 lines | 45 | 45 | ±2 ✓ |
| Counterfactual share | 1.04% | 1.08% | 1.0% ±0.2 pt ✓ |
| Recall risk | 5 of 45 | 5 of 45 | — |
| Spawn median pre-edit reading | 16.8k | 16,836 (14 spawns) | ±10% ✓ |
| Spawn median prompt / prefix / carry | 4,171 / 15.6k / 17% | 4,171 / 15,612 / 17.7% | — |
| Spawn median calls before edit | "8 calls" | 7 | — (definition: calls *before* the edit-issuing call) |
| Spawn median context at first edit | 48k | 41.7k | — (not an AC11 item; flagged for the Supervisor) |

The Bash count reproduces only when lines are counted on `toolUseResult.stdout` (AC7's "stdout");
on the tool_result text it is 39. The meter counts stdout and falls back to the tool_result text.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by the T124 implementing agent in `wt-t124`, before any implementation commit;
HEAD = `0f275fa` on `feat/t124-token-meter`):

```
$ date -u; git rev-parse --short HEAD; python3 scripts/token_meter.py
2026-09-25T04:28:27Z
0f275fa
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t124/scripts/token_meter.py': [Errno 2] No such file or directory
exit=2
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
