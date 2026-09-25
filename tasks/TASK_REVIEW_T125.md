# TASK_REVIEW — T125: Focused handoff — a spawned agent gets the memory lines its task touches, not the whole index

> Sibling of `tasks/TASK_GUIDE_T125.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | Implementer-filled, reviewer to re-run: `tests/test_memory_slice.py` (SC1–4, SC6, SC7, AC4, 6 edge cases), `.claude/hooks/tests/test_pre_agent_validate_guide.py` `test_t125_sc5_*` (SC5, 3 tests). Fixtures `tests/fixtures/memory_slice/{basic,nomatch}/`. `44 passed` on the three guide-named files at `e481526` — see Implementer notes below |
| Verification command run | ☐ pass / ☐ fail | Implementer run pasted under Implementer notes → AFTER (4th command uses the relocated script path) |
| Negative cases hold | ☐ pass / ☐ fail | M1–M5 (M3 split into M3a script / M3b hook) each RED mutated, GREEN reverted — Implementer notes → Mutation controls |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | Implementer: 855 passed at `598cc02` → 879 passed at `e481526` (+24 new, 0 failed); `validate.sh: PASS` |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☑ N/A — no UI component | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☑ N/A — no UI component | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☑ N/A — no UI component | [viewports tested, any overflow findings] |

### Implementer notes (T125 agent — data for the reviewer, not a verdict)

**Deviation from the guide, user-decided at Stage 3:** the script lives at
`skills/craft-spawn-prompt/scripts/memory_slice.py`, not `scripts/memory_slice.py`. `scripts/` is not
in MANIFEST; `skills` is. A downstream install would otherwise receive element 4 and the hook warning
without the script, and warn on every spawn. MANIFEST untouched. The guide's 4th verification command
is therefore `python3 skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_T125.md`.

**Matching design choices (not dictated by the ACs):** keys come from the *first column* of the two
Files tables only (the Change/Reason column is prose). A key matches a whole path token — not preceded
by a path character — so the basename `validate.sh` matches a bare mention but not `lib/validate.sh`.
That is what makes M1 bite: without the full-path key, `scripts/validate.sh` lines are lost. Generic
`SKILL.md` becomes its directory name (`craft-spawn-prompt`). Both caps apply to the *whole output*
(markers + header + headings); admission is by rank and stops at the first line that does not fit.

**AC7 — T065 assertions changed (one), with reason:** `test_memory_channel_and_budget.py::
test_ac5_and_ac6_the_contract_now_states_the_path_channel` pinned `**the agent must read it itself**`
in `pipeline-stages.md`, the unconditional rule AC6 replaces. It now asserts `nothing loads it for the
agent` (the T063 inversion it guarded) plus `**memory slice**` and `in full only if`. All other T065
assertions pass unchanged. That includes `The **path** \`memory/MEMORY.md\``, `Do **not** paste its
contents`, `read \`memory/MEMORY.md\` yourself` and `path to read` in the setup.sh stub (the stub
carried the old rule, so it was updated).

**AC8 — size budgets:** `test_agent_guide_dedup.py` is green with **no role floor repointed**. The
template sentence is net −12 chars (c-infra sat exactly at its 10,944 floor; backend's pair-drift had
3 chars of headroom), so the rule was worded to fit. `craft-spawn-prompt/SKILL.md` is 79 lines, under
T092's 80-line cap. The **CLAUDE.md byte pin** (`T070_BASELINE_REF`) was repointed `b1da25a → 2e5331e`
with the reason in a comment (`e481526`). CLAUDE.md diff: that one line, still 200 lines.

**Omission risk, observed on the first real run:** the T125 slice (AFTER below) does not include
`T065 merged: honest memory channel` or the `test_memory_channel_and_budget.py` history, the most
relevant memory for this task. No key names them. The escape-hatch line and the evaluation window's
revert trigger are the mitigation. Noise also shows: the `memory/*` and `tasks/TASK_GUIDE_T0*`
Must-NOT-Touch globs and `CLAUDE.md` pull in 18 lines, all within the caps.

**Not done here:** AC9 live-spawn measurement (Supervisor, Stage 5, after T124 merges),
`code-review`/`security-review` (a sub-agent has no `Skill` tool), `/verify` (user-run).
Drift outside AC6 scope, left untouched: `agents/common-infrastructure.md` / `backend.md` /
`frontend.md` / `qa.md` startup step 2 still say "Read `memory/MEMORY.md` yourself — the spawn prompt
gives you its path" (Must-NOT-Touch). `memory/MEMORY.md` header line 5 still states the path-only
channel (Supervisor-only). `CLAUDE_LEGACY.md` is not in the AC6 set.

#### Mutation controls (captured 2026-09-25T07:27:32Z at `e481526`; harness `mutate.py` edits, runs the three test files, restores from memory)

