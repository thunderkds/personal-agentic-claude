# 5-Stage Agentic Pipeline

> Extracted from `AGENTS.md` — full detail for Stage 0.5 through Stage 5. See `AGENTS.md` for the pointer back to this file and the Mandatory Session Startup / Hard-Stop Gates, which remain inline there.

These 5 stages are the **extended track** (`docs/claude-md/tracks.md`). The track rule sends big, risky or
multi-session work here, and small low-risk work to the minimal track. Hard-Stop Gate 1 applies to the
extended track only. Gates 2–6 still apply to it unchanged. Gate 5 (a new test with its pasted output) also
applies to the minimal track, through the Decision record's `Checked:` field. In **auto mode** (the user's
`[auto]` tag) the Supervisor asks the user nothing: each stop below names its auto rule, and the
`## Auto mode` table in `docs/claude-md/tracks.md` lists them all.

Strictly follow this order. Never skip or reorder stages.

---

## Stage 0.5: Requirement Grilling → Creative Brainstorming (The First Mind)
**Runs immediately after Phase 0 is confirmed. Must complete before Stage 1.**

### Step 0.5a — Requirement Grilling (PRD gate)

Confirm `PRD.md` exists. Then invoke `grill-with-docs` in requirement mode:
```
Skill({ skill: "grill-with-docs", args: "mode=requirement" })
```

The skill validates `PRD.md` against the Phase 0 answers: FR traceability, NFR completeness, scope clarity, and ambiguity. Resolve all flagged items with the user. Do NOT proceed to brainstorming until the skill reports **PRD gate: PASS**. Auto mode: answer them from the docs and code with Citations; a Choice question goes to a Debate.

### Step 0.5b — Creative Brainstorming

Invoke the `brainstorming` skill:
```
Skill({ skill: "brainstorming" })
```

1. **Divergent Exploration**: The skill analyzes the Phase 0 Context and `PRD.md`, then generates a `BRAINSTORMING_LOG.md` using the template at `templates/BRAINSTORMING_LOG_template.md`.
2. **User Review**: The user must approve one of the brainstormed directions before proceeding. Auto mode: the Supervisor takes the recommended direction and logs the alternatives (flagged).

Only after the user selects a direction (auto mode: the recommended one), invoke:
```
Skill({ skill: "thinking-report", args: "session=brainstorming task=— branch=<branch>" })
```
Save the emitted HTML to `reports/thinking-report_<branch>_<YYYYMMDDTHHMMSS>.html`, then announce:
> "Stage 0.5: Requirement grilling passed. Brainstorming complete. Direction locked. Moving to Stage 1: Environment & Provider Setup."

---

## Stage 1: Environment & Provider Setup
Guide the user through this checklist step by step. Auto mode: the Supervisor does each item itself, by rows 5–10 of the `## Auto mode` table in `docs/claude-md/tracks.md`.

