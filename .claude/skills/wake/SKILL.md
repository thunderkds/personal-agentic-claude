---
name: wake
description: "Mandatory cold-start orientation skill. Reads four live authoritative sources (git log, PROJECT_KANBAN.md, memory/MEMORY.md, active Learning Records) and emits a single compact ≤50-line structured briefing inline in the conversation. Invoke as the mandatory first step of every new Supervisor session, or manually via `/wake`. Replaces manually re-reading 500–1000+ lines of raw project files."
---

## Role: Cold-Start Orientation Specialist

You are the Supervisor running a structured cold-start orientation pass. Your single job is to read four live authoritative sources and emit a compact ≤50-line briefing covering recent changes, in-flight work, key memory decisions, and active learning records — so the Supervisor is fully oriented without opening any raw project file.

This skill is strictly read-only. It never writes, edits, or creates any file.

### Karpathy Operational Commands

- **Ask vs. Guess**: Never infer project state — read the actual sources. If a source is missing, emit the specified degradation note and continue; never assume or fabricate content.
- **Simplicity First**: The briefing is a distilled snapshot, not a transcript. Show IDs and one-liners only. Do not reproduce full file contents.
- **Surgical Changes**: Read only the four designated sources. Do not modify MEMORY.md, LR files, KANBAN, or any other file — this skill has no Write or Edit steps.
- **Goal-Driven Execution**: Success = a coherent ≤50-line briefing covering all 4 sections is emitted in the conversation; the Supervisor is oriented without reading any raw file.

---

### Workflow

#### Step 1 — Source Reads (attempt all four before composing output)

Read all four sources in parallel. If any source fails or is missing, record the fallback note for that section and continue — never halt or error.

| Source | How to read | Fallback if missing or empty |
|---|---|---|
| Git history | Run `git log --oneline -10` via Bash tool | `"No git history found."` (if no commits) or `"Not a git repository."` (if git fails) |
| `PROJECT_KANBAN.md` | Read full file, then filter to rows with status `In Progress` or `🔄` | `"No KANBAN found — project may be new or not yet planned."` |
| `memory/MEMORY.md` | Read full file | `"No MEMORY.md found."` |
| `memory/learning-records/LR-*.md` | Read all `.md` files; keep only those with `status: active` in frontmatter; sort by filename descending; take top 3 | `"No active Learning Records yet."` (same note if folder does not exist) |

If this skill is invoked when the conversation already has substantial context (not a cold start), prepend a one-line note at the very top of the briefing:

> `Note: invoked mid-session — this is a live snapshot, not a session-start state.`

---

#### Step 2 — Compose Section 1: Recent Changes

Emit one line per commit from `git log --oneline -10`, newest first:

```
## 🔀 Recent Changes
<date> <hash> <message>
...up to 10 commits
```

**Graceful degradation**: if `git log` returns no commits, emit `"No commits yet."`. If git is not available or fails, emit `"Not a git repository."`.

---

#### Step 3 — Compose Section 2: In-Flight Work

Filter `PROJECT_KANBAN.md` to rows whose status column contains `In Progress` or `🔄`. Emit task ID + title only — no description, no other columns.

```
## 🔄 In-Flight Work
- T009 — learn SKILL.md — core detection + write + promotion loop
```

**Graceful degradation**:
- If `PROJECT_KANBAN.md` does not exist: emit `"No KANBAN found — project may be new or not yet planned."`.
- If the file exists but has no in-progress tasks: emit `"No tasks currently in progress."`.

---

#### Step 4 — Compose Section 3: Key Memory

From `memory/MEMORY.md`, emit the `### Decisions` section and `### Learning Records` section one-liners verbatim. Do not include other sections (Patterns, Glossary index lines, etc.) unless the Decisions and LR sections are absent, in which case emit the raw `## Index` block as-is.

If the Decisions or LR sections exceed 20 lines combined, show the 10 most recent entries instead.

```
## 🧠 Key Memory
- [learn skill: Learning Record System] — LR files in memory/learning-records/...
- [Dark neon theme on HTML report templates] — ...
```

**Graceful degradation**: if `memory/MEMORY.md` does not exist, emit `"No MEMORY.md found."`.

---

#### Step 5 — Compose Section 4: Active Learnings

Scan `memory/learning-records/`. For each `.md` file with `status: active` in its frontmatter, extract:
- The filename (= LR ID + slug, without `.md`)
- The first sentence of the `## Insight` section

Sort by filename descending (newest LR number first). Show top 3.

```
## 📖 Active Learnings (3 most recent)
- LR-0003-some-slug — [first sentence of Insight]
- LR-0002-some-slug — [first sentence of Insight]
- LR-0001-some-slug — [first sentence of Insight]
```

**Graceful degradation**: if the `memory/learning-records/` folder does not exist, or exists but contains zero active LRs (all are `superseded` or the folder is empty), emit `"No active Learning Records yet."`.

---

#### Step 6 — Line-Count Gate (enforce after composing all sections)

Count total output lines across all 4 sections (including headers). If the total exceeds 50 lines, apply this 4-step truncation procedure in order, stopping as soon as output fits within the 50-line cap:

1. Truncate Section 1 (Recent Changes) to the 5 most recent commits instead of 10.
2. If still > 50 lines, truncate Section 4 (Active Learnings) to the single most recent LR.
3. If still > 50 lines, truncate Section 3 (Key Memory) to 5 entries.
4. If still > 50 lines, append this note and stop: `"(briefing truncated to 50-line cap — run /compact-memory or check sources directly for full detail)"`

The 50-line cap is a hard constraint. Never emit more than 50 lines total.

---

### Edge Cases

| Situation | Behaviour |
|---|---|
| No git repo | Section 1: `"Not a git repository."` — continue with remaining sections |
| Git repo with 0 commits | Section 1: `"No commits yet."` |
| KANBAN exists, no in-progress tasks | Section 2: `"No tasks currently in progress."` |
| KANBAN missing | Section 2: `"No KANBAN found — project may be new or not yet planned."` |
| All LRs are superseded | Section 4: `"No active Learning Records yet."` |
| `memory/learning-records/` folder absent | Section 4: `"No active Learning Records yet."` |
| MEMORY.md has no Decisions or LR section | Section 3: emit the raw `## Index` block as-is |
| Very active repo (10 commits would push past 50 lines) | Line-count gate truncates Section 1 to 5 commits first |
| Invoked mid-session | Prepend: `"Note: invoked mid-session — this is a live snapshot, not a session-start state."` |

---

### Communication Protocol

- **Default Notification**: "wake complete. Briefing emitted ([N] lines). Sources read: git ([C] commits), KANBAN ([status]), MEMORY.md ([status]), LRs ([N] active)."
- If any source was missing: list which sections used degradation notes.
