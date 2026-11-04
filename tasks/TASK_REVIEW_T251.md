# TASK_REVIEW — T251: Agents cannot write session transcripts (deny rule)

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t251_transcript_deny.py` (7 tests: AC 1 rule order and presence, AC 2 Bash rule, Bash pattern matches 4 forged-write commands and none of 9+ normal commands including every hook command in `.claude/settings.json`, AC 6 no `Read(` rule). Seen RED before the settings change: `3 failed, 4 passed`; GREEN after: `7 passed in 0.02s`). AC 4 install paths: `tests/test_settings_merge.sh` T251 block (3 new PASS lines: real kit deny merged add-only into a project with and without its own deny, idempotent) and `tests/test_plugin_init.py::test_t251_the_legacy_profile_adds_the_transcript_deny_rules_add_only`. Existing lock-step tests updated to the 4-rule list: `tests/test_settings_setup.py` (KIT_DENY), `tests/test_subagent_sandbox_profile.py` (ANCHOR_DENY_RULES), `tests/test_site_content.py`, `tests/test_site_story.py`, `tests/test_site_visual_first.py`, `tests/settings_tool/test_generate.mjs` (node is not installed here: that file was edited but not run; CI runs it). |
| Verification command run | ☑ pass (automated part) | Automated part: see the smoke-suite row. **Live denial check: the USER runs it after the merge (AC 3); the implementing agent ran no `claude -p` call.** One line, from a throwaway copy of the merged kit project: `d=$(mktemp -d) && git -C /home/hungnguyenhuu/workspace/pets/personal-agentic-claude archive HEAD \| tar -x -C "$d" && (cd "$d" && claude -p "Use the Write tool to create the file ~/.claude/projects/t251-check/fake.jsonl with the content {} and tell me exactly what happened." --permission-mode acceptEdits); test ! -e ~/.claude/projects/t251-check/fake.jsonl && echo ABSENT; rm -rf "$d"` (`--permission-mode acceptEdits` makes sure a refusal can only come from the deny rule, not from a missing approval in headless mode). **Expected:** Claude reports that the Write tool was refused by a permissions deny rule (matching `Edit(~/.claude/projects/**/*.jsonl)`), and the shell prints `ABSENT`. If the file exists, the rule did not hold: report it. Clean up if the folder was created: `rmdir ~/.claude/projects/t251-check 2>/dev/null`. Optional Bash twin (the same line with the prompt `Run: echo {} > ~/.claude/projects/t251-check/fake.jsonl` and `--allowedTools Bash` added): expect a refusal from the `Bash(*.claude/projects/*)` rule even though Bash is allowed, because a deny rule wins over an allow rule. | Live denial check: the user's, after the merge — pending.
| Negative cases hold | ☑ pass | `tests/test_t251_transcript_deny.py::test_bash_pattern_does_not_match_the_kits_normal_commands` (10+ normal commands: `git`, `python3 -m pytest`, every hook command in `settings.json` — none matched); `test_ac6_no_deny_rule_is_a_read_rule` (agents can still Read a transcript); `tests/test_settings_merge.sh` T251 block: a project's own deny rules kept first, a second merge changes nothing — `--- 49 passed, 0 failed ---`; `.claude/hooks/tests/test_t250_session_ownership.py` green inside the full suite (`3284 passed`) — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review and security-review read `git diff main...HEAD` (16 files) and the merge path `lib/merge-settings.py` (unchanged); `lane: C1, 15 files, 220 lines, EXCEEDS (files 15 > 6); unpredicted: commands/init.md, site/docs.html, skills/settings-setup/SKILL.md, skills/settings-setup/profiles.json` — the extra files are forced by the T148 lock tests (legacy preset = kit deny list = site catalog). Findings: code-review no P0/P1; P2 Bash wildcard semantics proven only by the user's live check; P2 `ux-evaluate` not run for a one-word copy change; security-review no finding >= 8; below threshold (6): `cd ~/.claude && … projects/<x>.jsonl` never contains `.claude/projects/` — a literal-path gap next to the documented "builds the path at run time" limit — pass |
| Full smoke suite still green (no regression) | ☑ pass | 2026-11-04T12:03Z, worktree `wt-t251`: `python3 -m pytest .claude/hooks/tests/ tests/ -q` printed `3284 passed, 25 subtests passed in 229.77s (0:03:49)`; `bash tests/test_settings_merge.sh` printed `--- 49 passed, 0 failed ---` (includes `.claude/hooks/tests/test_t250_session_ownership.py`, AC 6). Implementing agent's run only; not the `verify` row. |
| **Companion score (easy-verifier)** | ☑ N/A | Not run; `score` is optional at Stage 4 and the gate blocks on ☑ fail only |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI component: the only UI file change is copy in `site/docs.html` ("2 deny rules" → "4 deny rules") and the settings catalog JSON; pinned by `tests/test_site_content.py` / `tests/test_site_story.py` |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI component: the only UI file change is copy in `site/docs.html` ("2 deny rules" → "4 deny rules") and the settings catalog JSON; pinned by `tests/test_site_content.py` / `tests/test_site_story.py` |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI component: the only UI file change is copy in `site/docs.html` ("2 deny rules" → "4 deny rules") and the settings catalog JSON; pinned by `tests/test_site_content.py` / `tests/test_site_story.py` |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-04T11:46:53Z, before any implementation commit; verbatim `permissions` block of `.claude/settings.json` at branch `fix/t251-transcript-deny`, file last changed in `42859ce3`; no rule covers the transcripts folder):

```json
  "permissions": {
    "deny": [
      "Edit(~/.claude/harness-anchors/**)",
      "Bash(*harness-anchors*)"
    ]
  }
```

**AFTER** (2026-11-04T12:03Z; verbatim `permissions` block of `.claude/settings.json` on the branch):

```json
  "permissions": {
    "deny": [
      "Edit(~/.claude/harness-anchors/**)",
      "Bash(*harness-anchors*)",
      "Edit(~/.claude/projects/**/*.jsonl)",
      "Bash(*.claude/projects/*)"
    ]
  }
```

**DELTA**: An agent in a kit project can no longer create or change a session transcript with the Edit/Write tools or with a Bash command that names `~/.claude/projects/`, so the user-`/verify` proof has the same trust level as the run records; `docs/claude-md/tracks.md` `### Known limits` says what the rules miss (custom `CLAUDE_CONFIG_DIR`, a path built at run time, the human operator). The live denial is the user's check after the merge (see the `Verification command run` row).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
