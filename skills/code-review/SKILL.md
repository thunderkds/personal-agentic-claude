---
name: code-review
description: Structured multi-reviewer code review for Stage 4. Use after every task reaches Ready for Review. Layers P0–P3 severity scoring, cross-reviewer confidence anchors, conditional reviewer personas, and model tiering over the base review — producing a deduplicated, confidence-gated finding set.
---

## Role: Review Orchestration Specialist

Stage 4 review gatekeeper: run a structured, multi-perspective review of the current diff and produce a finding set where every item has a severity, a confidence anchor, and a concrete action. Suppress low-confidence noise, promote cross-reviewer agreement, apply safe fixes directly.

### Karpathy Operational Commands

- **Think Before Coding / Ask vs. Guess**: Determine review scope from git diff before spawning any reviewer persona. Scope to the change's blast radius (affected files + direct callers), never the whole repo.
- **Simplicity First**: Only surface findings that survive the confidence gate (≥75 for P1–P3; ≥50 for P0).
- **Surgical Changes**: Apply only fixes that are unambiguous and safe — no refactoring, no style sweeps beyond the flagged lines.
- **Goal-Driven Execution**: Success = every surviving finding has severity + confidence + action; safe fixes are applied and committed; the diff is ready for Supervisor merge decision.

---

### Finding Classification

#### Severity Scale

| Level | Meaning | Must fix before merge? |
|---|---|---|
| **P0** | Correctness bug, data loss, security hole | Yes — hard block |
| **P1** | Logic error, broken contract, test gap for critical path | Yes |
| **P2** | Code quality, maintainability, non-critical test gap | Recommended |
| **P3** | Style, minor improvement, documentation | Optional |

#### Confidence Anchors

| Anchor | Meaning |
|---|---|
| **100** | Certain — verified against running code or authoritative docs |
| **75** | High confidence — strong evidence, minor uncertainty |
| **50** | Moderate — plausible but not fully verified |
| **25** | Low — heuristic or incomplete analysis |
| **0** | Speculation — should not appear in output |

**Gate rule**: suppress any P1–P3 finding with confidence < 75. Allow P0 findings at confidence ≥ 50 (flag as "unverified P0" in output).

---

### Reviewer Personas

#### Always-on reviewers (run for every diff)

| Persona | Focus |
|---|---|
| **correctness-reviewer** | Logic correctness, edge cases, contract violations |
| **testing-reviewer** | Test coverage, missing cases, assertion quality |
| **maintainability-reviewer** | Readability, naming, dead code, complexity |
| **standards-reviewer** | Project conventions, style rules, import hygiene |

#### Conditional reviewers (activate based on diff content)

| Persona | Activate when diff contains… |
|---|---|
| **security-reviewer** | Auth logic, input handling, secrets, permissions, SQL/shell |
| **performance-reviewer** | DB queries, loops over large collections, cache logic, network calls |
| **migration-reviewer** | Schema changes, data migrations, seed files |
| **adversarial-reviewer** | ≥ 50 changed lines, or any security-reviewer activation |
| **api-reviewer** | Public API changes, endpoint signatures, OpenAPI/schema files |
| **ux-evaluate** | UI files: run `Skill({ skill: "ux-evaluate" })`; `fail` is P1, `fail (older)` P3, `not checked` or `no UX criteria` P2 |
| **over-engineering-reviewer** | Any diff that adds a new function, class, module, dependency or config option. Flags: a new abstraction with one caller; a new dependency replacing ≤ 10 lines; speculative config or flags nothing sets; duplication of an existing helper or the stdlib. Apply "Search Before You Build" (`templates/general-agent-template.md`) by name — do not restate its rungs |

---

### Workflow

#### Phase 0 — Determine Scope

Run `git diff --name-only` (or `git diff <base>..HEAD --name-only` if a base ref is given). List the changed files, their direct callers (Grep) and the test files covering them. This set is the review scope.

