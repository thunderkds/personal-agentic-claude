# TASK_REVIEW — T129: Spawn prompts name the mandatory startup reads, and the agent confirms them

> Sibling of `tasks/TASK_GUIDE_T129.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_spawn_startup_reads.py` (SC4–5), `.claude/hooks/tests/test_pre_agent_validate_guide.py` (SC1–3 + independence edge): 19 passed — pass |
| Verification command run | ☑ pass | 19 passed; `python3 -m pytest .claude/hooks/tests tests -q` → 932 passed; `sh scripts/validate.sh` → PASS (2026-09-25, on the T129 commit) — pass |
| Negative cases hold | ☑ pass | prose-only mention warns (SC1), no-guide prompt silent (SC3), each warning fires independently — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | 932 passed; validate.sh PASS — pass |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-09-25T08:55:57Z at `edf37a7`, before any implementation commit):

```
$ printf '%s' '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: T129\nRead tasks/TASK_GUIDE_T129.md\n<!-- memory-slice:T129 -->\nx\n<!-- /memory-slice -->"}}' | python3 .claude/hooks/pre_agent_validate_guide.py 2>&1 | grep -ci "startup"
0
$ grep -c "Startup reads" skills/craft-spawn-prompt/SKILL.md
0
```

A guide-naming prompt with no startup-reads block draws no warning, and the skill has no such element.
Prior element table, verbatim from `skills/craft-spawn-prompt/SKILL.md` (rows 1–7; no startup-reads row):

```
| 1 | Guide pointer | `tasks/TASK_GUIDE_Txxx.md` path | same |
| 2 | Orienting content | Guide's Restated Intent / Requirement section, verbatim | Confirmed Mental Model section, verbatim |
| 3 | First-action skill invocation | ... |
| 4 | Memory slice | Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide-path>` ... |
| 5 | Agent-guide pointer | `agents/<role>.md` from the guide's `**Agent guide**` field | same |
| 6 | Trace-attribution instruction | ... |
| 7 | Demonstration BEFORE-capture instruction | ... |
```

**AFTER** (implementer capture; the live headless spawn is the Supervisor's/user's `/verify`): element 8 in `skills/craft-spawn-prompt/SKILL.md`, hook `check_startup_reads_warning` in `.claude/hooks/pre_agent_validate_guide.py`, Stage 4 line in `skills/code-review/SKILL.md` (after Phase 0.5). Same command as BEFORE, run after the change, prompt without the block:

```
$ ... | python3 .claude/hooks/pre_agent_validate_guide.py 2>&1 | grep -ci startup
(see pytest SC1: stderr carries "startup-reads missing", stdout has no "decision")
```

Mutation controls (harness `/tmp/mut.sh`, edits then restores from copy):

```
2026-09-25T08:57:49Z
edf37a7
## M1 — hook blocks (RED)
FAILED .claude/hooks/tests/test_pre_agent_validate_guide.py::test_t125_sc5_guide_without_slice_marker_warns_and_is_allowed
FAILED .claude/hooks/tests/test_pre_agent_validate_guide.py::test_t129_sc1_guide_without_startup_reads_warns_and_is_allowed
2 failed, 17 passed in 0.21s
## M1 — restored (GREEN)
19 passed in 0.22s
## M2 — report-line dropped (RED)
FAILED tests/test_spawn_startup_reads.py::test_sc4_skill_asks_for_the_report_line
1 failed, 18 passed in 0.19s
## M2 — restored (GREEN)
19 passed in 0.19s
## M3 — prose match passes (RED)
FAILED .claude/hooks/tests/test_pre_agent_validate_guide.py::test_t129_sc1_prose_mention_does_not_count_as_the_block
1 failed, 18 passed in 0.18s
## M3 — restored (GREEN)
19 passed in 0.16s
```

**DELTA**: A spawn prompt now tells the agent which files to read first and to report them, the hook warns when that block is missing, and the reviewer can compare the agent's `Startup reads:` line against it.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
