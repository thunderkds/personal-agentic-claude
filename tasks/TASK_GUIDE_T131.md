# TASK_GUIDE — T131: The Agent focus section says "we apply A to save B"
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — static page content and drift tests; no script, no CSS change
**Priority**: P1
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `site/index.html` § `#agent-focus` (T130's section, which this task reframes) and the sources each row cites (listed in AC2)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25, on T130's "Agent focus" section: *"the mechanism do not focus on how much the token
as refactor, but we should said, we apply A for the save B, ... the example like that"*. Earlier the
same day the user asked to show how the three reference repos' ideas (headroom → input, caveman →
output, ponytail → coding) were applied.

**Restated intent:**
> The `#agent-focus` section presents each mechanism as "we apply **A** to save **B**" — what the kit
> does, and what cost or waste it avoids — with the idea's origin credited where it came from one of
> the three repos. It states purpose, not token totals.

**Out of scope:** savings figures or percentages (except the one measured fact in row 6, below); links
to the three repos (URLs not verified); copying text from them; any other section.

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's request above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-25)
- [x] Domain terms align: *memory slice*, *startup reads*, *Response Standard*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: T130 — the `#agent-focus` section this task rewrites

**Entry point**: `site/index.html` — sidebar link `#agent-focus`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | The `#agent-focus` table has three columns, headed **We apply**, **To save**, **Idea from**. The lead paragraph says in one or two sentences that each row is a mechanism and what it saves | "we apply A for the save B" |
| 2 | Six rows, in this order, worded from their sources (the draft below is the Supervisor's; tighten wording, keep meaning): (1) **Memory slice** — only the memory lines about the task's own files, capped at `MAX_LINES` lines / `MAX_CHARS` characters → saves each agent reading the whole memory index before it starts → *headroom* (`skills/craft-spawn-prompt/scripts/memory_slice.py`); (2) **Startup reads list** → saves rework from an agent that skipped the rules it must follow; the agent confirms with a `Startup reads:` line → — (`skills/craft-spawn-prompt/SKILL.md` element 8); (3) **Response Standard** — short replies, code/errors/paths/commands/security warnings verbatim, reports point to `path:line` → saves output tokens and the Supervisor carrying pasted logs for the rest of its session → *caveman* (`docs/claude-md/token-economy.md`); (4) **Over-engineering reviewer** in `code-review` → saves code nobody asked for, which someone must review and maintain → *ponytail* (`skills/code-review/SKILL.md`); (5) **Measured `compact-advisor`** → saves re-reading a long conversation on every call — the largest cost measured → — (`skills/compact-advisor/SKILL.md`); (6) **Measure before keeping** (session transcripts, DDR-0009) → saves building what doesn't pay: a headroom-style Bash-output compressor was measured at about 1% of spend and parked → — | user request |
| 3 | The audit trail staying fully detailed (T130 wording) stays in row 3 | no regression of meaning |
| 4 | Drift tests in `tests/test_site_content.py`: (i) the table's header cells are exactly the three in AC1; (ii) each of the six mechanism names appears in the section; (iii) `headroom`, `caveman`, `ponytail` each appear in the section; (iv) T130's slice-cap test still reads `MAX_LINES`/`MAX_CHARS` from source and passes; (v) no `%` sign in the section (purpose, not figures) — row 6's "about 1%" is the only exception: write it as "about 1 percent" or adjust (v) to allow exactly that one, and say which | can't rot |
| 5 | No `token_meter` mention (T130 test stays green); no external link added; no style change | T130 constraints |

---

## UI / Design Acceptance Criteria

| Check | Method | Expected |
|---|---|---|
| Visual regression | headless screenshot of `#agent-focus` at 1280, before vs after | only the section's table content changes |
| Design-system compliance | `git diff` of `<style>` | empty |
| Responsiveness | page in a 375px same-origin iframe (headless windows floor at ~500px): `scrollWidth/innerWidth` | ≤ 375, table scrolls inside `.table-wrap` |

---

## Evaluation & Acceptance

**Mutation controls:** **M1** — rename the "To save" header → (i) RED. **M2** — drop the ponytail credit → (iii) RED. **M3** — add "saves 40%" to a row → (v) RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T131.md`. BEFORE: T130's `#agent-focus` table, verbatim.

---

## Approach

**Pattern reference**: T130's tests at the end of `tests/test_site_content.py` (`_agent_focus_body`, `_slice_caps_from_source`).

**Vital slice**: AC1, AC2, AC4 (i–iii).

**Cut list**: repo links; per-row numbers; icons.

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | `#agent-focus` section only |
| `tests/test_site_content.py` | AC4 tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | Harness scope, byte-pinned |
| `memory/MEMORY.md` | Supervisor-only writes |

---

## Completion Checklist

- [ ] Implementation done; AC4 tests observed RED first
- [ ] M1–M3 pasted in `tasks/TASK_REVIEW_T131.md`
- [ ] UI Evidence rows filled with measured numbers (Hard-Stop Gate 6)
- [ ] `/verify` — user-run