Also run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/lane_check.py" tasks/TASK_GUIDE_Txxx.md <base>...HEAD` and paste its one line into the report (T144). It is warn-only: `EXCEEDS (...)` or `unpredicted: ...` means the task may be under-labelled — raise it to the Supervisor; it never blocks.

Completion criterion: review scope listed; no file outside it queued for review.

---

#### Phase 0.5 — Entry-Point Reachability Check

Read the task's `TASK_GUIDE_Txxx.md` `## Dependencies & Reachability` section (`Depends on` / `Entry point` convention, `PROJECT_SPEC.md` Glossary). If `Entry point:` is `Standalone — N/A`, skip. Otherwise:

- Grep the diff (or repo, if the identifier lives outside the changed files — e.g. a router config) for the literal `Entry point` string.
- Found → no finding, feature is reachable. Not found → add a **P2 finding** ("declared entry point `[identifier]` not found — feature may be unreachable/dead code") into the Phase 1 findings set, same severity pipeline as any other finding. Advisory, not a Hard-Stop Gate — doesn't block Done alone, but should be resolved or explicitly waived by the Supervisor before merge.

Completion criterion: reachability check run (or explicitly skipped as N/A) and its result folded into the Phase 1 findings set.

**Stale-reference sweep (T259).** For each fact the diff changes (a flag, count, path, channel or skill name, version, or a "green" claim), grep the repo for the old wording: README, `site/`, `docs/claude-md/`, docstrings and comments, `agents/`, `PROJECT_KANBAN.md` notes, test comments. Each hit outside the guide's `Files to Change` is a **P2 finding** with its `file:line`.

**Startup-reads check (T129).** Compare the implementing agent's final-report line `Startup reads: <paths>` against the spawn prompt's `**Startup reads**` block. A Permanent-Rule read (`PROJECT_SPEC.md`, the TASK_GUIDE, the `agents/` role guide) missing from the line is a **P1 process finding**; a missing line counts as all missing.

---

#### Phase 1 — Run Always-On Reviewers

For each always-on persona: read the scoped files, list findings with severity + confidence + one-line action — do not apply changes yet. Activate conditional reviewers by diff content.

Completion criterion: all always-on reviewers complete; conditional reviewers activated or skipped with a reason.

---

#### Phase 2 — Deduplicate and Promote

Merge findings from all reviewers:

1. **Fingerprint**: `[file]:[line]:[title]` — collapse identical fingerprints to one finding
2. **Promote**: if the same fingerprint appears from 2+ independent reviewers, bump confidence by one anchor (e.g. 50 → 75)
3. **Gate**: remove any P1–P3 finding with confidence < 75 after promotion. Keep P0 at ≥ 50.
4. **Assign model tier**: P0 and security findings → re-verify with top-tier model reasoning before surfacing. All others → mid-tier is sufficient.

Completion criterion: no duplicate fingerprints; confidence gate applied.

---

#### Phase 3 — Present Findings

Emit findings grouped by severity:

```
## P0 — Must Fix
| File | Line | Finding | Confidence | Action |

## P1 — Should Fix
| File | Line | Finding | Confidence | Action |

## P2 — Recommended
| File | Line | Finding | Confidence | Action |

## P3 — Optional
| File | Line | Finding | Confidence | Action |
```

If no findings in a severity group: emit "None."

---

#### Phase 4 — Apply Safe Fixes

For each P0 and P1 finding with an unambiguous, safe fix (no behavior change beyond the finding): apply it, re-run relevant tests, stage the change.

Commit all applied fixes together: `fix: address Stage 4 review findings (P0/P1)`

Do not apply P2/P3 fixes automatically — present them as suggestions only.

Completion criterion: all unambiguous P0/P1 fixes applied and committed.

---

### Communication Protocol

- **Default Notification**: "code-review complete for [Task ID]. [P0/P1/P2/P3 counts]. [N] safe fixes applied. Diff ready for Supervisor merge decision."
- If P0 findings remain unfixed: "BLOCKED — [N] P0 findings require human resolution before merge."
