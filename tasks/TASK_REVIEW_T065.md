# TASK_REVIEW — T065: Make the memory channel honest and the size gate measure what it costs

> Sibling of `tasks/TASK_GUIDE_T065.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_memory_channel_and_budget.py` (12 new tests: AC3, AC4, AC5/AC6, AC7, AC8, AC9 ×2, AC10, AC11, AC12, SC1, anti-vacuity guard) and `.claude/hooks/tests/test_token_audit_format.py` (`test_memory_md_hot_tier_stays_within_char_budget`, replacing `test_memory_md_hot_tier_stays_within_line_limit`) |
| Verification command run | ☑ pass | `pytest .claude/hooks/tests/ -q` → `338 passed in 7.90s`; `bash scripts/smoke-install.sh` → `smoke-install.sh: PASS` (all 15 installed-artifact assertions `[ok]`) |
| Negative cases hold | ☑ pass | 5 mutation controls, each confirmed to have **landed** (grep count / boolean printed) before the run and reverted after. M1 AC7 — reintroduced `Injected in full into every sub-agent spawn prompt` → RED. M2 AC9 — reintroduced `under 200 lines` → RED. M2b AC9 anti-count-allowance — added a **real** cap line to `CLAUDE.md`, the one file with a legitimately-excluded `200 lines` hit, and the Simplicity-First line still present → RED (proves the exclusion is by content, not by an allowance of one hit). M3 — reverted the gate to line-based → AC10 RED **and** AC11 RED. Post-revert: `338 passed`, `git status` clean of mutations. **Supervisor's own independent control (the implementer was not the sole oracle)**: on a copy of the live file, appended 400 chars to each of 10 index entries — `49,451 → 53,461` chars with a **line delta of exactly 0**, asserted before trusting the verdict. New gate went **RED** naming chars/budget/overage; the old `len(lines) <= 200` assertion is structurally blind to that mutation, which is the entire defect |
| verify | ☑ pass | `Skill()` is not available to this sub-agent (tools are Read/Write/Edit/Bash only), so `verify` was run manually and is labelled as such: the full verification command was re-run after the final edit, the AC10 defect was reproduced end-to-end on a copy against both the old and new gate (Demonstration below), and the live budget was measured at 49,451 / 52,000 — **pass** |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 16 changed files plus every location the AC9/AC7 sweep enumerates (23 shipping files). Skipped with reason: `memory/decisions.md` / `learnings.md` / `glossary.md` (cold tier, Supervisor-only), `docs/memory-usage-finding-2026-08-07.md` and `docs/ddr/*` (dated historical records), `PROJECT_KANBAN.md` / `BRAINSTORMING_LOG.md` / `tasks/*` (they quote the old rule as description), `.claude/hooks/tests/*` other than the two above (they carry the old prompt shape as fixture data and recorded rationale) |
| Full smoke suite still green (no regression) | ☑ pass | 338 passed (326 pre-existing, all previously green, none modified to pass) + `smoke-install.sh: PASS` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure-backend/docs task — no UI component. The guide's Completion Checklist marks this row N/A explicitly |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | As above — nothing rendered |
| **UI: Responsiveness at target viewports** | ☑ N/A | As above — nothing rendered |

### security-review (Medium risk — mandatory)

**PASS, 0 actionable.** Run by the **Supervisor at Stage 4**, not the implementer: the sub-agent
correctly reported it could not run `Skill()` at all (its tools are Read/Write/Edit/Bash) and
declined to claim a skill run it had not performed.

Run **manually and labelled** — this is the ninth occurrence of the recorded failure mode where the
built-in diffs the *checked-out* branch (`feat/t059-…`) rather than the work branch (`t065-work`),
which would have returned a false PASS on a mandatory gate.

Surface assessed against the real diff:
- Every change is prose or documentation except one test assertion. The two hook edits
  (`post_bash_memory_update.py`, `post_agent_move_to_review.py`) are **comment/docstring text only** —
  no executable line changed.
- `git diff | grep '^+'` for `subprocess|os.system|eval(|exec(|urllib|requests|socket|chmod|rm -rf`
  returns **0** hits. No new input, filesystem-write, or network surface.
- `setup.sh`'s seeded stub is the one place where new text enters a shell context. The heredoc is
  still `<<'EOF'` (quoted), and the new text introduces backticks (`` `/compact-memory` ``) which
  would be command substitution in an *unquoted* heredoc. Verified empirically rather than by
  inspection: ran `scaffold_project` into a temp dir and confirmed the backticks render literally.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**:

Captured 2026-08-09T12:40:13Z, at `HEAD = 8bd9b17` (Stage 2 guide commit — no implementation commit
exists on `t065-work` at this point). This is the AC10 contrast: the defect, live.

A **copy** of `memory/MEMORY.md` in a scratch dir (the real file is never written by any step here)
had ~4,000 characters appended **onto existing entry lines**, so not one line was added:

```
$ python3 - "$D/MEMORY.md"   # appends a 78-char clause to existing "- [" entry lines only
lines 199 -> 199  (delta 0)
chars 49156 -> 53212  (delta +4056)
```

