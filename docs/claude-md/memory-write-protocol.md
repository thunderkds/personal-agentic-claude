# Memory Write Protocol

> Extracted from `CLAUDE.md` — full detail. See `CLAUDE.md` for the pointer back to this file.

- **Writer**: Supervisor only. Sub-agents never write to memory directly.
- **Hot tier** (`memory/MEMORY.md`): ≤200 lines. Supervisor-curated index. One-line summaries + links to cold files. Injected verbatim into every sub-agent spawn prompt.
- **Cold tier routing**:
  - Architectural or infrastructure decisions → `memory/decisions.md`
  - Canonical biz-domain terms or core domain models → `memory/glossary.md`
  - Specs/requirement clarifications, patterns, gotchas → `memory/learnings.md`
- **Update triggers**: (1) PostToolUse hook on `git push` / `git merge` — diff-driven pass; (2) `/compact-memory` skill — human-invoked; (3) `learn` skill — fires inline during or after a significant exchange.
- **`learn` skill trigger rule**: The `learn` skill is the Supervisor's inline "Reflect & Encode" reflex. Fire it after any exchange that meets the materiality gate (see SKILL.md). Do not fire it on every message.
- **Diff-driven pass procedure**:
  1. `git diff HEAD~1 --name-only` — identify changed files
  2. Grep `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md` for references to those files
  3. Update matched entries in place (fix stale facts, expand with new context)
  4. Append any new decisions or learnings from the session to the appropriate cold file
  5. Summarize new/changed entries as one-liners in `memory/MEMORY.md` (keep ≤200 lines total)
