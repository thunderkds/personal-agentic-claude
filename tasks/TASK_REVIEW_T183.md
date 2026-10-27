# TASK_REVIEW — T183: Subagent definitions follow the "Creating a subagent" lesson

> Sibling of `tasks/TASK_GUIDE_T183.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**:

Captured 2026-10-27T11:05:43Z (UTC) on branch `feat/t183-subagent-frontmatter` at 31450d4, before any implementation commit, by common-infrastructure.

```text
$ date -u; ls agents/
2026-10-27T11:05:43Z
backend.md
common-infrastructure.md
frontend.md
general-agent-template.md
qa.md

$ python3 -m pytest tests/test_agent_frontmatter.py -q
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_required_keys_present[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_description_is_single_line_trigger[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/backend.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/common-infrastructure.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/frontend.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/general-agent-template.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[agents/qa.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/ai-agent/agents/ai-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/api/agents/api-designer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/data/agents/data-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/devops/agents/devops-engineer.md]
FAILED tests/test_agent_frontmatter.py::test_color_in_allowed_set[packs/mobile/agents/mobile-developer.md]
FAILED tests/test_agent_frontmatter.py::test_base_team_colors - AssertionErro...
FAILED tests/test_agent_frontmatter.py::test_template_lives_outside_agents_dir
32 failed, 2 passed in 0.11s
```

Frontmatter of the 4 base agents (verbatim, before the change) — no `color:`, descriptions say what the role *is*, not when to delegate:

```text
== agents/common-infrastructure.md
---
name: common-infrastructure
description: Environment and shared-config specialist. Handles worktree setup, migrations, shared services, and anything that cuts across backend and frontend. Always runs first before implementers start.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/backend.md
---
name: backend-developer
description: "The project's core backend engineering role — server-side APIs, services, business logic, and data-access layers. Builds production-ready code in the project's stack, scoped to a single TASK_GUIDE and built test-first, while actively guarding against over-engineering (Simplicity First)."
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/frontend.md
---
name: frontend-developer
description: "The project's core frontend engineering role — UI components, client-side state, interactions, and accessibility. Builds performant, accessible interfaces in the project's framework, scoped to a single TASK_GUIDE and built test-first, while guarding against over-engineering (Simplicity First)."
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
== agents/qa.md
---
name: qa-expert
description: "The project's quality and evaluation role — owns the smoke suite, regression safety, and independent verification of acceptance criteria. Acts as the Pillar 3 oracle: confirms a task actually works, with evidence, in a context separate from whoever implemented it."
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
---
```


**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
