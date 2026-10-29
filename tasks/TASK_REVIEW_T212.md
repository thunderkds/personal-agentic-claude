# TASK_REVIEW — T[NNN]: [Short Title]

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
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_content.py` (AC 1-5, contrast test; old no-glow test replaced). `python3 -m pytest tests/test_site_content.py -q` -> `134 passed in 0.27s`; `node --test tests/settings_tool/*.mjs` -> `tests 59, pass 59, fail 0`. Mutations RED then green: M1 (accent #7EDDB0) 2 failed (tokens verbatim, neon accent); M2 (stray text-shadow) 1 failed (shadows test); M3 (no glow on .btn-primary) 1 failed (placement test); M4 (linear-gradient) 1 failed (shadows test); restored -> 134 passed |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_site_content.py -q && node --test tests/settings_tool/*.mjs` -> 134 passed; 59 pass, 0 fail |
| Negative cases hold | ☑ pass | mutations M1-M4 each RED (M1 2 failed, M2 1, M3 1, M4 1), restored -> 134 passed |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor code-review 2026-10-29: diff main..HEAD only (site/theme.css, site/index.html, tests/test_site_content.py); `lane: C1, 3 files, 178 lines, FITS`; 0 P0, 0 P1, 1 P2 (partial startup reads of PROJECT_SPEC_SITE.md and agents/frontend.md; no code effect), 2 P3 (shadow regex misses `-webkit-box-shadow`; guide listed this review file as must-not-touch) |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor re-run in worktree: `134 passed in 0.26s`; node `tests 59, pass 59, fail 0` |
| **Companion score (easy-verifier)** | ☑ N/A | not run: optional; C1 Risk Low CSS token change |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | headless Chrome screenshots of served `site/`: /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/e0f91a3a-f3e1-424f-9e55-0c83adda3363/scratchpad/t212-1440.png, t212-375.png (also -1920, -1024, -768). Neon mint eyebrow, stat numbers, install box, Copy button, family-nav dot glow; links soft mint; layout as before |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | AC 1-3 tests: glow only via `--glow-*`, hex only in theme.css, `#7EDDB0` only `--link`. Contrast: `--accent` on `--bg` 13.05:1, `--on-accent` on `--accent` 13.48:1 (hover `#8AF9CB` 15.0:1) |
| **UI: Responsiveness at target viewports** | ☑ pass | 1920/1440/1024/768/375 px: `scrollWidth == clientWidth` at all five (1905/1425/1009/753/360 in an iframe with a scrollbar) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-29T15:16:56Z, before any implementation commit; `grep -n -E 'accent|shadow' site/theme.css` then `python3 -m pytest tests/test_site_content.py -q -k glow`): accent is `#7EDDB0`, no `box-shadow`/`text-shadow` anywhere, and the old no-glow test passes.

```
2026-10-29T15:16:56Z
39:  --accent:        #7EDDB0;
40:  --accent-hover:  #B2EDCF;
41:  --accent-soft:   rgba(126, 221, 176, 0.09);  /* active nav background */
42:  --accent-line:   rgba(126, 221, 176, 0.33);  /* highlighted card border */
43:  --on-accent:     #0E100F;                     /* text on a mint button */
93:.eyebrow { font: 400 12.5px/1.4 var(--font-mono); color: var(--accent); margin: 0 0 var(--s-3); }
96:a { color: var(--accent); text-decoration: none; }
97:a:hover { color: var(--accent-hover); text-decoration: underline; text-underline-offset: 3px; }
100::focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--r-xs); }
104:  background: var(--bg-sunken); color: var(--accent);
113:.btn-primary { background: var(--accent); color: var(--on-accent); border: 0; }
114:.btn-primary:hover { background: var(--accent-hover); color: var(--on-accent); text-decoration: none; }
124:.codebox .prompt { color: var(--accent); }
142:.step-no { font: 400 11.5px var(--font-mono); color: var(--accent); }
149:.card.is-highlight { border-color: var(--accent-line); }   /* at most one per section */
160:.bar > span { display: block; height: 100%; background: var(--accent); }
186:.brand svg { width: 26px; height: 26px; flex: none; color: var(--accent); }
196:.family-nav a[aria-current="page"] .dot { background: var(--accent); }
220:.sidebar a.active { background: var(--accent-soft); color: var(--accent); font-weight: 500; }
287:.flow-node.is-outcome { border-color: var(--accent-line); }
288:.flow-node.is-outcome > .flow-title { color: var(--accent); }
.                                                                        [100%]
1 passed, 116 deselected in 0.15s
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T212.jsonl`, never the
implementing agent alone]
