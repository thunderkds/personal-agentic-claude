# TASK_REVIEW — T133: Replies to the user read plainly — technical detail on request

> Sibling of `tasks/TASK_GUIDE_T133.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_response_standard.py` — count pins 7 -> 8 (AC1/2/5), `test_t133_plain_language_rule_is_in_both_channels` (probe read from the template, AC5). RED before the rule line landed: `4 failed, 2 passed`. Baseline repoints (AC7, only c-infra + CLAUDE.md pin, each commented T133): `.claude/hooks/tests/test_agent_guide_dedup.py`; `CLAUDE.md` line cap 200 -> 201 in `.claude/hooks/tests/test_vital_slice.py` (guide AC6 allows <=202). |
| Verification command run | ☑ pass | `python3 -m pytest tests/ .claude/hooks/tests/ -q` -> `979 passed in 12.64s` (2026-09-26). |
| Negative cases hold | ☑ pass | M1 (line deleted from `CLAUDE.md` only): `3 failed, 3 passed`, incl. `test_t103_ac1_ac4_claude_md_carries_the_six_rules_byte_identical_to_the_template` and `test_t133_plain_language_rule_is_in_both_channels`. M2 (line deleted from both): `4 failed, 2 passed`, incl. `AssertionError: the plain-language rule (probe 'the one thing to read or act on in bold') is not a Response Standard bullet in general-agent-template.md`. Files restored; `6 passed` after. M3 is a Stage 4 text check. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Stage 4 code-review (Supervisor, 2026-09-26) scoped to `e89c308..6448e96`: 6 files — `CLAUDE.md`, `agents/general-agent-template.md`, `tests/test_response_standard.py`, `.claude/hooks/tests/test_agent_guide_dedup.py`, `.claude/hooks/tests/test_vital_slice.py`, this file. Plus a repo grep for other copies of the Response Standard (`terse never means paraphrased`): none outside these two files and task records. **Result: 0 P0 / 0 P1 / 0 P2 / 2 P3.** Repoint controls re-run by the Supervisor: c-infra back on `T127_BASELINE_REF` -> `1 failed, 55 passed`; `T070_BASELINE_REF` back on `cb2163a` -> `1 failed, 55 passed` (both repoints forced, neither blanket); a stray line appended to `CLAUDE.md` under the new pins -> `2 failed, 91 passed` (pins still bite). P3a: `test_vital_slice.py` cap 200 -> 201 raises a gate's own limit, accepted — sanctioned by guide AC6 (<=202) and the cap's own comment calls it an as-of-task budget to be repointed after review. P3b: `test_t103_ac1_ac4_..._six_rules_...` name says six (stale since T127's seventh), not fixed — renaming is outside scope. Entry point `### Response Standard` present; startup reads 3/3 reported. |
| Full smoke suite still green (no regression) | ☑ pass | `979 passed` as above. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (non-executable change; verbatim prior content, captured 2026-09-26 before any implementation commit). `CLAUDE.md:26-34` and `agents/general-agent-template.md:49-61` end the Response Standard list with the seventh rule and nothing about vocabulary or highlighting:

```
### Response Standard

- Lead with the answer or verdict; method and caveats come after.
- Asking for a decision: recommendation first, alternatives one line each.
- Cut sentences restating the question or narrating what you read.
- A table only to compare on 3+ dimensions, never to lay out one thing.
- Say what is blocked and what you need, not all you could do.
- Don't re-list open items your last reply listed; point back in a line.
- Quote code, exact error text, file paths, commands and security warnings verbatim; terse never means paraphrased.
```

`CLAUDE.md` is 200 lines. `tests/test_response_standard.py` pins `== 7` rule lines (three places).

**AFTER**: both files (`CLAUDE.md:35`, `agents/general-agent-template.md:62`) gain, byte-identical, as the eighth bullet:

```
- Write for a reader who hasn't followed the project, above all when asking them to decide: plain words, a task ID or internal term gets a few words saying what it is, the one thing to read or act on in bold, technical depth only when asked.
```

`CLAUDE.md` is now 201 lines. Net growth: +1 line per file (AC6 <=4 total, <=202).

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
