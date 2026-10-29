# TASK_REVIEW — T196: Trace attribution per session and per sub-agent

> Sibling of `tasks/TASK_GUIDE_T196.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_task_context.py` (AC 1–6 slot tests incl. `test_t196_ac5_unsafe_session_ids_never_reach_a_path`, `test_t196_binding_declared_task_id_beats_an_earlier_guide_path`, `test_t196_binding_with_only_a_guide_path_binds_to_that_guide`), `.claude/hooks/tests/test_trace_per_session.py` (AC 7 incident replay through `post_tool_trace.py` + `trace_shows_verification`; AC 8 instruction test), `test_merge_gate_guard.py` (AC 9). Supervisor run 2026-10-29 at `6acedf8`: `2106 passed, 25 subtests passed in 98.50s` |
| Verification command run | ☑ pass | agent 2026-10-29T08:20:07Z at `6acedf8`: `94 passed` / `2106 passed, 25 subtests passed` / `11` (all 11 are continuation lines of the `ATTRIBUTION_REMEDY` string; read by the Supervisor). |
| Negative cases hold | ☑ pass | Old shared `.state/active_task` ignored; unsafe `session_id`/`agent_id` (`../x`, empty, 200 chars) never reach a path; missing/empty/non-JSON transcript and a prose-only mention fall through; a guide path written before `Task ID:` no longer wins (Stage 4 P2, fixed in `6acedf8`). |
| verify | ☑ pass | `/verify T196` (user-invoked) 2026-10-29 at `2fea9c5`, throwaway copy of the branch with the kit's real hooks. Two concurrent headless `claude -p` sessions (2.1.312, haiku, $0.024 total): session A wrote its per-session file T911 and spawned two parallel sub-agents (`Task ID: T912`; and a prompt naming `tasks/TASK_GUIDE_T175.md` before `Task ID: T913`); session B wrote T914 and ran 4 echoes during A's run. Traces: A main calls → `T911.jsonl`, X → `T912.jsonl`, Y → `T913.jsonl` (not T175), B → `T914.jsonl`; 0 crossings; decoy shared `.state/active_task` = T999 ignored (no `T999.jsonl`). Caches: `agent_task/<A>/<aid>` = T912 and T913. Gate hook fed a push event prints the per-session remedy text — pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | (Stage 4, Supervisor, 2026-10-29, `git diff main...6acedf8`) `task_context.py` read in full; gate diff = remedy string only; guard allowlist + comment; D5 instruction texts; two gate oracle files (remedy string swapped, 3 hits each). Callers of `resolve_task_id` (trace, step limit, sensitive path, move-to-review) take the same event dict — no caller change. |
| Full smoke suite still green (no regression) | ☑ pass | `2106 passed, 25 subtests passed`, 0 failed (Supervisor). |
| **Companion score (easy-verifier)** | ☑ N/A | Not run: optional companion. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: hook library, tests and instruction text only. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI: hook library, tests and instruction text only. |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI: hook library, tests and instruction text only. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T08:04:56Z, branch `feat/t196-trace-per-session` at `39fa195`
(`git diff main -- .claude/hooks/lib/task_context.py` empty: unchanged resolver). The AC 7 incident
replay `.claude/hooks/tests/test_trace_per_session.py` was written first and run against it:

```
$ python3 -m pytest -q -s .claude/hooks/tests/test_trace_per_session.py
T190.jsonl: []
T188.jsonl: ['cd /w/wt-t190-gate && git status', 'cd /w/wt-t188 && git log --oneline -1', 'cd /w/wt-t190-gate && python3 -m pytest -q .claude/hooks/tests/', 'cd /w/wt-t188 && ls tasks/', 'cd /w/wt-t190-gate && git diff --stat']
crossings: 3
trace_shows_verification('T188') = True
E           AssertionError: 3 crossing(s): ['cd /w/wt-t190-gate && git status', 'cd /w/wt-t190-gate && python3 -m pytest -q .claude/hooks/tests/', 'cd /w/wt-t190-gate && git diff --stat']
FAILED .claude/hooks/tests/test_trace_per_session.py::test_ac7_incident_replay_has_no_crossings_and_t188_is_not_verified_by_t190
1 failed in 0.17s
```

Every call of session A's T190 sub-agent landed in `T188.jsonl` (3 of 3 crossings), and the T188
gate check passed on T190's `pytest` run — the 2026-10-28 incident, reproduced.

**AFTER** (agent, 2026-10-29T08:16:02Z, `python3 -m pytest -q -s .claude/hooks/tests/test_trace_per_session.py`):

```
T190.jsonl: ['cd /w/wt-t190-gate && git status', 'cd /w/wt-t190-gate && python3 -m pytest -q .claude/hooks/tests/', 'cd /w/wt-t190-gate && git diff --stat']
T188.jsonl: ['cd /w/wt-t188 && git log --oneline -1', 'cd /w/wt-t188 && ls tasks/']
crossings: 0
trace_shows_verification('T188') = False
2 passed in 0.21s
```


**DELTA**: Two sessions, or two sub-agents with their own spawn prompts, can no longer file tool calls under each other's task, so one task's verification run can no longer satisfy another task's merge-gate trace check.


**WITNESS**: Supervisor, 2026-10-29: re-ran the full suite and the two Stage 4 P2 tests at `6acedf8` in `wt-t196`; read the agent's live AC 10 trace lines (main `T902`, sub-agent `T901`, same session `3b722d1a-…`).


---

## Stage 4 — code-review + security (Supervisor, 2026-10-29)

Scope: `git diff main...6acedf8`, 13 files. Startup reads: complete.

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P0 | — | None. | — | — |
| P1 | — | None. | — | — |
| P2 | `task_context.py` slot 2 | The spawn binding took the first `TASK_GUIDE_Txxx.md` path anywhere in the prompt before a `Task ID:` line, so "read TASK_GUIDE_T175.md … Task ID: T177" bound (and cached) T175 for every call of that agent. | 95 | **Fixed** in `6acedf8`: an explicit `Task ID:` wins; guide path only without one; 2 tests. Slot 5 unchanged (documented). |
| P3 | `pre_bash_block_unsafe_merge.py` comment above `ATTRIBUTION_REMEDY` | Still says "`task_context.py`'s slot 2"; the per-session file is slot 3. | 100 | Left: the user approved the remedy string only (D6). |
| P3 | trust model | A session can still write any task ID into its own per-session file, and could write a cache file under `agent_task/`. Same trust as T047's file, but it can no longer touch another session's or a sibling sub-agent's attribution. | 90 | None. |

Security (High risk, manual pass): path inputs are `session_id`/`agent_id` from the harness event, gated by `SAFE_KEY` (`\A[A-Za-z0-9_-]{1,128}\Z`, test proves `../x` never reaches a path); the transcript is derived only from the event's absolute `transcript_path`, read-only, first line capped at 1 MB; cache writes are best-effort and confined to `.state/agent_task/<sid>/<aid>`. `resolve_task_id` keeps its never-raises contract. Gate logic unchanged; `AUTHORISED_TASKS` gains `T196` with its rule, as the user approved.

Verdict: no open P0/P1; 1 P2 fixed. Ready for the user's `/verify T196`.
