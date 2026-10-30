# BRAINSTORMING_LOG.md — Companion Scoring (easy-verifier + easy-ui at the Evidence Gate)
**Date**: 2026-10-28 · **Tier**: Standard · **Input**: `PRD_companion-scoring.md` (FR-001..FR-013, decisions D1–D5)

---

## The Problem Space

The locked decisions fix *what* the gate does: a `changes`-scope score becomes an Evidence row, `overall < 80`
or a failing `change_risk` rule makes it `fail`, the existing merge hook refuses that row, the kit answers the
verifier's evaluate gate from evidence it already holds, easy-ui is one named option for the three UI rows, and a
missing tool degrades to an `N/A` row instead of a stall. What is open is *where the scoring lives in the pipeline*
and therefore what cannot be forgotten.

Verified facts (read in the two repos and this one, 2026-10-28):

- **`task` scope cannot satisfy the floor.** `change_risk.py:260` abstains unless the scope is in `RATED_SCOPES`,
  with the reason `SCOPE_ONLY = "change risk is rated at changes/worktree scope only"` (`change_risk.py:91`). FR-002
  requires `change_risk`, so the row must be backed by a `changes` (or `worktree`) run. **OQ-001 is closed by the
  tool's own behaviour, not by preference:** `changes --ref <base>...HEAD`. The kit-aware `task --task-id` scope stays
  useful for `requirement-fidelity` against a guide's Acceptance Criteria table
  (`requirement_fidelity.py:8,95,225`) but can never produce the sharp half of the floor.
- **A scoring session is 1–3 `score` calls, then an optional `write_report`** (`docs/SCORING_FLOW.md`). Round 1 may
  ask `picks`; round 2 may ask `gate_evaluations`; round 3 always returns the final result. `needs_input` is MCP-only:
  "The CLI runs the same core but never asks: one pass, rules-only ratings, no `needs_input`."
- **A gate answer's shape is fixed** (`mcp_server.py:150`): `"gate_evaluations": {dimension: {"score": 0-100,
  "confidence": 0-1, "evidence_refs": [...]}}`, and the engine blends it at `w = 0.5 × confidence`.
- **Findings get a separate assessment, never blended** (`docs/SCORING_FLOW.md`, "Findings, when passed, get a
  separate **assessment**. It is shown next to the rating with any divergence"). The kit's Stage 4 `code-review`
  already produces exactly this shape (P0–P3 findings), so the divergence between the kit's reviewer and the rules is
  available for free.
- **The merge hook reads no Evidence row but `verify`.** `pre_bash_block_unsafe_merge.py:496-510` checks
  `has_filled_verify_row(tid)` **and** `trace_shows_verification(tid)` per Ready-for-Review task, and nothing else. A
  `fail` in any other row does not block today. FR-004 is therefore a real code change, not a restatement.
- **The hook already distrusts text.** The same lines reject an evidence row with no matching tool call in
  `memory/event-trace/<task>.jsonl`, with the comment "The text claim alone is not trusted (the model can lie about
  success)." FR-005 reuses that rule against the verifier's report file.
- **Every `SKILL.md` must stay ≤ 8192 bytes.** Enforced by tests (`tests/test_auto_mode.py:406,599,663`,
  `tests/test_board_triage.py:232`) because `lib/harness-fetch.sh` skips a Codex skill over 8 KB.
- **New skills ship automatically.** `MANIFEST:45` carries one line, `skills  codex=.codex/skills`, for the whole
  directory. No MANIFEST edit is needed per skill.
- **The honesty test blocks the honest sentence.** `tests/test_site_content.py:820` sets
  `HONESTY_PHRASES = ("the kit uses", "ships with", "built in", "required")` and asserts none appear inside `#mcps`.
  "never required" contains `required`, so FR-012 must re-base the blocklist, not just rewrite the copy.
