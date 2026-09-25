# 0008. Saved tool output lives inside the repo

> **What this is**: A Design Decision Record — a permanent, dated note capturing *one* design decision and the trade-off behind it.

---

**Status**: Accepted
**Date**: 2026-09-24
**Deciders**: User (project owner), over the Supervisor's recommendation
**Related**: T124 · `BRAINSTORMING_LOG_token-economy.md` · `tasks/TASK_GUIDE_T124.md` (D3, D5, D7; AC4, AC5, AC7, AC8)

---

## Context

T124 adds a PostToolUse hook that compresses Bash stdout above 200 lines before Claude reads it
(headroom's idea, built locally with `updatedToolOutput` and proven live on Claude Code 2.1.281).
Compression is only safe if it can be undone, so the hook saves the full original and prints its path
inside the compressed output. The open question was **where that copy lives**.

Gate criteria met (2 of 3):
- **Surprising without context** — the Supervisor recommended outside the repo, and a future reader
  seeing command output, which may contain secrets, written into the working tree will ask why.
- **Genuine trade-off** — both locations were viable and the user chose after a side-by-side comparison.
- *Not* hard to reverse — moving the directory is a one-constant change.

What the evaluation established before the decision:
- A saved file costs **zero context** until something reads it. Only the one-line path pointer enters
  the conversation. Location therefore affects disk, secrets and management — not tokens.
- The link to the project comes from the path printed in the compressed output, not from where the file
  sits. So an outside location does not detach the file from the project.
- **One real context risk exists only inside the repo**: shell `grep -r` from the repo root descends into
  `.claude/hooks/.state/` (measured), so saved logs would surface in later searches. The built-in Grep
  tool honours `.gitignore` and is unaffected.

---

## Decision

We will save the original output of every compressed Bash call at
`.claude/hooks/.state/output/<sanitised-session>/NNNN.log`, inside the repo, with directory mode 0700
and file mode 0600. The hook itself deletes session folders older than 24 hours on each run.
An append-only `stats.tsv` in the same folder records counts only, never command text or output.
Lines that begin with the saved-output path are removed from every Bash stdout and replaced by one
"N matches inside saved outputs hidden" line, so recursive searches do not surface old logs.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **Inside repo, `.claude/hooks/.state/output/`** | Visible and manageable next to the project; sits beside existing hook state (`step_count_*`); each sub-agent worktree keeps its own | Secrets in the working tree; commit safety rests on `.gitignore:52`; needs its own pruning; `grep -r` pollution; installer copy must be checked | **Selected** — the user preferred manageability |
| Outside repo, `${TMPDIR}/claude-output-<uid>/<project>/<session>/` (Supervisor's recommendation) | Cannot be committed; OS clears it; no `grep -r` pollution; one place for all worktrees | Less visible; lost on reboot | User preferred files inside the project folder |
| Do not save originals | Simplest; nothing on disk | Compression becomes lossy: an elided line can only be recovered by re-running the command | Rejected in grilling — reversibility is what makes compression safe |

---

## Consequences

### Positive
- Saved outputs are browsable from the project and inspectable with ordinary tools.
- Sub-agent worktrees are self-contained: removing a worktree removes its logs.
- Cleanup, stats and the path filter live in one hook with no external moving parts.

### Negative (accepted trade-offs)
- Secrets printed by commands sit in the working tree for up to 24 hours, reachable by editor search, backups and folder sync.
- "Never committed" depends on the `.gitignore` rule and on nobody running `git add -f`. A test pins the rule, but cannot stop a forced add.
- The hook carries responsibilities an outside location would not need: pruning (with symlink and scope safety) and the `grep -r` filter.
- Logs persist until the hook runs again. A project idle for a week keeps week-old logs until the next large output triggers pruning.

### Follow-up
- [ ] T124 AC8: confirm `setup.sh`'s `cp -r` (`setup.sh:674`) and `MANIFEST`'s `.claude/hooks` entry cannot ship `.state/`; add `!.claude/hooks/.state` to `MANIFEST` if they can.
- [ ] Revisit if a secret is ever found committed or synced from `.state/output/`. The move is a one-constant change to the outside-repo alternative above.
