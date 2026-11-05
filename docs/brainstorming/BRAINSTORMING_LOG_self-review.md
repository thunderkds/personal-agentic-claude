# BRAINSTORMING_LOG.md — self-review
**Generated**: 2026-11-05
**Task / Context**: Stage 0 step Direction for `docs/prd/PRD_self-review.md` (PRD gate PASS). Evidence: `experiments/self-review-spike/RESULTS.md`.
**Skill**: `Skill({ skill: "brainstorming" })` — tier **Standard**

---

## The Problem Space

Read the Stage 4 review records written since the last run, find defects recurring on >=3 tasks, and
propose <=3 kit changes the user approves — with a hard no-loop guarantee. Non-negotiable (PRD):
manual start only (FR-001); reviews-only input, never self-output (FR-002); 0 model calls when
nothing is new (FR-003); deterministic citation check (FR-004); register states open/rejected/fixed
(FR-005); cap 3 (FR-006); never edits kit files, commits to main, merges or pushes (FR-008);
deterministic parts testable without a paid model (NFR-004).

Open implementation choices: watermark/register storage, fingerprint method, miner model, spawn shape.

## Questions for the User

1. Budget enforcement (NFR-001, USD 2): an in-session `Agent` miner has no USD cap — cost is bounded
   only by input size and model. A headless `claude -p --max-budget-usd 2` child (as
   `stop_auto_verify.py:8`) enforces it hard. Which? (Decides Path B vs C.)

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Minimalist — inline | `SKILL.md` + `scripts/self_review.py` (gate/check/register). The Supervisor reads the new reviews in its own context and mines them itself. No spawn. | Low | ~250 lines + tests | Low | |
| B | Simple — script + one Agent miner | Same script, split `pre` / `post`. `pre` = watermark gate (exit 0 lines -> stop), file list (<=40 oldest-first), register. One `Agent` (sonnet) runs the spike's `MINER_PROMPT.md` and writes JSON to scratch. `post` = citation check, <3-task drop, register filter, cap 3, report, watermark advance. | Low | ~350 lines + tests | Low | ✅ Yes |
| C | Strict — headless child | As B, but `pre`/miner/`post` run in a `claude -p --max-budget-usd 2` child with `CLAUDE_SELF_REVIEW_RUN=1`, like auto verify. | Medium | ~500 lines + tests | Medium | |

**50% less code:** drop `post`'s register logic and let the miner judge duplicates (spike: 0/10
re-proposed). Rejected: the PRD's no-loop and regression rules then rest on model judgment, which
NFR-004 forbids. The deterministic script is the part that cannot be cut.

### Shared decisions (all paths)
- **Storage:** one git-tracked, human-editable file `memory/self-review/register.md`: a
  `watermark:` line (commit SHA of `main` at the last completed run) + one table row per pattern
  (`fingerprint | state | tasks | task_id | fixed_at`). The user deletes a `rejected` row to allow it
  again (FR-005). Git-tracked so it survives worktrees and shows in review.
- **Watermark:** a review file counts as new when `git log <watermark>..main -- <file>` is non-empty.
  Uncommitted review files are skipped and named in one note line.
- **Fingerprint:** miner slugs are unstable (spike: A `sibling-text-not-updated` vs B
  `stale-reference-left-after-change`). So: the miner gets the register and marks known patterns
  (semantic, spike 10/10), and `post` adds a deterministic backstop — task-set Jaccard >= 0.5 with
  a register row = same pattern. Stored fingerprint = the first slug.
- **`fixed`:** `post` reads `PROJECT_KANBAN.md`; a row whose `task_id` is Done becomes `fixed`,
  `fixed_at` = its merge commit. No manual step.
- **Miner model:** sonnet (spike: 65/65 valid citations, ~100k tokens, ~2 min).

## Adversarial Review

| Option | Why this might fail |
|--------|---------------------|
| A | First run reads up to 149 review files (~2 MB) into the Supervisor's own context — the self-monitoring rule's overwhelm case. No isolation, no budget. |
| B | No hard USD stop: a bug in `pre` that lists every file would cost several 100k tokens before anyone notices. Mitigated by the 40-file cap in `pre` (deterministic, tested). |
| C | Headless child needs `--dangerously-skip-permissions` or a permission set; more failure modes (budget stop, no output, timeout) to parse; the plugin install path must also ship the runner. Most code for a manual, user-watched command. |

## Edge Case Checklist (for every TASK_GUIDE)
1. **Second-order loop through reviews:** a fix task drafted by self-review gets its own
   TASK_REVIEW that discusses the pattern. `post` must not count a review file of a task listed in
   that pattern's register row (`task_id`) as evidence for that same pattern.
2. Run stopped between report and approvals: rows stay `open` and are never re-proposed; the next
   report lists open rows in one line each.
3. Watermark advances only after the report file is written (FR-007); a crash before = rerun is
   safe and identical in input.
4. Miner returns a quote not at the line, a non-existent file, or a task outside the input set ->
   dropped by `post`; a pattern left with <3 tasks is dropped.
5. Review text is data: an instruction inside a review file must not change miner behaviour.
6. `regressed` counts only review files whose commit is after `fixed_at`.
7. Empty register / missing register file = first run; `pre` creates nothing until `post` writes.
8. Codex 8 KB skill-body cap: keep `SKILL.md` under it (prompt lives in `references/`).

## Surgical Scope

**Should touch:** `skills/self-review/SKILL.md`, `skills/self-review/references/miner-prompt.md`,
`skills/self-review/scripts/self_review.py`, `tests/test_self_review.py` (+ fixtures),
`memory/self-review/register.md` (created by first real run, not by the task),
`skills/learn/SKILL.md` Step 8 (one rule: kit proposals belong to self-review, FR-009),
`AGENTS.md` Stage index cross-cutting list (one name), any skill-list pin the tests require
(`tests/test_plugin_names.py:648` — check at Stage 2), site skill chips if a test pins them.

**Must not touch:** any file in `.claude/hooks/` (FR-001: no hook starts it), `hooks/hooks.json`,
`.claude/settings.json`, `pre_bash_block_unsafe_merge.py` (the dead `is_error` skip is a separate
task), `memory/event-trace/`.

## Recommended Path

**Chosen: Path B — user 2026-11-05.** NFR-001 amended: 40-file cap + Sonnet instead of a USD 2 hard stop.

**B — script + one Agent miner.** It keeps every no-loop rule deterministic and tested (the
script), isolates the expensive reading in a sonnet sub-agent, and stays a small, manual,
user-watched command. C's hard budget is worth it only for unattended runs, which the PRD rules out.

## Next Actions (Stage 2)
- Split: T-a `self_review.py` + tests (pre/post, register, watermark, citation check, cap, edge
  cases 1-7) — C2 / Low; T-b `SKILL.md` + miner prompt + learn Step 8 + AGENTS.md index — C1 / Low,
  depends on T-a.
- AC for T-a must include: two runs on the same fixture -> second prints the nothing-new line, 0
  Agent spawns (fake miner call count = 0).
