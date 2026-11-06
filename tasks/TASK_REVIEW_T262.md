# TASK_REVIEW — T262: Native Windows support, step 1 - decision record and LF line endings

> Sibling of `tasks/TASK_GUIDE_T262.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_windows_gitattributes.py` (7 tests: eol=lf on 3 paths, binary on 4 extensions, no CRLF in index, ADR five headings, ADR no TODO + template sections, symlink fallback with source, mutation control). Red first: `6 failed, 1 passed` before the ADR and `.gitattributes` existed; green after: `7 passed in 0.16s` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_windows_gitattributes.py -q` -> `7 passed in 0.16s`. After: `git check-attr eol -- setup.sh ...` prints `eol: lf` for all 3 paths (asserted by test) |
| Negative cases hold | ☑ pass | Mutation: dropping every `eol=lf` line (`diff` shows `1,3d0`, the 3 rules gone) in a temp repo turns `git check-attr eol` into `setup.sh: eol: unspecified` / `.claude/hooks/post_tool_trace.py: eol: unspecified`; `test_deleting_the_eol_rules_turns_the_check_red` asserts it. AC5: `git ls-files --eol` index column before and after identical (23 `i/`, 906 `i/lf`, 2 `i/none`, 7 `i/-text`; `diff` printed `index eol identical`); no `i/crlf` |
| verify | ☐ pass / ☐ fail / ☐ N/A | not run by the implementing agent; left for the auto verify run (Supervisor) |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Blast radius = the 4 new files (`.gitattributes`, ADR, test, this review). No MANIFEST change: it lists neither root dotfiles nor `docs/adr/`. Stale-reference grep of `README.md`, `site/`, `docs/claude-md/folder-structure.md`: no Windows or WSL prose to update (only a settings-key list in `site/docs.html`). No `.ps1` rules added. Self-review done by reading the diff; the `code-review` Skill tool is not available to this agent, so the Supervisor runs it at Stage 4 |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q -x` exit 0 (all dots, 100%). `sh tests/test_manifest_exclusions.sh` exit 0, `sh tests/test_pack_catalog.sh` exit 0. `sh tests/test_readme_current.sh` exit 1 at baseline too (verified with `git stash -u`: `FAIL: AC2: could not parse any skill names from README's Codex-skip bullet list`), unrelated to this task |
| **Companion score (easy-verifier)** | ☑ N/A | not run by the implementing agent; Supervisor decides |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component (docs and a git attribute file) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component (docs and a git attribute file) |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component (docs and a git attribute file) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-11-06T11:54:45Z at HEAD `0aafdf84`, before any implementation commit. The change adds a git attribute file and a decision record (no executable code), so BEFORE is the prior state, pasted verbatim:

```
$ cat .gitattributes
cat: .gitattributes: No such file or directory
$ ls docs/adr/
0001-direct-repo-install-no-central-clone.md
0002-one-confirmed-menu-driven-installer.md
$ git check-attr eol -- setup.sh .claude/hooks/post_tool_trace.py skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh
setup.sh: eol: unspecified
.claude/hooks/post_tool_trace.py: eol: unspecified
skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh: eol: unspecified
$ git check-attr binary -- site/fonts/ibm-plex-mono-latin-400-normal.woff2
site/fonts/ibm-plex-mono-latin-400-normal.woff2: binary: unspecified
$ git ls-files --eol | awk '{print $1}' | sort | uniq -c
     23 i/
    906 i/lf
      2 i/none
      7 i/-text
```

**AFTER**: Same commands at the finished branch, 2026-11-06:

```
$ git check-attr eol -- setup.sh .claude/hooks/post_tool_trace.py skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh
setup.sh: eol: lf
.claude/hooks/post_tool_trace.py: eol: lf
skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh: eol: lf
$ ls docs/adr/
0001-direct-repo-install-no-central-clone.md
0002-one-confirmed-menu-driven-installer.md
0003-native-windows-support.md
$ python3 -m pytest tests/test_windows_gitattributes.py -q
.......                                                                  [100%]
7 passed in 0.16s
```

`.gitattributes` content: `* text=auto eol=lf`, `*.sh text eol=lf`, `*.py text eol=lf`, `*.png`/`*.jpg`/`*.ico`/`*.woff2` `binary`.

**DELTA**: A Windows checkout now keeps LF in shell and Python files whatever `core.autocrlf` says, and the native-Windows design is recorded once in ADR-0003.

**WITNESS**: Pending. The implementing agent (common-infrastructure) ran the commands above on 2026-11-06; the Supervisor or the auto verify run adds the independent witness from `memory/event-trace/T262.jsonl`.

---

## Review fixes

Stage 4 review found three P3 items. All fixed on 2026-11-06.

1. `docs/adr/0003-native-windows-support.md` Context said "ten hook commands". `grep -c 'python3' .claude/settings.json` printed `11` (the pattern in the review message, `python3 "$CLAUDE_PROJECT_DIR`, matches 0 because the JSON escapes the quotes as `\"`; the 11 lines are all `python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/*.py`). The ADR now says "eleven".
2. Line 1 of this file now reads `Native Windows support, step 1 - decision record and LF line endings`.
3. `test_attribute_file_leaves_no_crlf_in_the_index` now carries a comment: it is a regression guard for the current index state, not a proof of AC 5.

Re-run: `python3 -m pytest tests/test_windows_gitattributes.py -q` -> `7 passed in 0.11s`.
