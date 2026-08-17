# TASK_REVIEW — T075: Decouple the hot-tier budget mutation from the live file's size, and ratchet 50,000 → 45,000

> Sibling of `tasks/TASK_GUIDE_T075.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `.claude/hooks/tests/test_memory_channel_and_budget.py` — `test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red` (rewritten, AC1/AC2/AC4), `test_ac10_turns_red_at_any_live_file_size` (new, AC3) |
| Verification command run | pass | `cd /home/hungnguyenhuu/workspace/pets/wt-t075 && python3 -m pytest .claude/hooks/tests/ -q` → `452 passed in 9.32s` |
| Negative cases hold | pass | SC6 (old size-coupled loop restored: at current live-file size + 45,000 budget the old loop still happens to breach — PASSED green, does not reproduce RED; reported to Supervisor as a discovery, see notes below), SC7 (breach assertion deleted + 1-entry stub, single non-cycling pass: `Failed: DID NOT RAISE` — RED as required, reverted, confirmed 13 passed), SC8 (deleted one Simplicity First line from `.claude/agents/backend.md`: `test_ac8` went RED — `{'If 200 lines can be 50, rewrite': 2, 'If 200 lines can be 50, write 50': 1}` — reverted, confirmed 1 passed) |
| verify | N/A | not run by qa-expert per project convention (verify is user-only); Supervisor/user to run `/verify` at Stage 5 |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Reviewed: `.claude/hooks/tests/test_memory_channel_and_budget.py`, `.claude/hooks/tests/test_token_audit_format.py`, `.claude/hooks/tests/test_vital_slice.py`, `memory/MEMORY.md` (header line only), `setup.sh` (seeded stub line only) — the exact set touched, both directly and by the AC5 ratchet's two-module import. `assert_hot_tier_within_budget`/`measure_hot_tier` (off-limits) confirmed untouched by diff. Skipped: rest of the 451-test suite beyond confirming it stays green, since `HOT_TIER_CHAR_BUDGET` fans out no further than the two modules already reviewed |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest .claude/hooks/tests/ -q` → `452 passed in 9.32s` (451 baseline +1 for AC3's new test; AC16 removed an assertion, not a test) |
| **UI: Visual regression (diff or verdict pasted)** | N/A | pure test-infrastructure task, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | pure test-infrastructure task, no UI component |
| **UI: Responsiveness at target viewports** | N/A | pure test-infrastructure task, no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-08-17T08:45:27Z, before any implementation commit, by qa-expert
(QA-Automation-Agent), in worktree `/home/hungnguyenhuu/workspace/pets/wt-t075`:

```
$ cd /home/hungnguyenhuu/workspace/pets/wt-t075 && date -u +%Y-%m-%dT%H:%M:%SZ && \
  python3 -m pytest .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red -v
2026-08-17T08:45:27Z
...
        # The NEW gate is red, and says something actionable (AC2).
>       with pytest.raises(AssertionError) as exc:
E       Failed: DID NOT RAISE <class 'AssertionError'>

.claude/hooks/tests/test_memory_channel_and_budget.py:266: Failed
=========================== short test summary info ============================
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red
============================== 1 failed in 0.04s ===============================
```

**AFTER**: captured 2026-08-17T08:56:14Z, after the Stage 2 amendment (AC15/AC16/SC8) was applied,
by qa-expert (QA-Automation-Agent), in worktree `/home/hungnguyenhuu/workspace/pets/wt-t075`:

```
$ cd /home/hungnguyenhuu/workspace/pets/wt-t075 && date -u +%Y-%m-%dT%H:%M:%SZ && \
  python3 -m pytest .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red -v
2026-08-17T08:56:14Z
.claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red PASSED [100%]
============================== 1 passed in 0.02s ===============================
```

Full suite: `452 passed` (see Evidence table).

**DELTA**: `test_ac10` now constructs its own budget breach unconditionally (cycling the padding
loop over existing entry lines, independent of the live file's distance to the cap) and asserts the
breach actually happened before expecting the gate to fire — so the gate that the `/compact-memory`
tool exists to keep honest can no longer be silently disarmed by that same tool doing its job. The
ratchet is banked (`HOT_TIER_CHAR_BUDGET` 50,000 → 45,000, both `memory/MEMORY.md`'s header and
`setup.sh`'s seeded stub updated to match, ratchet sentence byte-identical in both), and the
scope-guard byte-identity pin in `test_vital_slice.py::test_ac8` — which made this fix structurally
impossible to land — is removed while its content assertion stays.

**WITNESS**: qa-expert (QA-Automation-Agent), 2026-08-17, this worktree. Two Stage-2 defects found
during implementation (the AC5/Must-Not-Touch contradiction, and the unsatisfiable byte-identity pin
in `test_vital_slice.py`) were reported and ruled on by the Supervisor before this AFTER capture —
see commit `4789377` (Stage 2 amendment) and the qa-expert report preceding it.
