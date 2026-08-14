# TASK_REVIEW — T070: Repoint the stale Complexity-matrix pointers at the guaranteed channel

> Sibling of `tasks/TASK_GUIDE_T070.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_complexity_matrix_pointers.py` (new — AC4 ×3 params, AC5 ×4 params, AC7 historical-carrier + frozen + already-correct ×2) and `.claude/hooks/tests/test_agent_guide_dedup.py` (AC6 repoint). 11 tests in the new file; suite `394 → 405 passed` |
| Verification command run | ☑ pass | Supervisor re-ran it independently from the repo root, 2026-08-14: <br>`$ rm -rf .claude/hooks/tests/__pycache__ .pytest_cache`<br>`$ python -m pytest .claude/hooks/tests/ -q > /tmp/t070-full.log 2>&1; echo "SUITE exit=$?"`<br>`SUITE exit=0`<br>`405 passed in 9.54s` |
| Negative cases hold | ☑ pass | 9 mutation controls total, each confirmed landed via `git diff --stat` before its verdict and reverted with `cp`, never `git checkout`. Implementer 6: old clause re-inserted into each of the three shipping files → AC4 RED naming **only** that file (×3); `## Complexity & escalation` → `## Process depth` in `qa.md` → AC5 RED naming `qa.md`; one byte appended to `CLAUDE.md` → AC6 RED; AC4's path list typo'd → test **ERRORS on the existence check** rather than free-passing. Supervisor 3, on the Stage 4 P2 fix: legitimate later edit to `general-agent-template.md` → GREEN (the case the removed byte-pin got wrong), regression into the stale pointer → RED, matrix statement deleted from `README.md` → RED |
| verify | ☐ pass / ☐ fail / ☐ N/A | **NOT RUN — blocked, not skipped.** `Skill({ skill: "verify" })` is marked `disable-model-invocation` and is reserved for explicit user invocation, so the Supervisor cannot run it. Awaiting the user running `/verify`; this row is deliberately left unfilled rather than ticked on the strength of the other rows |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Scoped to `git diff 2baecb9..HEAD` — 6 files (3 one-line prose edits, 1 test repoint, 1 new test file, 1 review file) plus their direct consumers: the four role guides AC5 reads, and `test_memory_channel_and_budget.py`, whose `SHIPPING_FILES` includes `CLAUDE.md` (verified independently: 12 passed). No file outside the diff + consumer set reviewed |
| Full smoke suite still green (no regression) | ☑ pass | `$ bash scripts/smoke-install.sh` → `SMOKE exit=0`, `smoke-install.sh: PASS` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI component. T070 edits three markdown prose lines and two test files; the harness has no BE and no FE. The guide's UI/Design AC section was deleted at Stage 2 per Hard-Stop Gate 6 |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | As above — no rendered surface exists to comply with a design system |
| **UI: Responsiveness at target viewports** | ☑ N/A | As above — no viewport |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: T070 changes no executable code — it edits prose in three markdown files — so BEFORE is
the verbatim prior content of each line about to change, quoted from the tree at `2baecb9` (captured
2026-08-14, before any implementation commit exists on `feat/t070-impl`).

`CLAUDE.md:86`
```
- Scale process to the task's **Complexity Level (C0–C3)** — see the Complexity matrix in `.claude/agents/general-agent-template.md`. **Risk Level** separately gates `security-review`.
```

`docs/claude-md/pipeline-stages.md:118`
```
5. Assign each task three independent labels: **Complexity (C0–C3)**, **Risk (Low/Med/High)**, and **Priority (P0–P2)**. Split any task larger than C3 (an **Epic**) into smaller tasks before generating guides. (Complexity drives agent process; Risk gates `security-review`; Priority sets ordering — see the matrix in `.claude/agents/general-agent-template.md`.) When setting **Risk**, factor in whether the task touches a **hub file** — one many others depend on, so its code-dependency blast radius is large. In legacy mode this is recorded in `docs/legacy/risk-hotspots.md`; in greenfield it's a judgment call (optionally informed by a structural code-graph approach — see Stage 1). A hub touch raises Risk a level even when the edit itself is small.
```

`templates/TASK_GUIDE_template.md:18`
```
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
```

**AFTER**: the same three lines at `0d3053f`, read back from the files by the Supervisor.

`CLAUDE.md:86`
```
- Scale process to the task's **Complexity Level (C0–C3)** — see the Complexity matrix in each role guide (`.claude/agents/<role>.md`). **Risk Level** separately gates `security-review`.
```

`docs/claude-md/pipeline-stages.md:118` (pointer clause only; the hub-file, legacy-mode and Risk
remainder of the sentence is byte-identical to BEFORE)
```
… (Complexity drives agent process; Risk gates `security-review`; Priority sets ordering — see the Complexity matrix in each role guide (`.claude/agents/<role>.md`).) When setting **Risk**, …
```

`templates/TASK_GUIDE_template.md:18`
```
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in your role guide (`.claude/agents/[agent-file].md`)
```

Note the wording differs per file by design: the template addresses an implementing agent, who *has*
a role guide and already carries the `[agent-file].md` placeholder; the other two address the
Supervisor, who has none, so they name the directory. One phrasing applied to all three would repeat
the exact error T066 diagnosed.

**DELTA**: an agent or Supervisor following any of the three surviving Complexity-matrix pointers now
arrives at a file that actually contains the matrix. Before this change all three led to
`general-agent-template.md`, which T066 emptied of it — and the template one, the only one in the
**guaranteed channel** (it ships downstream via `MANIFEST:11` and is step 5 of the Mandatory Startup
block every implementing agent reads at the top of every future task), misdirected the one reader
who could not route around it.

**WITNESS**: derived from `memory/event-trace/T070.jsonl` (48 records, 2026-08-13T09:46Z →
2026-08-14T10:15Z), which per T063 holds **both** actors' calls, separable by time window — so the
implementer is not its own sole oracle here:
- **Implementer** (`common-infrastructure`, `claude-opus-5`, spawned 2026-08-14T02:54:31Z): suite runs
  at 08:33:29Z, 09:49:08Z, 09:54:18Z, 09:57:53Z and 09:59:12Z, all `is_error=false`.
- **Supervisor** (independent re-run after the Stage 4 P2 fix): 10:07:33Z (fix + its three controls),
  10:13:56Z (control sweep), 10:14:24Z (full suite `405 passed, exit=0` + `smoke-install.sh PASS`),
  all `is_error=false`.

Instrument note, recorded rather than glossed: the `Agent` record carries only
`{"resolved_model": "claude-opus-5", "status": "async_launched"}` — T061's token/duration/tool-mix
capture reads the *completion* payload, which an async launch does not deliver at PostToolUse time.
So this spawn has no cost telemetry, unlike T067's. Not a T070 defect; worth a follow-up.
