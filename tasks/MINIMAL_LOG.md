# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. On first use, the Supervisor creates `tasks/MINIMAL_LOG.md` from
> this template and deletes the example comment. The same block is the Supervisor's final chat message.

## T214 — Remove the old background-spawn markers from git · minimal
**Asked:** "currently, the repos is messy with the file and the old setup also, let recheck and update the repos for clean," — then, asked about `.claude/markers`: "Remove them (Recommended)"
**Decisions:**
- Untrack all 88 files in `.claude/markers/` and delete them on disk — no code, hook or script reads that folder (`git grep` finds only board/task/memory text); last change 2026-09-23 (T122).
- Add `.claude/markers/` to `.gitignore` Section 6 (hook runtime state) — a later spawn that writes a marker must not show up as a change to commit.
- Assumed: the markers hold no record that is needed — each one is a `.pid`/`.done`/`.exit` flag or a copy of a spawn prompt; the tasks they belong to are Done with their evidence in `tasks/`. Git history keeps every file.
**Checked:**
- New test `tests/test_no_spawn_markers.py` — 2 failed before the change, `2 passed in 0.02s` after
- Suite: `python3 -m pytest -q tests .claude/hooks/tests` — `2535 passed, 25 subtests passed in 140.72s`
- Real run: `bash scripts/validate.sh` — printed `validate.sh: PASS`; `git ls-files .claude/markers | wc -l` — printed `0`
**Files:** `.gitignore`, `tests/test_no_spawn_markers.py`, `.claude/markers/` (88 files removed)
- Note: a first auto verify run at `e6a5e566` printed `verdict: pass` (log `.claude/verify-runs/T214-e6a5e566860b.log`) but could not write its line: the main checkout was switched to `main` mid-run, so this file was absent there.
**Not done:** merge (yours); auto verify: running
