# TASK_REVIEW — T137: A backup is named after the kit version it replaces, and Update's "overwrite" takes one too

> Sibling of `tasks/TASK_GUIDE_T137.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured 2026-10-08T15:04:20Z at `792b486` (no implementation commit yet), by the
common-infrastructure sub-agent. The guide names no Demonstration command, so this script (offline
fixture kit with two commits A → B; one project Reinstalled, one Updated with `o`) is the command;
AFTER re-runs it unchanged. Run: `sh demo_t137.sh "$PWD"` from the worktree root.

<details><summary>demo_t137.sh</summary>

```sh
#!/bin/sh
# T137 demonstration: what backup does each action leave, and does the lock know the kit version?
# usage: sh demo_t137.sh <repo-root>
set -u
REPO_ROOT="$1"
. "$REPO_ROOT/tests/lib/pty.sh"
W=$(mktemp -d "${TMPDIR:-/tmp}/t137-demo.XXXXXX"); trap 'rm -rf "$W"' EXIT
K="$W/kit"; mkdir -p "$K/agents" "$K/.claude" "$K/lib"
printf 'backend v1\n' > "$K/agents/backend.md"
printf '{ "hooks": {} }\n' > "$K/.claude/settings.json"
cp "$REPO_ROOT/lib/merge-settings.py" "$K/lib/"
printf '# Claude Project Supervisor Guidelines\n' > "$K/CLAUDE.md"; printf 'LEGACY\n' > "$K/CLAUDE_LEGACY.md"
printf 'agents\n' > "$K/MANIFEST"
git -C "$K" init -q; git -C "$K" -c user.email=t@e -c user.name=t add -A; git -C "$K" -c user.email=t@e -c user.name=t commit -qm A
A=$(git -C "$K" rev-parse --short HEAD)
for p in reinstall update; do
  P="$W/$p"; mkdir -p "$P"; git -C "$P" init -q
  ( cd "$P" && SUPERVISOR_REPO="file://$K" setsid sh "$REPO_ROOT/setup.sh" </dev/null >/dev/null 2>&1 )
  printf 'MY EDIT\n' > "$P/agents/backend.md"
done
printf 'backend v2\n' > "$K/agents/backend.md"; git -C "$K" -c user.email=t@e -c user.name=t commit -qam B
echo "kit commit installed (A): $A"
echo "\$ grep kit_commit .claude/harness-lock.json   # after install at A"
grep kit_commit "$W/reinstall/.claude/harness-lock.json" || echo "(no kit_commit field)"
( cd "$W/reinstall" && SUPERVISOR_REPO="file://$K" run_in_pty '2\n\n\n\n\n' "sh '$REPO_ROOT/setup.sh'" ) > "$W/r.log" 2>&1
echo "\$ Reinstall (menu 2) -> plan line + backups left:"
grep -a 'agents/backend.md' "$W/r.log" | tr -d '\r' | grep -av 'diff\|^[-+@]' | head -3
( cd "$W/reinstall" && ls -1d agents/backend.md* )
( cd "$W/update" && SUPERVISOR_REPO="file://$K" run_in_pty '\n\no\n' "sh '$REPO_ROOT/setup.sh'" ) > "$W/u.log" 2>&1
echo "\$ Update (menu 1), answer 'o' on the edited file -> backups left:"
( cd "$W/update" && ls -1d agents/backend.md* )
echo "agents/backend.md now: $(cat "$W/update/agents/backend.md")"
grep -a 'Backed up' "$W/u.log" | tr -d '\r' || echo "(no backup line in Update output)"
```
</details>

```
captured 2026-10-08T15:04:20Z at 792b486
kit commit installed (A): 9821f53
$ grep kit_commit .claude/harness-lock.json   # after install at A
(no kit_commit field)
$ Reinstall (menu 2) -> plan line + backups left:
      agents/backend.md
Proceed? [Y/n] [warn]  Backed up your existing './agents/backend.md' to './agents/backend.md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
agents/backend.md
agents/backend.md.bak
$ Update (menu 1), answer 'o' on the edited file -> backups left:
agents/backend.md
agents/backend.md now: backend v2
  - Backed up: nothing. Update keeps your edits in place instead.
```

Absent before T137: the lock records no kit version; Reinstall's backup is a bare `.bak`; Update's
`o` replaced the user's `MY EDIT` with `backend v2` and left **no backup at all**.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