- **`ui-test` was built once and never landed.** `memory/decisions.md:109` carries a `STALE` marker: the
  2026-07-01 skill exists only on the unmerged branch `feat/ui-test-mcp-integration` (`6f08d4a`). It is prior art to
  read, not code to trust.

---

## Questions for the User

1. Which path (below)? Asked in chat with the enforcement consequence of each spelled out.

---

## Alternative Paths

### Path A — The Simple Path: a standalone `score` skill at Stage 4

A new skill beside `code-review`, `security-review` and `blast-radius`. It runs the 1–3 round MCP session at
`scope=changes`, `ref=<base>...HEAD`, passes the preceding `code-review` findings as `findings`, answers
`change_kind` and `gate_evaluations`, calls `write_report`, and writes the row. The degradation ladder lives in the
skill's own text. Enforcement is the hook (FR-004): a task that never scored has no row, and an unfilled row is
treated exactly as an unfilled `verify` row.

**Pros**
- Matches the shape of every other Stage 4 skill, so there is nothing new to learn and nothing new to document.
- Invokable alone: "score this branch" works without running a review.
- The thing that can be forgotten is caught by the hook, which FR-004 already pays for.
- Testable on its own: the row-writing contract is one skill's output.

**Cons**
- A new skill is one more thing a Supervisor must remember at Stage 4, and LR-0002 records exactly that bypass.
- The findings handoff from `code-review` is by convention (run order), not by construction.

**50% less code**: the skill is a prompt, not a program. No Python, no HTTP client, no report renderer — the
verifier's own `write_report` emits the HTML, so the kit's `html-report` skill is not extended at all. The only code
written anywhere in this path is the hook's row check and its tests.

### Path B — The Integrated Path: fold scoring into `code-review`

`code-review` already runs for every extended-track task by Hard-Stop doctrine, and already holds the findings the
verifier wants as input. Add a closing step to it: run the session, pass its own findings, write the row.

**Pros**
- Genuinely less surface: no new skill file, no second invocation, no run-order convention. The findings handoff is
  free because both live in one context.
- The row exists for every extended task without any new rule, because the skill that produces it is already
  mandatory.
- The rules-versus-reviewer divergence is computed where both halves are in hand.

**Cons**
- `code-review` takes on a tool dependency and a degradation ladder, so a review now has two unrelated reasons to be
  partial, and a reader cannot tell which failed without reading the row.
- Scoring alone becomes impossible: there is no way to ask for a number without re-running a full review.
- `code-review/SKILL.md` is already near the 8 KB Codex cap, so the added text would push something else out.
- It couples a kit gate to an external tool's availability at the one step that must always run.

**50% less code**: strictly less than Path A on day one — no new file. The cost is paid later, in a skill that now
does two jobs.

### Path C — The Minimalist Path: the hook scores, nothing else changes

No new skill. A hook runs `python -m easy_verifier.adapters.cli score` and refuses under the floor.

**Pros**
- Cannot be forgotten or bypassed, by anyone, ever. This is the only path with that property.
- Smallest doctrine change: no skill text, no template row, no Stage 4 step.

**Cons**
- **Contradicts D3.** The CLI never asks, so the evaluate gate cannot be answered and `solution-fit` stays
  permanently abstained. A locked decision would have to be unlocked.
- **Contradicts D5.** A hook that scores needs the package present; a machine without it is either blocked or gets a
  silent hole in the gate.
- No findings handoff, so no divergence signal.
- A full repository score on every push is slow, and the operator cannot see the evidence that produced the refusal
  at the moment it refuses.

**50% less code**: it is already the smallest, which is its only real argument.

---

## Adversarial Review — why each might fail

**Path A fails if** the Supervisor treats the new skill as optional on a task that "feels small". That is LR-0002's
documented failure mode and the reason it is an active Learning Record. The mitigation is structural rather than
textual: the hook refuses the merge on an unfilled row, so skipping the skill does not produce a quiet pass, it
produces a blocked push with a named reason. If FR-004 and FR-005 ship late or weak, Path A degrades into an
advisory number and the whole feature is decoration.

