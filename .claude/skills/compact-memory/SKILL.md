---
name: compact-memory
description: Human-invocable compaction pass for the two-tier memory system. Use when a cold memory file exceeds ~500 lines, entries look stale, or the hot-tier index feels cluttered. Reads all cold files, flags duplicates and stale entries for human approval, consolidates, and re-syncs the MEMORY.md hot-tier index.
---

## Role: Memory Compaction Specialist

You are the Supervisor running a structured compaction pass on the project memory system. The goal is to keep the hot tier lean (≤200 lines) and the cold files accurate — without deleting anything the human hasn't approved.

### Karpathy Operational Commands

- **Ask vs. Guess**: Never delete an entry without explicit human approval. Flag, present, wait.
- **Simplicity First**: Compact only what is clearly stale or duplicated. Do not reorganise sections speculatively.
- **Surgical Changes**: Touch only `memory/` files. Do not modify CLAUDE.md, task guides, or any other file.
- **Goal-Driven Execution**: Success = cold file line counts reduced, hot-tier index accurate, zero unapproved deletions.

---

### Workflow

#### 1. Size Check

Run:
```bash
wc -l memory/decisions.md memory/glossary.md memory/learnings.md memory/MEMORY.md
```

Report the counts. Flag any cold file exceeding **500 lines** as a compaction candidate. If all files are under 500 lines and the user still invoked this skill, note it and ask if they want to proceed anyway.

#### 2. Stale Detection

For each entry in each cold file, check all of the following heuristics:

**a. Dead file reference** — does the entry cite a file path? If yes:
```bash
# for each cited path, e.g.:
ls memory/decisions.md   # or use Glob
```
If the file no longer exists → mark `<!-- STALE: file deleted -->` inline.

**b. Outdated library version** — does the entry mention a library + version? Cross-check:
```bash
# e.g. grep the version in package.json / pyproject.toml / go.mod
grep -r "library-name" package.json pyproject.toml go.mod 2>/dev/null | head -5
```
If the project has since upgraded past the version in the entry → mark `<!-- STALE: version upgraded -->`.

**c. Duplicate** — is the same fact stated under two different entries or sections? Mark the older/vaguer one `<!-- STALE: duplicate of [other entry] -->`.

**d. Superseded** — is there a newer entry in the same section that contradicts this one? Mark the older one `<!-- STALE: superseded by [newer entry date] -->`.

#### 3. Human Review

Present all flagged entries as a numbered list:
```
Flagged entries (N total):
1. decisions.md §Architecture — "[entry text]" — STALE: file deleted
2. learnings.md §Gotchas — "[entry text]" — STALE: duplicate of entry #3
...

Approve removal of all? Or list numbers to keep (e.g. "keep 2, 5")?
```

**Do not delete anything until the human responds.** Remove the `<!-- STALE: ... -->` comment from any entry the human chooses to keep — leave no markup clutter regardless of outcome.

#### 4. Consolidation

For entries approved for removal: delete them.

For duplicate entries approved for consolidation: merge into a single canonical entry, keeping the most recent date and the clearest wording.

#### 5. Hot-Tier Re-Sync

After cold files are compacted, rewrite the `## Index` section of `memory/MEMORY.md`:
- One line per cold-file section that has content
- Format: `- [Section title](cold-file.md#section) — one-line summary (≤150 chars)`
- Keep total `MEMORY.md` under **200 lines**
- Do not modify the `## Memory Architecture` header block — only the `## Index` section

#### 6. Confirmation Report

Output:
```
Compaction complete.
decisions.md:  [before] → [after] lines
glossary.md:   [before] → [after] lines
learnings.md:  [before] → [after] lines
MEMORY.md:     [before] → [after] lines  ([N] index entries)
Entries removed: [N] | Consolidated: [N] | Kept (human override): [N]
```

---

### Communication Protocol

- **Default Notification**: "compact-memory complete. Cold files: [N] lines saved. Hot tier: [M] entries, [K] lines. [N] stale entries removed (human-approved)."
