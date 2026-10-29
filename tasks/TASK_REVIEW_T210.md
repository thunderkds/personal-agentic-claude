# TASK_REVIEW — T210: Merge gate closes four gaps — `git pull` is gated, `timeout`-wrapped test runs count, `git

> Sibling of `tasks/TASK_GUIDE_T210.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T20:21+07:00 on the UNCHANGED gate (`5c17cf5`, before any T210 implementation commit), by feeding real PreToolUse JSON events to `python3 <clone>/.claude/hooks/pre_bash_block_unsafe_merge.py` in a throwaway clone. Driver: `python3 $S/demo_gate.py /home/hungnguyenhuu/workspace/pets/wt-t210 $S/before` (`$S` = this session's scratchpad, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad`).

```text
gate under test: $S/before/clone/.claude/hooks/pre_bash_block_unsafe_merge.py (source /home/hungnguyenhuu/workspace/pets/wt-t210 @ 5c17cf5)
[2026-10-29T20:21:23+07:00] G1 pull, In Progress row
  event command: 'git pull'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
[2026-10-29T20:21:23+07:00] G1 pull --ff-only, In Progress row
  event command: 'git pull --ff-only'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
[2026-10-29T20:21:23+07:00] G3 merge-base --is-ancestor, In Progress row
  event command: 'git merge-base --is-ancestor HEAD main'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:21:23+07:00] G3 control: merge feat/x, In Progress row
  event command: 'git merge feat/x'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:21:23+07:00] G2 trace = only `timeout 900 python3 -m pytest -q`
  event command: 'git merge feat/x'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T900 (evidence row present but no verified tool call in memory/event-trace/T900.jsonl)
  worktree status: ?? tasks/TASK_REVIEW_T900.md
[2026-10-29T20:21:24+07:00] G4 merge feat/t900-x, verify row uncommitted in worktree
  event command: 'git merge feat/t900-x'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
  worktree status after commit: (clean)
[2026-10-29T20:21:24+07:00] G4 merge feat/t900-x, verify row committed on the branch
  event command: 'git merge feat/t900-x'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
```

Read: G1 `git pull` ALLOWED with an In Progress row; G3 `git merge-base` BLOCKED as a merge; G2 a trace whose only test run is `timeout 900 python3 -m pytest -q` reads "no verified tool call"; G4 the merge is ALLOWED while the verify row is only an untracked file in the worktree.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
