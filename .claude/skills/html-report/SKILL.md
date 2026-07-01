---
name: html-report
description: Generate a self-contained HTML report from the immediately preceding Stage 4 skill output (code-review, security-review, blast-radius). Produces scored dimensions (Risk %, Code Quality %, Adaptation Effort %) with progress bars, a findings table, and summary prose. Invoke immediately after any Stage 4 skill completes. Args: skill=<name> task=<TASK_ID> branch=<branch-name>
---

## Role: HTML Report Renderer

You transform the output of the immediately preceding Stage 4 skill into a self-contained HTML report page using the project's report template.

### Activation
Invoked by the Supervisor immediately after `code-review`, `security-review`, or `blast-radius` completes.

```
Skill({ skill: "html-report", args: "skill=code-review task=T001 branch=main" })
```

### Workflow

#### 1. Read the preceding skill output
The output of the just-completed Stage 4 skill is already in the current conversation context above. Read it carefully. Identify:
- All findings (each with severity: High / Med / Low / Info, file path, line range, description)
- The overall narrative / summary prose
- Any explicit risk signals, vulnerability classifications, or hardening recommendations

#### 2. Score the three dimensions (0–100 integers)

**Risk % (0 = no risk, 100 = critical risk)**
- Count High findings: each adds ~15 pts
- Count Med findings: each adds ~7 pts
- Count Low findings: each adds ~2 pts
- Security vulnerabilities (from security-review or blast-radius) add extra weight
- Cap at 100

**Code Quality % (0 = poor, 100 = excellent)**
- Start at 90
- Subtract per High finding: −12
- Subtract per Med finding: −6
- Subtract per Low finding: −2
- Add back for positive signals (good test coverage, clear structure mentioned in narrative): +5 each
- Floor at 5

**Adaptation Effort % (0 = no work, 100 = major rework required)**
- Estimate total effort to address all findings
- 1–2 trivial fixes: ~10–20%
- 3–5 moderate fixes: ~30–50%
- Many fixes or architectural changes: ~60–90%

**Overall health (badge):**
- Derive from Risk score: 0–30 → `green` / "Healthy", 31–65 → `yellow` / "Needs Attention", 66–100 → `red` / "Critical"
- If Code Quality < 40, bump badge one level worse (green→yellow, yellow→red)

#### 3. Build the findings rows

For each finding, produce one `<tr>` block. Severity class mapping:
- High → `sev-high`
- Med → `sev-med`
- Low → `sev-low`
- Info → `sev-info`

Wrap the finding description in `<pre>` — do NOT manually HTML-escape; `<pre>` handles display safely.

```html
<tr>
  <td><span class="sev sev-high">High</span></td>
  <td><code>path/to/file.sh</code></td>
  <td>42–55</td>
  <td><pre>Unquoted variable $TARGET_DIR in rm call — word-splitting can delete wrong path.</pre></td>
</tr>
```

If the preceding skill produced no discrete findings (e.g. blast-radius narrative only), emit one info row summarising the top concern.

#### 4. Emit the complete HTML

Read `templates/report_template.html` (it is in the project root `templates/` folder). Populate every `{{SLOT}}` with the values derived above. Output the result as a single fenced code block:

````
```html
<!DOCTYPE html>
...complete filled template...
```
````

Slot reference:

| Slot | Value |
|------|-------|
| `{{SKILL_NAME}}` | Friendly name from args (e.g. `Code Review`, `Security Review`, `Blast Radius`) |
| `{{BRANCH}}` | branch value from args |
| `{{DATE}}` | Today's date, e.g. `2026-06-18` |
| `{{OVERALL_CLASS}}` | `green` / `yellow` / `red` |
| `{{OVERALL_LABEL}}` | `Healthy` / `Needs Attention` / `Critical` |
| `{{RISK_SCORE}}` | Integer 0–100 (bare number, no `%`) |
| `{{QUALITY_SCORE}}` | Integer 0–100 |
| `{{EFFORT_SCORE}}` | Integer 0–100 |
| `{{FINDINGS_ROWS}}` | All `<tr>` blocks concatenated |
| `{{SUMMARY_PROSE}}` | The skill's narrative summary, plain text |
| `{{MODEL}}` | `claude-sonnet-5` (or the model in use) |
| `{{TASK_ID}}` | task value from args, or `—` |
| `{{TIMESTAMP}}` | ISO-8601 datetime, e.g. `2026-06-18T14:30:22` |

#### 5. Instruct the Supervisor to save

After the fenced block, output exactly this line so the Supervisor knows what to do:

```
SAVE → reports/<skill-arg>_<branch-arg>_<YYYYMMDDTHHMMSS>.html
```

Example: `SAVE → reports/code-review_main_20260618T143022.html`

The Supervisor uses the Write tool to save the HTML block to that path.

### Rules
- Never omit a slot — if a value cannot be determined, use `0` for scores or `—` for text slots
- Never add CDN links, external font references, or `<script>` tags — pure inline CSS only
- The output must be a single, valid, self-contained HTML file that opens correctly in a browser with no network access
- Do not summarise or paraphrase findings — copy them verbatim from the preceding skill output

### Communication Protocol
After saving, notify: "HTML report generated: `reports/<filename>.html` — Risk: X%, Quality: Y%, Effort: Z%."
