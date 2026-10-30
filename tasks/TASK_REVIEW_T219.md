# TASK_REVIEW — T219: Pipeline pointers for the tech-lead pack

> Sibling of `tasks/TASK_GUIDE_T219.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. Pointer placement: one conditional line in `AGENTS.md` `## 5-Stage Agentic Pipeline` plus the full pointer in `docs/claude-md/pipeline-stages.md` — DEBATED: AGENTS.md line + pipeline-stages pointer (Advocate 1: pipeline-stages.md only, AGENTS.md unchanged — dormant packs, 4 lines of cap headroom; Advocate 2: one AGENTS.md line too — only always-loaded stage text, matches FR-009) ⚠ decided for you — please review
3. Decision 1 reversed after the build: the pointer lives in `docs/claude-md/pipeline-stages.md` only; `AGENTS.md` is unchanged and no line-freeing follow-up is opened now — DEBATED: pipeline-stages.md only, no follow-up (Advocate 1: pipeline-stages.md only — AGENTS.md is capped at 196 by `tests/test_auto_mode.py` and `test_vital_slice.py`, cannot name a dormant path per `scripts/validate.sh` §3; Advocate 2: ship pipeline-only now plus a follow-up task appending a path-free pointer to the Stage 2 bullet with a `REPLACED_SPANS` entry in `tests/test_agents_md_primary.py`). Both Advocates agree on shipping pipeline-only; the follow-up is not opened because it loosens a doctrine-drift guard for a pointer Advocate 2 itself calls possibly unnecessary ⚠ decided for you — please review
Checks: tests `bash tests/test_tech_lead_pipeline_pointer.sh` — `6 passed, 0 failed`; full suite `5 failed, 2545 passed` (pre-existing memory budget, fixed on main); `bash scripts/validate.sh` — `validate.sh: PASS`; reviews code-review — pass (0 P0/P1), security-review — no findings; real run: read Stage 2 item 6 and Stage 5 item 4 against T218's verify run, where the real `tech-lead` agent wrote the map, drafted 5 approved documents and refreshed only the matched one (`.claude/verify-runs/T218-8752b101c19d.log`) (auto-checked, not /verify)
Memory: memory/learnings.md — "AGENTS.md has zero lines of headroom: cap 196, and named paths must exist" (`d529b589`, on main); memory/decisions.md — T218–T220 entry records the pipeline-stages-only placement (`031c22c8`)
Not done: merge (yours; merge T218 first — this branch is cut from it); auto verify: running (T182)
2. Branch cut from `feat/t218-tech-lead-pack`, so merge T218 first — RULE: `tasks/TASK_GUIDE_T219.md` § Dependencies & Reachability "Depends on: T218"
Paused: auto-mode check failed — no `Memory:` line in the report — run the memory pass before you stop and record it there (each entry written, or `Memory: nothing new`); extended track, but the trace has no `code-review` Skill call (Stage 4 runs in auto mode); Risk Medium, but the trace has no `security-review` Skill call

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_tech_lead_pipeline_pointer.sh` (wired in `.github/workflows/ci.yml` after the T218 step): `6 passed, 0 failed` — AC1 Stage 2 item 6, AC2 Stage 5 item 4 sub-bullet, AC3 exactly two tech-lead mentions in pipeline-stages.md, AGENTS.md size cap, mutation controls M1 and M2 (condition stripped → check fails). AC 3b (AGENTS.md line) NOT delivered, see Blocked below |
| Verification command run | ☑ pass | `bash tests/test_tech_lead_pipeline_pointer.sh` → PASS x6, `6 passed, 0 failed`, rc=0. Related shell suites: test_harness_projection 41 passed; test_install_backups 17 passed; test_update_claude_md 52 passed; test_setup 21 passed. Pytest `.claude/hooks/tests/ tests/`: 2545 passed, 5 failed — all 5 are the MEMORY.md char budget (42,252 > 42,000, branch base predates main's 5e0c7588 fix), not caused by T219 |
| Negative cases hold | ☑ pass | mutation controls M1 (Stage 2 pointer without its `agents/tech-lead.md` condition) and M2 (Stage 5 sub-bullet without its condition) each fail the check; AGENTS.md unchanged (196 lines); `bash scripts/validate.sh` — `validate.sh: PASS` |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review on `feat/t218-tech-lead-pack...feat/t219-tech-lead-pointers` (pipeline-stages.md, ci.yml, new test, task files) — 0 P0, 0 P1, 1 P2 (PRD FR-009 text, fixed on main `7bfc68a5`), 1 P3 (test label says blocked); lane_check `C1, 4 files, 97 lines, FITS`. security-review — no findings (Markdown pointers, fixed ci.yml run line, test with no untrusted input) |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` — `5 failed, 2545 passed`; the 5 are the hot-tier memory budget tests, red on this branch's base and fixed on `main` by `5e0c7588`; none from this diff |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional companion; T219 is two Markdown lines + one shell test |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component: doctrine text and a shell test only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component: doctrine text and a shell test only |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component: doctrine text and a shell test only |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim prior content, captured 2026-10-30 before any implementation commit):

