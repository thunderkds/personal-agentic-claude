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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
