# Memory Write Protocol

> Extracted from `CLAUDE.md` — full detail. See `CLAUDE.md` for the pointer back to this file.

- **Writer**: Supervisor only. Sub-agents never write to memory directly.
- **Hot tier** (`memory/MEMORY.md`): ≤50,000 characters. Supervisor-curated index. One-line summaries + links to cold files. Passed to every sub-agent as a **path to read**, not pasted into the spawn prompt — the agent opens it itself as a mandatory startup step.
  - The character budget is enforced by `.claude/hooks/tests/test_token_audit_format.py` and is a **ratchet**: `/compact-memory` may lower it, nothing may raise it to accommodate growth. It replaced a 200-*line* cap that stayed green while the file grew 15.5% in characters.
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
  5. Summarize new/changed entries as one-liners in `memory/MEMORY.md` (keep ≤50,000 characters total)
