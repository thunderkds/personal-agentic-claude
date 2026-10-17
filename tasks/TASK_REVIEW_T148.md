# TASK_REVIEW — T148: A rewritten event trace is detectable — hash-chained, with the chain head anchored outside the repo

> Sibling of `tasks/TASK_GUIDE_T148.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass (AC3 not covered — not implemented, see Implementation notes) | `.claude/hooks/tests/test_trace_chain.py` (new, 15 tests): AC1 `test_ac1_lines_carry_prev_and_hash_chained_from_genesis`, `test_canonical_json_ignores_key_order_and_spacing`; AC2 `test_ac2_each_append_anchors_task_line_and_hash_outside_the_root`; AC4/SC1-SC4 `test_sc1_…intact`, `test_sc2_…broken_at_that_line`, `test_sc3_…anchor_mismatch`, `test_sc4_…unanchored…`, plus deletion, forged-append, truncated-line, bad-name/missing-trace; AC6/SC5 `test_sc5_unwritable_anchor_dir_…[file]`, `[relative]`, `test_lock_failure_still_appends_and_is_marked`; AC7/SC6 `test_sc6_two_processes_fifty_appends_each_stay_intact`. Run by the implementing agent 2026-10-17T05:15:32Z: `15 passed in 3.09s` |
| Verification command run | ☐ pass / ☑ fail (5 failures, none from T148; see the smoke row) | `python3 -m pytest .claude/hooks/tests/test_trace_chain.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q` at 2026-10-17T05:15:32Z (implementing agent): first half `15 passed in 3.09s`; second half `5 failed, 1051 passed, 25 subtests passed in 25.85s` |
| Negative cases hold | ☑ pass (SC8, the live Write-to-anchor denial, not run: AC3 blocked) | SC2 `BROKEN at line 2`, SC3 `ANCHOR MISMATCH at line 2`, deleted last line `ANCHOR MISMATCH at line 3`, forged appended line `ANCHOR MISMATCH at line 3: no anchor recorded for it`. **SC7 mutation control** (2026-10-17T05:15:12Z): with `mismatched = []` replacing the anchor comparison in `scripts/verify_trace.py`, `FAILED …test_sc3_rewrite_with_whole_chain_recomputed_is_an_anchor_mismatch` / `E       assert 0 == 1` / `1 failed, 1 passed, 13 deselected`; restored → `2 passed`. The Supervisor should re-run SC7 independently |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass, no regression (the suite is not fully green) | The 5 failures are in the MEMORY.md budget tests, which T148 does not touch: `test_memory_channel_and_budget.py` (4) and `test_token_audit_format.py::test_memory_md_hot_tier_stays_within_char_budget` (`hot-tier report: 42,268 / 42,000 chars (-268 remaining)`). They fail the same way with T148's changes stashed (`5 failed, 13 passed`). AC5: `test_merge_gate_evidence.py` (`trace_shows_verification`) passes unmodified. `scripts/token_meter.py` reads Claude transcripts, not event traces, and has no change. Two schema pins changed for the new `prev`/`hash` fields: `test_post_tool_trace_spawn.py` (golden lines compared with the chain fields dropped) and `test_task_context.py::test_trace_record_schema_matches_pre_change_records`. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Pure backend: hook, script and tests only, no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Pure backend, no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | Pure backend, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-17T05:10:20Z at `364d883`, before any T148 implementation commit, in
worktree `wt-t148`. The hook was run from a scratch copy, so the real `memory/event-trace/` stayed
untouched. A trace line has no `prev`/`hash`, there is no verifier, and `.claude/settings.json` has
no deny rule:

```
$ date -u
2026-10-17T05:10:20Z
$ git rev-parse --short HEAD
364d883
$ python3 -m pytest .claude/hooks/tests/test_trace_chain.py -q
ERROR: file or directory not found: .claude/hooks/tests/test_trace_chain.py
no tests ran in 0.00s
exit=4
$ python3 scripts/verify_trace.py T148
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t148/scripts/verify_trace.py': [Errno 2] No such file or directory
exit=2
$ echo <Bash event> | CLAUDE_ACTIVE_TASK=T900 python3 <sandbox>/.claude/hooks/post_tool_trace.py; cat <sandbox>/memory/event-trace/T900.jsonl
{"timestamp": "2026-10-17T05:10:20.532873+00:00", "tool_name": "Bash", "summary": "{\"command\": \"echo hi\"}", "is_error": false}
$ grep -c permissions .claude/settings.json
0
```

**AFTER**: captured 2026-10-17T05:16:40Z at `92cdcff` (implementing agent), with the same scratch-copy
setup and `CLAUDE_TRACE_ANCHOR_DIR` set to a scratch dir:

```
$ date -u
2026-10-17T05:16:40Z
$ git rev-parse --short HEAD
92cdcff
$ python3 -m pytest .claude/hooks/tests/test_trace_chain.py -q
15 passed in 3.55s
$ (3 hook runs) cat <sandbox>/memory/event-trace/T900.jsonl | head -1
{"timestamp": "2026-10-17T05:16:44.584930+00:00", "tool_name": "Bash", "summary": "{\"command\": \"echo 1\"}", "is_error": false, "prev": "genesis", "hash": "53624c2906d0707b12bd2c853d8ec6834df63ad8dbe23ebef51361bdab356891"}
$ python3 <sandbox>/scripts/verify_trace.py T900
INTACT: lines 1-3 chained and anchored
exit=0
$ (edit line 2 summary and recompute the whole chain) python3 <sandbox>/scripts/verify_trace.py T900
ANCHOR MISMATCH at line 2: anchored hash differs
exit=1
```

**DELTA**: A user can run `python3 scripts/verify_trace.py <task>` and see when a task's trace was edited after it was written. This includes an edit that recomputes the whole in-file chain, which shows as `ANCHOR MISMATCH`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Implementation notes (implementing agent)

**AC3 blocked: it conflicts with an accepted T147 test.** `tests/test_subagent_sandbox_profile.py::test_sc5_supervisor_settings_have_no_permissions_or_sandbox`
asserts `"permissions" not in settings` for `.claude/settings.json`, and that `git diff main -- .claude/settings.json`
contains no `permissions`. That is T147's AC4: "Supervisor keeps today's permissions". Adding T148's deny rules would turn
that test red. The implementing agent did not edit another task's acceptance test. `.claude/settings.json` is unchanged.
Supervisor decision needed. Recommended: add the block below and narrow T147's test to allow a `permissions` block whose
only key is `deny`, holding only these anchor rules:

```json
"permissions": {
  "deny": [
    "Edit(~/.claude/harness-anchors/**)",
    "Bash(*harness-anchors*)"
  ]
}
```

**Assumption verified: path syntax for a `~`-rooted directory.** Source: https://code.claude.com/docs/en/permissions, fetched 2026-10-17.
- Path table, verbatim: *"`~/path` | Path from home directory | `Read(~/Documents/*.pdf)`"*.
- Also: *"To write a rule in user settings that applies inside every project, use a `//` absolute path or a `~/` home-relative path instead."*
- `Edit`, not `Write`, verbatim: *"Claude Code checks file permissions against `Edit(path)` and `Read(path)` rules only. If you write a path rule for `Write` … Claude Code accepts the rule but never consults it … Use `Edit(docs/**)` in place of `Write(docs/**)`"*.
- So `Edit(~/.claude/harness-anchors/**)` covers both Edit and Write.
- Bash, verbatim: *"Bash rules match the whole command text, with `*` standing in for any text."*

**Bash denial is pattern-based and evadable.** `Bash(*harness-anchors*)` matches only commands whose text names the directory.
For example, `d=harness; cat ~/.claude/${d}-anchors/...` or a Python one-liner that builds the path does not match. The anchor
raises the bar against an agent quietly rewriting its trace. It is not a proof. The human operator is out of scope by design.
The verifier and `lib/trace_chain.py` are repo code, so an agent could also edit them; that edit shows in the branch diff.

**Design choices:**
- Line numbers are physical lines in the `.jsonl`.
- The anchor line is written before the trace line, under the trace's exclusive lock. If the anchor write fails, the line
  gets `"anchor": "failed"` inside its hash.
- The verifier reads the trace and the anchor file under a shared lock, so an append in progress is never reported as a
  mismatch.
- A chained line with no anchor entry and no `anchor: failed` is an `ANCHOR MISMATCH`. This catches forged appends.
- Lines marked `anchor: failed` are chain-checked only. The verifier lists them in a `note:` line. Known gap: a forger could
  mark appended lines `anchor: failed`.
- `<repo-slug>` is the root directory's basename plus `-` and the first 8 hex chars of sha256(`remote.origin.url`), or
  `noremote`. Renaming or moving the checkout changes the slug, and the old anchors then report `ANCHOR MISMATCH`.
- `.claude/hooks/tests/conftest.py` (new, not in Files to Change) points `CLAUDE_TRACE_ANCHOR_DIR` at a temp dir for the
  whole hook test suite. Without it, the existing spawn and task-context tests would write anchors under the real home.
