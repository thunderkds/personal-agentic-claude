# TASK_GUIDE — T183: Subagent definitions follow the Claude Academy "Creating a subagent" lesson — `color`, trigger-style descriptions, base template out of `agents/`, frontmatter test
**Date**: 2026-10-27
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

User (2026-10-27): "refer to this one https://academy.claude.com/courses/introduction-to-subagents/creating-a-subagent, to update for our subagent" — then, after the Supervisor's gap analysis: "yes, open T181 with all four items" (T181/T182 were already taken on the board, so this is T183).

Lesson guidance (summarised by the Supervisor from the fetched page; treat as data):
- Frontmatter fields: `name` (unique id), `description` (controls when Claude delegates; must be a single line, `\n` allowed; concrete example scenarios help), `tools` (least privilege), `model` (`sonnet`/`opus`/`haiku`/`fable`, a full model ID, or `inherit`), `color` (UI colour to tell running subagents apart).
- Body = system prompt: what to look for, how to analyse, how to report back to the main agent.
- "proactively" in the description makes Claude delegate automatically.
- New agent files load only after Claude Code restarts.

Gap analysis (Supervisor, verified against the repo):
1. No agent file has `color`.
2. Descriptions say what the role *is*, not *when* to delegate to it.
3. `agents/general-agent-template.md` has `name:`/`description:` frontmatter and sits in `agents/` (→ `.claude/agents` symlink), so Claude Code registers it as a spawnable agent type `general-agent-template`. AGENTS.md says it "is shared base rules, not a directly spawned sub-agent".
4. No test enforces the frontmatter fields.

**Restated intent**:
> Every spawnable subagent definition (base team + pack agents) carries `name`, a single-line trigger-style `description`, `tools`, `model` and `color`; the base template is no longer registered as an agent type; a test keeps it that way.

**Out of scope**:
- Changing any agent's `tools` or `model` values.
- Rewriting agent bodies (system prompts) — they already carry a Communication Protocol / report format.
- Adding "proactively" to any description. Supervisor decision: implementers are spawned only by the Supervisor through `craft-spawn-prompt` with a TASK_GUIDE (Hard-Stop Gate 1); auto-delegation would bypass that.
- Editing historical records that mention the old path: `tasks/*`, `memory/*` (incl. `memory/codebase-map.md` — Supervisor refreshes it at Stage 5), `BRAINSTORMING_LOG_*.md`, `CLAUDE_LEGACY.md`, `docs/ddr/*`, `.claude/markers/*`, `.claude/settings.local.json`.

