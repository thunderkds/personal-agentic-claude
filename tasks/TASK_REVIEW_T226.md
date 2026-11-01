# TASK_REVIEW — T226: Stage 1 offers the optional companion MCP servers

> Sibling of `tasks/TASK_GUIDE_T226.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. New Stage 1 skill `companion-setup` driven by a data file; on a pick it shows the install link and missing tools, and the kit never installs; `setup.sh` gets one log line, no menu — DEBATED: Stage 1 skill, link only, plus one log line (Advocate 1: Stage 1 prompt-only skill `companion-setup`, `setup.sh` unchanged; Advocate 2: skill `companions` with a data file, plus one `log_info` line in `setup.sh`) ⚠ decided for you — please review
2. List easy-ui and easy-verifier as choices; easy-memory and easy-personal as "needs repo access" unless installed; leave out easy-context — DEBATED: two public choices, private ones not choices (Advocate 1: offer easy-ui, easy-verifier and easy-context, private ones a neutral skipped line; Advocate 2: offer easy-ui and easy-verifier, leave out easy-context, never attempt an install) ⚠ decided for you — please review
3. Implementation ran on `claude` with sonnet, the C2 cell — RULE: `PROJECT_SPEC.md` § CLI Model Table
4. easy-verifier's link is its site, not Docker Hub, because the site carries the `docker run` steps — FACT: `tasks/TASK_GUIDE_T226.md:111` "easy-verifier's link is its public Docker image or site, never its repo"
5. The site's dead repo links stay, registered as T227 — RULE: `tasks/TASK_GUIDE_T226.md` § Requirement
Checks: tests `python3 -m pytest tests/ .claude/hooks/tests/ -q` — see Evidence; reviews code-review — P2×2 fixed, P3×1 open, security-review — no findings; real run `python3 skills/companion-setup/scripts/check_companions.py --installed easy-memory,easy-personal` — printed 2 `choice:` lines and 2 `already installed:` lines (auto-checked, not /verify)
Memory: memory/decisions.md — T226 entry with the memory search experiment; memory/MEMORY.md — T226 index line
Not done: merge (yours), without squash; companion-setup: nothing installed, offer not asked — yours to choose (/companion-setup); settings-setup: not run, no Stage 1 ran in this task; auto verify: running (T182)
Paused: auto-mode check failed — no test run in memory/event-trace/T226.jsonl — write /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID with the task ID (minimal-track step 1): `mkdir -p /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d && printf '%s\n%s\n' "T226" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID`, then rerun the task's tests so the trace records them under the task, then stop; extended track, but the trace has no `code-review` Skill call (Stage 4 runs in auto mode); Risk Medium, but the trace has no `security-review` Skill call [report a11e3457f371]

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_companion_setup.py` (22 tests, AC1-AC8). 2026-11-01T05:06Z: `python3 -m pytest tests/test_companion_setup.py tests/test_site_content.py tests/test_readme_slim.py tests/test_docs_match_installer.py -q` -> `172 passed in 0.61s`. Test-first: all 22 failed before the skill existed (`22 failed in 0.23s`). Also edited: `tests/test_site_content.py` (Stage 1 chip group), `tests/test_site_visual_first.py` (3 allow-list entries with reasons), `tests/test_agents_md_primary.py` (`CLAUDE_LEGACY_REF` -> `89117f1`). |
| Verification command run | ☑ pass | pytest line above; then `python3 skills/companion-setup/scripts/check_companions.py --installed easy-memory,easy-personal` printed `choice: easy-verifier ... Needs docker; all present. Link: https://easy-verifier.vercel.app/`, `choice: easy-ui ... Link: https://github.com/thunderkds/easy-ui-mcp`, `already installed: easy-memory (private)`, `already installed: easy-personal (private)`, `Default: skip. The kit never installs a server.`; exit 0 |
| Negative cases hold | ☑ pass | `PATH=/nonexistent` run: easy-verifier and easy-ui print `missing docker`; easy-memory and easy-personal print `needs repo access: ... not a choice here` with no link; exit 0. `--installed unknown-id` and `--installed ""`: ignored, exit 0. Tests: no network/process import in the script source, no file written (empty temp dir after a run), `sudo` lines in SKILL.md all say not/never. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Scope `git diff main...HEAD` + `tests/test_companion_setup.py`. lane_check: `lane: C2, 13 files, 430 lines, FITS`, 3 unpredicted test files (forced by pins). Entry point `companion-setup` found. Startup reads complete. code-review: P2 1 easy-verifier link had no run steps (fixed: site link); P2 2 AGENTS.md Stage index lacked the skill (fixed, pin updated); P3 1 site lead says "offers them" though 2 are not choices (open). security-review: no findings; script has no shell, process or network call. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests/ .claude/hooks/tests/ -q` -> `2673 passed, 25 subtests passed in 137.34s (0:02:17)`; `bash scripts/validate.sh` -> `validate.sh: PASS` |
| **Companion score (easy-verifier)** | ☑ N/A | not run by the implementing agent: the Supervisor's Stage 4 step; change is a skill, a data file, doc lines and site copy |
| **UI: Visual regression** | ☑ N/A | no UI component: the site edit is one sentence of copy in the `#mcps` lead, one chip and a skill count (33 to 34); no CSS, layout or token changed |
| **UI: Design-system compliance** | ☑ N/A | no UI component: the site edit is one sentence of copy in the `#mcps` lead, one chip and a skill count (33 to 34); no CSS, layout or token changed |
| **UI: Responsiveness** | ☑ N/A | no UI component: the site edit is one sentence of copy in the `#mcps` lead, one chip and a skill count (33 to 34); no CSS, layout or token changed |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured before any implementation commit.

```
2026-11-01T05:01:06Z
$ python3 skills/companion-setup/scripts/check_companions.py
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t226/skills/companion-setup/scripts/check_companions.py': [Errno 2] No such file or directory
exit=2
$ grep -n -i companion setup.sh
exit=1
```

**AFTER**: 2026-11-01T05:06Z, same two commands.

```
$ python3 skills/companion-setup/scripts/check_companions.py --installed easy-memory,easy-personal
choice: easy-verifier - Scores a change with no-LLM evidence at Stage 4 review (the score skill uses it). Needs docker; all present. Link: https://easy-verifier.vercel.app/
choice: easy-ui - Tests a web UI in a real browser and returns a report with screenshots. Needs docker; all present. Link: https://github.com/thunderkds/easy-ui-mcp
already installed: easy-memory (private)
already installed: easy-personal (private)
Default: skip. The kit never installs a server.
exit=0
$ grep -n -i companion setup.sh
878:  log_info "Companion MCP servers (optional): your Supervisor shows them at Stage 1. Skip is the default; the kit never installs one."
```

**DELTA**: At Stage 1 the user sees which companion MCP servers exist, which are installed, what each adds and needs, and can pick or skip (skip is the default); the kit installs nothing.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
