# TASK_REVIEW — T122: CI goes green — validate.sh reads MANIFEST's `!` exclusions as paths

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | Implementer: `tests/test_manifest_exclusions.sh` (new, wired in `.github/workflows/ci.yml` as "MANIFEST exclusions test suite (T122)"). SC1=AC1, SC2=AC2, SC3=AC3, SC4=guide SC4, SC5=`harness_manifest_dest` (AC5). Run at `ffb2a9c`/`8d64849`: `----- summary: 8 passed, 0 failed -----`. Red before the fix (4 passed, 4 failed: sc1, sc2 `!`-reported, sc4, sc5). |
| Verification command run | ☐ pass / ☐ fail | Implementer, 2026-09-23T08:23:33Z at `ffb2a9c`: `validate.sh` exit=0, 0 FAIL lines, `validate.sh: PASS`; `test_manifest_exclusions.sh` 8/0; `test_ci_wires_shell_suites.py` 4/0; `test_setup.sh` 18/0; `test_update.sh` 31/0; `test_harness_projection.sh` 41/0; `shellcheck -x scripts/validate.sh lib/harness-fetch.sh` rc=0 (0.11.0); new suite shellchecks clean after `8d64849`. |
| Negative cases hold | ☐ pass / ☐ fail | Implementer mutation controls, each run against the committed fix and restored from a scratch copy (`git status` clean after): **M1** validate.sh filter back to `(#\|$)` → sc1, sc2, sc4 FAIL (5/3). **M2** `AGENTS.md` moved off disk → sc1, sc2 (`'AGENTS.md' not reported [ok]`), sc4 FAIL (5/3) — note M2 as the guide words it turns the AC1/AC2 cases red, not SC3, since SC3 adds its own missing path. **M3** (added, proves SC3): missing entries reported `ok` instead of `err` → sc3 FAIL (7/1). **M4** `harness_manifest_dest` filter back to `(#\|$)` → sc5 FAIL (7/1). A first M1 attempt via `sed` did not land (no diff) and read 8/0; it was re-run with a verified edit — the result above is the verified run. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | Implementer, at `ffb2a9c`: `smoke-install.sh` PASS; `test_t098_harness_presence` 20/0 (exercises `resolve_projection_harnesses` → `harness_manifest_dest`); `test_update_removals` 30/0; `test_harness_fetch` 9/0; `test_one_command_menu` 22/0; `test_install_update_smoke` 9/0; `test_shellcheck_clean` PASS; CI's own shellcheck line rc=0. pytest was not run — out of scope per the guide. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | Implementer: no UI component — shell/CI only. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | Implementer: no UI component — shell/CI only. |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | Implementer: no UI component — shell/CI only. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Implementer: captured 2026-09-23T08:20:50Z on `fix/t122-validate-exclusions` at
`04d0ab7`, before any implementation commit. `sh scripts/validate.sh; echo "exit=$?"` (MANIFEST
section and result line shown; the one other `FAIL`-matching line in the full output is the final
`validate.sh: FAIL` — every other section is `[ok]`):

```
== MANIFEST entries resolve on disk ==
  [ok]   agents
  [ok]   skills
  [ok]   .claude/hooks
  [ok]   templates
  [ok]   docs/claude-md
  [ok]   AGENTS.md
  [ok]   .cursor/rules
  [FAIL] MANIFEST entry not found: !.claude/hooks/tests
...
validate.sh: FAIL
exit=1
```

**AFTER**: Implementer: 2026-09-23T08:23:33Z at `ffb2a9c`, `sh scripts/validate.sh; echo "exit=$?"`
(MANIFEST section and result line; the full output has 0 lines matching `FAIL`):

```
== MANIFEST entries resolve on disk ==
  [ok]   agents
  [ok]   skills
  [ok]   .claude/hooks
  [ok]   templates
  [ok]   docs/claude-md
  [ok]   AGENTS.md
  [ok]   .cursor/rules
...
validate.sh: PASS
exit=0
```

**DELTA**: A maintainer can merge to `main` with CI's `Validate framework integrity` step green
again. The MANIFEST `!` exclusion no longer reads as a missing path, and a truly missing entry
still fails the step.

---

## Implementer notes — MANIFEST reader survey (AC5)

Survey method: `grep -rnE "MANIFEST|manifest"` over `setup.sh update.sh lib/ scripts/ .github/`,
then every call site of `harness_manifest_path` / `harness_manifest_dest`, plus the test-side
readers of the real MANIFEST. **I agree with the Supervisor's table on four of five rows. The fifth
row's premise was wrong.**

| Reader | Verdict |
|---|---|
| `lib/harness-fetch.sh:285` `harness_manifest_path` | confirmed correct — `(#\|$\|!)` |
| `lib/harness-fetch.sh:292` `harness_manifest_exclusions` | confirmed correct — consumes `!` |
| `setup.sh:837` plan "Copies in" | confirmed correct — `grep -v '^[[:space:]]*[#!]'` |
| `scripts/validate.sh:32` | **fixed** — `(#\|$)` → `(#\|$\|!)` |
| `lib/harness-fetch.sh:310` `harness_manifest_dest` | **fixed** — see below |

Readers not in the table, all checked: `setup.sh:557,821`, `lib/harness-fetch.sh:143,391`,
`lib/harness-update.sh:57,94,120,357,369` all go through `harness_manifest_path` (correct).
Test-side readers `tests/test_install_update_smoke.sh:95` and `tests/test_update_removals.sh:204`
already filter `(#|$|!)`. `tests/test_provider_adapters.py:184` checks list membership only, so an
extra `!` line cannot break it.

**`harness_manifest_dest` verdict: it had a live, unfiltered caller. Fixed.** It has two call sites:
- `lib/harness-fetch.sh:393` (`harness_project_manifest`) is safe: `harness_manifest_path` returns
  empty on a `!` line and the loop `continue`s before calling it.
- `lib/harness-update.sh:506` (`resolve_projection_harnesses`, also reached from `setup.sh`
  `default_clis` on Reinstall) is **not** filtered. It reads raw MANIFEST lines and hands each one
  to `harness_manifest_dest`. Before the fix, `harness_manifest_dest '!skills codex=.codex/skills'
  codex` returned `.codex/skills` (the pre-fix red run of SC5 shows it). So a `!<path>
  <cli>=<dest>` line would count toward "this CLI is present", while `harness_project_manifest`
  would never project it. That is the same syntax-reached-some-consumers defect.
  Today's MANIFEST has no `!` line carrying a pair, so nothing misbehaves now; the next such line
  would. It is a one-token fix in the Files-You-May-Touch list, pinned by SC5 and by mutation M4.

**Registered out of scope, not built:** wiring pytest into CI (the guide's named T109 follow-up).
It is still open, and the Supervisor should give it its own board row. I cannot edit
`PROJECT_KANBAN.md`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
