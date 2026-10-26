# TASK_REVIEW — T174: Update can overwrite or keep all edited files in one choice, and logs every decision

> Sibling of `tasks/TASK_GUIDE_T174.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured by common-infrastructure on the base `af8f1d2` (no T174 commit yet). Scratch
project under `mktemp -d`, installed from a local `file://` kit fixture, `CLAUDE.md` and
`agents/qa.md` edited, fixture bumped, then Update run in a pty (`script -qec`) with answers
Enter (Update), Enter (Proceed), `s`, `s`. ANSI colours stripped. The plan ends in `Proceed? [Y/n]`,
each edited file gets its own `Resolve:` prompt, and no `.claude/update-log.md` is written:

```
== 2026-10-26T04:07:22Z kit=/home/hungnguyenhuu/workspace/pets/wt-t174 @ af8f1d2 fixture=12d0839


s
s
[info]  Using repo: file:///tmp/tmp.dDARtZfTLu/fixture
[info]  Fetching (shallow clone): file:///tmp/tmp.dDARtZfTLu/fixture

Easy Kit is already installed in /tmp/tmp.dDARtZfTLu/project.
  1) Update (keeps your edits)
  2) Reinstall (backs up your edits)
  3) Cancel
Choose [1]: 
Plan: Update Easy Kit in /tmp/tmp.dDARtZfTLu/project (keeps your edits)
  - Kit files you never edited are refreshed from upstream.
  - Files to add or restore: 0
  - You edited these; you will be asked about each one ([o]verwrite / [s]kip).
    [o]verwrite moves your version to <file>.bak-2b6279f first:
      agents/qa.md
      CLAUDE.md
  - Upstream no longer ships these and you never edited them; they will be removed:
      (none)
  - Upstream no longer ships these, but you edited them; they will be kept:
      (none)
  - Backed up: only a file you choose to [o]verwrite. [s]kip keeps your edit in place.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
Proceed? [Y/n] [warn]  conflict: 'agents/qa.md' has local changes since install
[info]  diff (current vs upstream) for agents/qa.md:
--- ./agents/qa.md	2026-10-26 11:07:22.790129537 +0700
+++ /tmp/harness-fetch.O5jhh8/agents/qa.md	2026-10-26 11:07:22.860529458 +0700
@@ -1,2 +1,2 @@
 agent v1
-my edit
+v2
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [info]  skipped: agents/qa.md (kept your local version)
[warn]  conflict: 'CLAUDE.md' has local changes since install
[info]  diff (current vs upstream) for CLAUDE.md:
--- ./CLAUDE.md	2026-10-26 11:07:22.790129537 +0700
+++ /tmp/harness-fetch.O5jhh8/CLAUDE.md	2026-10-26 11:07:22.860529458 +0700
@@ -1,3 +1,3 @@
 GREENFIELD RULES
 v1
-my edit
+v2
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [info]  skipped: CLAUDE.md (kept your local version)
[warn]  .claude/settings.json not found in fetched Easy Kit — hook wiring left unchanged.
[info]  Claude Code: re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
== exit: 0
== $ ls .claude/update-log.md
ls: cannot access '.claude/update-log.md': No such file or directory
== $ ls *.bak* agents/*.bak*
ls: cannot access '*.bak*': No such file or directory
ls: cannot access 'agents/*.bak*': No such file or directory
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