**Path B fails if** the verifier is unavailable on the machine where review runs. `code-review` is mandatory for
every extended task, so a review that now carries a degradation ladder will sometimes report a partial result for a
reason that has nothing to do with the code. Over a few sessions the reader stops distinguishing "review was thin"
from "verifier was down", and the row's meaning rots. The 8 KB cap makes this worse: the text that explains the
distinction is the text most likely to be cut.

**Path C fails on its own terms.** Two locked decisions have to be reversed for it to work at all, and the one
property it buys — unbypassable enforcement — is already delivered by FR-004 inside Path A. It is kept here as the
honest baseline and rejected.

**All three fail if** the floor is read as a target. The verifier's own README shows a one-file bugfix scoring
`overall` 85 while `change_risk` was 0: a number near the floor can sit beside a change with no test at all. The row
must print both numbers, never one. A single blended number would have passed that example.

**A fourth failure, independent of path:** `memory/learnings.md` already records that "an agent can satisfy a gate by
editing the thing the gate measures." A score row is text in a Markdown file. FR-005 is the whole defence — the row
is trusted only against a report file on disk — so FR-005 is not a refinement, it is load-bearing.

---

## Surgical Scope

**Should be touched**

| Path | Why |
|---|---|
| `skills/score/SKILL.md` (new) | The scoring session, the ladder, the row contract. ≤ 8192 bytes. |
| `skills/ui-test/SKILL.md` (new) | Health check, labelled session, the three UI rows. ≤ 8192 bytes. |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | FR-004 row check, FR-005 report-file check. The only real code. |
| `.claude/hooks/tests/` | Hook tests, including the negative cases. |
| `templates/TASK_REVIEW_template.md` | One Evidence row (FR-001). |
| `templates/TASK_GUIDE_template.md` | easy-ui named in the three UI/Design sections (FR-011). |
| `AGENTS.md`, `docs/claude-md/pipeline-stages.md` | Stage 4 step and the floor (FR-003). |
| `PROJECT_SPEC.md` | Two glossary terms kept apart (FR-013). |
| `site/index.html`, `tests/test_site_content.py` | Honesty copy and its re-based blocklist (FR-012). |
| `PROJECT_KANBAN.md`, `tasks/TASK_GUIDE_T*.md`, `memory/decisions.md` | Stage 2 output and the decision record. |

**Must not be touched**

| Path | Why |
|---|---|
| `skills/code-review/SKILL.md` review logic | Path B rejected. The findings handoff is run order, not an edit. |
| `.claude/hooks/lib/verify_record.py`, the `verify` row logic | A separate gate with its own history (T182). Changing it here would mix two gates. |
| `.claude/skills`, `.claude/agents` symlinks | Load-bearing relative symlinks (AGENTS.md). Never absolutised. |
| `../_easy-family-ref/easy-ui-mcp`, `../_easy-family-ref/easy-verifier-mcp` | Read-only reference. This feature changes the kit, not the tools. |
| `MANIFEST` | `MANIFEST:45` already ships the whole `skills` directory. |
| `CLAUDE.md` | Asserted byte-for-byte as `b"@AGENTS.md\n"` (`tests/test_agents_md_primary.py:130`). |

---

## Selected Path — A (user, 2026-10-28, D6)

> *"if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the normal flow,
> that all"* — the constraint selected the path by itself. Path B folds an optional tool into the one Stage 4 skill
> that must always run; Path C makes the scorer required on every machine. Only A leaves the normal flow untouched
> when neither tool is used. FR-014 turns that into a regression test, and FR-015 states the other half: a tool that
> **did** run is binding.

**Path A, with Path B's handoff made explicit and Path C's enforcement delivered by the hook.**

