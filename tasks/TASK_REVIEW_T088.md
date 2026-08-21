# TASK_REVIEW — T088: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T088.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_pack_docs_flags.py` — `test_every_pack_doc_flag_is_accepted_by_setup_sh` covers AC1, AC3, AC4, AC5 |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_pack_docs_flags.py -q` → `1 passed in 0.01s`. `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `5 failed, 697 passed in 9.70s` (5 failures pre-existing, unrelated — see Notes below) |
| Negative cases hold | ☑ pass | M1 (space-form regression), M2 (typo'd `--packs=`), M3 (delete `--pack=*` from `setup.sh`) all reproduced RED with the correct failing assertion, byte-change confirmed via `git diff`/`grep`, then reverted — see report below |
| verify | ☑ pass | User-run `/verify` 2026-08-21 — **pass**. Driven against **the real `setup.sh`**, not a replica: safe because `check_target_is_git_repo` runs before any file is written and before any network fetch, so from a non-git temp dir an accepted flag stops at that guard and a rejected one stops at the parser, making the two distinguishable with nothing installed. Corrected form `--pack=mobile` → past the parser, `[error] The current directory is not a git repository`, exit 1. Old documented form `--pack mobile` (two real args) → `[error] Unknown flag: --pack. Valid flags: --copy, --pack=<name>`, exit 1 — the exact hard failure every pack user was being sent into. Multi-pack `--pack=mobile --pack=api` accepted. Typo'd `--packs=mobile` rejected with the offending token named. `ls -a` after all runs: `. ..` — nothing written, nothing cloned. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed only `packs/*/PACK.md` (5 files, one-token edit each) and the new `tests/test_pack_docs_flags.py`; `setup.sh`, `site/index.html`, `README.md` read-only for reference, not edited, per Files Must NOT Touch |
| Full smoke suite still green (no regression) | ☑ pass | Baseline (pre-change, stashed): `5 failed, 696 passed` — the 5 MEMORY.md-budget failures are pre-existing (confirmed by stashing this task's diff and re-running; `memory/MEMORY.md` untouched by this task). Post-change: `5 failed, 697 passed` — same 5 pre-existing failures, +1 new passing test, 0 regressions |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | Docs + test only, no UI component (per TASK_GUIDE UI/Design AC section) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Docs + test only, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | Docs + test only, no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: The five `PACK.md` lines, verbatim, before any implementation commit:

```
packs/ai-agent/PACK.md:40:sh ~/.supervisor/setup.sh --pack ai-agent
packs/api/PACK.md:40:sh ~/.supervisor/setup.sh --pack api
packs/data/PACK.md:40:sh ~/.supervisor/setup.sh --pack data
packs/devops/PACK.md:40:sh ~/.supervisor/setup.sh --pack devops
packs/mobile/PACK.md:41:sh ~/.supervisor/setup.sh --pack mobile
```

Reproduced safely by replicating `setup.sh`'s arg loop (lines 87-90) in an isolated scratch script
(`/tmp/.../scratchpad/repro_argloop.sh`) — the real installer was never invoked:

```
2026-08-21T10:25:02Z
=== space form (as documented) ===
Unknown flag: --pack. Valid flags: --copy, --pack=<name>
exit=1
=== = form (as setup.sh actually requires) ===
OK packs: mobile
exit=0
```

Full-suite baseline captured before any implementation commit (stashed working tree, i.e. pre-change
state): `python3 -m pytest .claude/hooks/tests/ tests/ -q` → `5 failed, 696 passed in 9.91s` (696
passing, matching the 701-total-collected baseline; the 5 failures are pre-existing MEMORY.md-budget
failures unrelated to this task).

**AFTER**: All five files now read `--pack=<name>` (the `=` form `setup.sh` accepts). New test
`tests/test_pack_docs_flags.py::test_every_pack_doc_flag_is_accepted_by_setup_sh` passes:
`python3 -m pytest tests/test_pack_docs_flags.py -q` → `1 passed in 0.01s`. Full suite:
`python3 -m pytest .claude/hooks/tests/ tests/ -q` → `5 failed, 697 passed in 9.70s` (same 5
pre-existing failures, +1 new test, 0 regressions).

**DELTA**: A user following any `packs/*/PACK.md` verbatim now runs a command `setup.sh` actually
accepts (`--pack=<name>`, exit 0) instead of one it rejects (`--pack <name>`, exit 1) — and this
agreement between the two files is now enforced by an automated test that fails if it drifts again.

**WITNESS**: common-infrastructure agent, worktree `/home/hungnguyenhuu/workspace/pets/wt-t088`,
branch `fix/t088-pack-flags`, 2026-08-21 (see `memory/event-trace/T088.jsonl` if present).


---

## Stage 5 `/verify` findings (2026-08-21, user-run)

1. **⚠️ `--pack=` with an empty value is accepted silently.** It passes the parser to the git guard
   exactly like a real pack name. Pre-existing in `setup.sh`, not introduced here, and the resulting
   failure would land later and more confusingly than an upfront `pack name required`. Small, but it
   is the adjacent case nobody has run.
2. **A verification step of the Supervisor's own was invalid and was caught before reporting.** The
   first attempt passed `$f` unquoted in zsh, which does not word-split, so `--pack mobile` arrived as
   a *single* argument and the error read `Unknown flag: --pack mobile` — subtly different from what a
   user typing two arguments gets. Re-run with explicit separate args to obtain the real
   `Unknown flag: --pack`. Same class as the T083 no-op mutation: the output looked like confirmation
   and was not.
3. The `curl | sh` bootstrap path was **not** exercised — it clones from GitHub, and a network install
   was not run to verify a documentation fix. The site's `sh -c "$(curl …)" -- --pack=<name>` form is
   therefore unverified, though unchanged by this task.
4. Probe that held: the rejection message names the specific bad token, so a mistyped flag produces an
   actionable error rather than a usage wall.

## Stage 4 note

0 P0 / 0 P1 / 0 P2 / 1 P3 (noted, not fixed): `_setup_sh_invocations` treats any token after
`setup.sh` starting with `-` as a flag, including tokens inside a trailing shell comment —
`setup.sh --pack=api   # note -v for verbose` fails on the `-v`. No `PACK.md` has a trailing comment
today and the failure is loud and self-explaining, so it was left as a note rather than widening a
task whose value is the assertion itself.

All three mandatory mutation controls reproduced independently by the Supervisor with byte-changes
confirmed. **M3 is the one that mattered**: deleting the `--pack=*` case line from `setup.sh` turned
the test RED, proving AC4 — the test reads the script rather than a hardcoded constant, so it is
measuring an agreement between two files. Two further Supervisor probes: deleting an invocation line
entirely goes RED (`found 4`, so "the docs stopped documenting" cannot pass vacuously), and the
trailing-comment case above.
