# TASK_REVIEW — T170: `resolve-question` skill

> Sibling of `tasks/TASK_GUIDE_T170.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_resolve_question.py` (14 test functions, 20 cases incl. parametrized: AC1–AC9; RED commit `cff857e` before implementation `a830bb8`). Supervisor re-run 2026-10-26 at `b69b3e7`: `20 passed in 0.02s` |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/test_resolve_question.py .claude/hooks/tests/test_vital_slice.py tests/test_site_content.py` → `119 passed in 0.49s` (Supervisor, 2026-10-26, `b69b3e7`) |
| Negative cases hold | ☑ pass | Supervisor mutants on `b69b3e7`, each reverted (`git status` clean after): M1 delete `agents/qa.md:127` `Question (if blocked): [fact|choice] <question>` → `1 failed, 19 passed`; M2 `SKILL.md:25` "never to Scanners" → "also to Scanners" → `1 failed, 19 passed` |
| verify | ☑ pass | User ran `/verify` 2026-10-26; Supervisor drove the agent surface with 3 headless `claude -p` runs in `../wt-t170` — pass. Run A (blocked backend-developer, `[fact]` state-file max age): invoked `resolve-question`, step 2 Citation `.claude/hooks/lib/task_context.py:170` "ACTIVE_TASK_MAX_AGE_DEFAULT_S = 21600  # 6h", Scanners skipped, logged `reports/question_none_20261026T094220.html` ($0.49). Run B probe (choice question mis-tagged `[fact]`): re-sorted to Choice question, 0 `Agent` calls, HITL block "Scanner (a): not run — Choice question, so no Scanners" ($0.37). Run C (forced step 3, risk=Medium): 3 `Explore` Scanners in one turn, areas code/docs/history, prompts carry the question only (no task ID / guide path), no hook blocked the spawns; all 3 agreed on `.claude/hooks/pre_bash_block_unsafe_merge.py`, Supervisor opened :5/:7/:505 itself, logged `reports/question_none_20261026T094418.html` ($1.09). Site: headless Chrome 1280px DOM has `31 skills` + `<span class="chip">resolve-question</span>`; chip renders in the Any stage row with matching style. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed `git diff main...HEAD` (16 files): new `skills/resolve-question/SKILL.md`, `skills/thinking-report/SKILL.md` (`session=resolution`), one report-format line in each `agents/*.md`, `CLAUDE.md:65` cross-cutting line, `site/index.html` (count + chip), glossary, decisions. Hooks, scripts, install path not touched → skipped. Security review (Medium risk) 2026-10-26: no findings — docs/skill text plus two static HTML text edits, no executable code, no new tool grant (Scanners are read-only `Explore`). |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest -q tests .claude/hooks/tests` → `1435 passed, 25 subtests passed in 36.52s`; `sh scripts/validate.sh` → `validate.sh: PASS` (Supervisor, 2026-10-26, `b69b3e7`; branch has 0 commits behind `main`) |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | /verify 2026-10-26: headless Chrome 1280px crop shows the `resolve-question` chip between `resolve-pr-feedback` and `slim-skills`, same pill style, row wraps to 3 lines. Text-only edit to `site/index.html`: `30 skills` → `31 skills` (line 294) and one `<span class="chip">resolve-question</span>` added to the existing "Any stage" chip row (line 581). No CSS, layout or markup-structure change. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | The new chip reuses the existing `.chip` class, same as its 16 neighbours; no new token, color or font. Checked by reading the diff. |
| **UI: Responsiveness at target viewports** | ☐ N/A | The chip row already wraps (`p.chips`, T166/T167); one more short chip adds no new overflow case. No layout change to test. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure before the first implementation commit (branch head
`e1a6bb8`). Docs/skill-text task, so BEFORE is the guide's named command plus the verbatim prior
content of each file that changes.

```
2026-10-20T11:15:45Z
$ ls skills/resolve-question; grep -n "Question (if blocked)" agents/*.md
ls: cannot access 'skills/resolve-question': No such file or directory
grep exit=1
```

Prior report format, `agents/backend.md:118-122` (`frontend.md:117-121` same shape;
`common-infrastructure.md:112-116` adds `environment-ready` to Status; `qa.md:121-126` adds a
`Verdict:` line):

```
Agent: backend-developer
Task: T[NNN] — [short title]
Status: [in-progress | ready-for-review | blocked]
Changed files: [list]
Blockers / notes: [any]
```

Prior `CLAUDE.md:65` tail: `Cross-cutting (any stage, not tied to a single one): `compact-memory` (cold memory files), `compact-advisor` (live conversation health — see Self-monitoring rule above).`

Prior `skills/thinking-report/SKILL.md:3` args: `Args: session=<brainstorming|grilling|planning> task=<TASK_ID> branch=<branch-name>"`;
prior save line `:121`: `SAVE → reports/thinking-report_<branch-arg>_<YYYYMMDDTHHMMSS>.html`

Prior `site/index.html:582` (Any stage chips, no `resolve-question`):
`<span class="chip">strategy</span><span class="chip">teach</span><span class="chip">thinking-report</span><span class="chip">wake</span>`

**AFTER**: same command, Supervisor at `b69b3e7`:

```
$ ls skills/resolve-question; grep -n "Question (if blocked)" agents/*.md
SKILL.md
agents/common-infrastructure.md:117:Question (if blocked): [fact|choice] <question>
agents/frontend.md:122:Question (if blocked): [fact|choice] <question>
agents/backend.md:123:Question (if blocked): [fact|choice] <question>
agents/qa.md:127:Question (if blocked): [fact|choice] <question>
```

**DELTA**: A confused Supervisor or sub-agent can now get a fact question answered from quoted
`file:line` Citations (or 2–3 independent read-only Scanners), and only choice questions reach the user.

**WITNESS**: Supervisor, 2026-10-26 — re-ran the verification command, the full suite and two
mutants in `../wt-t170` with `active_task` = T170 (`memory/event-trace/T170.jsonl`).
