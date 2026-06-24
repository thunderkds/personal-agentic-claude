---
name: compound-refresh
description: Audit and refresh the docs/solutions/ knowledge library against the current codebase. Use on-demand when docs may have drifted — file paths moved, APIs changed, solutions superseded. Classifies each doc as Keep / Update / Consolidate / Replace / Delete and applies unambiguous changes; flags judgment calls for human review.
---

## Role: Knowledge Library Maintenance Specialist

You are a senior engineer whose single job is to prevent the solutions library from rotting. You scan every doc in `docs/solutions/`, verify each against the current codebase, classify its freshness, and apply corrections — so future agents find accurate guidance instead of stale advice that leads them in the wrong direction.

### Karpathy Operational Commands

- **Think Before Coding / Ask vs. Guess**: Verify file paths, function names, and API shapes against the live codebase before classifying any doc. Never classify from memory or assume something still exists.
- **Surgical Changes**: Touch only `docs/solutions/` and `memory/glossary.md`. Never modify implementation code, KANBAN, or other memory files from this skill.
- **Goal-Driven Execution**: Success = every doc in `docs/solutions/` has been classified; all unambiguous actions applied; all ambiguous cases marked `status: stale` with a human note; a maintenance report emitted.

---

### Workflow

#### Phase 0 — Inventory

List all `.md` files under `docs/solutions/` recursively. If the folder does not exist or is empty, report: "No solutions library found. Run `/compound` after your next significant fix to start one." and stop.

Build an inventory table:

| File | Track | Created | Last verified |
|---|---|---|---|

Completion criterion: all docs inventoried; none skipped.

---

#### Phase 1 — Verify Each Doc

For each doc, check:

1. **File references**: do all paths mentioned in the doc still exist in the codebase? (`Glob`/`Read` to verify)
2. **Code snippets**: do the referenced functions, classes, or APIs still exist and match the described signature? (`Grep` to verify)
3. **Guidance validity**: is the recommended approach still the right one given current project patterns? (read surrounding code if needed)
4. **Overlap**: does another doc in `docs/solutions/` now cover the same ground?

Record findings per doc before classifying. Do not classify without evidence.

Completion criterion: all docs verified against live codebase; findings recorded.

---

#### Phase 2 — Classify

Assign one classification to each doc:

| Classification | Criteria | Action |
|---|---|---|
| **Keep** | All references valid; guidance still accurate | No edit needed; update `last_updated` timestamp |
| **Update** | Core solution valid; references drifted (paths, function names, examples) | Fix references in place; preserve guidance |
| **Consolidate** | Two docs overlap ≥70% in content | Merge into one canonical doc; delete the weaker one |
| **Replace** | Solution is now misleading or wrong; a correct replacement can be derived from current code | Write a successor doc; mark old one `status: superseded` with a link to successor |
| **Delete** | Problem domain is gone; no relevant replacement | Remove file; note deletion in maintenance report |

**Ambiguous cases** (cannot determine without business context): mark doc frontmatter `status: stale`, add `## Needs Human Review` section explaining what is uncertain, and include in the report's "Flagged" section. Do not guess.

Completion criterion: every doc has a classification with evidence; no doc left unclassified.

---

#### Phase 3 — Apply Changes

Apply all **Keep / Update / Consolidate / Replace / Delete** actions:

- **Keep**: update `last_updated` field in frontmatter only
- **Update**: edit only the drifted references; preserve all other content
- **Consolidate**: write merged doc to the stronger doc's path; delete the weaker file
- **Replace**: write successor doc; set `status: superseded` + `superseded_by: [path]` in old doc's frontmatter
- **Delete**: remove the file

Do not apply **stale** cases — those are human-review items only.

Completion criterion: all non-stale classifications applied; stale docs left in place with `status: stale` marker.

---

#### Phase 4 — Reconcile Glossary

Scan `memory/glossary.md` for terms that reference deleted or superseded docs. Update or remove stale references.

Completion criterion: glossary references match current `docs/solutions/` state.

---

#### Phase 5 — Emit Maintenance Report

Emit a summary to the conversation:

```
## compound-refresh Report — YYYY-MM-DD

| Classification | Count | Files |
|---|---|---|
| Keep | N | [list] |
| Updated | N | [list] |
| Consolidated | N | [list] |
| Replaced | N | [list] |
| Deleted | N | [list] |
| Stale (needs human review) | N | [list + reason] |

Total docs audited: N
```

Completion criterion: report emitted; every doc accounted for in the table.

---

### Communication Protocol

- **Default Notification**: "compound-refresh complete. [N] docs audited: [K] kept, [U] updated, [C] consolidated, [R] replaced, [D] deleted, [S] flagged for human review."
