# TASK_GUIDE — T011: Core `wake` SKILL.md — live 4-section cold-start briefing
**Date**: 2026-06-19
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `templates/SKILL_template.md` (standard skill authoring format)
6. Read `.claude/skills/learn/SKILL.md` (prior art — calibrate tone, depth, and structure)
7. Read `.claude/skills/compact-memory/SKILL.md` (prior art — how a memory-reading skill is written)
8. Apply C2 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Write `.claude/skills/wake/SKILL.md` — the Supervisor's mandatory cold-start orientation skill. When invoked at the start of any new session (or by the user via `/wake`), it reads four live authoritative sources and emits a single compact structured briefing of ≤50 lines inline in the conversation.

The four sections, in order:

1. **Recent Changes** — `git log --oneline -10` with commit dates; shows what actually changed since the last session
2. **In-Flight Work** — `PROJECT_KANBAN.md` filtered to in-progress tasks only (not the full board)
3. **Key Memory** — `memory/MEMORY.md` distilled highlights: Decisions section + any Learning Records one-liners
4. **Active Learnings** — scan `memory/learning-records/` for files with `status: active`, summarise the 3 most recent by filename date

**Graceful degradation rule** (mandatory, per section): if a source file is missing, the git repo has no commits, or the LR folder is empty — emit a one-line note for that section (`"No KANBAN found — new project or not yet created."`) and continue. Never error or halt.

**Token efficiency is a first-class design goal**: the entire briefing must stay under 50 lines. The skill must enforce this cap explicitly — if content would exceed it, summarise further rather than overflow.

**Restated intent**: At the start of every session, one `/wake` invocation replaces the Supervisor manually re-reading 500–1000+ lines of raw project files, cutting cold-start cost to ~50 lines of distilled state.

