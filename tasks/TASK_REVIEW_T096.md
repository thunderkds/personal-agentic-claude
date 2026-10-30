# TASK_REVIEW — T096 (B1): Relocate canonical `skills/` and `agents/` to plain root

**Task ID**: T096
**Branch**: `feat/t096-canon-plain-root`
**Agent**: Common-Infrastructure-Agent
**Guide**: `tasks/TASK_GUIDE_T096.md`
**Date**: 2026-08-28

---

## Guide defects found at intake (reported to Supervisor, work proceeded)

Recorded here because the guide's Requirement Fidelity Gate asserts facts that do not hold
against this tree. Neither defect changes the live surface being modified.

### D1 — `DDR-0007` does not exist

Mandatory Startup step 6 requires reading
`docs/ddr/0007-canonical-skills-and-agents-at-plain-root.md` **in full**, calling it "the decision
this task implements". The Fidelity Gate ticks "Requirement Refs resolve: `DDR-0007` exists on
disk". It does not exist — not in the worktree, and not on any local or remote branch:

```
$ ls docs/ddr/
0001-measure-first-token-refactor.md
0002-retire-measure-first-token-instrument.md
0003-demonstration-block-and-delivery-report.md
0004-uphold-hard-stop-gate-1-over-spawn-elimination.md
0005-vital-slice-extends-simplicity-first.md
0006-provider-adapters-inline-non-negotiables.md

$ git log --all --oneline --diff-filter=A -- 'docs/ddr/0007*' 'BRAINSTORMING_LOG_harness*'
(no output)
```

`docs/brainstorming/BRAINSTORMING_LOG_harness-kit-portability.md`, cited in Requirement Refs, is likewise absent.

**Why work proceeded anyway**: the guide restates the prohibition inline in full — the
live/historical split, the `sed`/`xargs`/`find -exec` ban, the `memory/codebase-map.md`
regeneration exception, and the relative-symlink requirement. The task boundary is fully
determinable from the guide alone, so the missing DDR blocks provenance, not execution.

**Recommended follow-up**: write DDR-0007 retroactively, or correct the guide's Requirement Refs.

### D2 — The historical baseline of 1,764 is wrong; the real number is 909

The guide's AC4 fixes the historical count at 1,764 and breaks it down as memory/ 1013,
tasks/ 707, PROJECT_KANBAN.md 22, reports/ 18, ddr+adr 4, BRAINSTORMING_LOG 3. Re-running the
guide's own count command gives **909**, and the per-directory breakdown diverges sharply:

| Directory | Guide claims | Actually measured |
|---|---|---|
| `memory/` | 1013 | 128 |
| `tasks/` | 707 | 736 |
| `PROJECT_KANBAN.md` | 22 | 22 |
| `reports/` | 18 | **0** (directory is empty) |
| `docs/ddr/` + `docs/adr/` | 4 | 4 |
| `BRAINSTORMING_LOG_*.md` | 3 | 21 (4 logs, not 1) |
| **Total** | **1,764** | **909** |

The guide's figures were derived against a different tree state. AC4's intent — *the historical
audit trail must be byte-identical after the move* — is unaffected; only its literal constant is
stale. **AC4 is therefore evaluated as "unchanged from the measured BEFORE value of 909".**

