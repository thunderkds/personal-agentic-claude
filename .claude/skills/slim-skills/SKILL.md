---
name: slim-skills
description: Audit and prune bloated SKILL.md files — scan all skills for line count, extract behavioral checksums, propose trimmed versions, show diff, gate on human approval. Never auto-saves.
disable-model-invocation: true
---

## Role: Skill Pruner

Audits every SKILL.md in `.claude/skills/`, identifies bloated files, extracts behavioral checksums (hard constraints, never-do rules, output assertions), proposes a pruned version, and presents a diff for human approval before any write.

**Prune** = reduce tokens while leaving every behavioral assertion intact.

### Karpathy Overrides
- **Ask vs. Guess**: If a constraint is ambiguous (could be essential or redundant), keep it — flag it in the diff for human judgment. Never silently drop.
- **Surgical Changes**: Touch only lines that are redundant, over-explained, or duplicate. Match existing formatting exactly.
- **Goal-Driven Execution**: Success = diff shown, human approves, file saved with zero behavioral assertions lost.

---

### Step 1 — Scan & Rank

Run `wc -l .claude/skills/*/SKILL.md` and sort descending. Flag all files **> 150 lines** as candidates.

Emit a ranked table:

| Skill | Lines | Status |
|---|---|---|
| learn | 182 | 🔴 Candidate |
| map-codebase | 165 | 🔴 Candidate |
| ... | ... | ✅ OK |

**Completion criterion**: every SKILL.md listed; candidates flagged; table emitted.

---

### Step 2 — Extract Behavioral Checksum

For each candidate, read the file and extract every line matching these patterns:
- Explicit output assertions: "must emit", "always output", "emit X before Y"
- Hard constraints: "never", "must not", "prohibited", "mandatory", "hard stop"
- Completion criteria lines (lines after "Completion criterion:")
- Communication Protocol notification lines

Emit the checksum as a numbered list per skill. This list is the **preservation contract** — every item must survive pruning.

**Completion criterion**: checksum list emitted for each candidate; zero inferred items (only explicit text from the file).

---

### Step 3 — Propose Pruned Version

For each candidate, produce a pruned version applying these cuts in order:
1. Remove sentences that restate what the skill name already says
2. Collapse redundant edge-case rows in tables (same rule, different wording)
3. Trim Karpathy blocks to ≤3 overrides — drop items that repeat the general-agent-template rule verbatim
4. Shorten over-explained steps to their completion criterion + one imperative sentence
5. Never cut: checksum items, step headers, completion criteria, communication protocol

Target: ≤ 120 lines. If target unreachable without cutting checksum items, stop at the safe floor and note it.

**Completion criterion**: pruned version produced; line count at or below target (or safe-floor noted); zero checksum items missing from pruned version.

---

### Step 4 — Diff & Approval Gate

Show a fenced diff block (unified format) for each candidate. Then ask:

> "Review the diff above. Reply **approve [skill-name]** to save, **skip [skill-name]** to leave unchanged, or **edit [skill-name]** to adjust before saving."

**Do not write any file until the user explicitly approves it.**

For each approved skill: write the pruned content to `.claude/skills/<name>/SKILL.md`.
For each skipped skill: leave file unchanged, note it.
For each edit request: apply the requested change, re-show the diff, wait for re-approval.

**Completion criterion**: every candidate has a user decision (approve/skip/edit); approved files written; skipped files untouched; no file written without explicit approval.

---

### Step 5 — Checksum Verification

After each write, re-read the saved file and verify every item from Step 2's checksum is present.
If any item is missing: revert to original immediately, report which item was lost, and ask the user to resolve manually.

**Completion criterion**: all approved files pass checksum verification; any failure triggers immediate revert and explicit report.

---

### Communication Protocol
- **Default Notification**: "slim-skills complete. Scanned [N] skills. Candidates: [N]. Approved: [N] pruned ([avg% reduction]). Skipped: [N]. Checksum violations: [N] (reverted)."