```
## M1 basenames only (drop full-path keys) — RED (mutated)
            assert kept and dropped, "control failed: the cap must have bitten"
            assert kept and dropped, "control failed: the cap must have bitten"
    FAILED tests/test_memory_slice.py::test_sc1_exactly_the_matching_lines_under_headings_inside_markers
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[line-cap]
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[char-cap]
    FAILED tests/test_memory_slice.py::test_edge_skill_md_needs_its_directory
    FAILED tests/test_memory_slice.py::test_edge_bugfix_flavoured_guide_same_tables_same_behaviour
    FAILED tests/test_memory_slice.py::test_edge_session_handoff_section_is_matched_like_any_other
    6 failed, 25 passed in 0.37s
## M1 basenames only (drop full-path keys) — GREEN (reverted)
    31 passed in 0.36s

## M2 remove the cap — RED (mutated)
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[line-cap]
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[char-cap]
    2 failed, 29 passed in 0.48s
## M2 remove the cap — GREEN (reverted)
    31 passed in 0.57s

## M3a drop the marker (script) — RED (mutated)
    FAILED tests/test_memory_slice.py::test_sc1_exactly_the_matching_lines_under_headings_inside_markers
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[line-cap]
    FAILED tests/test_memory_slice.py::test_sc2_cap_keeps_highest_hit_lines_and_counts_the_dropped[char-cap]
    FAILED tests/test_memory_slice.py::test_sc3_no_tables_no_matches_prints_markers_and_says_so
    FAILED tests/test_memory_slice.py::test_sc4_real_t124_guide_against_real_memory_runs_within_caps
    FAILED tests/test_memory_slice.py::test_edge_missing_memory_md_prints_markers_and_exits_zero
    6 failed, 25 passed in 0.66s
## M3a drop the marker (script) — GREEN (reverted)
    31 passed in 0.76s

## M3b drop the marker (hook check) — RED (mutated)
    FAILED .claude/hooks/tests/test_pre_agent_validate_guide.py::test_t125_sc5_guide_with_slice_marker_is_silent_about_it
    1 failed, 30 passed in 0.74s
## M3b drop the marker (hook check) — GREEN (reverted)
    31 passed in 0.56s

## M4 hook blocks instead of warns — RED (mutated)
    FAILED .claude/hooks/tests/test_pre_agent_validate_guide.py::test_t125_sc5_guide_without_slice_marker_warns_and_is_allowed
    1 failed, 30 passed in 0.55s
## M4 hook blocks instead of warns — GREEN (reverted)
    31 passed in 0.53s

## M5 template restores unconditional full read — RED (mutated)
    FAILED tests/test_memory_slice.py::test_sc6_doc_states_slice_in_prompt_and_full_file_on_need[templates/TASK_GUIDE_template.md]
    FAILED tests/test_memory_slice.py::test_sc6_the_old_unconditional_rules_are_gone
    2 failed, 29 passed in 0.53s
## M5 template restores unconditional full read — GREEN (reverted)
    31 passed in 0.45s
```

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-09-25T05:51:32Z at `598cc02`, before any T125 implementation commit):

1. `skills/craft-spawn-prompt/SKILL.md` element 4, verbatim as it exists at `598cc02` (line 33):

   > \| 4 \| Memory reference \| The **path** `memory/MEMORY.md`, with an instruction to read it in full. Do **not** paste its contents \| same \|

2. Baseline row, `docs/token-focus-finding-2026-09-25.md` § 3 (14 spawns, medians):

   > \| **Read before the first Edit/Write** \| **16.8k tokens over 8 calls** \| — most-read file before
   > the first edit: `memory/MEMORY.md` (6 of 14; 41k chars ≈ 12k tokens).

3. The slice command does not exist, and the spawn hook says nothing about a missing slice:

```
$ date -u; git rev-parse --short HEAD
2026-09-25T05:51:32Z
598cc02
$ python3 scripts/memory_slice.py tasks/TASK_GUIDE_T125.md; echo exit=$?
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t125/scripts/memory_slice.py': [Errno 2] No such file or directory
exit=2
$ printf %s '{"tool_name":"Agent","tool_input":{"prompt":"Task ID: T125\nRead tasks/TASK_GUIDE_T125.md"}}' | python3 .claude/hooks/pre_agent_validate_guide.py; echo exit=$?
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Advisory warning (not blocking):\n  \u2022 T125 declares 'Depends on: T124', which is currently 'Ready for Review' (not Done). Confirm this is intentional (e.g. parallel stub work) before proceeding.\n  \u2022 T125's Demonstration BEFORE field is blank. Capture it BEFORE your first implementation commit \u2014 a BEFORE taken after the change is not a BEFORE, and there is no N/A path."}}
exit=0
```

