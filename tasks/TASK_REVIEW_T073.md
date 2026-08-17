# TASK_REVIEW — T073: the memory-update hook tells every session not to commit tracked files

> Sibling of `tasks/TASK_GUIDE_T073.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_memory_hook_note_truthfulness.py` — 7 tests covering AC1–AC4, AC6, AC7. Imports the hook's real `MEMORY_UPDATE_PROMPT` constant (via `importlib.util.spec_from_file_location`, one import, no copy) and cross-checks `git check-ignore` ground truth |
| Verification command run | ☑ pass | `cd .../personal-agentic-claude/../wt-t073 && python -m pytest .claude/hooks/tests/ -q` → `449 passed in 8.44s`, pytest exit=0 (was 442 at HEAD per guide; +7 new) |
| Negative cases hold | ☑ pass | AC4 file-wide negative (`gitignored except MEMORY.md`, `writes are local-only`, `Do NOT commit` absent from all `.claude/hooks/*.py`) passes; mutation control SC5 (restore old NOTE text) confirmed RED on AC1–AC4 tests, reverted, suite green again |
| verify | ☑ pass | `/verify` run by the user 2026-08-17 against the **running hook**, not the suite — the hook was driven as a process (`/tmp/t073_drive.py`) with real PostToolUse event payloads on stdin, the surface the harness itself uses. `{"tool_name":"Bash","tool_input":{"command":"git push origin fix/t073-impl"}}` → exit 0, valid JSON, and the line actually delivered into model context is `NOTE: the cold-tier files (decisions.md, glossary.md, learnings.md) are git-tracked. Commit this pass — writing the files to disk is not sufficient. Only memory/event-trace/ is local-only (gitignored).` The same event against **main's unfixed copy** still emits `NOTE: memory/ writes are local-only (memory/* is gitignored except MEMORY.md). Do NOT commit or push…`, so the delta was observed at runtime and not inferred from the diff. `merge` and `pull` events fire identically (all 3 trigger patterns live). Every clause of the new sentence re-checked against real git state: `git ls-files memory/` → `MEMORY.md, codebase-map.md, decisions.md, feedback_no-claude-credit.md, glossary.md, learnings.md, 2 LRs`; `git check-ignore` → decisions/glossary/learnings **not ignored**, `memory/event-trace/x.jsonl` **IGNORED**; tracked files under `memory/event-trace/` = **0**. Probes: non-git Bash (`ls -la`) silent exit 0; non-Bash tool (`Write`) carrying `git push` silent exit 0; malformed stdin, empty stdin, and missing `tool_input.command` all exit 0 with empty stdout and no traceback. Feature confirmed working at its real surface — **pass** |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 1-line NOTE in `.claude/hooks/post_bash_memory_update.py` (the whole behavioural change), the new `.claude/hooks/tests/test_memory_hook_note_truthfulness.py`, and the 5-line narrowing of `test_vital_slice.py::test_ac12`. Skipped: the rest of the repo — the diff is 3 files, the hook's `main()`/`GIT_MEMORY_PATTERNS` are byte-unchanged, and the changed constant is prose inside one module with no importers outside the new test. The `test_ac12` edit was reviewed against DDR-0005 §5 rather than as a test relaxation: the byte-identity half was a scope guard committed as an invariant (occurrence 7), the content half that actually enforces the DDR is retained |
| Full smoke suite still green (no regression) | ☑ pass | `python -m pytest .claude/hooks/tests/ -q` → `449 passed in 8.44s` after commit `3ac08e3` and after reverting all 3 mutation controls (SC5, SC6, AC10). `test_memory_channel_and_budget.py` (AC8, unmodified) and the other 36 tests in `test_vital_slice.py` (AC9 scope) all still pass |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component — hook prose only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component — hook prose only |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component — hook prose only |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-08-16T09:39:59Z, before any implementation commit.

Verbatim prior NOTE text, `.claude/hooks/post_bash_memory_update.py:33`:
```
NOTE: memory/ writes are local-only (memory/* is gitignored except MEMORY.md). Do NOT commit or push the results of this pass — writing the files to disk is sufficient.
```

Ground-truth contradiction, same timestamp:
```
$ git check-ignore -v memory/decisions.md; echo "exit=$?"
exit=1

$ git check-ignore -v memory/event-trace/x.jsonl; echo "exit=$?"
.gitignore:53:memory/event-trace/	memory/event-trace/x.jsonl
exit=0
```
`memory/decisions.md` is NOT ignored (exit 1) — contradicting the NOTE's "gitignored except MEMORY.md" claim. Only `memory/event-trace/` is ignored (exit 0).

**AFTER**: Captured 2026-08-16T09:47:54Z, at commit `3ac08e3`.

Verbatim new NOTE text, `.claude/hooks/post_bash_memory_update.py`:
```
NOTE: the cold-tier files (decisions.md, glossary.md, learnings.md) are git-tracked. Commit this pass — writing the files to disk is not sufficient. Only memory/event-trace/ is local-only (gitignored).
```

Same ground-truth checks, unchanged since BEFORE (the NOTE changed, reality didn't):
```
$ git check-ignore -v memory/decisions.md; echo "exit=$?"
exit=1

$ git check-ignore -v memory/event-trace/x.jsonl; echo "exit=$?"
.gitignore:53:memory/event-trace/	memory/event-trace/x.jsonl
exit=0
```
The NOTE now agrees with the ground truth it previously contradicted.

**DELTA**: A Supervisor following the post-`git`-push/merge hook prompt now commits the cold-tier
memory pass instead of being told not to — closing the mechanism behind T046's silently-lost memory
pass (shipped, tests passing, Kanban closed, `grep T046 memory/` still empty two weeks later).

**WITNESS**: Common-Infrastructure-Agent, task T073, ran the implementation, both guide-specified
mutation controls (SC5, SC6) and the Stage-2-amendment mutation control (AC10) directly, 2026-08-16
09:39:59Z–09:48:09Z. Derived from `memory/event-trace/T073.jsonl` (live trace of every Bash command
run under the T073 active-task pointer, timestamps 2026-08-16T09:3x–09:4x UTC).
