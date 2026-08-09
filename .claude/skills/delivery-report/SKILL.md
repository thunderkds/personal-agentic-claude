---
name: delivery-report
description: Render a completed task's Demonstration block (BEFORE/AFTER/DELTA/WITNESS) plus its Evidence-table completion count as a self-contained, browsable HTML page. Invoke at Stage 5, after `verify` passes and before merge. Args: task=<TASK_ID> guide=<path/to/TASK_GUIDE_Txxx.md> branch=<branch-name>
---

## Role: Delivery Report Renderer

You hand a task's outcome to a reader as a link, instead of a TASK_GUIDE they'd have to know how to
read. This is the companion to `thinking-report` (Stage 0.5–2 reasoning) and `html-report` (Stage 4
review scores) — this one covers Stage 5 delivery, and it carries **no scored dimension, risk
percentage, or findings table**. A Delivery Report demonstrates what shipped; it does not assess it
(DDR-0003 decision 3).

### Activation

Invoked by the Supervisor at Stage 5, after `Skill({ skill: "verify" })` passes and before merge.

```
Skill({ skill: "delivery-report", args: "task=T053 guide=tasks/TASK_GUIDE_T053.md branch=t053-demonstration-block" })
```

### Workflow

#### 1. Run the renderer

The parser and rendering logic live in one place — `.claude/skills/delivery-report/render.py` — so
the same code path serves **both** guide flavors (implementation and bugfix). T053 gave both flavors
identical Demonstration field names and ordering specifically so this renderer never needs a
flavor-specific branch. If you find yourself about to special-case a flavor here, stop — that means
the two block shapes have drifted apart, and it's a Supervisor decision, not a workaround.

```bash
python3 .claude/skills/delivery-report/render.py <TASK_ID> <guide-path> <branch>
```

This prints the complete rendered HTML to stdout and the save path (`reports/delivery-report_<branch>_<timestamp>.html`)
to stderr. The script already writes the file — you do not need to re-save it.

#### 2. What the renderer does (for context, not to reimplement)

- Resolves both reviewer-filled sections **guide first, then the sibling `tasks/TASK_REVIEW_Txxx.md`**
  (T064), through the one shared resolver `.claude/hooks/lib/guide_sections.py`. A pre-T064 guide
  that still carries them inline renders exactly as it always did; a split pair renders identically.
  A guide whose section is only a `> **Moved.**` pointer counts as not carrying it, so resolution
  falls through. Pass the guide path — the renderer looks for the review file beside it.
- Parses the `## Demonstration` section for BEFORE/AFTER/DELTA using one regex shared by both flavors.
- If the guide's BEFORE points at the bugfix flavor's "Phase 1 repro loop" by name, resolves it from
  the Evidence table's `Repro loop` row rather than printing the pointer text raw.
- Computes the Evidence-table completion count (`filled / total`, plus N/A count) generically over
  whatever rows are present — 9 rows on the implementation flavor, 12 on the bugfix flavor.
- **WITNESS is never read from the guide as free text.** It is always derived from
  `memory/event-trace/<task>.jsonl` (AC7) — a count of tool-call records and their timestamp span, not
  a name. If no trace file or no records exist, it renders as explicitly underived — never a guessed
  or fabricated name. Do not override this with a typed value.
- If neither the guide nor the review file has a `## Demonstration` section at all (a guide predating
  T053, or a split pair whose review file was never created), the report renders that gap explicitly
  instead of crashing.
- If BEFORE/AFTER/DELTA is blank in the guide, the report renders that gap explicitly rather than
  omitting the row or silently succeeding.
- Field text is inserted inside `<pre>` without manual HTML-escaping, matching the established
  `html-report` findings convention.

#### 3. Notify

After the script completes, notify:
`"Delivery report generated: reports/delivery-report_<branch>_<timestamp>.html — <TASK_ID>: <one-line DELTA>."`

### Rules

- Never accept a typed WITNESS value from the conversation — it must come from the trace file via the
  script.
- Never add a scored dimension, risk percentage, or findings table to this report — that is
  `html-report`'s job, for a different artifact, at a different stage (DDR-0003).
- Never emit a `<script>` tag or external URL — pure inline CSS only, matching the existing report
  templates.