The shipping gate, copied **verbatim** from `.claude/hooks/tests/test_token_audit_format.py:63-66`
and pointed at that mutated copy:

```python
def test_memory_md_hot_tier_stays_within_line_limit():
    memory_path = Path(__file__).resolve().parents[3] / "memory" / "MEMORY.md"
    lines = memory_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200
```

```
$ date -u '+BEFORE captured %Y-%m-%dT%H:%M:%SZ'
BEFORE captured 2026-08-09T12:40:13Z
$ git log -1 --format='HEAD at capture: %h %s'
HEAD at capture: 8bd9b17 docs(T065): Stage 2 guide — honest memory channel + a size gate that measures cost
$ python3 -m pytest "$D/t/a/b/c/test_old_cap.py" -q
.                                                                        [100%]
1 passed in 0.00s
```

**A file that just grew by 4,056 characters is GREEN.** The gate measures a quantity that was pinned
at 199–201 across the last 12 commits while the quantity that maps to cost rose 15.5%.

Fiction 1's prior content, quoted verbatim from the files as they exist at `8bd9b17`:

- `.claude/skills/craft-spawn-prompt/SKILL.md:33`
  `| 4 | Memory injection | Full contents of `memory/MEMORY.md`, verbatim | same |`
- `docs/claude-md/pipeline-stages.md:155` (the load-bearing one, AC6)
  `- **Memory injection**: Always paste the full contents of `memory/MEMORY.md` verbatim into every sub-agent spawn prompt, after the task pointer. This is the hot-tier memory index (≤200 lines) — the agent must not re-read it; it is already in context.`
- `memory/MEMORY.md:3-4`
  `> **Rules**: Supervisor-only writes. Max 200 lines. One-line summaries + links to cold files.`
  `> Injected in full into every sub-agent spawn prompt.`

The spawn prompt that produced this document handed a **path** and said "read `memory/MEMORY.md` in
full" — first-person evidence, and the third independent confirmation after T063's corpus and T064.

**AFTER**:

Captured 2026-08-09T12:50:03Z at `HEAD = 6ecc4a4`. **The identical mutation, on a copy of the
post-change file**: ~4,000 characters appended onto existing entries, zero lines added.

```
$ python3 - "$D/MEMORY.md"   # same padding script as the BEFORE capture
lines 202 -> 202  (delta 0)
chars 49451 -> 53507  (delta +4056)
NEW GATE: AssertionError: MEMORY.md is 53,507 characters, over the 52,000-character
hot-tier budget by 1,507. Run `/compact-memory` to shrink the file — do NOT raise
HOT_TIER_CHAR_BUDGET, it is a ratchet that only ever goes down.
$ date -u '+AFTER captured %Y-%m-%dT%H:%M:%SZ'
AFTER captured 2026-08-09T12:50:03Z
```

The message names the current size, the budget and the overage (AC2), and it names the only
sanctioned remedy — because the temptation the old cap died of was to edit the number.

Fiction 1's new content, verbatim:

- `.claude/skills/craft-spawn-prompt/SKILL.md:33`
  `| 4 | Memory reference | The **path** `memory/MEMORY.md`, with an instruction to read it in full. Do **not** paste its contents | same |`
- `docs/claude-md/pipeline-stages.md:155` (AC6 — the sentence is inverted, not merely deleted)
  `- **Memory injection**: Pass the **path** `memory/MEMORY.md` in every sub-agent spawn prompt, after the task pointer, with an instruction to read it in full. Do **not** paste its contents. This is the hot-tier memory index (≤52,000 characters) — **the agent must read it itself** as a mandatory startup step, so the cost is paid once, by the agents that need it, rather than on every spawn.`
- `.claude/agents/general-agent-template.md:11` — a **second** copy of the harmful sentence, outside
  the guide's predicted eight locations, found by AC9's sweep:
  `2. Load the hot-tier memory index — **read `memory/MEMORY.md` yourself**. The spawn prompt gives you its path, not its contents, so nothing loads it for you.`
- `memory/MEMORY.md:3-5`
  `> **Rules**: Supervisor-only writes. Max 52,000 characters — a ratchet: `/compact-memory` may lower`
  `> it, never raise it to fit growth. One-line summaries + links to cold files.`
  `> Passed to every sub-agent as a path to read; the contents are not pasted into the spawn prompt.`

**DELTA**: A Supervisor can no longer grow `memory/MEMORY.md` past its cost budget while the suite
stays green — the gate now measures characters, refuses a 4,056-character increase that added no
lines, and tells the reader to compact the file rather than raise the number; and an agent that
follows the documented startup sequence now actually reads memory instead of being told it is
already in context when it is not.

**WITNESS**: [to be filled at Stage 4/5 from `memory/event-trace/T065.jsonl` — not by the
implementing agent alone. The active-task pointer was armed at 2026-08-09T12:38:48Z, before any
test or verification command, so the runs above are attributable.]