Concretely: a standalone `score` skill, invoked at Stage 4 after `code-review` so its findings are in hand and can be
passed as `findings` for the separate assessment and divergence. `code-review`'s closing text names `score` as the
next step for an extended-track task — one sentence, not a fold. The hook does the enforcing, which is the only
reason Path A's forgettability is acceptable: FR-004 and FR-005 turn a skipped score into a blocked push with a named
reason rather than a quiet pass.

The reason not to choose Path B, stated plainly: scoring must be able to fail without making the mandatory review
look partial, and a number must be obtainable without re-running a review. The reason not to choose Path C: it
requires unlocking D3 and D5 to buy enforcement that Path A already has.

---

## Next Actions (for Stage 2)

1. `to-issues` on FR-001..FR-013. Expected split: the hook change and its tests (the only code, and the only thing
   the other tasks depend on), the `score` skill, the `ui-test` skill, the two template edits, the doctrine and
   glossary edit, and the site honesty change with its test.
2. The hook task starts at **C2 / Medium Risk** minimum: it edits the merge gate, and a wrong edit either blocks
   every push or opens a hole in the gate that T044's history shows can go unnoticed for sessions.
3. Each new `SKILL.md` carries a size assertion in its own task's Acceptance Criteria (≤ 8192 bytes), because the
   existing tests only cover the skills that already have one.
4. Resolve OQ-002 (skill names) at Stage 2. `ui-test` is the name the unlanded branch used; reusing it keeps one term
   for one thing.
5. FR-014 is its own Acceptance Criterion on the hook task, not a separate task: a test that runs the gate with no
   score row and no UI row present and asserts the decision is byte-identical to today's. Without it, "optional" is
   a claim rather than a measurement — and the hook is the only place it can break.
6. The gate check is **method-agnostic**: it reads `fail`, not which tool produced it. A UI row failed by LLM vision
   blocks exactly as one failed by easy-ui. Deliberate cut: the gate does **not** generalise to every Evidence row
   (`Negative cases hold`, `Full smoke suite still green`), because that would bind rows this feature was not asked
   to touch and could block a push on a pre-existing row the moment it ships.

---

## Edge Case Checklist (for every `TASK_GUIDE` in this feature)

- The verifier is registered over MCP but its container is stopped — the ladder must fall to the CLI, not stall.
- The CLI is run with stdin left open by an agent shell: `score` waits forever for findings. Every CLI invocation in
  kit text ends with `< /dev/null`, as the verifier's own README requires.
- `--ref main...HEAD` (three dots) versus `--ref main..HEAD` versus a bare branch name: the bare name means one
  commit against its parent, which would score the wrong thing on a multi-commit branch.
- A worktree task whose base is not `main` — the ref must be computed from the branch's actual base.
- `overall` abstains for a dimension the change does not touch: the row must print `overall.abstentions`, or an 80
  built from two rated dimensions reads as the same number as one built from twelve.
- A score of exactly 80 passes; 79.9 fails. The row states the comparison it made.
- `change_kind` detected as `chore` means the change-risk dimension abstains by design ("chore: no test
  expectation") — that is not a failing rule and must not read as `fail`.
- `write_report` with `EASY_VERIFIER_REPORTS_DIR` set writes outside the repo and returns an absolute path; the row
  cites that path, and FR-005's existence check must handle a path outside the checkout.
- A secret the verifier matched is returned as a fingerprint. The row never carries a raw value (NFR-003).
- easy-ui: `ui_assert` in a retry loop permanently fails a session; waiting is `ui_wait_for`. The `ui-test` skill
  must say this, because the kit's reviewers will reach for `ui_assert` first.
- easy-ui is reachable but the target dev server is not — `network_mode: host` means `localhost:<port>` is the host's,
  and a wrong host silently times out rather than erroring clearly.
- Two live sessions score the same task: reports are unique per scope and timestamp, so the row must cite the one it
  read, not the newest in the directory.