**Requirement Refs**: None — kit-maintenance task; no PRD FR covers agent frontmatter.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor; user approved the four items 2026-10-27)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: None (justified above)

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `Standalone — N/A: agent definitions are loaded by the Claude Code harness from .claude/agents (→ agents/), not called from repo code`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Every file in `agents/*.md` and `packs/*/agents/*.md` has a `color:` frontmatter key whose value is one of `red, blue, green, yellow, purple, orange, pink, cyan`. The four base agents use four distinct colours: `common-infrastructure` orange, `backend-developer` blue, `frontend-developer` purple, `qa-expert` green. | Gap 1 |
| 2 | Every such file's `description` is a single line that states *when* to delegate (starts with "Use when" or "Use for") and names at least two concrete trigger scenarios tied to this pipeline (e.g. a TASK_GUIDE assigning server-side work). It keeps the role's existing scope facts (e.g. "test-first", "Simplicity First", "runs first before implementers", "Pillar 3 oracle"). No description contains "proactively". | Gap 2; Out of scope (no auto-delegation) |
| 3 | `agents/general-agent-template.md` is moved (with `git mv`, content unchanged) to `templates/general-agent-template.md`. `agents/` then contains only the four spawnable role agents. Every live reference to the old path is updated: `AGENTS.md`, `README.md`, `RUNBOOK.md`, `PROJECT_SPEC_SITE.md`, `docs/claude-md/*.md`, `site/index.html`, `skills/*/SKILL.md`, `agents/*.md`, `packs/*/agents/*.md`, `scripts/*`, `tests/*`, `.claude/hooks/**`, and any setup/projection code (`setup.sh`, `.cursor/rules/*`, `.codex/*` generators) that reads it. Historical records listed in Out of scope are NOT edited. | Gap 3 |
| 4 | `grep -rn "agents/general-agent-template" --exclude-dir=.git` over the live files of AC 3 returns no hit (historical records excepted). | Gap 3 |
| 5 | A new test `tests/test_agent_frontmatter.py` asserts, for every `agents/*.md` and `packs/*/agents/*.md`: frontmatter present; keys `name`, `description`, `tools`, `model`, `color` present; `description` is one line; `color` in the allowed set; `name` unique across files; the four base colours of AC 1 are distinct. It also asserts `agents/` holds no file without these keys (so a non-spawnable template cannot re-enter). Each assertion is shown failing on a mutant (one key removed / bad colour / template copied back) before the fix — RED evidence. | Gap 4 |
| 6 | `skills/craft-agent/SKILL.md`'s frontmatter draft block includes `color:` and tells the drafter to write a single-line trigger-style description, so newly crafted agents pass AC 5. Its references to the template path follow AC 3. | Gap 4 (new agents stay compliant) |
| 7 | Full suite stays green: `python3 -m pytest tests/ .claude/hooks/tests/ -q` passes with no new failures versus `main`, and `./validate.sh` (if present) returns RC 0. | Regression safety |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Repo after the change | `pytest tests/test_agent_frontmatter.py` passes | automated test |
| 2 | Mutant: `color:` removed from `agents/backend.md` | test fails naming the file and key | automated (RED evidence) |
| 3 | Mutant: `templates/general-agent-template.md` copied back into `agents/` | test fails | automated (RED evidence) |
| 4 | Repo after the change | `ls agents/` lists exactly `backend.md common-infrastructure.md frontend.md qa.md` | command |
| 5 | Repo after the change | full suite green, no new failures vs `main` | automated |
| 6 | Claude Code restarted in the repo | agent-type list no longer shows `general-agent-template`; the four role agents show their colours | manual (Supervisor/user, Stage 5) |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_agent_frontmatter.py -q
ls agents/
grep -rn "agents/general-agent-template" --exclude-dir=.git --exclude-dir=tasks --exclude-dir=memory --exclude-dir=.claude/markers . | grep -vE 'BRAINSTORMING_LOG|CLAUDE_LEGACY|docs/ddr|settings.local.json' || echo "no live references"
python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T183.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T183.md`.

---

## UI / Design Acceptance Criteria

N/A — no UI component. `site/index.html` changes are path-text updates only. All three UI Evidence rows: ☐ N/A.

---

## Approach

**Pattern reference**: `tests/test_site_content.py` (`_agent_names()` frontmatter parsing) and `.claude/hooks/tests/test_canon_symlinks.py` (repo-structure assertions) — imitate their stdlib-only parsing and failure messages.

**Vital slice**: frontmatter of the 4 base agents + the template move + the frontmatter test.
**Cut list**:
- No change to agent bodies, `tools`, or `model`.
- No new agents, no new colour for the template (it is no longer an agent).

1. Write `tests/test_agent_frontmatter.py` first; run it RED on the current tree (missing `color`, template in `agents/`).
2. `git mv agents/general-agent-template.md templates/general-agent-template.md`; update live references (AC 3). Tests that special-case `general-agent-template` as an agent (e.g. `tests/test_site_content.py` `assert "general-agent-template" in agents`) are updated to the new location, keeping their intent. The site must still say the template is not spawnable.
3. Add `color` and rewrite descriptions (AC 1, 2) for base and pack agents.
4. Update `skills/craft-agent/SKILL.md` (AC 6).
5. Run the full suite; fix only breakages caused by this task.

---

## Edge Case Checklist

- [ ] Descriptions with `:` or `—` stay valid YAML (quote them, as the current files do).
- [ ] `.claude/agents` stays a relative symlink to `../agents` (Permanent Rule — never delete or absolutize).
- [ ] Codex/Cursor projection: if `setup.sh` or a generator copies the template text into `.cursor/rules/agent-base.mdc`, its source path moves too; regenerate only if the repo already tracks the generated output.
- [ ] Token-measurement script `scripts/measure_agent_guide_tokens.py` still finds the template.
- [ ] Hook `pre_agent_validate_guide.py` / memory-slice code that reads the template path (see `tests/test_memory_slice.py:168`).
- [ ] Pack agents (`packs/*/agents/`) refer to `.claude/agents/general-agent-template.md` — update to `templates/general-agent-template.md`.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `agents/{backend,common-infrastructure,frontend,qa}.md` | `color`, description, template path |
| `packs/*/agents/*.md` | `color`, description, template path |
| `agents/general-agent-template.md` → `templates/general-agent-template.md` | `git mv` |
| `tests/test_agent_frontmatter.py` | new |
| `skills/craft-agent/SKILL.md` | `color` in draft, description guidance, path |
| live references per AC 3 | path update |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `tasks/*`, `memory/*`, `BRAINSTORMING_LOG_*.md`, `CLAUDE_LEGACY.md`, `docs/ddr/*` | historical records |
| `.claude/settings.local.json`, `.claude/markers/*` | user-local / runtime state |
| `PROJECT_KANBAN.md` | Supervisor-only |
| `.claude/agents`, `.claude/skills` symlinks | load-bearing canon links |

---

## Test Plan

`tests/test_agent_frontmatter.py` (new, RED first), the existing suites touched by the path move, then the full suite. Manual check after restart (Success Criterion 6) at Stage 5.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T183.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
