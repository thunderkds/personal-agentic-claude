# TASK_GUIDE — T127: Terse but verbatim — replies and sub-agent reports keep code, errors and paths exact; review catches over-engineering
**Date**: 2026-09-25 (carried over from the 2026-09-24 T124 plan, decisions D9 and D10)
**Complexity Level**: C1
**Risk Level**: Low — instruction text and one review persona; no executable behaviour changes
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (or the memory slice in your spawn prompt, once T125 has shipped)
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-24: *"We can use the headroom for the input, ponytail for the coding, and the caveman
for the output … just investigate the idea and see what we can apply from that."* Decisions carried
over unchanged: **D9** — the Response Standard gains a verbatim-preserve rule, and sub-agent reports
point to evidence instead of pasting it; audit trail unchanged. **D10** — an `over-engineering-reviewer`
persona in `code-review`. (Headroom's idea became T124's meter and a parked hook — DDR-0009.)

No token saving is claimed for this task. Output is 15% of spend (finding doc § 1); the value is focus:
a Supervisor that receives a pointer instead of a pasted log carries less, and a paraphrased error is
a wrong error.

**Restated intent:**
> Replies stay terse without ever paraphrasing code, exact error text, file paths, commands or
> security warnings; a sub-agent's final report points to evidence by path and line instead of pasting
> logs, while the Evidence table still carries the full output; and Stage 4 review flags diffs that
> build more than the task needed.

**Out of scope:** intensity modes, a `/terse` skill, `ponytail:` comments (user rejected, 2026-09-24);
any change to Evidence, KANBAN, `memory/` or commit-message detail; copying text from the three repos.

**Requirement Refs**: no `PRD.md` — N/A. Traces to D9, D10.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (D9/D10, 2026-09-24; re-confirmed in the 2026-09-25 re-plan)
- [x] Domain terms align: *Response Standard*, *Search Before You Build*, *reviewer persona*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `CLAUDE.md` `### Response Standard`; `skills/code-review/SKILL.md` persona table

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | The Response Standard gains exactly **one** verbatim-preserve rule line, byte-identical in `CLAUDE.md` and `agents/general-agent-template.md`; `tests/test_response_standard.py` stays green with its count/wording updated from six to seven | D9 |
| 2 | New `docs/claude-md/token-economy.md`: the verbatim-preserve list (code, exact error text, file paths, commands, security warnings); sub-agent final reports **point to evidence by path:line** in `TASK_REVIEW_Txxx.md` instead of pasting logs; the Evidence table still carries full pasted output (Hard-Stop Gate 5 unchanged); and a pointer to `scripts/token_meter.py` as the way any token claim is measured (DDR-0009). `CLAUDE.md` gets one pointer line; bodies are not duplicated into `CLAUDE.md`, the template or any role guide | D9; T082 delivery pattern |
| 3 | `skills/code-review/SKILL.md` gains a conditional `over-engineering-reviewer` persona with a concrete activation condition, checking the diff for: a new abstraction with one caller, a new dependency replacing ≤ 10 lines, speculative config/flags, duplication of an existing helper or stdlib. It cites "Search Before You Build" by name and does **not** copy its rungs | D10 |
| 4 | Size budgets measured, not reframed: `test_agent_guide_dedup.py` stays green; a breached role floor is repointed for that role only, with before/after numbers | Surgical |
| 5 | No existing test modified except AC1's count/wording and any AC4 repoint, each named with its reason in the TASK_REVIEW | Surgical |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | `CLAUDE.md` + template | seven Response Standard lines, byte-identical | `tests/test_response_standard.py` |
| 2 | `CLAUDE.md` | pointer to `docs/claude-md/token-economy.md` present; the verbatim-list paragraph absent | `tests/test_token_economy_docs.py` (new) |
| 3 | `token-economy.md` | states all five verbatim items, the point-not-paste rule, "Evidence table still carries full output", and names `scripts/token_meter.py` | same |
| 4 | `code-review` SKILL | persona row with an activation condition, the four checks, "Search Before You Build", none of the rung text | same |
| 5 | Provider mirrors (`AGENTS.md`, `.cursor/rules/agent-base.mdc`) | if `tests/test_provider_adapters.py` requires the new line mirrored, it is | existing test |

**Mutation controls:** **M1** — paste the verbatim paragraph into `CLAUDE.md` → SC2 RED. **M2** — make the template line differ by one character → SC1 RED. **M3** — drop the activation condition → SC4 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_response_standard.py tests/test_token_economy_docs.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -3
sh scripts/validate.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T127.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T127.md`. BEFORE/AFTER: the Response Standard block and the persona table, verbatim.

---

## Approach

**Pattern reference**: `docs/claude-md/untrusted-content-boundary.md` + its one-line `CLAUDE.md` pointer (T082); `tests/test_response_standard.py` (byte-identity read at test time); existing conditional personas in `skills/code-review/SKILL.md`.

**Vital slice**: AC1 + AC2 (the rule reaches every agent). AC3 rides along.

**Cut list**: examples of good/bad replies; a linter for replies; per-role variants.

---

## Edge Case Checklist

- [ ] Response Standard scope sentence ("conversation only: … stay fully detailed, as the audit trail") preserved exactly
- [ ] `test_site_content.py` — does the site list personas? Add rather than weaken
- [ ] Hard-Stop Gate 5 wording untouched

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | One Response Standard line; one pointer line |
| `agents/general-agent-template.md` | The same Response Standard line |
| `docs/claude-md/token-economy.md` | **New** |
| `skills/code-review/SKILL.md` | Persona row |
| `tests/test_token_economy_docs.py` | **New** |
| `tests/test_response_standard.py` | six → seven only |
| `AGENTS.md`, `.cursor/rules/agent-base.mdc` | Only if the provider-adapter test requires |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md` | No rule bodies in role guides (T100 test) |
| `skills/craft-spawn-prompt/**`, `skills/compact-advisor/**`, `scripts/**` | T124–T126 |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: SC1–4 first. 2. Implement. 3. M1–M3 RED/GREEN pasted. 4. User-run `/verify` (or SKIP — no runtime surface; say which).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Risk Low)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T127.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M3 pasted
- [ ] UI Evidence rows: ☐ N/A — no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
