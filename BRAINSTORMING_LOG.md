# BRAINSTORMING_LOG.md
**Generated**: 2026-07-14
**Task / Context**: New skill `craft-spawn-prompt` — auto-generate sub-agent spawn prompts from TASK_GUIDE_Txxx.md
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (bounded problem, but touches a hard-block guardrail hook's failure surface — worth the adversarial pass)

---

## The Problem Space

Spawn-prompt construction currently lives in 3 uncoordinated places (`CLAUDE.md` Stage 3, `bugfix` SKILL.md Step 4, `general-agent-template.md`'s expected-input assumptions), so the Supervisor hand-assembles prompts from memory each time — proven inconsistent this session (T018–T020 prompts were built ad hoc). A new skill should centralize this. But investigation surfaced a **live, pre-existing landmine that any design must survive**: `.claude/hooks/pre_agent_validate_guide.py` hard-blocks any `Agent()` spawn if the prompt text contains a bare `T\d+` token with no backing `tasks/TASK_GUIDE_Txxx.md` — and `memory/MEMORY.md` (mandatorily pasted into *every* spawn prompt per Stage 3) **currently contains `T013`/`T014`, which have no guide files**. This is not caused by the new skill — the very next `Agent()` call, for any task, will trip this hook right now.

**Claim verification**: confirmed via `grep -oE '\bT[0-9]+\b' memory/MEMORY.md memory/decisions.md` cross-checked against `tasks/TASK_GUIDE_*.md` on disk — `T013`/`T014` are dangling in both files, all other referenced IDs (T005, T012, T017–T020) have real guides. Also confirmed the hook's regex is `\bT(\d+)\b` scanned over the **entire prompt string** (`event.get("tool_input", {}).get("prompt", "")`), with no exemption for code fences, quoted text, or "this ID is historical, not a spawn target." Also confirmed only 2 real call sites currently construct spawn prompts (`CLAUDE.md` Stage 3, `bugfix` Step 4) — `tdd`/`migration-safety`/`to-issues` read a TASK_GUIDE but don't spawn agents themselves.

---

## Questions for the User

1. Should the fix include hardening the hook itself (so this landmine class can never recur), or should the new skill just defensively work around the current hook behavior?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Simple Path | New skill only; assembles the 5-element prompt from TASK_GUIDE + MEMORY.md as-is | Low | ~80 lines (SKILL.md) | Medium — landmine still live | |
| B | The Scalable Path | New skill + harden the hook to only match structural `TASK_GUIDE_Txxx.md` references, not bare prose `Txxx` | Medium | ~80 lines + ~15-line hook diff | Medium — touching a security-relevant hook repeats the exact "regex looked right, wasn't tested against real input" mistake from T018 | |
| C | The Minimalist Path | No new skill — just a Stage 3 checklist + one-time memory cleanup | Low | ~10 lines (doc edit) | Low, but doesn't solve the actual ask (no automation) | |
| D | The Synthesis Path | New skill, with a built-in pre-flight scan that greps the assembled prompt (incl. pasted MEMORY.md) for dangling `Txxx` tokens and flags them *before* handing back the prompt — hook stays untouched | Low-Medium | ~100 lines (SKILL.md) | Low — no changes to the hard-block hook itself | ✅ Yes |

### Option A — The Simple Path
**Approach**: `craft-spawn-prompt` reads TASK_GUIDE + agent guide + `MEMORY.md`, assembles the 5-element prompt (guide pointer, mental model/restated intent, first-action skill invocation if any, `MEMORY.md` verbatim, agent-guide pointer), hands it back as text for the Supervisor to paste into `Agent()`.
**Pros**: Minimal surface area, exactly matches "just a skill" framing from the original ask.
**Cons**: Does nothing about the landmine — the very first real spawn after this skill exists will hard-block on `T013`/`T014` inside the pasted `MEMORY.md`, undermining the whole point (a "better prompt" that gets blocked isn't better).
**Why it might fail**: Ships a skill that looks done, passes a manual demo (if that demo happens to use a MEMORY.md snapshot without dangling refs), then blocks in the very next real session once a new dangling ref appears — silent, recurring, exactly the kind of gap the user asked to rule out.

### Option B — The Scalable Path
**Approach**: Same skill as A, plus rewrite `pre_agent_validate_guide.py`'s task-ID extraction to only recognize IDs in structural markers (e.g. `TASK_GUIDE_Txxx.md` filename pattern, or a `**Task ID**: Txxx` header line) instead of any bare `\bT\d+\b` in free text.
**Pros**: Fixes the root cause permanently — no future cold-file prose (decisions.md, learnings.md, MEMORY.md) can ever trip this hook again, regardless of what generates the spawn prompt.
**Cons**: Touches a security-relevant guardrail hook. Higher blast radius than the actual ask required.
**Why it might fail**: This is structurally the same mistake T018 just made — "the fix looks right in isolation" — applied to a hook whose whole job is a hard block. A regex change here that's subtly wrong (e.g. misses a legitimate `Depends on: T005` reference) silently defeats the guardrail instead of just mis-labeling a Kanban row. Blast radius mismatch: the user asked for a prompt-crafting skill, not a hook rewrite.

### Option C — The Minimalist Path
**Approach**: Skip the new skill. Add an explicit "Spawn Prompt Checklist" to `CLAUDE.md` Stage 3 (mirroring `bugfix` Step 4's 5 elements) and do a one-time cleanup of the `T013`/`T014` mentions in `MEMORY.md`/`decisions.md`.
**Pros**: Lowest possible invasiveness; closes the immediate landmine.
**Cons**: Doesn't automate anything — the Supervisor still hand-assembles prompts from memory every time, which is the exact inconsistency this whole request was about.
**Why it might fail**: Solves today's instance of the gap but not the recurring pattern — the next time a completed task's cold-memory summary mentions its own ID (which is normal and expected, e.g. this very brainstorming's future decision entry will mention T-numbers), nothing catches it before it's pasted into a spawn prompt again.

### Option D — The Synthesis Path
**Approach**: Build `craft-spawn-prompt` per Option A, but before returning the assembled prompt, it greps the full assembled text for `\bT\d+\b` (mirroring the hook's own regex, so the check is guaranteed accurate to what will actually run), cross-checks each against `tasks/TASK_GUIDE_*.md` on disk, and either (a) if all resolve — hands the prompt back clean, or (b) if any are dangling — flags them explicitly to the Supervisor ("`MEMORY.md` contains a dangling reference to T013 with no guide file; this will hard-block the spawn — fix the memory entry or the hook will block") rather than silently handing back a prompt that's about to fail.
**Pros**: Solves the actual ask (automated, consistent prompt generation) *and* makes the landmine impossible to ship unnoticed, without touching the hard-block hook's logic at all — smallest blast radius that still closes the real gap. Self-correcting: as more cold-memory entries accumulate over the project's life, this check keeps working because it re-derives from the hook's actual regex each time, not from a snapshot of "known-bad" IDs.
**Cons**: Slightly more logic in the skill than Option A (one extra verification pass).
**Why it might fail**: If the skill's copy of the regex drifts from the hook's real regex over time (two independent copies of `\bT\d+\b`), the pre-flight check could pass something the hook then blocks anyway. Mitigate by having the skill's check documentation explicitly point at the hook file as the source of truth, and note in the skill that if the hook regex ever changes, this check must be updated in lockstep.

---

## 50% Rule Check

Could Option D be done in half the code? Yes, partially: skip the "flag it to the Supervisor" branch and just silently auto-redact any dangling `Txxx` mention in the pasted `MEMORY.md` block (e.g. `[Txxx]`) before handing back the prompt. Fewer lines, but worse: it hides the underlying data-quality problem (memory files with dangling refs) instead of surfacing it, and a Supervisor who never sees the warning won't go fix `decisions.md`/`MEMORY.md`, so the drift compounds silently across sessions. Kept the explicit-flag version — Karpathy "Ask vs. Guess" favors surfacing over silently patching.

---

## Recommended Path

**Option D — The Synthesis Path**

Closes the actual gap (consistent, automated prompt generation across all current and future spawn call sites) without repeating the T018 lesson (don't touch a hard-block security hook without exhaustive real-data testing, when a smaller-blast-radius fix achieves the same outcome). The pre-flight check is derived from the hook's real regex, so it can't silently drift out of sync with what will actually block a spawn — and it surfaces data hygiene problems (dangling memory references) instead of masking them.

Option B (hook hardening) is not rejected outright — it's a legitimate follow-up if dangling-reference false-positives become a recurring nuisance even with D's pre-flight warnings — but it's out of scope for "build a prompt-crafting skill" and should be its own separately-scoped task if pursued.

---

## Surgical Scope

Files that **should** be touched:
- `.claude/skills/craft-spawn-prompt/SKILL.md` (new) — the skill itself
- `CLAUDE.md` Stage 3 — replace the ad hoc spawn-prompt bullet with a pointer to the new skill
- `.claude/skills/bugfix/SKILL.md` Step 4 — replace the 5-element checklist restatement with a pointer to the new skill, so the two call sites can't drift again
- `memory/MEMORY.md`, `memory/decisions.md` — immediate cleanup of the `T013`/`T014` dangling references (needed regardless of which option is chosen)

Files that **must not** be touched:
- `.claude/hooks/pre_agent_validate_guide.py` — no changes under Option D; its current behavior is exactly what the skill's pre-flight check must match
- `.claude/agents/general-agent-template.md` — its expected-input contract (MEMORY.md pasted, TASK_GUIDE read, agent guide read) is already correct; the new skill must produce prompts that satisfy it, not change it

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Prompt assembled for a task whose `Depends on:` field points to a not-yet-Done task — confirm the advisory (non-blocking) warning behavior from T017 is preserved, not escalated to a block
- [ ] `MEMORY.md` or `decisions.md` contains a dangling `Txxx` reference at generation time — skill must flag it, not silently emit a prompt that will hard-block
- [ ] Task has no `Depends on`/`Entry point` section at all (older guides predating T017) — skill must not error, just skip that part of assembly
- [ ] Bugfix-flavored spawn (needs mental model + `diagnose` first-action) vs. standard Stage 3 spawn (no mental model field) — skill must detect which TASK_GUIDE shape it's reading and assemble the right prompt shape, not force bugfix's 5-element structure onto every task

---

## Next Actions

1. Immediately clean the `T013`/`T014` dangling references in `memory/MEMORY.md` and `memory/decisions.md` (do this regardless of which path is chosen — it's a live landmine today).
2. If Option D approved: draft `craft-spawn-prompt` SKILL.md via `teach`, wire the pre-flight regex check to mirror `pre_agent_validate_guide.py`'s exact pattern.
3. Update `CLAUDE.md` Stage 3 and `bugfix` Step 4 to call the new skill instead of restating the checklist inline.

---

## User Selection

> **Approved direction**: Option B — The Scalable Path (skill + harden `pre_agent_validate_guide.py` to only match structural task-ID references, not bare prose `Txxx`)
> Approved by user on 2026-07-14. User explicitly chose the higher-blast-radius root-cause fix over Option D's defensive pre-flight-only approach — hook hardening must therefore get its own regression tests against real `MEMORY.md`/`decisions.md`/TASK_GUIDE content (per the T018 lesson: a regex fix that only passes isolated-string tests is not verified) before it's considered done.
