# TASK_REVIEW — T200: settings-setup skill — Stage 1 settings profiles, High security default, add-only

> Sibling of `tasks/TASK_GUIDE_T200.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Implementer-run (common-infrastructure, 2026-10-29), reviewer to confirm. `tests/test_settings_setup.py` (new, 35 tests: AC 1-11). RED before code, 2026-10-29T05:1xZ: `35 failed in 0.51s`. After: `python3 -m pytest tests/test_settings_setup.py -q` → `35 passed in 1.10s`. Mutations M1-M4 each RED then green on revert (see `## Mutations` below). |
| Verification command run | ☑ pass | Implementer-run. `python3 -m pytest tests/test_settings_setup.py -q && python3 -m pytest tests -q` → `35 passed in 1.10s` then `959 passed in 63.88s (0:01:03)` (at 0735407). |
| Negative cases hold | ☑ pass | Implementer-run. Exit 2 + byte-identical + mtime unchanged + `apply_profile: ` reason for JSONC, invalid JSON, top-level array, `permissions` a list, `deny` a string, `ask` null, symlinked file, unknown id (lists the 5 ids); real-run JSONC: `apply_profile: j.json is not valid JSON, file left unchanged (...)` exit=2. |
| verify | ☑ pass | /verify T200 run by the user 2026-10-29 — pass. Surfaces driven in a scratch project: (1) CLI `apply_profile.py`: legacy dry-run `no change`; high-security dry-run 12 `+` lines, file sha256 unchanged; real run wrote, hooks equal; 2nd run `no change`, mtime unchanged; probes held (JSONC / string deny / null ask / symlink / unknown id → exit 2, file unchanged; user file keeps `allow`, `defaultMode`, own `disableBypassPermissionsMode` as `= kept`, no duplicate `rm -rf` ask). (2) Real `claude -p` (sonnet, $0.08 + $0.10): user skips → Supervisor says Legacy baseline, picks High security, shows the dry run, writes nothing; `--resume` "yes" → writes exactly 7 deny + 4 ask + disable, 2 kit rules kept. (3) Effect: haiku session asked to Read `.env` → `permission_denials` Read, canary not in output — pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor 2026-10-29: code-review scoped to `git diff main...feat/t200-settings-setup` (12 files; `main..` showed T202 files only because `main` moved after the branch was cut). Result: 0 P0, 0 P1, 1 P2 (frozen pins name `65fe3a8`, so merge with a merge commit, never squash), 1 P3 (SKILL.md Step 1 does not name the 'no profile prints no change' case; flow still reaches Step 2). Startup reads line complete. lane_check: `C2, 11 files, 729 lines, EXCEEDS (lines 729 > 500)` — 348 of them are the new test file; Complexity C2 kept. security-review scoped manually to the same diff (built-in over-scoped to origin/HEAD again): no findings — no subprocess/eval, json only, symlink refused, atomic write, profiles only add deny/ask + disableBypassPermissionsMode. Supervisor re-run: `35 passed`, `tests` `959 passed`, hook failures identical to `main` (15 = 15, diff empty). |
| Full smoke suite still green (no regression) | ☑ pass | Implementer-run at 0735407: `tests` 959 passed; `.claude/hooks/tests` `15 failed, 1108 passed` — the 15 failures are byte-identical to the untouched baseline 0deff10 (`15 failed, 1102 passed`; test_agent_guide_dedup ac7 x4 + t069_ac9, test_memory_channel_and_budget x4, test_token_audit_format, test_verify_row_fill_detection ac6, test_vital_slice ac11 x4); `bash tests/test_readme_current.sh` → `test_readme_current: ALL PASS`; `sh scripts/validate.sh` → `validate.sh: PASS`; `scripts/test-claude-md-refs.sh` FAILED identically at 0deff10 (AC5/AC6 vs 99940b8, pre-existing). |
| **Companion score (easy-verifier)** | ☑ N/A | easy-verifier is optional (T190) and was not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Guide: copy-only roster chip (`settings-setup` in the Stage 1 step) and two count labels 31 → 32, existing markup; covered by `tests/test_site_content.py` roster/count tests. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Same justification: reuses `<span class="chip">`, no new style. |
| **UI: Responsiveness at target viewports** | ☑ N/A | Same justification: one more chip in an existing wrapping `.chips` row. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure in `/home/hungnguyenhuu/workspace/pets/wt-t200`, at HEAD
`0deff10`, before the first implementation commit:

```
2026-10-29T05:11:25Z
0deff10
$ python3 skills/settings-setup/scripts/apply_profile.py high-security --dry-run
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t200/skills/settings-setup/scripts/apply_profile.py': [Errno 2] No such file or directory
exit=2
$ ls skills/settings-setup
ls: cannot access 'skills/settings-setup': No such file or directory
exit=2
$ grep -c settings-setup AGENTS.md docs/claude-md/pipeline-stages.md site/index.html
AGENTS.md:0
site/index.html:0
docs/claude-md/pipeline-stages.md:0
```