`AGENTS.md` line 150 and line 153 (Stage 2 and Stage 5 bullets; no tech-lead mention anywhere in the pipeline section):
```
- **Stage 2** (`/plan` — Intent Transformation): produce `PROJECT_SPEC.md` + `PROJECT_KANBAN.md`, assign Complexity/Risk/Priority per task, generate every `tasks/TASK_GUIDE_Txxx.md`.
- **Stage 5** (Integration & Verification): `Skill({ skill: "verify" })`, smoke tests, memory update (diff-driven pass), merge + close Kanban, `Skill({ skill: "ship" })` for release planning.
```
`docs/claude-md/pipeline-stages.md`, end of the Stage 2 numbered list (item 5 is the last item):
```
5. Assign each task three independent labels: **Complexity (C0–C3)**, **Risk (Low/Med/High)**, and **Priority (P0–P2)**. [...] A hub touch raises Risk a level even when the edit itself is small.

**Task State Management (Token-Efficient Design)**
```
`docs/claude-md/pipeline-stages.md`, Stage 5 item 4 (the memory-update item, no refresh step):
```
4. **Memory update** (diff-driven pass — run before `ship`):
   - `git diff HEAD~1 --name-only` — identify files changed in this merge
   - Grep `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md` for references to those files
   - Update matched entries in place (fix stale facts, expand with new context)
   - Append any new decisions or learnings from this session to the appropriate cold file
   - Summarize new/changed entries as one-liners in `memory/MEMORY.md` (keep hot tier ≤50,000 characters)
```

**AFTER**: `docs/claude-md/pipeline-stages.md` Stage 2 gains item 6, Stage 5 item 4 gains a sub-bullet after the `git diff HEAD~1 --name-only` bullet; `AGENTS.md` is unchanged (see Blocked).
```
6. If `agents/tech-lead.md` exists (tech-lead pack activated, `packs/tech-lead/PACK.md`), once `PROJECT_SPEC.md` is locked, spawn `tech-lead` to write the document map `docs/architecture/README.md` for user approval. Auto mode: map only, listed in the final report.
...
   - `git diff HEAD~1 --name-only` — identify files changed in this merge
   - If `agents/tech-lead.md` and `docs/architecture/README.md` both exist (tech-lead pack, `packs/tech-lead/PACK.md`), match this list against the map's watched paths: on a match, spawn `tech-lead` in refresh mode for the matched documents only; no match (or no watched-paths column), nothing.
```

**DELTA**: In a project with the tech-lead pack activated, the Supervisor now spawns `tech-lead` for the document map at Stage 2 and for a refresh at Stage 5 item 4; in every other project the pipeline reads as before.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

---

## Blocked (AC 3b) — resolved by the Supervisor: Auto decision 3 (pipeline-stages.md only)

AC 3b (one conditional line in `AGENTS.md`) is not delivered. AGENTS.md has 0 lines of headroom: the guide's "cap 200" is wrong. A line added to it failed 4 existing tests: `.claude/hooks/tests/test_vital_slice.py::test_ac11_line_cap[AGENTS.md]` (197 > 196, "do not raise the cap (DDR-0005 §6)"), `tests/test_auto_mode.py::test_ac1_agents_md_gains_no_line_and_stays_under_the_byte_cap`, `tests/test_agents_md_primary.py::test_ac1_...` (adds lines outside the allowed blocks), and `scripts/validate.sh` (path `agents/tech-lead.md` in AGENTS.md does not resolve in the kit, which fails `test_agents_md_primary::test_ac8` and `test_companion_scoring_skills::test_ac1`). So the line was reverted. This leaves the pipeline-stages.md pointers only (Advocate 1's option).
