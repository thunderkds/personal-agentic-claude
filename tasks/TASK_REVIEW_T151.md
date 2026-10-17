# TASK_REVIEW — T151: The docs and site describe what T144, T145, T148 and T149 changed

> Sibling of `tasks/TASK_GUIDE_T151.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_docs_t151.py` (6 tests, AC1–AC6); RED before the edits (`6 failed in 0.04s`); mutation (drop `verify_trace.py` from the hook row) → `1 failed, 5 passed` |
| Verification command run | ☑ pass | Supervisor re-run 2026-10-17: `tests/test_docs_t151.py tests/test_site_content.py` → `45 passed in 0.10s`; full suite in this worktree `1 failed, 1092 passed` — the 1 is `test_find_kanban_section_on_real_current_board`, caused by a duplicate auto-registered T151 Todo row in the board this branch forked from; fixed on the integration branch in `408c5ed` (`19 passed` there) |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `feat/t144-t145-t148-t149...feat/t151-docs`: 2 doc files + new test; each added sentence checked against lane_check.py, memory_slice.py, post_tool_trace.py/trace_chain.py/verify_trace.py, merge-settings.py, ship/SKILL.md |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | text-only edits inside existing cells/paragraphs; only inline `<code>` added — no new elements, classes, styles or sections (guide § UI) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | text-only edits inside existing cells/paragraphs; only inline `<code>` added — no new elements, classes, styles or sections (guide § UI) |
| **UI: Responsiveness at target viewports** | ☑ N/A | text-only edits inside existing cells/paragraphs; only inline `<code>` added — no new elements, classes, styles or sections (guide § UI) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (non-executable change: verbatim prior text, captured 2026-10-17 before any implementation commit):

- `docs/claude-md/pipeline-stages.md:159`: "...verbatim: the `memory/MEMORY.md` index lines that name the guide's files, its `Depends on` tasks or its ID (T125). Then the fallback: ..."
- `docs/claude-md/pipeline-stages.md:171-175` (Stage 4 code-review): "Bound the review to the change's **blast radius** ... `code-review` also runs the Entry-Point Reachability Check (Phase 0.5) against the task's declared `Entry point:` field." (no lane_check mention)
- `docs/claude-md/pipeline-stages.md:231-235` (ship): "... `ship` **plans and de-risks** the release — it never auto-deploys; the operator executes the plan." (no approval / smoke-test mention)
- `site/index.html:531`: "<span class="tag tag-advise">advises</span> — appends every tool call to <code>memory/event-trace/&lt;task&gt;.jsonl</code>"
- `site/index.html:548`: "<strong>Memory slice</strong> — the spawn prompt pastes only the <code>memory/MEMORY.md</code> lines about the task's own files, capped at 30 lines / 4,000 characters"
- `site/index.html:655`: "...the <strong>memory slice</strong> — the index lines naming the task's files, dependencies or ID — and the agent reads the whole file only if its work reaches what the slice misses"
- `site/index.html:371-373`: "the kit's hooks are reconciled into it on install <em>and</em> on update, while your own permissions and your own hook entries are kept exactly as they are."
- `site/index.html:516-518`: "...including into one your project already has — and never touch your own permissions or hook entries. No manual merge step."

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Stage 4 — code-review (Supervisor, 2026-10-17)

Scope: `feat/t144-t145-t148-t149...feat/t151-docs`. lane_check: `lane: C1, 3 files, 78 lines, FITS`. Startup reads line is complete (all three read in full).
- Fact check, every added sentence against the code on this branch:
  - Memory injection (T145): `memory_slice.py` matches the `**Files**:` line, uses `### From decisions.md`, drops cold entries first. ✓
  - Lane check (T144): `<base>...HEAD`, three dots, warn-only. ✓
  - `ship` (T149): approval of `<version> @ <commit>` recorded in the Release Log; smoke test written before the deploy; "never auto-deploys" kept. ✓
  - Trace hook row (T148): the hash chain, a per-line hash copy under `~/.claude/harness-anchors/`, and `verify_trace.py <task>`. ✓
  - Settings merge (T148): the deny entries are added, add-only, and the kit's allow/ask rules are never copied. ✓
- P0–P2: none.
- P3 (pre-existing, not T151's): `pipeline-stages.md` says the hot tier is "≤50,000 characters", while the site and the enforced budget say 42,000.
- P3: the settings-merge text doesn't list the new refusal, a project `permissions.deny` that is not a list. That's minor; the existing "if it cannot be merged" sentence covers the outcome.