**AFTER** (implementer capture, 2026-09-25T07:27:54Z at `e481526`; AC9's live-spawn row is still to be added by the Supervisor at Stage 5):

New element 4 (`skills/craft-spawn-prompt/SKILL.md:33`): run `memory_slice.py <guide-path>`, paste its
output verbatim, then *"Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or
decision the slice does not cover."* Pre-flight (step 4) flags a prompt without the marker.

```
2026-09-25T07:27:54Z
e481526
$ python3 -m pytest tests/test_memory_slice.py .claude/hooks/tests/test_pre_agent_validate_guide.py .claude/hooks/tests/test_memory_channel_and_budget.py -q
44 passed in 0.44s
$ python3 -m pytest .claude/hooks/tests tests -q | tail -3
879 passed in 14.85s
$ sh scripts/validate.sh | tail -1
validate.sh: PASS
$ python3 skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_T125.md
<!-- memory-slice:T125 -->
memory/MEMORY.md — 18 of 239 index lines matched on: craft-spawn-prompt, CLAUDE.md, setup.sh, memory/, tasks/TASK_GUIDE_T0
### Decisions
- [`claude_md_source` records the CLAUDE file a project installed with](decisions.md) — T110: `update.sh` now delivers `CLAUDE.md` under the edit-safe rule
- [CLAUDE_LEGACY.md sync policy](decisions.md) — mirror new skills + session-startup gates + Hard-Stop Gates from CLAUDE.md into CLAUDE_LEGACY.md on each addition
- [Codebase Map](codebase-map.md) — structural snapshot (tree, entry points, hotspots) in memory/codebase-map.md; C2/C3 agents read it
- [learn skill: Learning Record System](decisions.md) — LR files in memory/learning-records/
- [Code Naming Conventions in CLAUDE.md](decisions.md) — code-level only (funcs=verbs, classes=nouns, tests, DB, env vars, etc.)
- [T021/T022/T023: craft-spawn-prompt skill + hardened spawn-hook](decisions.md) — spawn-hook matches structural Txxx refs only
- [Stage 2 planning T039-T042, 2026-07-21](decisions.md) — CLAUDE.md `## Skills vs Agents` dedup (T039, the harness already auto-injects both rosters)
- [T039 merged: CLAUDE.md Skills-vs-Agents dedup](decisions.md) — 580→536 lines; kept only what the harness does not already auto-inject
- [T090 merged: provider adapters, split by mandate](decisions.md) — `CLAUDE.md` stays primary
- [setup.sh clones the remote, so unmerged work is unverifiable](learnings.md) — an install can run green and build a tree without your change
- [T092 merged: the cache finding reaches the spawn assembler](decisions.md) — DDR-0004's "size is ~free, count is the lever" lived in a hook, a DDR and two cold files, never in `craft-spawn-prompt`
- [T091 merged: the Staleness Guard describes the channel it guards](decisions.md) — names `CLAUDE.md` + both adapters + the conformance test
### Patterns & Gotchas
- [CLAUDE.md gains Supervisor Communication Style section, 2026-08-03](decisions.md) — lives in the harness's master CLAUDE.md so setup.sh propagates to other repos (not machine-level `~/.claude/CLAUDE.md`, wrong
- [CLAUDE.md gains context-overwhelm self-monitoring rule, 2026-08-03](decisions.md#claudemd-gains-a-context-overwhelm-self-monitoring-rule-2026-08-03) — the Supervisor's own long-session accuracy, judged off
- [T049 merged: CLAUDE.md split 565→198 lines, 2026-08-04](decisions.md) — 5 docs/claude-md/ files
- ["Already covered" must mean reaches-the-context](learnings.md) — not "exists in the repo"; CLAUDE.md isn't in the sub-agent read list and `tdd` is invocation-triggered, so both "cover" things they never deliver
- [A memory pass is uncommitted work like any other, and stashes hide it](learnings.md) — T046 shipped with a merged commit, passing tests and a closed row, yet `grep T046 memory/` was empty two weeks later: its
### Glossary
- [T099: quoted spans are sometimes code] — naive quoted-span stripping would ALLOW `bash -c "git push"`. Needs wrapper-awareness. → tasks/TASK_GUIDE_T099.md
<!-- /memory-slice -->
exit=0
$ printf ... no-marker spawn | python3 .claude/hooks/pre_agent_validate_guide.py
[hook:pre_agent] memory-slice missing: Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4).
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Advisory warning (not blocking):\n  \u2022 T125 declares 'Depends on: T124', which is currently 'Ready for Review' (not Done). Confirm this is intentional (e.g. parallel stub work) before proceeding.\n  \u2022 Spawn prompt names a TASK_GUIDE but has no `<!-- memory-slice:` marker, so the agent gets none of the memory lines its task touches. Run `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>` and paste its output verbatim (craft-spawn-prompt element 4)."}}
exit=0
```

**DELTA**: The Supervisor can now paste a spawned agent the few `MEMORY.md` lines its task touches with one deterministic command. The spawn hook warns (never blocks) when a guide-naming prompt goes out without them, so the agent no longer needs the whole 41k-char index before its first edit. The token effect is AC9's, still to be measured.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
