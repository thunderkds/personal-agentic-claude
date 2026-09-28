# TASK_REVIEW — T136: The spawn model is picked per CLI from the task's Complexity, never hard-coded to Claude names

> Sibling of `tasks/TASK_GUIDE_T136.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_cli_model_table.py` — 8 tests, one per AC1–AC8 (observed RED before doc edits, GREEN after: `8 passed in 0.04s`) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_cli_model_table.py -q` → `........  8 passed in 0.04s`; `python3 -m pytest .claude/hooks/tests tests -q \| tail -1` → `1 failed, 990 passed in 13.37s` (the 1 failure is `test_find_kanban_section_on_real_current_board`, a pre-existing PROJECT_KANBAN.md Todo/In-Progress status drift unrelated to this task — reproduced identically on the unmodified tree before any T136 edit, and PROJECT_KANBAN.md is out of scope/Files-Must-NOT-Touch for this agent); `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | M1 (re-add `C0→haiku` map to step 5) → AC3+AC8 RED as predicted (`2 failed, 6 passed`). M2 (delete STOP-and-ask sentence) → AC4 RED as predicted (`1 failed, 7 passed`). M3 (rename `## CLI Model Table` heading in the template) → AC1 RED as predicted (`1 failed, 7 passed`). All three files restored after each mutation; suite re-confirmed GREEN (`8 passed`) after restore |
| verify | ☐ N/A | User-run per `memory/MEMORY.md` (`verify` skill is user-only) — not run by this agent |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed only the 6 predicted files (`templates/PROJECT_SPEC_template.md`, `PROJECT_SPEC.md`, `skills/craft-spawn-prompt/SKILL.md`, `docs/claude-md/pipeline-stages.md`, `templates/TASK_GUIDE_template.md`, new `tests/test_cli_model_table.py`) plus the one adjacent regression surfaced by the full suite (`.claude/hooks/tests/test_spawn_prompt_cache_note.py`'s SKILL.md line-cap, fixed by trimming step 5/6 prose back to 80 lines, no content dropped). Did not re-review unrelated repo areas **Supervisor Stage 4 (2026-09-28):** `git diff main...feat/t136-cli-model-table` — the 6 predicted files + test + review file; direct callers of `craft-spawn-prompt` grepped (`skills/bugfix/SKILL.md:167`, `docs/claude-md/pipeline-stages.md:153`, `CLAUDE.md:158`). Findings: **P1 ×1 fixed** (`ef6e194` — bugfix called the spawn step without the CLI it now takes); **P2 ×1** (AC8 test carries dead code: an unused first `git grep` call, a never-true `"frontmatter" in path` clause, a duplicate exclusion check); **P3 ×2** (step 6 Output reflowed from a list to one line beyond scope; AC5 test's `or` repeats the same string). P0: none. Supervisor re-ran M1 → `2 failed, 6 passed`, M2 → `1 failed, 7 passed`, restored → `8 passed`. |
| Full smoke suite still green (no regression) | ☑ pass | `990 passed, 1 failed` — the 1 failure is the pre-existing, out-of-scope Kanban drift noted above; no regression introduced by this task's diff (confirmed: same failure reproduces on the unmodified tree) **Supervisor re-check (2026-09-28):** the 1 failure is `test_find_kanban_section_on_real_current_board` on the branch's stale board copy (duplicate T136 row from the Supervisor's `d7bda94`, fixed on `main` in `49ff9fa`); with `main`'s board swapped in: `991 passed in 14.97s`. `validate.sh: PASS`. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI component — doctrine/template text only (per guide's UI/Design AC section) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Same reason |
| **UI: Responsiveness at target viewports** | ☐ N/A | Same reason |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Doc-only change (no executable code) — verbatim prior content, quoted as it exists right now (captured 2026-09-28 before any implementation commit):

`skills/craft-spawn-prompt/SKILL.md` `#### 5. Recommend spawn model`:
```
#### 5. Recommend spawn model
Map the guide's `**Complexity Level**` to a model, per the table already in `CLAUDE.md` Stage 3 / `general-agent-template.md`: C0→haiku, C1→sonnet, C2→sonnet/opus, C3→opus.
```

`docs/claude-md/pipeline-stages.md` Stage 3 line (line 153):
```
- Invoke `Skill({ skill: "craft-spawn-prompt" })` with the task's guide path first — it assembles the spawn prompt, pre-flight-checks it against the spawn hook, and recommends the model per the task's **Complexity** (C0→haiku, C1→sonnet, C2→sonnet/opus, C3→opus). Then issue the `Agent()` call in that worktree using its output.
```

`docs/claude-md/pipeline-stages.md` Stage 1 item 2 (before edit):
```
2. **Multi-CLI Authentication**
   Please list every agentic CLI you have authenticated and the exact command to run it.
   Example: "Claude: claude | Codex: codex | Gemini: gemini"
```

Repo-wide grep at this point (`git grep -nE 'C[0-3] ?→ ?(haiku|sonnet|opus)'` outside the excluded paths) hits exactly these two files/lines — confirmed via Bash on 2026-09-28.

**AFTER**: Same two places, post-change, plus one worked lookup read off this repo's own table:

`skills/craft-spawn-prompt/SKILL.md` `#### 5. Recommend spawn model`:
```
#### 5. Recommend spawn model
Takes the CLI as input; look up the guide's `**Complexity Level**` (C0–C3) in that CLI's row in
`PROJECT_SPEC.md`'s `## CLI Model Table` — that cell is the model. No row/empty cell → **STOP and
ask the user** (suggest `templates/PROJECT_SPEC_template.md`); never fall back to another CLI's model, never invent one. A two-model cell (`sonnet or opus`) isn't ambiguity — pick per Risk.
```

`docs/claude-md/pipeline-stages.md` Stage 3 line (after edit):
```
- Invoke `Skill({ skill: "craft-spawn-prompt" })` with the task's guide path and the CLI that will run it — it assembles the spawn prompt, pre-flight-checks it against the spawn hook, and recommends the model by looking the task's **Complexity** up in `PROJECT_SPEC.md`'s `## CLI Model Table` for that CLI (no row/empty cell → it stops and asks, never a Claude-name fallback). Then issue the `Agent()` call in that worktree using its output.
```

Worked lookup, read off this repo's `PROJECT_SPEC.md` `## CLI Model Table` for T136 itself (C2):
`claude · C2 → sonnet or opus` (Supervisor picks per this task's Risk — Low — so `sonnet`); `codex · C2 → STOP (no model recorded — the codex row's C2 cell is empty; the user must fill it, this agent did not invent a value)`.

Repo-wide grep after the edits (`git grep -nE 'C[0-3] ?→ ?(haiku|sonnet|opus)'`, same excluded-paths filter as AC8): zero hits outside `tests/test_cli_model_table.py` itself.

---

## Round 2 (AC10 — no CLI named → STOP and ask)

**BEFORE** (doc-only change — verbatim prior content, captured 2026-09-28 before any round-2 implementation commit):

`skills/craft-spawn-prompt/SKILL.md` `#### 5. Recommend spawn model` (round-1 final state, i.e. round-2's BEFORE):
```
#### 5. Recommend spawn model
Takes the CLI as input; look up the guide's `**Complexity Level**` (C0–C3) in that CLI's row in
`PROJECT_SPEC.md`'s `## CLI Model Table` — that cell is the model. No row/empty cell → **STOP and
ask the user** (suggest `templates/PROJECT_SPEC_template.md`); never fall back to another CLI's model, never invent one. A two-model cell (`sonnet or opus`) isn't ambiguity — pick per Risk.
```
No sentence here covers the caller naming **no CLI at all** — confirmed by re-reading the block above verbatim before editing.

**AFTER**: step 5, post-edit:
```
#### 5. Recommend spawn model
Takes the CLI as input; look up the guide's `**Complexity Level**` (C0–C3) in that CLI's row in
`PROJECT_SPEC.md`'s `## CLI Model Table` — that cell is the model. No row/empty cell → **STOP and
ask the user** (suggest `templates/PROJECT_SPEC_template.md`); never fall back to another CLI's model, never invent one. A two-model cell (`sonnet or opus`) isn't ambiguity — pick per Risk. **No CLI named** by the caller at all → **STOP and ask which CLI will run the task**; never assume `claude` or any other CLI as a default.
```
Default Notification also updated to name the new STOP form (`STOP: no CLI named — ask which CLI runs <Task ID>`).

**DELTA**: A `craft-spawn-prompt` call with no CLI argument at all now stops and asks instead of silently defaulting to `claude` — closing the exact gap `/verify` caught (`claude · C2 → sonnet` returned with no warning when no CLI was named).

**WITNESS**: common-infrastructure agent, T136 round 2, 2026-09-28 — ran all commands above directly (`Bash` tool calls tagged via `.claude/hooks/.state/active_task`).

### Round 2 Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_cli_model_table.py::test_ac10_step5_stops_and_asks_when_no_cli_named` — observed RED before the step-5 edit (`1 failed, 8 passed`), GREEN after (`9 passed in 0.04s`) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_cli_model_table.py -q` → `9 passed`; `python3 -m pytest .claude/hooks/tests tests -q \| tail -1` → `1 failed, 991 passed in 12.24s` (same pre-existing out-of-scope `test_find_kanban_section_on_real_current_board` PROJECT_KANBAN.md drift as round 1 — reproduces on the unmodified tree, KANBAN is Files-Must-NOT-Touch); `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | **M4** (delete the no-CLI-named STOP sentence) → AC10 RED as predicted (`1 failed, 8 passed`), restored → `9 passed`. Re-ran **M1** (re-add `C0→haiku` map) → AC3+AC8 RED (`2 failed, 7 passed`), **M2** (delete STOP-and-ask sentence) → AC4 RED (`1 failed, 8 passed`), **M3** (delete `## CLI Model Table` heading) → AC1 RED (`1 failed, 8 passed`) — all three still hold unchanged from round 1; all restored, suite re-confirmed GREEN (`9 passed`) |
| verify | ☐ N/A | User-run per `memory/MEMORY.md` (`verify` skill is user-only) — not run by this agent |
| Full smoke suite still green (no regression) | ☑ pass | `991 passed, 1 failed` — the 1 failure is the pre-existing, out-of-scope Kanban drift noted above; no regression from this task's diff. Fixing round 2 also required re-tightening `#### 6. Output` back to single-line prose (kept, not reflowed to a numbered list as the round-1 P3 note suggested) and merging the new STOP sentence onto the existing line, to stay within `.claude/hooks/tests/test_spawn_prompt_cache_note.py`'s 80-line `SKILL.md` cap (`test_ac4_added_lines_within_cap_and_no_new_heading` — file is exactly 80 lines; confirmed passing) |
| Applied same-commit cleanups (optional, per guide) | ☑ done — 2 of 3 | AC8 test's dead code (unused first `git grep` call, dead `"frontmatter" in path` clause, duplicate exclusion check) removed; AC5 test's duplicate `... in skill or ... in skill` simplified to a single check. Step 6 Output reflow **not** applied — restoring it to a numbered list pushed `SKILL.md` over the 80-line cap (`test_ac4_added_lines_within_cap_and_no_new_heading` went RED at 84 then 81 lines); left as single-line prose to keep the suite green, since this cleanup was explicitly optional and the cap test is not |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI component — doctrine/template text only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Same reason |
| **UI: Responsiveness at target viewports** | ☐ N/A | Same reason |

**DELTA**: The Supervisor no longer needs Claude installed to pick a spawn model for a Codex (or any other) CLI task — it reads the model straight from that CLI's own row/column in `PROJECT_SPEC.md`, and is forced to stop and ask (never guess a Claude-only name) the moment that CLI has no row or an empty cell for the task's Complexity level.

**WITNESS**: common-infrastructure agent, T136, 2026-09-28 — ran all commands above directly (`Bash` tool calls tagged via `.claude/hooks/.state/active_task`); `memory/event-trace/T136.jsonl` was empty of Bash-tagged entries at the time this file was filled (only pre-verification `Read` calls had landed), so this WITNESS line is the agent's own contemporaneous record, to be cross-checked against the trace by the Stage 4 reviewer.
