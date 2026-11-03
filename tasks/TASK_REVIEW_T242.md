# TASK_REVIEW — T242: Smaller plugin source: a `plugin/` folder of symlinks

> Sibling of `tasks/TASK_GUIDE_T242.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. Picked T242, not T243: T243 needs the listing icon, which the directory keeps from the first submission and never changes — RULE: `skills/resolve-question/SKILL.md` § Decide, rule 2 ("it can be undone" ranks first); the icon choice stays the user's
2. Extended track, C2 / Risk Medium: new component and a packaging change across many paths — RULE: `docs/claude-md/tracks.md` `## Track rule`
3. Layout: a `plugin/` folder of per-path symlinks, `"source": "./plugin"`, root `.claude-plugin/plugin.json` kept a real file — DEBATED: A (Advocate 1: A, per-path links, root plugin.json linked or removed; Advocate 2: A, per-path links, plugin.json moved into `plugin/`); both Advocates also left the 16 MB marketplace clone out of scope; the root file stays because it is the smaller change ⚠ decided for you — please review
Paused: auto-mode check failed — no `Memory:` line in the report — run the memory pass before you stop and record it there (each entry written, or `Memory: nothing new`); no test run in memory/event-trace/T242.jsonl — write /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID with the task ID (minimal-track step 1): `mkdir -p /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d && printf '%s\n%s\n' "T242" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /home/hungnguyenhuu/workspace/pets/personal-agentic-claude/.claude/hooks/.state/active_task.d/$CLAUDE_CODE_SESSION_ID`, then rerun the task's tests so the trace records them under the task, then stop; Risk Medium: decision 2 (`RULE`) is a choice — its RULE cites no written rule (`path:line`, `path § <heading>` or `docs/claude-md/tracks.md` `### <section>`) — so it must be `DEBATED` with exactly 2 Advocates named; 1 `DEBATED` line(s) need ≥2 Advocate `Agent` calls (description `Advocate <n>:` and a prompt starting `Using the repo, answer alone:`); the trace has 0 [report be95b3abeafa]

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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-03T12:03:46Z by common-infrastructure, before any implementation commit;
branch at `c67b5159` = `main`). Recipe: a bare clone of the worktree, served over smart HTTP on
`127.0.0.1:18742` (`git http-backend` in a stdlib `wsgiref` wrapper, `<scratch>/t242/drv/smart_http.py`),
because the CLI refuses `file://` (`✘ Invalid marketplace source format. Try: owner/repo, https://..., or ./path`)
and the dumb HTTP protocol (`fatal: dumb http transport does not support shallow capabilities`). Isolated
`CLAUDE_CONFIG_DIR=<D>/cfg`, `HOME=<D>/home`, `GIT_TERMINAL_PROMPT=0`. Driver `<scratch>/t242/drv/install.sh`.

```
2026-11-03T12:03:46Z
c67b5159 plan(T242): guide, review file, board In Progress (auto; layout DEBATED)
$ claude plugin marketplace add http://127.0.0.1:18742/repo.git
Adding marketplace…Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): http://127.0.0.1:18742/repo.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
✔ Successfully added marketplace: easy-kit (declared in user settings)
exit 0
$ claude plugin install easy-kit@easy-kit
Installing plugin "easy-kit@easy-kit"...✔ Successfully installed plugin: easy-kit@easy-kit (scope: user)
exit 0
cache: <cfg>/plugins/cache/easy-kit/easy-kit/2.2.0
$ du -sh <cache>
12M	<D>/cfg/plugins/cache/easy-kit/easy-kit/2.2.0
$ find <cache> -type l | wc -l
2
$ find <cache> -type l | head -5
<cache>/.claude/agents
<cache>/.claude/skills
$ du -sh <marketplace clone>
16M	<D>/cfg/plugins/marketplaces/easy-kit
$ test -e <cache>/.claude/hooks/tests
present
$ ls <cache>
.claude .claude-plugin .cursor .github .gitignore .in_use .vercelignore AGENTS.md BRAINSTORMING_LOG.md CLAUDE.md CLAUDE_LEGACY.md LICENSE MANIFEST PROJECT_KANBAN.md PROJECT_KANBAN_SITE.md PROJECT_SPEC.md PROJECT_SPEC_SITE.md README.md RUNBOOK.md agents commands docs experiments hooks lib memory packs reports scripts setup.sh site skills tasks templates tests update.sh vercel.json
```

The whole repo is copied (12 MB, matching T236's 12 MB), with `tasks/`, `tests/`, `site/` and `.claude/hooks/tests`.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
