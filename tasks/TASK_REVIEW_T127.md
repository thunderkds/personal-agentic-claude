# TASK_REVIEW — T127: Terse but verbatim — replies and sub-agent reports keep code, errors and paths exact; review catches over-engineering

> Sibling of `tasks/TASK_GUIDE_T127.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_token_economy_docs.py` (new: SC2, SC3, SC4); `tests/test_response_standard.py` six→seven (SC1). Targeted run: `8 passed in 0.03s` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests tests -q` → `858 passed in 11.98s`; `sh scripts/validate.sh` → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | M1 RED `test_sc2_claude_md_points_and_does_not_carry_the_body` (1 failed, 7 passed); M2 RED `test_t103_ac1_ac4_…byte_identical_to_the_template` (1 failed, 7 passed); M3 RED `test_sc4_code_review_has_the_over_engineering_persona` (1 failed, 7 passed); restored, GREEN `8 passed in 0.03s`, `git status --short` empty |
| verify | ☐ N/A | Implementer cannot run `/verify` (user-only); no runtime surface — instruction text only. Supervisor to decide SKIP or user-run |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 (2026-09-25): `git diff tokenization-refactor...docs/t127-terse-verbatim` — all 8 files read; the three repointed test pins examined line by line (below). |
| Full smoke suite still green (no regression) | ☑ pass | 858 passed (above); before the repoints it was 4 failed / 854 passed |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI component — instruction text, a doc and a skill row. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI component. |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI component. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (non-executable change; verbatim prior content, captured 2026-09-25 before any implementation commit, from `CLAUDE.md:25-33`, identical in `agents/general-agent-template.md`, and `skills/code-review/SKILL.md:57-63`):

```
### Response Standard

- Lead with the answer or verdict; method and caveats come after.
- Asking for a decision: recommendation first, alternatives one line each.
- Cut sentences restating the question or narrating what you read.
- A table only to compare on 3+ dimensions, never to lay out one thing.
- Say what is blocked and what you need, not all you could do.
- Don't re-list open items your last reply listed; point back in a line.
```

```
#### Conditional reviewers (activate based on diff content)
| Persona | Activate when diff contains… |
|---|---|
| **security-reviewer** | Auth logic, input handling, secrets, permissions, SQL/shell |
| **performance-reviewer** | DB queries, loops over large collections, cache logic, network calls |
| **migration-reviewer** | Schema changes, data migrations, seed files |
| **adversarial-reviewer** | ≥ 50 changed lines, or any security-reviewer activation |
| **api-reviewer** | Public API changes, endpoint signatures, OpenAPI/schema files |
```

`docs/claude-md/token-economy.md` and `tests/test_token_economy_docs.py`: absent.

**AFTER**: `CLAUDE.md:26-33` and `agents/general-agent-template.md` Response Standard now end with the same seventh line: `- Quote code, exact error text, file paths, commands and security warnings verbatim; terse never means paraphrased.` `CLAUDE.md:24` carries one pointer to `docs/claude-md/token-economy.md` (new). `skills/code-review/SKILL.md` gains an `over-engineering-reviewer` row with activation "Any diff that adds a new function, class, module, dependency or config option" and the four checks, citing "Search Before You Build" by name.

**DELTA**: A reply can no longer be terse at the cost of a paraphrased error or path, sub-agent reports have a rule to cite Evidence by path:line, and Stage 4 review has a persona that flags diffs building more than the task needed.

**WITNESS**: [reviewer, from `memory/event-trace/T127.jsonl`]

---

## Implementer notes (deviations from the guide, for the reviewer)

Existing tests changed beyond AC1's count/wording (AC5 asks each be named with its reason). All forced by AC1's mandatory CLAUDE.md/template edit; each follows the T082/T100/T103 repoint precedent inside the test file, assertion bodies untouched:
- `.claude/hooks/tests/test_agent_guide_dedup.py` `T070_BASELINE_REF` `b1da25a`→`998166d`: CLAUDE.md byte-identity pin is red by construction for any CLAUDE.md edit.
- Same file, AC7 `c-infra` only (AC4): 10,944 → 11,054 chars (+110); new `T127_BASELINE_REF`. backend/frontend/qa keep T066's strict floor.
- Same file, AC9 pair-size baseline `T082_BASELINE_REF`→`T127_BASELINE_REF`: backend delta +727 vs the 620-char budget, all pairs +110 from the new rule line, no table copied.
- `test_vital_slice.py` cap not touched: CLAUDE.md was already at 200/200, so the paragraph "Keep the question short and plain…" was tightened (same meaning, 4→2 lines) instead of raising the cap. The scope sentence is preserved exactly.
- `tests/test_response_standard.py` function names still say "six"; only counts/messages changed.
- `scripts/token_meter.py` does not exist in this branch (T124); `token-economy.md` names it as specified. `test_provider_adapters.py` did not require a mirror in `AGENTS.md`/`.cursor/rules/agent-base.mdc`.

## Supervisor Stage 4 (2026-09-25)

**`code-review`: 0 P0 / 1 P1 (fixed) / 1 P2 / 0 P3.** `security-review`: not required (Risk Low).

| Sev | Finding | Conf. | Outcome |
|---|---|---|---|
| P1 | To stay within CLAUDE.md's 200 lines, the self-monitoring paragraph was rewritten and **dropped the rule** "a judgment call from observed behavior, not a rigid step/token trigger" — outside T127's scope (Surgical Changes) and the premise T126 builds on | 100 | **Fixed** `05bb7fe`: clause restored in the same two lines (still 200). CLAUDE.md byte pin `T070_BASELINE_REF` repointed `998166d → 05bb7fe` in `f9862b0` (RED before: `1 failed, 55 passed`); suite `858 passed`, `validate.sh: PASS` |
| P2 | AC9 pair-size baseline repointed `T082 → T127` for **all** roles, resetting the 620-char growth budget for backend/frontend/qa too, where AC4 asked for the breached role only. The growth is one legitimate 110-char rule line per pair; backend sat at 617/620 before it | 75 | Accepted for this task (the rule must reach every role); noted so the next growth is measured from `998166d`, not T082 |

**Test pins reviewed:** (1) `T070_BASELINE_REF` CLAUDE.md byte pin — legitimate repoint, assertion
unchanged; (2) `AC7_ROLE_BASELINE["c-infra"]` → T127 — +110 chars, c-infra only, backend/frontend/qa keep
T066's strict floor ✓; (3) AC9 pair baseline — see P2. No assertion body was weakened.

**Remaining:** Stage 5 — no runtime surface (instruction text only); `/verify` expected to SKIP.
