# MEMORY.md — fixture (SC1): 3 matching and 20 non-matching index lines

> Rules header. Mentions scripts/validate.sh and T122 on purpose: only `- [` bullets are index lines.

---

## Memory Architecture

- [decisions.md](decisions.md) — decisions
- [glossary.md](glossary.md) — terms
- [learnings.md](learnings.md) — gotchas

---

## Index

### Decisions
- [T122 merged: CI is green again](decisions.md) — red since 2026-09-22
- [T1220 is a longer ID](decisions.md) — must not match its prefix
- [T12 is a shorter ID](decisions.md) — must not match as a prefix
- [lib/validate.sh is a different file](decisions.md) — only the full path disambiguates it
- [validate.sh.bak is a backup, not the script](decisions.md) — extension continues
- [T115 merged: the installer takes no options](decisions.md) — unrelated
- [T116 merged: packs ship dormant](decisions.md) — unrelated
- [T113: update removes unedited dropped files](decisions.md) — unrelated

### Patterns & Gotchas
- [A validator is a consumer of the format](learnings.md) — `scripts/validate.sh` read `!` lines as paths
- [validate.sh runs in CI](learnings.md) — a bare basename mention
- [my_validate.sh is someone else's](learnings.md) — a basename suffix must not match
- [An atomic write changes the mode](learnings.md) — unrelated
- [A subshell cd doesn't wrap a pipeline](learnings.md) — unrelated
- [Clear __pycache__ after a mutation](learnings.md) — unrelated
- [Interactive CLIs need a pty](learnings.md) — unrelated
- [Worktree gotchas](learnings.md) — unrelated

### Glossary
- [Report / Report Slot](glossary.md) — unrelated
- [Pack / Core framework](glossary.md) — unrelated
- [Thinking Report](glossary.md) — unrelated
- [Kanban merge hygiene](learnings.md) — unrelated