**Checklist**
1. **One-Time Setup (first use only)**
   Run these skills to reduce friction for future sessions:
   - `Skill({ skill: "fewer-permission-prompts" })` — scans transcripts and whitelists common read/bash operations
   - `Skill({ skill: "update-config" })` — configure any automated hooks (e.g. "always run brainstorming before /plan")
   - `Skill({ skill: "settings-setup" })` — offers settings profiles for `.claude/settings.json`; High security when the user skips; add-only, writes after approval

   Auto mode: skip `fewer-permission-prompts` and `update-config` (they change the user's permission settings and hooks) and name them under `Not done:`. Run `settings-setup` as a dry run only: it writes nothing, and its recommendation goes under `Not done:` in the final report.

2. **Multi-CLI Authentication**
   Please list every agentic CLI you have authenticated, the exact command to run it, and which
   model it should spawn at each Complexity level (C0–C3). Record this as the `## CLI Model Table`
   in `PROJECT_SPEC.md` (from `templates/PROJECT_SPEC_template.md`): one row per CLI, one column
   per level. Example: "Claude: claude — C0 haiku, C1 sonnet, C2 sonnet/opus, C3 opus | Codex: codex
   — [ask the user; never guess a Codex/Gemini model name]". A CLI with no row, or an empty cell for
   a level, means `craft-spawn-prompt` will STOP and ask rather than pick a model for it. In auto mode
   the Supervisor reads the table instead of asking; with no row or an empty cell it spawns on the CLI that
   runs this session, with the model this session runs as, logged `SAFER OPTION` with the review flag, and
   never invents another CLI's model name.

   *(Optional)* For non-trivial codebases, a structural code-graph approach — building a dependency graph of the code — can auto-compute hub/centrality (→ Risk, Stage 2) and a change's code-dependency blast radius (→ review scope, Stage 4). It's optional: if absent, those signals stay manual judgment. See the same note in `CLAUDE_LEGACY.md`.

3. **Agent Guide Folder Verification**
   Confirm that the folder `agents/` exists in the project root and contains all required files.
   If any file is missing, output the template for it from `templates/` and ask the user to save it.
   Auto mode: the Supervisor writes it from the template on the task branch.

4. **Git Repository Verification**
   Please run `git status` in your terminal and paste the output here. Auto mode: the Supervisor runs it itself.

5. **`PRD.md` File**
   - Confirm `PRD.md` exists in the project root (generated at end of Phase 0 Step 2).
   - If missing, generate it now using `templates/PRD_template.md` from the Phase 0 answers.

6. **Master `PROJECT_SPEC.md` File**
   - If the file does not exist yet, use `templates/PROJECT_SPEC_template.md` and fill in the Project Context Document.
   - Ask the user to save it as `PROJECT_SPEC.md` in the project root, or confirm it already exists.
   - Auto mode: the Supervisor checks the file, or writes it from the template.

7. **Codebase Map**
   If the project has existing code (not a blank scaffold), run:
   ```
   Skill({ skill: "map-codebase" })
   ```
   This writes `memory/codebase-map.md` — directory tree, entry points, blast-radius hotspots.
   C2/C3 sub-agents will read it for structural orientation; C0/C1 agents skip it.
   Re-run via `/map-codebase` after any major refactor.

8. **Core Domain Models**
   Scan the codebase for domain model and interface files (`Glob` for `models/`, `entities/`, `types/`, `schemas/`, `interfaces/`). Present the findings: "These look like core domain models: [list]. Are they correct? Any missing or excluded?" Record the confirmed models in `memory/glossary.md` under the `## Domain Models` section. Auto mode: record the models the scan found, with their paths (flagged).

After all items are confirmed:
> "Stage 1: Environment & Provider Setup completed successfully. Moving to Stage 1.5: Sub-Agent Architecture."

---

## Stage 1.5: Sub-Agent Architecture (Dynamic Team Design)
Using the locked Project Context Document:
- Reference the **General Agent Template** (`templates/general-agent-template.md`).
- Reference the files in the `agents/` folder.
- Design the exact sub-agent team needed. Always include **Common-Infrastructure-Agent**, **Backend-Implementer**, **Frontend-Implementer**, and **QA-Automation-Agent** as the base team for greenfield projects — unconditional and never gated by any skill.
- If, and only if, the requirement implies a role the base team doesn't cover (e.g. a mobile/data/ML-specific agent), invoke `Skill({ skill: "craft-agent" })` to draft the supplemental roster. This is optional and conditional — do not invoke it as a required step on every pass; skip it entirely when the base team already covers the requirement.
- For each sub-agent, clearly state:
  - Name
  - Role and responsibilities
  - Required skills / expertise
  - Specific rules (only overrides)
  - **CLI & exact spawn command**
  - Reference to its guide in the `agents/` folder

Output in a clear Markdown table, then ask:
"Here is the proposed sub-agent team (with exact CLI commands and references to agents/ folder). Approve or request any modifications?"
Auto mode: no question; the base team (plus `craft-agent` only for an uncovered role) is locked and logged.

Only after explicit user approval (auto mode: at once), announce:
> "Sub-agent architecture locked. Moving to Stage 2: Intent Transformation (Planning)."

---

## Stage 2: Intent Transformation (Planning) — `/plan`

**This stage maps to `/plan` in Claude Code.**

When the user invokes `/plan`, the Supervisor must:
1. Confirm Stage 0.5 (brainstorming) has been completed and a direction approved. If not, run it first.
2. Take the approved Project Context Document and brainstorming direction.
3. Create (or update) `PROJECT_SPEC.md` as the single source of truth using `templates/PROJECT_SPEC_template.md`.
4. Create (or update) `PROJECT_KANBAN.md` as the compact task board using `templates/PROJECT_KANBAN_template.md`.
5. Assign each task three independent labels: **Complexity (C0–C3)**, **Risk (Low/Med/High)**, and **Priority (P0–P2)**. Split any task larger than C3 (an **Epic**) into smaller tasks before generating guides. (Complexity drives agent process; Risk gates `security-review`; Priority sets ordering — see the Complexity matrix in each role guide (`agents/<role>.md`).) When setting **Risk**, factor in whether the task touches a **hub file** — one many others depend on, so its code-dependency blast radius is large. In legacy mode this is recorded in `docs/legacy/risk-hotspots.md`; in greenfield it's a judgment call (optionally informed by a structural code-graph approach — see Stage 1). A hub touch raises Risk a level even when the edit itself is small.
6. If `agents/tech-lead.md` exists (tech-lead pack activated, `packs/tech-lead/PACK.md`), once `PROJECT_SPEC.md` is locked, spawn `tech-lead` to write the document map `docs/architecture/README.md` for user approval. Auto mode: map only, listed in the final report.

**Task State Management (Token-Efficient Design)**
Use two files:
- `PROJECT_SPEC.md` → Full context + detailed task descriptions
- `PROJECT_KANBAN.md` → Compact dynamic board (status updates go here)

**After user approves the task breakdown:** (auto mode: the Supervisor's own breakdown, with no approval step)
- Generate **all** TASK_GUIDE_Txxx.md files (one for every task) using `templates/TASK_GUIDE_template.md`.
- Save every file into the `tasks/` folder (e.g. `tasks/TASK_GUIDE_T001.md`).
- **Board mode `online`** (`.claude/board.json` exists): draft each guide to a scratch file and run `python3 scripts/board_sync.py create --guide <draft.md>` per task instead — the board assigns the ID, the guide becomes the issue description, and `tasks/TASK_GUIDE_<ID>.md` is written as its cache; later edits go back with `board_sync.py update --guide <ID>`.
- In each TASK_GUIDE file, explicitly instruct the sub-agent to read the relevant guide from `agents/`.
- Fill each guide's `## Dependencies & Reachability` section: `Depends on:` names another Task ID this one needs as a precondition (or `None`); `Entry point:` names the literal, grep-able identifier (route, button label, function/consumer name) that reaches this task's output, or `Standalone — N/A` with a one-line reason. This is **advisory, not a Hard-Stop Gate** — `Depends on` is checked (non-blocking warning) by `pre_agent_validate_guide.py` at spawn time; `Entry point` is checked (non-blocking finding) by `code-review` Phase 0.5. It is distinct from `PROJECT_KANBAN.md`'s `## Blocked` table, which remains a manual escape hatch for non-task blockers (external people/APIs/decisions) that can't be checked automatically.

Ask the user to confirm the tasks/ folder has been populated. Auto mode: the Supervisor lists `tasks/` itself.

After confirmation, invoke:
```
Skill({ skill: "thinking-report", args: "session=planning task=— branch=<branch>" })
```
Save the emitted HTML to `reports/thinking-report_<branch>_<YYYYMMDDTHHMMSS>.html`, then announce:
> "Stage 2: Planning completed. All task guides generated in tasks/. Moving to Stage 3: Parallel Execution via Isolation."

---

## Stage 3: Parallel Execution via Isolation

> **The three-pillar chain every task must pass through, in order:**
> **(1) Adapt the requirement** → **(2) Right implementation** → **(3) Evaluation.**
> Each pillar has a gate. A pillar's gate must be green before the next pillar begins — no skipping ahead.

For every task moved to In Progress:
- Common-Infrastructure-Agent creates the git worktree.
- **Pillar 1 gate (before any code):** the spawned agent must confirm the **Requirement Fidelity Gate** in its `TASK_GUIDE_Txxx.md` is checked — restated intent matches the request, terms align with the glossary, and every Acceptance Criterion traces to the requirement. If not, the agent STOPs and asks the Supervisor instead of guessing. Auto mode: the Supervisor signs the gate `auto (Supervisor)`, and settles a sub-agent's `Status: blocked` question through `resolve-question` (a Choice question goes to a Debate).
- **Pillar 2 (implementation):** build the slice test-first (`tdd`), touching only the predicted files. If the slice adds or changes a **DB schema/migration**, run `Skill({ skill: "migration-safety" })` and pass its go/no-go gate **before** the implementation gate goes green.
- The TASK_GUIDE_Txxx.md already exists in tasks/ — no need to regenerate it.
- Invoke `Skill({ skill: "craft-spawn-prompt" })` with the task's guide path and the CLI that will run it — it assembles the spawn prompt, pre-flight-checks it against the spawn hook, and recommends the model by looking the task's **Complexity** up in `PROJECT_SPEC.md`'s `## CLI Model Table` for that CLI (no row/empty cell → it stops and asks, never a Claude-name fallback). Auto mode: on that stop, spawn on the CLI that runs this session, with the model this session runs as (`SAFER OPTION`, flagged). Then issue the `Agent()` call in that worktree using its output.
- **Spawn mode**: every spawn is a background `Agent()` call (`run_in_background`) — the final report and the commits are what the Supervisor reads. Use a CLI pane instead only when the user asks to watch the agent work, or the task runs on a non-Claude CLI. Do not use the T147 sandboxed profile until a nested-userns check passes. A background agent dies with the Supervisor session, so `wake` reports any In Progress task whose worktree has uncommitted changes.
- The sub-agent must read both its TASK_GUIDE_Txxx.md (from tasks/) and the relevant agent guide from agents/.
- **Memory injection**: Paste the task's **memory slice** in every sub-agent spawn prompt, after the task pointer — the output of `python3 skills/craft-spawn-prompt/scripts/memory_slice.py <guide>`, verbatim: the `memory/MEMORY.md` index lines that name the guide's files, its `Depends on` tasks or its ID (T125), plus any `memory/decisions.md` entry whose `**Files**:` line names the guide's files (T145), listed under `### From decisions.md` and dropped first when the cap bites. Then the fallback: *"Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover."* Do **not** paste the whole hot-tier index (≤50,000 characters); nothing loads it for the agent, so the full file is read only when the slice falls short.

Run the app during implementation to catch regressions early:
```
Skill({ skill: "run" })
```

---

## Stage 4: Review
For every task that reaches "Ready for Review" (auto mode: Stage 4 still runs before the run ends — `code-review`, plus `security-review` at Medium/High — because it is not a user stop):

**Pull moment 3 (board mode `online`, FR-009).** Before moving the task to Ready for Review, run `python3 scripts/pull_moment.py review <ID>`. If it prints `<ID>'s guide changed while you were working — review against the new version?`, ask the user before reviewing (auto mode: review against the new version). If it prints `board unreachable — using cache (N unsynced)`, continue on the cache. In board mode `local` it prints nothing.

1. **Code Review** (always):
   ```
   Skill({ skill: "code-review" })
   ```
   Bound the review to the change's **blast radius** — its affected callers, dependents, and tests — rather than re-reading the whole repo. This keeps review focused and token-efficient (the affected set comes from `risk-hotspots.md`/`architecture.md` in legacy mode, or from the predicted files + judgment in greenfield). `code-review` also runs the Entry-Point Reachability Check (Phase 0.5) against the task's declared `Entry point:` field, and prints one line from `scripts/lane_check.py <guide> <base>...HEAD` (three dots) comparing the branch diff to the declared Complexity; it warns and never blocks (T144).

2. **Security Review** (if task Risk Level is Medium or High):
   ```
   Skill({ skill: "security-review" })
   ```

3. **Blast-Radius Analysis** (if task Risk Level is Medium or High and the task touches sensitive data — PII/PHI/credentials/payment data):
   ```
   Skill({ skill: "blast-radius" })
   ```
   Quantifies the breach impact of the exposure surface `security-review` finds.

4. **Migration Safety** (mandatory if the task added or changed a DB schema/migration):
   ```
   Skill({ skill: "migration-safety" })
   ```
   Confirms the migration is reversible, backward-compatible, zero-downtime, and loses no data before it ships. A DB task with a failing or unrun migration-safety gate is **not** review-complete.

5. **Evidence Gate** (always): open the task's `TASK_GUIDE_Txxx.md` **Evaluation & Acceptance** block and confirm the reviewer has filled the **Evidence** table — **especially the "New test(s) cover Acceptance Criteria" row** (test file paths and passing output must be pasted; a blank or unchecked row blocks Done per Hard-Stop Gate 5), the verification command was actually run and its real output pasted in, negative cases hold, and the full smoke suite is still green. For UI tasks: also confirm the three UI Evidence rows (visual regression, design-system compliance, responsiveness) are filled with pasted evidence — blank or ☐ N/A without justification blocks Done per Hard-Stop Gate 6. Also confirm every **Requirement Refs** entry (FR/NFR/US IDs) listed in the task's Pillar 1 section maps to at least one passing Acceptance Criterion. A task with empty evidence rows or uncovered Requirement Refs is **not** review-complete, regardless of how the diff looks. The implementing agent must not be the sole author of its own acceptance test — the Supervisor writes or signs off on the oracle.

6. **HTML Report** (after every review skill that produces findings):
   After each of the above skills completes, invoke:
   ```
   Skill({ skill: "html-report", args: "skill=<skill-name> task=<TASK_ID> branch=<branch>" })
   ```
   Save the emitted HTML block using the Write tool to:
   `reports/<skill-name>_<branch>_<YYYYMMDDTHHMMSS>.html`
   One report per skill per invocation (e.g. `reports/code-review_main_20260618T143022.html`).

7. Address all findings before moving to Stage 5. Update PROJECT_KANBAN.md status. Auto mode: a finding whose fix needs a choice goes to a Debate.

---

## Stage 5: Integration & Verification
After all Stage 4 reviews pass:

1. **Verify the feature works end-to-end**:
   ```
   Skill({ skill: "verify" })
   ```
   Record the observed result in the task guide's **Evidence** table (`verify` row). Do not merge while any evidence row reads fail or is blank.
   The Supervisor starts this run, never in its own session: right after it moves a task to Ready for Review, it runs `python3 .claude/hooks/stop_auto_verify.py --start <ID>` (every task, both tracks, any mode; the Stop hook is the backstop). That headless run writes the `verify` row and its run record; the Supervisor waits for the verdict and reports it. The user may still run `/verify`, and does when the run is blocked or `CLAUDE_AUTO_VERIFY=off` (`docs/claude-md/tracks.md` `### Auto verify (Stop hook)`).
   Auto mode: the Supervisor also writes its own real-run check under the final report's `Checks:` as `auto-checked, not /verify`. It never runs `/verify` in its own session or fills the `verify` row: T182's hook does, or the user.

2. **Confirm smoke tests pass** (coordinate with QA-Automation-Agent).

3. Update `PROJECT_SPEC.md` Memory/Insights section with key learnings.

4. **Memory update** (diff-driven pass — run before `ship`):
   - `git diff HEAD~1 --name-only` — identify files changed in this merge
   - If `agents/tech-lead.md` and `docs/architecture/README.md` both exist (tech-lead pack, `packs/tech-lead/PACK.md`), match this list against the map's watched paths: on a match, spawn `tech-lead` in refresh mode for the matched documents only; no match (or no watched-paths column), nothing.
   - Grep `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md` for references to those files
   - Update matched entries in place (fix stale facts, expand with new context)
   - Append any new decisions or learnings from this session to the appropriate cold file
   - Summarize new/changed entries as one-liners in `memory/MEMORY.md` (keep hot tier ≤50,000 characters)

5. Merge the worktree and close the task on PROJECT_KANBAN.md. In auto mode the merge is never automatic: it waits for the user. After an auto verify pass, the hook moves the row to Done (`docs/claude-md/tracks.md` `### Auto close-out`), and the Supervisor ran item 4 before it stopped (the report's `Memory:` line).

6. **Post-merge release planning** (once all tasks for the milestone are integrated):
   ```
   Skill({ skill: "ship" })
   ```
   Turns the merged tasks/commits into a runnable deployment plan, a rollback plan, and user-facing release notes, then appends a runbook entry. Not in auto mode: `ship` runs after the merge. `ship` **plans and de-risks** the release — it never auto-deploys; the operator executes the plan. A GO also needs the human's approval of the exact `<version> @ <commit>`, recorded in the runbook's Release Log, and the smoke test with its pass condition is written before the deploy step (T149).

Only after all tasks are integrated, announce:
> "Stage 5: Integration complete. All tasks merged. Project milestone delivered."