**Out of scope**:
- Writing to any file (wake is read-only — it never modifies MEMORY.md, LRs, or any other file)
- Registering `wake` in CLAUDE.md or README.md (that's T012)
- `--brief` / `--full` depth modes (deferred)
- Monorepo / cross-project support (deferred)
- Auto-trigger via settings.json hook (deferred)

**Requirement Refs**:
- Brainstorming decision 2026-06-19: Option B — Live Cold-Start Skill, 4-section briefing
- Brainstorming decision 2026-06-19: token efficiency first-class goal, ≤50 lines hard cap
- Brainstorming decision 2026-06-19: graceful degradation per section mandatory
- User decision 2026-06-19: `/wake` is mandatory first step, not optional

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `BRAINSTORMING_LOG.md` and `memory/MEMORY.md`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No dependency on T012 — T011 can start immediately

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `.claude/skills/wake/SKILL.md` exists and `grep "^name: wake"` exits 0 | Skill registration requirement |
| 2 | SKILL.md `description` frontmatter names both triggers: Supervisor mandatory first-step + user `/wake` | Trigger requirement |
| 3 | SKILL.md documents all 4 sections in order: Recent Changes (git) → In-Flight Work (KANBAN) → Key Memory (MEMORY.md) → Active Learnings (LRs) | 4-section briefing requirement |
| 4 | SKILL.md documents an explicit ≤50-line output cap with enforcement rule (summarise further if content would overflow) | Token efficiency requirement |
| 5 | Each of the 4 sections has an explicit graceful-degradation rule (what to emit if the source is missing/empty) | Graceful degradation requirement |
| 6 | SKILL.md is read-only — no Write, Edit, or file-creation step anywhere in the workflow | Out-of-scope constraint |
| 7 | Mental walkthrough: simulating `/wake` on this repo produces a coherent ≤50-line briefing covering all 4 sections | End-to-end verification |
| 8 | SKILL.md documents the LR scan step: filter `memory/learning-records/` for `status: active`, sort by filename date, show 3 most recent summaries | Active Learnings section requirement |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `grep "^name: wake" .claude/skills/wake/SKILL.md` | Match | bash |
| 2 | Read SKILL.md workflow | 4 sections present, each with degradation rule | manual review |
| 3 | Count explicit "50" or "50-line" references in SKILL.md | At least 1 — the cap is documented | `grep -c "50" .claude/skills/wake/SKILL.md` |
| 4 | Simulate invoking on this repo (git log exists, KANBAN missing, MEMORY.md present, LRs empty) | 4 section headers present; KANBAN and LR sections show degradation notes; git and memory sections show real content | mental walkthrough |

### Verification Command

```bash
grep "^name: wake" .claude/skills/wake/SKILL.md && \
grep -c "50" .claude/skills/wake/SKILL.md && \
grep -c "degrad" .claude/skills/wake/SKILL.md && \
grep -c "git log" .claude/skills/wake/SKILL.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold (all 4 degradation rules present) | ☐ pass / ☐ fail | |
| Mental walkthrough — `/wake` on this repo produces ≤50-line briefing | ☐ pass / ☐ fail | [sketch the output] |
| Review scope bounded to `.claude/skills/wake/` only | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |

---

## Approach

Write `.claude/skills/wake/SKILL.md` following `templates/SKILL_template.md`. The skill runs entirely in-context — no shell scripts, no file writes. Structure the workflow as 5 steps:

### Step 1 — Source Reads (parallel)

Read all four sources before composing output. If a source fails or is missing, note it and continue — never halt.

| Source | Read | Fallback if missing |
|---|---|---|
| `git log --oneline -10` via Bash | Last 10 commit hashes + messages + dates | `"No git history found."` |
| `PROJECT_KANBAN.md` | Full file, then filter to in-progress rows only | `"No KANBAN file found — project may be new."` |
| `memory/MEMORY.md` | Full file | `"No MEMORY.md found."` |
| `memory/learning-records/LR-*.md` | All files with `status: active` in frontmatter, sorted by filename (descending), top 3 | `"No active Learning Records."` |

### Step 2 — Compose Section 1: Recent Changes

```
## 🔀 Recent Changes
<date> <hash> <message>   ← one line per commit, newest first
...up to 10 commits
```

If 0 commits: emit `"No commits yet."`

### Step 3 — Compose Section 2: In-Flight Work

Filter `PROJECT_KANBAN.md` to rows with status `In Progress` or `🔄`. Show task ID + title only — no description.

```
## 🔄 In-Flight Work
- T009 — learn SKILL.md — core detection + write + promotion loop
```

If no in-progress tasks: emit `"No tasks currently in progress."`.
If no KANBAN file: emit `"No KANBAN found — project may be new or not yet planned."`.

### Step 4 — Compose Section 3: Key Memory

Emit the `### Decisions` section and `### Learning Records` section from `memory/MEMORY.md` verbatim (one-liners only, no headers from other sections). This is already compact — no further summarisation needed unless it exceeds 20 lines, in which case show the 10 most recent entries.

```
## 🧠 Key Memory
- [learn skill: Learning Record System] — LR files in memory/learning-records/...
- [Dark neon theme on HTML report templates] — ...
```

### Step 5 — Compose Section 4: Active Learnings

Scan `memory/learning-records/`. For each `.md` file with `status: active` in its frontmatter, extract: filename (= LR ID + slug) and the first sentence of `## Insight`. Sort by filename descending. Show top 3.

```
## 📖 Active Learnings (3 most recent)
- LR-0003-… — [first sentence of Insight]
- LR-0002-… — [first sentence of Insight]
- LR-0001-… — [first sentence of Insight]
```

If 0 active LRs: emit `"No active Learning Records yet."`.

### Line-count gate (enforce after composing all sections)

Count total output lines across all 4 sections. If > 50:
1. Truncate Section 1 (Recent Changes) to last 5 commits instead of 10.
2. If still > 50, truncate Section 4 (Active Learnings) to top 1.
3. If still > 50, truncate Section 3 (Key Memory) to 5 entries.
4. Append a note: `"(briefing truncated to 50-line cap — run /compact-memory or check sources directly for full detail)"`

---

## Edge Case Checklist

- [ ] **No git repo**: `git log` fails — Section 1 emits `"Not a git repository."` and continues
- [ ] **Git repo with 0 commits**: `git log` returns empty — emit `"No commits yet."`
- [ ] **KANBAN exists but has no in-progress tasks**: Section 2 emits `"No tasks currently in progress."` (not an empty section)
- [ ] **All LRs are superseded (none active)**: Section 4 emits `"No active Learning Records yet."`
- [ ] **MEMORY.md has no Decisions or LR section**: Section 3 emits the raw MEMORY.md index as-is rather than erroring
- [ ] **Very active repo (10 commits overflow 50 lines)**: line-count gate truncates Section 1 first (most expendable — git log is readable elsewhere)
- [ ] **Invoked mid-session (not cold-start)**: skill emits a note `"Note: invoked mid-session — this is a live snapshot, not a session-start state."` at the top
- [ ] **No `memory/learning-records/` folder**: Section 4 emits `"No active Learning Records yet."` (same as empty — folder presence is not required)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/wake/SKILL.md` | Create (new skill) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/MEMORY.md` | `wake` is strictly read-only |
| `memory/learning-records/` | Read-only |
| `PROJECT_KANBAN.md` | Read-only |
| `CLAUDE.md` | Registration belongs to T012 |
| `README.md` | Registration belongs to T012 |

---

## Test Plan

- `grep "^name: wake" .claude/skills/wake/SKILL.md` → exits 0
- `grep -c "50" .claude/skills/wake/SKILL.md` → ≥ 1 (cap is documented)
- `grep -c "degrad" .claude/skills/wake/SKILL.md` → ≥ 4 (one per section)
- Mental walkthrough for this repo:
  - Section 1: shows last 10 commits from `git log`
  - Section 2: KANBAN missing → degradation note
  - Section 3: shows MEMORY.md Decisions + LR one-liners
  - Section 4: LR folder empty → degradation note
  - Total lines ≤ 50 ✅

---

## Completion Checklist

- [ ] `.claude/skills/wake/SKILL.md` created with 5-step workflow
- [ ] Frontmatter `name: wake` matches folder name
- [ ] All 4 sections documented with explicit degradation rules
- [ ] ≤50-line output cap documented with 4-step enforcement procedure
- [ ] Skill is strictly read-only (no Write/Edit steps anywhere)
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T011 ready for Stage 4 review