Prior content of the lines this task changes (verbatim):

- `AGENTS.md:66` stage index: ``1=`git-guardrails-claude-code`,`map-codebase` ``
- `docs/claude-md/pipeline-stages.md` Stage 1 item 1:
  ```
  1. **One-Time Setup (first use only)**
     Run these skills to reduce friction for future sessions:
     - `Skill({ skill: "fewer-permission-prompts" })` — scans transcripts and whitelists common read/bash operations
     - `Skill({ skill: "update-config" })` — configure any automated hooks (e.g. "always run brainstorming before /plan")

     Auto mode: skip both (they change the user's permission settings and hooks) and name them under `Not done:`.
  ```
- `site/index.html` `#skills`: `<h2>Skills (31)</h2>`; Stage 1 chips `git-guardrails-claude-code`, `map-codebase`.

**AFTER**: implementer-run at `0735407`, in a scratch project whose `.claude/settings.json` is a copy of
this repo's kit file (hooks + 2 anchor deny rules):

```
2026-10-29T05:23:51Z
0735407
$ apply_profile.py legacy --dry-run
no change
exit=0
$ apply_profile.py high-security --dry-run
+ permissions.deny: Read(./.env)
+ permissions.deny: Read(./.env.*)
+ permissions.deny: Read(./**/*.pem)
+ permissions.deny: Read(./**/*.key)
+ permissions.deny: Read(~/.ssh/**)
+ permissions.deny: Read(~/.aws/**)
+ permissions.deny: Read(~/.config/gh/**)
+ permissions.ask: Bash(git push --force *)
+ permissions.ask: Bash(git push -f *)
+ permissions.ask: Bash(git reset --hard *)
+ permissions.ask: Bash(rm -rf *)
+ permissions.disableBypassPermissionsMode: "disable"
dry run: nothing written
exit=0
$ apply_profile.py high-security
+ permissions.deny: Read(./.env)
+ permissions.deny: Read(./.env.*)
+ permissions.deny: Read(./**/*.pem)
+ permissions.deny: Read(./**/*.key)
+ permissions.deny: Read(~/.ssh/**)
+ permissions.deny: Read(~/.aws/**)
+ permissions.deny: Read(~/.config/gh/**)
+ permissions.ask: Bash(git push --force *)
+ permissions.ask: Bash(git push -f *)
+ permissions.ask: Bash(git reset --hard *)
+ permissions.ask: Bash(rm -rf *)
+ permissions.disableBypassPermissionsMode: "disable"
wrote .claude/settings.json
exit=0
hooks unchanged: yes
$ apply_profile.py high-security   (second run)
no change
exit=0
{
 "deny": [
  "Edit(~/.claude/harness-anchors/**)",
  "Bash(*harness-anchors*)",
  "Read(./.env)",
  "Read(./.env.*)",
  "Read(./**/*.pem)",
  "Read(./**/*.key)",
  "Read(~/.ssh/**)",
  "Read(~/.aws/**)",
  "Read(~/.config/gh/**)"
 ],
 "ask": [
  "Bash(git push --force *)",
  "Bash(git push -f *)",
  "Bash(git reset --hard *)",
  "Bash(rm -rf *)"
 ],
 "disableBypassPermissionsMode": "disable"
}
$ apply_profile.py high-security --settings j.json   (JSONC)
apply_profile: j.json is not valid JSON, file left unchanged (Expecting property name enclosed in double quotes: line 2 column 3 (char 4))
exit=2
```

New lines: `AGENTS.md` ``1=`git-guardrails-claude-code`,`map-codebase`,`settings-setup` ``;
`pipeline-stages.md` Stage 1 item 1 gains ``- `Skill({ skill: "settings-setup" })` — offers settings
profiles for `.claude/settings.json`; High security when the user skips; add-only, writes after
approval`` and the auto line "Run `settings-setup` as a dry run only: it writes nothing, and its
recommendation goes under `Not done:` in the final report."; `site/index.html` `<h2>Skills (32)</h2>`.

