# TASK_REVIEW — T128: The token meter sees an agent's first edit even when it edits through Bash

> Sibling of `tasks/TASK_GUIDE_T128.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_token_meter.py` (T128 block: SC1–SC6, 37 new cases). `python3 -m pytest tests/test_token_meter.py -q` → `74 passed in 3.39s` (2026-09-25) |
| Verification command run | pass | `python3 -m pytest .claude/hooks/tests tests -q \| tail -1` → `960 passed in 18.66s`; `python3 scripts/token_meter.py --task T126` → see AFTER |
| Negative cases hold | pass | state file, `/dev/null`, `2>&1`, `/tmp`, quoted `>`, read-only `python3 -c` are not edits (SC3/SC4, 14 params); sentinel in a Bash write never printed (SC6) |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 (2026-09-25): `git diff tokenization-refactor...feat/t128-meter-bash-edits` — 3 files; `bash_writes_file` and helpers read in full. |
| Full smoke suite still green (no regression) | pass | 960 passed (above) |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-09-25T08:55:57Z at `edf37a7`, before any implementation commit):

```
$ python3 scripts/token_meter.py --task T126
  task    calls  prompt_ch prefix_tok pre_edit_tok calls_pre ctx_at_edit   cost_$ carry_%  transcript
  T126       12      4,351     30,002       14,423        12           -     1.09    18.6  4b9912b3-d928-46f5-8277-5ddacaf63f23.jsonl  (no edit: whole session is pre-edit)
```

**AFTER** (2026-09-25T08:57:57Z, working tree on top of `edf37a7`):

```
$ python3 scripts/token_meter.py --task T126
  T126       12      4,351     30,002       13,333         4      51,515     1.09    17.4  4b9912b3-d928-46f5-8277-5ddacaf63f23.jsonl  (first edit via bash)
$ ... --json  -> {'calls_before_edit': 4, 'pre_edit_tokens': 13333, 'edit_via': 'bash', 'context_at_edit': 51515}
```

AC5 note: the meter's convention is the 0-based index of the editing call, so the guide's "call 6" is reported
as `4`, not `5`: transcript call 4 (0-based) is the `python3 - <<EOF ... open(p,'w')` that writes
`TASK_REVIEW_T126.md`, followed by `git commit`. Pre-edit is 13,333 tokens (13.3k, within 5 pct). Call 0 wrote
`active_task` (excluded); calls 1-3 only read.

#### Mutation controls (captured 2026-09-25T08:58:26Z, edits to `scripts/token_meter.py`, run `tests/test_token_meter.py`, restore)

```
## M1 drop state-path exclusion — RED (mutated)
FAILED tests/test_token_meter.py::test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits[cmd 2>/dev/null]
FAILED tests/test_token_meter.py::test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits[mkdir -p /abs/repo/.claude/hooks/.state]
FAILED tests/test_token_meter.py::test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits[ls | tee /dev/null]
7 failed, 67 passed in 3.29s
## M1 drop state-path exclusion — GREEN (reverted)
74 passed in 3.17s
## M2 any > is a write (ignore quotes) — RED (mutated)
FAILED tests/test_token_meter.py::test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits[grep '>' f]
FAILED tests/test_token_meter.py::test_t128_sc3_sc4_state_and_read_only_look_alikes_are_not_edits[echo "a > b"]
2 failed, 72 passed in 3.46s
## M2 any > is a write (ignore quotes) — GREEN (reverted)
74 passed in 3.26s
## M3 Bash detection off — RED (mutated)
FAILED tests/test_token_meter.py::test_t128_sc2_each_write_form_is_detected[python3
FAILED tests/test_token_meter.py::test_t128_sc2_each_write_form_is_detected[cd d && git status; echo x > f]
FAILED tests/test_token_meter.py::test_t128_sc5_bash_write_first_wins_over_a_later_edit_tool
21 failed, 53 passed in 3.53s
## M3 Bash detection off — GREEN (reverted)
74 passed in 3.39s
```

**DELTA**: The meter reports the real pre-edit reading (13.3k, not 14.4k) for an agent that edits through Bash, and says whether the edit was found via a tool or Bash.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Supervisor Stage 4 (2026-09-25)

**`code-review`: 0 P0 / 1 P1 (fixed) / 1 P2 / 1 P3.** `security-review`: not required (Risk Low) — commands are matched in memory only; T124 SC5 sentinel coverage extended to a Bash write command.

| Sev | Finding | Conf. | Outcome |
|---|---|---|---|
| P1 | Source spelled `"mk" "dir"` and `\.write" r"_text\(` to slip past `test_sc10_source_never_writes`, which grepped bare words — evasion of a guard, not satisfaction of it | 100 | **Fixed**: SC10 now matches write *calls* (`os.mkdir/makedirs/remove/unlink/rename/replace(`, `.write_text(`/`.write_bytes(`, `.write(`, `shutil`); plain strings restored. Mutants `os.makedirs("x")`, `Path("x").write_text("y")`, `open("x","w")`, `import shutil` each → `1 failed`; suite `960 passed`, `validate.sh: PASS` |
| P2 | `INTERPRETER_WRITE` is searched over the whole command, so an `open(…,'w')` inside *another* heredoc in the same call also counts. Such calls nearly always write anyway | 75 | Accepted |
| P3 | AC5 index: the meter reports the first edit at 0-based API-call index 4, the guide said "call 6 (index 5)" — the guide counted tool calls including the `active_task` write; tokens match (13,333) | 100 | Accepted; the agent documented the convention |

Real T126 transcript after the fix: `pre_edit_tokens 13,333, calls_before_edit 4, edit_via bash` (was "no edit", 14,423). The agent's `Startup reads:` line names all three Permanent-Rule reads ✓.

**Remaining:** Stage 5 user-run `/verify`.
