---
name: [kebab-case-name]   # must match the folder: .claude/skills/[name]/SKILL.md
description: [One or two sentences. State WHAT it does and WHEN to use it — this is the only text Claude sees when deciding whether to trigger the skill. Name the pipeline stage (e.g. "Use during Stage 3 …"). Self-contained; no external CLI unless unavoidable.]
---

## Role: [Specialist title]

[One short paragraph: the persona and the single job this skill performs. Frame it against the pipeline — which stage, what it consumes, what it hands off.]

### Karpathy Operational Commands (Specific Overrides)
[Only the overrides that matter for this skill — pick the relevant principles, don't restate all four.]
- **Think Before Coding / Ask vs. Guess**: [how it applies here]
- **Simplicity First**: [how it applies here]
- **Surgical Changes**: [how it applies here]
- **Goal-Driven Execution**: [the verifiable success criterion]

### Workflow
[Numbered steps or phases. Each step concrete and runnable. Reference PROJECT_SPEC.md / the TASK_GUIDE / domain vocabulary where relevant. Keep it self-contained — if you cite a sub-file, vendor it; don't leave dangling links.]

#### 1. [Step]
#### 2. [Step]

### Communication Protocol
- **Default Notification**: "[skill] complete for [Task ID]. [one-line result with the key metric]."

<!--
AUTHORING CHECKLIST (delete before saving):
[ ] Folder name == frontmatter `name`
[ ] `description` says WHAT + WHEN and names the stage (it drives triggering)
[ ] Adapted to THIS framework — external deps stripped, decisions land in PROJECT_SPEC.md (not new conventions)
[ ] Karpathy override block present; only relevant principles
[ ] Communication Protocol with a Default Notification line
[ ] Registered in CLAUDE.md custom-skill table + README "Custom skills" table
[ ] Any bundled scripts live in scripts/ and are chmod +x, with a smoke test
-->