**DELTA**: At Stage 1 the Supervisor can now show a project the exact security rules it would add to `.claude/settings.json` (High security by default) and write them on approval, without removing any existing key, hook or rule.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T200.jsonl`, never the
implementing agent alone]

---

## Mutations (AC 12)

Implementer-run 2026-10-29 at `0735407`, on `tests/test_settings_setup.py`; each mutation reverted with `git checkout --`.

| ID | Mutation | Mutated | Reverted |
|----|----------|---------|----------|
| M1 | `apply_profile.py`: `node[leaf] = current + missing` → `node[leaf] = list(value)` (assign, no union) | `3 failed, 32 passed`: `test_ac5_high_security_on_kit_file_adds_7_deny_4_ask_1_scalar_and_keeps_the_rest`, `test_ac5_existing_list_order_kept_and_no_duplicates`, `test_ac5_user_rules_never_removed` | `35 passed` |
| M2 | `apply_profile.py`: `elif leaf not in node:` → `elif True:` (set scalar even when present) | `3 failed, 32 passed`: `test_ac5_scalar_set_only_if_absent`, `test_ac7_dry_run_prints_adds_and_kept_writes_nothing`, `test_ac7_second_run_says_no_change_and_does_not_rewrite` | `35 passed` |
| M3 | `profiles.json`: `"permissions.allow": ["Bash(*)"]` added to `high-security` | `4 failed, 31 passed`: `test_ac2_...`, `test_ac5_user_rules_never_removed`, `test_ac6_no_file_creates_it_with_the_profile_only`, `test_ac8_no_profile_lowers_safety[high-security]` | `35 passed` |
| M3b | same, added to `empty` (shows AC 8 catches it apart from AC 2) | `2 failed, 33 passed`: `test_ac4_shared_profiles_equal_the_page_presets[empty]`, `test_ac8_no_profile_lowers_safety[empty]` | `35 passed` |
| M4 | `profiles.json`: last rule popped from `legacy` `permissions.deny` | `1 failed, 34 passed`: `test_ac3_legacy_equals_the_kit_settings_deny_read_from_the_file` | `35 passed` |

---

## Decisions (implementer, run without stopping for questions)

1. **Detection treats Legacy as the baseline, not as "already set up".** Restated intent says "if `.claude/settings.json` holds none of a profile's rules". Every kit-installed project holds Legacy's 2 anchor rules, so a literal reading would never offer the profiles to the main audience (P2). SKILL.md Step 1 stops only when `high-security`, `solo-engineer` or `team-project` dry-runs to `no change`; Legacy-only says so and goes on. Supervisor to confirm.
2. **Question mapping (SKILL.md Step 3).** Q1 keep kit behavior → `legacy` only; Q2 solo/team → `solo-engineer`/`team-project`; Q3 secrets yes or skip → also `high-security`; empty list → `high-security`. Applied in order (Q2 profile, then high-security); add-only merge makes stacking safe.
3. **`null` in a target list (`"ask": null`) → exit 2**, not "treat as empty". `merge-settings.py` treats null as `[]`; refusing is the safer choice (no write to a value the user set).
4. **Output format** after a write: 2-space indent, `ensure_ascii=False`, trailing newline; original indent not kept. Documented in the script docstring and SKILL.md Step 5. A file is rewritten only when something is added.
5. **Symlinked settings file → exit 2** (mirrors `merge-settings.py`). Parent `.claude/` being a symlink is not refused.
6. **Real run with `--settings PATH` creates missing parent dirs**; `--dry-run` never creates anything.
7. **CLAUDE_LEGACY.md mirrored** (skills list line) per the sync policy; this broke `tests/test_agents_md_primary.py::test_ac10_claude_legacy_md_unchanged`, whose comment says to repoint the pin. Added `CLAUDE_LEGACY_REF = "65fe3a8"`; `BASE_REF` stays for CLAUDE.md AC 1. The CLAUDE_LEGACY.md Stage 1 line ("Verify Multi-CLI commands, git status, etc.") was not changed.
8. **Frozen AGENTS.md pins repointed, not deleted**: `test_agent_guide_dedup.T070_BASELINE_REF` `c8a9af9` → `65fe3a8`; one `REPLACED_SPANS` entry in `test_agents_md_primary.py`. Comment says "required by TASK_GUIDE_T200 AC 10, not separately user-approved".
9. **Files outside the guide's table changed**: `tests/test_site_content.py` (`SKILL_FLOW_GROUPING["1"]` gains `settings-setup` — the roster test pins the grouping), `site/index.html` quick-reference `31 skills` → `32 skills` and heading `Skills (31)` → `(32)` (count tests), the two frozen-pin test files above, `CLAUDE_LEGACY.md`.
10. **`docs/claude-md/tracks.md` `## Auto mode` row 5 not changed.** It still names only `fewer-permission-prompts` / `update-config` for Stage 1 item 1. Adding `settings-setup` there is a doctrine edit outside the guide's Files table; the auto rule lives in pipeline-stages.md item 1 and SKILL.md. Supervisor to decide whether row 5 should name it (`tests/test_auto_mode.py` pins one row per stop).
11. **Script is 0644**, like `skills/wake/scripts/*.py`; SKILL.md calls it via `python3`.
