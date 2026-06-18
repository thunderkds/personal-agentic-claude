---
name: thinking-report
description: Render the Supervisor's reasoning from a completed session (brainstorming, grilling, or planning) as a self-contained HTML page with a Decision box, Trade-Off Matrix, and Assumptions list. Invoke after any brainstorming, grill-with-docs, or /plan session where a direction was locked. Args: session=<brainstorming|grilling|planning> task=<TASK_ID> branch=<branch-name>
---

## Role: Thinking & Decision Visualiser

You transform the reasoning that just occurred in the current session into a self-contained HTML report showing *how* the decision was reached — the problem, the options compared, the chosen path, and the assumptions tracked along the way.

This is the companion to `html-report` (which covers Stage 4 review output). `thinking-report` covers Stage 0.5–2 decision output.

### Activation

Invoked by the Supervisor after a brainstorming, grilling, or planning session concludes and a direction is locked.

```
Skill({ skill: "thinking-report", args: "session=brainstorming task=T001 branch=main" })
```

### Workflow

#### 1. Read the session output from context

The output of the just-completed session is already in the current conversation above. Identify:

- **The problem** — what question or challenge was being decided
- **The options** — typically 2–4 named paths or approaches that were evaluated
- **The chosen option** — which one was selected (or recommended)
- **The criteria** — what dimensions were used to compare options (e.g. Code Volume, Offline Support, Regression Risk, Invasiveness)
- **The rationale** — why the chosen option won
- **Assumptions** — explicit assumptions stated, items deferred, and questions resolved during the session

#### 2. Build the Decision Box slots

| Slot | Value |
|------|-------|
| `{{PROBLEM_STATEMENT}}` | One sentence: what decision was being made |
| `{{DECISION_STATEMENT}}` | The chosen option name + one-line summary |
| `{{DECISION_RATIONALE}}` | 2–4 sentences: the "why" — what made this the best path |

#### 3. Build the Trade-Off Matrix

**Header row** — one `<th>` per option. Mark chosen column with `class="col-chosen"`. Include option name and ✅ on the chosen one.

```html
<th class="criteria-label"></th>
<th>Option A — Shell Pipe</th>
<th class="col-chosen">Option B — LLM Renderer ✅</th>
<th>Option C — Dedicated Skill</th>
```

**Body rows** — one `<tr>` per criterion. Use these cell classes:
- `cell-yes` → ✅ Yes (green)
- `cell-partial` → ⚠️ Partial (amber)
- `cell-no` → ❌ No (red)

Always add `col-chosen` as a second class on `<td>` cells in the chosen column.

```html
<tr>
  <td class="criteria-label">Offline / no CDN</td>
  <td class="cell-yes">✅ Yes</td>
  <td class="col-chosen cell-yes">✅ Yes</td>
  <td class="cell-partial">⚠️ Partial</td>
</tr>
```

Standard criteria to include (use what applies, skip what doesn't):
- Offline / no CDN
- Code volume (Low / Medium / High)
- Regression risk (Low / Medium / High)
- Invasiveness (files touched)
- Reversibility
- Complexity
- Any session-specific criteria that were explicitly discussed

**Minimum 3 criteria rows. Maximum 8.**

#### 4. Build the Assumptions list

One `<li>` per item. Classify each with a tag:
- `tag-resolved` (green) — question answered during the session
- `tag-assumption` (amber) — taken as given, not explicitly confirmed
- `tag-deferred` (purple) — acknowledged but intentionally left for later

```html
<li><span class="tag tag-resolved">Resolved</span> Score scale is 0–100% — confirmed by user.</li>
<li><span class="tag tag-assumption">Assumption</span> No Python runtime guaranteed — POSIX sh only.</li>
<li><span class="tag tag-deferred">Deferred</span> Flowchart section — revisit after matrix pilot.</li>
```

Include all material assumptions from the session. Minimum 2 items.

#### 5. Fill the remaining slots

| Slot | Value |
|------|-------|
| `{{SESSION_TYPE}}` | `Brainstorming` / `Grilling` / `Planning` |
| `{{BRANCH}}` | branch arg value |
| `{{DATE}}` | today's date, e.g. `2026-06-18` |
| `{{BADGE_CLASS}}` | `green` if direction locked; `yellow` if pending approval; `blue` if deferred |
| `{{BADGE_LABEL}}` | `Direction Locked` / `Pending Approval` / `Deferred` |
| `{{SESSION_REF}}` | source file — e.g. `BRAINSTORMING_LOG.md` or `tasks/TASK_GUIDE_T001.md` |
| `{{TASK_ID}}` | task arg value, or `—` |
| `{{TIMESTAMP}}` | ISO-8601 datetime, e.g. `2026-06-18T14:30:22` |

#### 6. Emit the complete HTML

Read `templates/thinking_report_template.html` from the project root. Populate every `{{SLOT}}`. Output as a single fenced code block:

````
```html
<!DOCTYPE html>
...complete filled template...
```
````

Then output exactly this save instruction:

```
SAVE → reports/thinking-report_<branch-arg>_<YYYYMMDDTHHMMSS>.html
```

### Rules

- Never emit a `<script>` tag or external URL — pure inline CSS only
- Never leave a `{{SLOT}}` unfilled — use `—` for unknown text values, `0` is not applicable for text slots
- The Trade-Off Matrix must have at least 2 option columns and 3 criteria rows
- Copy rationale and assumption text verbatim from the session output — do not paraphrase
- If fewer than 2 options were discussed, create a 2-column matrix with "Chosen Approach" vs "Alternative Not Taken" and reconstruct the implicit trade-off from context

### Communication Protocol

After the save instruction, notify:
`"Thinking report generated: reports/thinking-report_<branch>_<timestamp>.html — Decision: <one-line summary>."`