Note the live-surface count, which is the guide's own designated halt trigger
(Success Criteria #1: "If your count differs from 49, stop and report"), matches the guide
**exactly** at 49 files / 225 refs. The scope of what gets rewritten is confirmed unchanged.

---

## BEFORE

Captured on `feat/t096-canon-plain-root` at `695f5d8`, prior to any modification.

### Live surface — 49 files / 225 references

```
$ grep -rIl '\.claude/\(skills\|agents\)' --exclude-dir=.git --exclude-dir=__pycache__ \
    .claude/hooks .claude/skills .claude/agents docs/claude-md tests scripts lib templates \
    CLAUDE.md CLAUDE_LEGACY.md AGENTS.md MANIFEST setup.sh update.sh .cursor 2>/dev/null \
    | sort -u | wc -l
49

$ grep -rIo '\.claude/\(skills\|agents\)' --exclude-dir=.git --exclude-dir=__pycache__ \
    .claude/hooks .claude/skills .claude/agents docs/claude-md tests scripts lib templates \
    CLAUDE.md CLAUDE_LEGACY.md AGENTS.md MANIFEST setup.sh update.sh .cursor 2>/dev/null | wc -l
225
```

Per-file reference counts (the rewrite worklist):

```
AGENTS.md:1
.claude/agents/backend.md:1
.claude/agents/common-infrastructure.md:1
.claude/agents/frontend.md:1
.claude/agents/general-agent-template.md:1
.claude/agents/qa.md:1
.claude/hooks/lib/guide_sections.py:1
.claude/hooks/tests/test_agent_guide_dedup.py:12
.claude/hooks/tests/test_bugfix_evidence_parity.py:1
.claude/hooks/tests/test_complexity_matrix_pointers.py:8
.claude/hooks/tests/test_diagnose_evidence_loop.py:1
.claude/hooks/tests/test_memory_channel_and_budget.py:13
.claude/hooks/tests/test_post_write_register_task_metadata.py:1
.claude/hooks/tests/test_post_write_register_task.py:3
.claude/hooks/tests/test_skill_reference_pointers.py:1
.claude/hooks/tests/test_skill_spec_conformance.py:5
.claude/hooks/tests/test_task_context.py:1
.claude/hooks/tests/test_vital_slice.py:8
CLAUDE_LEGACY.md:4
CLAUDE.md:13
.claude/skills/craft-agent/SKILL.md:6
.claude/skills/craft-spawn-prompt/SKILL.md:2
.claude/skills/delivery-report/render.py:1
.claude/skills/delivery-report/SKILL.md:2
.claude/skills/git-guardrails-claude-code/SKILL.md:1
.claude/skills/learn/SKILL.md:1
.claude/skills/slim-skills/SKILL.md:3
.claude/skills/teach/SKILL.md:2
.claude/skills/write-better-skill/references/descriptions.md:1
.claude/skills/write-better-skill/SKILL.md:3
.cursor/rules/agent-base.mdc:1
docs/claude-md/folder-structure.md:8
docs/claude-md/pipeline-stages.md:8
docs/claude-md/untrusted-content-boundary.md:2
MANIFEST:2
scripts/measure_agent_guide_tokens.py:5
scripts/smoke-install.sh:2
scripts/test-agent-template.sh:9
scripts/test-claude-md-refs.sh:8
scripts/validate.sh:5
setup.sh:4
templates/SKILL_template.md:1
templates/TASK_GUIDE_template.md:3
tests/test_harness_fetch.sh:5
tests/test_install_update_smoke.sh:2
tests/test_provider_adapters.py:1
tests/test_setup.sh:17
tests/test_site_content.py:1
tests/test_update.sh:29
```

### Historical audit trail — 909 references (must be identical AFTER)

```
$ grep -rIo '\.claude/\(skills\|agents\)' tasks memory reports docs/ddr docs/adr \
    PROJECT_KANBAN.md BRAINSTORMING_LOG*.md 2>/dev/null | wc -l
909
```

### Canon inventory

```
$ ls .claude/skills | wc -l
30
$ ls .claude/agents | wc -l
5
```

30 skills and 5 agent guides — matching AC1.

### Green baseline

```
$ python3 -m pytest .claude/hooks/tests/ -q
697 passed in 9.43s

$ python3 -m pytest tests/ -q
40 passed in 0.08s

$ bash scripts/validate.sh >/dev/null 2>&1; echo "exit=$?"
exit=0
```

### Pre-move link state

`.claude/skills` and `.claude/agents` are real directories; no symlinks exist.

---

## AFTER

### Canon relocated, `.claude/` entries are relative symlinks

```
$ git ls-files -s .claude/skills .claude/agents
120000 fd65c790eeaf1ea0b802c5ab6d79e184eba08636 0	.claude/agents
120000 42c5394a18a882778ebf50eb940fb5a96bc4a6d9 0	.claude/skills

$ readlink .claude/skills && readlink .claude/agents
../skills
../agents

$ ls skills | wc -l && ls agents | wc -l
30
5
```

Mode `120000` is git's symlink mode — the links are committed, not gitignored working-tree
artifacts, so a clone reproduces them (AC2).

### AC1 — history followed the move

The relocation commit records 39 pure renames (`R`), zero delete+add pairs:

```
$ git show --format= --name-status --find-renames 2cbfa99 | grep -c '^R'
39

$ git log --follow --oneline -- skills/wake/SKILL.md | tail -1
9acd3ad feat: add wake skill — mandatory session-start orientation briefing

$ git log --follow --oneline -- agents/qa.md | tail -1
b4582e5 Create qa.md
```

Pre-move history is intact on the post-move paths.

### AC4 — historical audit trail untouched

The raw count reads 953 against a BEFORE of 909. Both deltas are accounted for, and neither is a
rewritten historical file:

| Source of the +44 | Refs | Tracked? |
|---|---|---|
| `tasks/TASK_REVIEW_T096.md` — this file, authored by this task | 23 | yes (new file) |
| `memory/event-trace/_untagged.jsonl` — hook telemetry that logged this session, 4 -> 23 | +19 | **no — gitignored** |

The decisive check is not the count but the diff. No pre-existing historical file was modified:

```
$ git diff --name-only 695f5d8 HEAD -- tasks/ memory/ reports/ docs/ddr docs/adr \
    PROJECT_KANBAN.md 'BRAINSTORMING_LOG*.md'
tasks/TASK_REVIEW_T096.md
```

Per-directory, excluding this task's own new file and the gitignored trace:

| Directory | BEFORE | AFTER |
|---|---|---|
| `tasks/` | 736 | 736 |
| `memory/` (excl. `event-trace/`) | 124 | 124 |
| `PROJECT_KANBAN.md` | 22 | 22 |
| `docs/ddr/` + `docs/adr/` | 4 | 4 |
| `BRAINSTORMING_LOG_*.md` | 21 | 21 |
| `reports/` | 0 | 0 |

`memory/codebase-map.md` is the guide's declared exception and was regenerated, not hand-edited
(AC10 below).

### AC5 — live surface

225 references rewritten to 0 functional references. 29 textual occurrences remain, every one
deliberate:

| Category | Refs | Why it stays |
|---|---|---|
| `tests/canon_paths.py` — the pre-move path map + its docstring | 4 | must name the old path to resolve baselines at pre-move refs |
| `RETIRED_CLAUSE` in `test_complexity_matrix_pointers.py` | 1 | greps the audit trail at a pre-move ref; repointing it would match nothing and pass vacuously |
| Byte-pin repointing comments (`test_agent_guide_dedup.py`, `test_vital_slice.py`) | 4 | describe what changed and when |
| `test_canon_symlinks.py` docstring | 3 | the tests are *about* the symlink |
| `docs/claude-md/folder-structure.md` | 4 | documents the symlink arrangement |
| `scripts/smoke-install.sh` | 2 | asserts the symlink exists downstream |
| `CLAUDE.md` | 2 | names the symlink as load-bearing |
| `setup.sh` — `install_canon_symlinks()` comment | 1 | creates the symlink |
| `setup.sh` — `install_pack()` targets | 4 | **out of scope per the guide**; see DELTA |

Beyond the guide's 49 files, **15 further live references in 8 files** were found and rewritten
(see DELTA).

### AC6 / verification command

```
$ python3 -m pytest .claude/hooks/tests/ -q
707 passed in 9.70s

$ python3 -m pytest tests/ -q
40 passed in 0.05s

$ bash scripts/validate.sh   # exit 0, incl. new symlink section
== Claude harness symlinks (.claude/{skills,agents} -> ../{skills,agents}) ==
  [ok]   .claude/skills -> ../skills
  [ok]   .claude/agents -> ../agents
validate.sh: PASS

$ readlink .claude/skills && readlink .claude/agents
../skills
../agents
```

707 = the 697 baseline + 10 new tests. Nothing was removed to get to green.

### AC7 — fresh clone

```
$ git clone --branch feat/t096-canon-plain-root . /tmp/.../clone
$ ls -l /tmp/.../clone/.claude/
.claude/agents -> ../agents
.claude/skills -> ../skills

$ head -2 /tmp/.../clone/.claude/skills/wake/SKILL.md
---
name: wake

$ python3 -c "import os;print(os.path.realpath('/tmp/.../clone/.claude/skills/wake/SKILL.md'))"
/tmp/.../clone/skills/wake/SKILL.md
```

Readable, and resolving **inside the clone** rather than back into this worktree.

### AC8 — `git worktree add`

```
$ git worktree add -b t096-throwaway-probe /tmp/.../wt HEAD
$ ls -l /tmp/.../wt/.claude/skills
.claude/skills -> ../skills

$ python3 -c "import os;print(os.path.realpath('/tmp/.../wt/.claude/skills/wake/SKILL.md'))"
/tmp/.../wt/skills/wake/SKILL.md

$ head -2 /tmp/.../wt/.claude/agents/qa.md
---
name: qa-expert
```

Resolves within the worktree. This is the property an absolute symlink target would have broken,
and the reason the guide forbids one: a sub-agent would otherwise read canon from the main
checkout, outside its isolation boundary. Probe worktree and branch were removed afterwards.

### AC9 — `MANIFEST` + `smoke-install.sh`

`MANIFEST` now lists `agents` and `skills`. A real end-to-end install:

```
$ bash scripts/smoke-install.sh
  [ok]   agents
  [ok]   skills
  [ok]   .claude/agents
  [ok]   .claude/skills
  ...
  [ok]   .claude/skills -> ../skills resolves
  [ok]   .claude/agents -> ../agents resolves
  [ok]   no central-clone directory created by the core install
smoke-install.sh: PASS
```

### AC10 — `memory/codebase-map.md` regenerated

```
$ git diff --stat memory/codebase-map.md
 memory/codebase-map.md | 319 +++++++++++++++++++-----------
 1 file changed, 230 insertions(+), 89 deletions(-)
```

230 insertions against 89 deletions across the whole file: a full `/map-codebase` regeneration,
not a targeted path substitution (which would have shown a handful of one-line changes). The
`.claude/agents` strings still present in it are the symlink entries in the tree section and
git-history hotspot paths — both correct regenerated output.

### AC11 — anti-vacuity: the symlink is load-bearing

```
$ rm .claude/skills
$ python3 -m pytest .claude/hooks/tests/ -q
48 failed, 659 passed in 9.92s

$ ln -s ../skills .claude/skills
$ python3 -m pytest .claude/hooks/tests/ -q
707 passed in 9.77s
```

`scripts/validate.sh` also fails loudly:

```
  [FAIL] .claude/skills is not a symlink (canon lives at ./skills; .claude must link to it)
validate.sh: FAIL
```

Deleting the link turns 48 tests red. It is not decorative.

### AC12 — a new test pins the symlink

`.claude/hooks/tests/test_canon_symlinks.py`, 10 tests, asserting the links exist, are symlinks
rather than copies, resolve onto real canon content, and target a **relative** `../path`. It ships
mutation controls (the `DDR-0006` / `test_provider_adapters.py` shape the guide points at) that
rebuild the layout in a tmpdir and prove each assertion goes red when the link is deleted,
replaced by a copy, or given an absolute target — so the checks cannot pass vacuously.

---

## DELTA

| # | Change | Why |
|---|---|---|
| 1 | `.claude/skills/` -> `skills/`, `.claude/agents/` -> `agents/` via `git mv` (39 renames) | the vital slice |
| 2 | `.claude/skills`, `.claude/agents` re-created as committed relative symlinks | Claude Code only discovers canon under `.claude/` |
| 3 | 225 live references rewritten across the guide's 49 files, file by file | no repo-wide `sed`/`xargs`/`find -exec` was used at any point |
| 4 | **+15 references in 8 files beyond the guide's list** | see below |
| 5 | `setup.sh` gains `install_canon_symlinks()` | see below |
| 6 | `.claude/hooks/tests/canon_paths.py` (new) | see below |
| 7 | Three byte-pins repointed | see below |
| 8 | `test_canon_symlinks.py` (new, 10 tests) + symlink assertions in `validate.sh` and `smoke-install.sh` | AC11/AC12 |
| 9 | `memory/codebase-map.md` regenerated | AC10 |

### 4 — references the guide's derivation command could not see

Eight files build the path as `os.path.join(ROOT, ".claude", "skills", ...)` rather than the
literal `".claude/skills"`, so they never matched the guide's grep and were absent from its
49-file list:

```
.claude/hooks/tests/test_skill_spec_conformance.py   .claude/hooks/tests/test_guide_sections.py
.claude/hooks/tests/test_skill_reference_pointers.py .claude/hooks/tests/test_delivery_report_render.py
.claude/hooks/tests/test_spawn_prompt_cache_note.py  .claude/hooks/tests/test_untrusted_content_boundary.py
tests/test_provider_adapters.py                      tests/test_site_content.py
```

They resolved through the new symlink and so were never red — which is precisely why they had to
be hunted deliberately. Worth recording: **a repo-wide pattern rewrite would have missed these
too**, and would have left the live surface quietly half-migrated while looking complete.

### 5 — `install_canon_symlinks()` in `setup.sh`

Moving `MANIFEST` to plain root means a downstream install copies `skills/` and `agents/` to the
target root and creates no `.claude/skills` at all — Claude Code would stop discovering the kit
after install. `install_canon_symlinks()` re-creates both relative links post-copy.

It runs **before** `install_pack()`, which means pack writes to `./.claude/agents/<name>.md`
resolve through the link into `agents/`. `install_pack()` itself is therefore untouched, honouring
the guide's "`packs/` and `install_pack()` out of scope" rule while keeping pack behaviour correct.
Those 4 references are the only live ones left that are not symlink mentions.

### 6 — `canon_paths.py`

Several suites byte-pin files by reading them at a historical ref via `git show <ref>:<path>`.
Those refs predate the move, so the file exists there only under its old `.claude/`-prefixed name
and `git show` fails on the new one — this broke 18 tests. `canon_paths.read_at()` tries the
current path and falls back to the pre-move path. It keys on *whether the path exists at that ref*
rather than on commit ancestry, so a later rebase cannot silently break it.

### 7 — the three byte-pins

`CLAUDE.md`, `MANIFEST` and `scripts/test-agent-template.sh` are pinned byte-identical to
baselines set by T070/T082/T090/T071 — scope fences proving *those* tasks did not touch these
files. T096 necessarily edits all three. Each pin was repointed to T096's edit commit with the
reason recorded inline, following the precedent T082 and T090 already set in the same file. The
pins remain live and will still fail on any later unexplained edit. They were not deleted or
weakened.

### Not done, and why

- **`DDR-0007` was not written.** It does not exist (defect D1). Authoring the decision record
  this task supposedly implements is not this task's scope; flagged for the Supervisor.
- **`README.md` Windows-limitation note.** The Approach cut list says to document that committed
  symlinks do not materialise on a stock Windows checkout. `README.md` is not in the live-surface
  file list and has no reference to rewrite; the limitation is documented in
  `docs/claude-md/folder-structure.md` instead, where the symlink contract now lives. Flagging
  rather than silently expanding scope to `README.md`.
- **`AGENTS.md` content correction, `.codex/`, `--harness`** — explicitly `T097`.

---

## WITNESS

**Commits on `feat/t096-canon-plain-root`** (8, in dependency order; the repo is runnable at each):

```
beec8cb docs(T096): capture BEFORE state and guide defects D1/D2
2cbfa99 refactor(T096): relocate canon to plain root; .claude/{skills,agents} become relative symlinks
ffa6712 refactor(T096): point install machinery at plain-root canon
9e9419a refactor(T096): rewrite scripts/ references to plain-root canon
8f8cc47 refactor(T096): rewrite the live surface onto the plain-root canon
56d2df3 test(T096): repoint the three byte-pins the relocation necessarily breaks
7060c13 refactor(T096): repoint split-string canon paths the guide's grep missed
5a27a96 docs(T096): regenerate memory/codebase-map.md via /map-codebase
```

**Method witness.** No `sed -i`, `xargs`, or `find -exec` rewrite was run against the repo at any
point. Every substitution was made file by file against an explicitly enumerated list, each with
an asserted match count so a silent no-op or over-match would raise. Two corruptions were caught
by that discipline and would have shipped under a pattern rewrite:

1. `scripts/test-claude-md-refs.sh` — replacing `.claude/agents/` inside the escaped regex
   `` `\.claude/agents/...` `` left `` `gents/ ``, a broken pattern that would have matched no
   CLAUDE.md table row. The test would still have passed its own `-z` guard only by accident.
2. `test_complexity_matrix_pointers.py` `RETIRED_CLAUSE` — a constant that is grepped *against the
   audit trail at a pre-move ref*. Rewriting it made the grep match nothing; the test caught it,
   but a pattern rewrite plus a green suite would have hidden it.

**Anti-vacuity witness.** The suite is green at 707 with the symlink present and 48-red without
it, so the tests demonstrably discriminate on the thing this task built.

**Residual risk.** A stock Windows checkout without Developer Mode or `core.symlinks=true`
materialises the two links as plain text files, and skill discovery fails there. The guide's cut
list deliberately excludes a copy-fallback as speculation; the limitation is now documented.

---

## Upgrade path (Stage 5 regression)

Stage 4 code-review passed and the **fresh-install** path verified clean. Stage 5 `/verify` then
drove the REAL installers against a **pre-relocation install** and found a regression this diff
introduces. The guide was amended with AC13/AC14/AC15 and Success Criteria rows 6 and 7; this
section is the evidence for those three rows.

### Root cause

Before T096, `MANIFEST` listed `.claude/skills`, so `update.sh` copied the fresh canon exactly where
Claude Code reads it. After T096, `MANIFEST` lists `skills`/`agents` at plain root and **nothing in
`update.sh` ever touches `.claude/skills` or `.claude/agents`** — it contains zero `ln -s`.
`setup.sh` did have `install_canon_symlinks()`, but on finding a real directory there it logged a
`[warn]` and `continue`d, so the run still reached `Setup complete` with RC=0 over content Claude
Code would keep reading forever.

The bug is the **RC=0**, not the wording of the warning. An installer that reports success while the
harness silently serves stale skills is worse than one that fails.

### BEFORE (as observed by `/verify`, verbatim)

```
# setup.sh over a pre-T096 install (.claude/skills a real dir with stale content)
[warn]  './.claude/skills' is a real directory from an older install. ...
setup.sh RC=0                       <-- reports SUCCESS
$ cat .claude/skills/wake/SKILL.md
STALE CONTENT FROM OLD INSTALL      <-- what Claude Code now reads, forever

# update.sh on the same install
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
update.sh RC=0                      <-- no warning at all
$ cat .claude/skills/wake/SKILL.md
STALE CONTENT FROM OLD INSTALL

# update.sh on a CORRECT-shape install with the link deleted
update.sh RC=0 ; link STILL MISSING
```

### The fix

`harness_install_canon_symlinks [target]` in `lib/harness-fetch.sh` — the library both installers
already source, so the link contract lives in exactly one place. Per canon directory:

| State at `.claude/<canon>` | Behavior |
|---|---|
| symlink (any target) | removed, replaced with the correct **relative** `../<canon>` link |
| missing | created |
| real directory (pre-relocation install) | moved aside to `<link>.bak`, then linked. Content is preserved, never deleted |
| real directory **and** `<link>.bak` already exists | `return 1` → run exits non-zero, no success message |
| regular file | left to `ln -s`, which fails; `set -e` exits non-zero. **Unchanged — failing loudly here was already correct and was not "fixed"** |

`update.sh` calls it after the copy and lock rewrite, before `log_info "Update complete"`, so a
failed migration can never print that line. `setup.sh`'s `install_canon_symlinks()` now delegates to
it, replacing the warn-and-continue. `detect_symlinks()` is untouched: it inspects MANIFEST paths
(`skills`, `agents` at plain root, both real dirs), never `.claude/skills`, so the two do not
collide. The lock/decision model is unchanged.

### AFTER (same probes, re-run against this branch)

```
=== PROBE 1: setup.sh over a pre-T096 install ===
[warn]  './.claude/skills' was a real directory from an older install — moved to './.claude/skills.bak' and replaced with a symlink onto './skills'.
[info]  Setup complete. Harness copied into /tmp/probeA
setup.sh RC=0
lrwxrwxrwx 1 ... .claude/skills -> ../skills
---
name: wake
description: "Mandatory cold-start orientatio      <-- the FRESH canon
--- backup preserved:
STALE CONTENT FROM OLD INSTALL

=== PROBE 2: update.sh on a pre-T096 install ===
[warn]  './.claude/skills' was a real directory from an older install — moved to './.claude/skills.bak' and replaced with a symlink onto './skills'.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
update.sh RC=0
lrwxrwxrwx 1 ... .claude/skills -> ../skills
cmp: .claude/skills/wake/SKILL.md == skills/wake/SKILL.md

=== PROBE 3: update.sh on a CORRECT-shape install with the link deleted ===
update.sh RC=0
readlink: ../skills ../agents

=== PROBE 4: .claude/skills as a regular FILE (must still fail loudly) ===
setup.sh RC=1
```

Probe 1/2 RC=0 satisfies AC14: the criterion is *migrate **or** exit non-zero*, and the directory was
migrated — the content read through `.claude/skills` is now the canon, proven by `cmp`. Probe 4 is
the deliberately-unchanged case.

### Automated coverage (AC15)

`tests/test_update.sh` tests 7–9 and `tests/test_setup.sh` test 4 drive the **real installers** end
to end — no function is called directly, and every assertion is on installer-observable state.

```
PASS: test7: update.sh exited 0 on a pre-T096-shape install
PASS: test7: .claude/skills is the relative symlink after update
PASS: test7: .claude/skills/brainstorming/SKILL.md matches the plain-root canon
PASS: test7: the stale directory was preserved at .claude/skills.bak, not deleted
PASS: test8: update.sh exited 0 with the canon links missing
PASS: test8: update.sh re-established both canon symlinks
PASS: test9: update.sh exits non-zero when a stale canon dir cannot be migrated (rc=1)
PASS: test9: no 'Update complete' printed over a stale canon

----- summary: 30 passed, 0 failed -----   (was 20)

PASS: test4: setup.sh did not silently succeed over a stale real .claude/skills
PASS: test4: stale directory migrated — .claude/skills now serves the fresh canon
PASS: test4: the stale directory was preserved at .claude/skills.bak, not deleted

----- summary: 18 passed, 0 failed -----   (was 15)
```

Test 7's central assertion is `cmp` of `.claude/skills/brainstorming/SKILL.md` against
`skills/brainstorming/SKILL.md` — the path Claude Code actually reads, versus the canon.

**Mutation control** (DDR-0006 shape). Removing the single `harness_install_canon_symlinks .` call
from `update.sh` and re-running the suite:

```
FAIL: test7: .claude/skills is not '../skills' after update
FAIL: test7: content read via .claude/skills does not match the canon (stale canon regression)
FAIL: test7: stale content was not preserved at .claude/skills.bak
FAIL: test8: canon symlinks still missing after update.sh
FAIL: test9: update.sh reported success over a stale, unmigratable .claude/skills
FAIL: test9: printed 'Update complete' over a stale canon
----- summary: 24 passed, 6 failed -----
```

The call was restored immediately; the tests are load-bearing, not decorative.

### No regression

```
python3 -m pytest .claude/hooks/tests/ -q   ->  707 passed in 10.20s
python3 -m pytest tests/ -q                 ->   40 passed in 0.05s
bash scripts/validate.sh                    ->  validate.sh: PASS      (RC=0)
bash scripts/smoke-install.sh               ->  smoke-install.sh: PASS (RC=0)
readlink .claude/skills                     ->  ../skills
readlink .claude/agents                     ->  ../agents
```

### Scope witness

Touched: `lib/harness-fetch.sh`, `update.sh`, `setup.sh`, `tests/test_update.sh`,
`tests/test_setup.sh`, `docs/claude-md/folder-structure.md`. No `sed`/`xargs`/`find -exec` rewrite
was run. The relocation and the reference rewrite were not revisited; `tasks/`, `memory/`,
`reports/`, `docs/ddr`, `docs/adr`, `PROJECT_KANBAN.md` and `BRAINSTORMING_LOG*` are unchanged apart
from this section appended to this review file.

---

## Stage 5 — `/verify` (Supervisor, re-run after the fix)

**Verdict: PASS**

The first `/verify` pass returned **FAIL**: it drove the real installers and found that the
relocation broke the upgrade path — `update.sh` never touched `.claude/{skills,agents}`, so an
existing install kept reading stale canon while both installers reported RC=0 success. The guide
was amended with AC13/AC14/AC15 and the fix slice landed in `72c8225`.

Re-running the same probes against the fixed branch, driving the real `setup.sh` / `update.sh`
CLIs (not tests, not import-and-call):

| # | Probe | Before the fix | After the fix |
|---|---|---|---|
| 1 | `update.sh` over a pre-T096 real dir | RC=0, `STALE CONTENT FROM OLD INSTALL` | migrated to `.claude/skills.bak`, link restored, reads fresh canon (`name: wake`) |
| 2 | `update.sh` with the link deleted | RC=0, link STILL MISSING | RC=0, `link restored: ../skills` |
| 3 | `setup.sh` over a pre-T096 real dir | RC=0 "Setup complete" over stale content | migrated + linked, serves fresh canon |
| 4 | `.bak` already exists (cannot migrate) | n/a | **RC=1**, explicit error, existing `.bak` preserved unclobbered |
| 5 | Regular *file* at the link | RC=1 (correct) | RC=1 — unchanged by design |
| 6 | `git worktree add` isolation | resolves inside the worktree | unchanged |
| 7 | Absolute target | `validate.sh` RC=1 with a precise message | unchanged |

Non-destructive migration is the right call: the stale directory is moved to `<link>.bak`, never
deleted, and a `.bak` collision hard-fails rather than clobbering a previous rescue.

**Suite state at merge:**

```
python3 -m pytest .claude/hooks/tests/ -q   ->  707 passed
python3 -m pytest tests/ -q                 ->   40 passed
bash tests/test_update.sh                   ->   30 passed, 0 failed
bash tests/test_setup.sh                    ->   18 passed, 0 failed
bash scripts/validate.sh                    ->  exit 0
bash scripts/smoke-install.sh               ->  exit 0
readlink .claude/skills .claude/agents      ->  ../skills, ../agents
```

Anti-vacuity confirmed twice: deleting `.claude/skills` turns 3 tests red (AC11); removing the
single `harness_install_canon_symlinks` call turns 6 upgrade tests red (AC15).
