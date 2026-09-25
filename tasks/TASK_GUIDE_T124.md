# TASK_GUIDE — T124: Token economy — compress oversized Bash output (input), enforce the build ladder at review (coding), verbatim-safe terse replies (output)
**Date**: 2026-09-24 (rewritten same day after live probe + `grill-with-docs` + `brainstorming`)
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. **C2**: read `memory/codebase-map.md` and `BRAINSTORMING_LOG_token-economy.md` (the chosen path, its adversarial review, and the full edge-case list)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-24, verbatim:

> "We can use the headroom for the input, ponytail for the coding, and the caveman for the output
> — https://github.com/headroomlabs-ai/headroom, https://github.com/dietrichgebert/ponytail,
> https://github.com/juliusbrussee/caveman. Do not clone the repos as plugin or refer to raw of
> repos, just investigate the idea and see what we can apply from that."

**What each idea became here** (repos' public README pages read as data, per `docs/claude-md/untrusted-content-boundary.md`; nothing installed, cloned or copied):

| Idea | Their mechanism | This repo before T124 | T124 adds |
|---|---|---|---|
| headroom (input) | Proxy compresses tool output before the model reads it; originals retrievable | Nothing | A **PostToolUse hook** that compresses oversized Bash stdout via `updatedToolOutput`, saves the original, records stats |
| ponytail (coding) | 7-rung "does this need to exist → … → minimum" ladder | **Already shipped**: "Search Before You Build", `agents/general-agent-template.md` (T041) | A review-side `over-engineering-reviewer` persona in `code-review` |
| caveman (output) | Terse prose; code/errors/paths kept verbatim | **Partly shipped**: Response Standard (T100/T103) | One verbatim-preserve rule; sub-agent reports point to evidence instead of pasting it |

**Premise proven live, 2026-09-24 (Claude Code 2.1.281):** a throwaway PostToolUse/`Bash` hook
returned `hookSpecificOutput.updatedToolOutput` and `additionalContext` with random tokens; the
Supervisor received `REPLACED token=fbe5b2fc1c` instead of the real stdout and `CTX token=6627288dc8`
as context. Documented in `code.claude.com/docs/en/hooks` (*PostToolUse decision control*):
"`updatedToolOutput` — replaces the tool's output with the provided value before it is sent to
Claude. The value must match the tool's output shape"; "for built-in tools, a value that doesn't
match the tool's output schema is ignored and the original output is used"; "Stripping error
details that Claude needs can cause it to proceed on a false assumption."

**User decisions (2026-09-24):**

| # | Decision |
|---|---|
| D1 | Compression replaces the originally planned advisory warning hook — no PreToolUse hook |
| D2 | Bash **stdout** only, only when it exceeds **200 lines**; keep first 40 + last 60 + every error/fail/warn/Traceback/assert line; **stderr verbatim**; Read/Grep untouched |
| D3 | Originals saved **inside the repo**: `.claude/hooks/.state/output/<session>/NNNN.log`, dir 0700 / file 0600 (user overrode the Supervisor's outside-repo recommendation, for manageability) — see `docs/ddr/0008-saved-tool-output-lives-inside-the-repo.md` |
| D4 | `CLAUDE_FULL_OUTPUT=1` command prefix skips compression for that call; otherwise the agent Reads the saved log |
| D5 | The hook itself prunes session folders older than 24 h |
| D6 | Append-only `.claude/hooks/.state/output/stats.tsv`: timestamp, session, lines/chars before → after. **No command text, no output content.** Not pruned |
| D7 | `grep -r` pollution fix: drop lines starting with `.claude/hooks/.state/output/` from any Bash stdout, replaced by one "N matches inside saved outputs hidden" line |
| D8 | Brainstorming path **A — Line selector** (stdlib, one file); content-type routing (path B) deferred until stats justify it |
| D9 | Output side: Response Standard gains a verbatim-preserve rule; applies to replies and sub-agent reports; audit trail unchanged |
| D10 | Coding side: `over-engineering-reviewer` persona in `code-review` |

**Restated intent:**
> Agents read far fewer tokens when a Bash command prints hundreds of lines, without ever losing an
> error line or the ability to recover the full output; replies and reports stay terse without
> paraphrasing code, errors, paths or commands; over-engineered diffs are caught at Stage 4. The
> saving is **measured** by the hook's own stats, not borrowed from the three READMEs.

**Out of scope:**
- Installing, vendoring, cloning or proxying headroom / ponytail / caveman, or copying their text.
- Compressing Read, Grep, or any non-Bash tool; compressing stderr.
- Content-type-specific compressors (pytest/JSON/diff) — brainstorming path B, a follow-up only on stats evidence.
- Rewriting commands before they run (PreToolUse `updatedInput`) — rejected: a `| tail` rewrite hides the real exit code and re-enters the permission flow.
- Intensity modes, `/terse` skill, `ponytail:` deferral comments (user rejected).
- A savings report skill — the stats file only.
- Any change to the audit trail's detail (Evidence, KANBAN, `memory/`, commits).

**Requirement Refs**: no `PRD.md` exists in this repo — N/A. Traces to the user request and D1–D10 above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor + user decisions D1–D10, 2026-09-24)
- [x] Domain terms align: *Response Standard*, *Search Before You Build*, *reviewer persona*, *saved original*, *compression*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T123 — CI workflow must be green, so this task's CI run is observable rather than masked by the known step-20 failure

**Entry point**: `post_bash_compress_output.py` (registered under `PostToolUse` / matcher `Bash` in `.claude/settings.json`); `over-engineering-reviewer` (persona row in `skills/code-review/SKILL.md`); `docs/claude-md/token-economy.md` (pointed to from `CLAUDE.md`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | New `.claude/hooks/post_bash_compress_output.py`, registered PostToolUse/`Bash`. When Bash stdout exceeds 200 lines it emits `hookSpecificOutput.updatedToolOutput` whose stdout = first 40 lines · one elision marker naming the elided count **and the saved-log path** · every line matching the error pattern (each prefixed with its original line number, capped at 60 with the remainder counted) · last 60 lines | D2, D8 |
| 2 | The replacement is the **original `tool_response` object with only `stdout` changed** — every other key and value (`stderr`, `interrupted`, `isImage`, and any others present) is preserved unchanged | docs: shape mismatch is silently ignored |
| 3 | At ≤ 200 lines, with `CLAUDE_FULL_OUTPUT=1` in the command, on non-UTF-8/binary stdout, with no stdout (background/interrupted), or for a non-Bash tool: **no output from the hook**, exit 0 (subject to AC7's path filter) | D2, D4 |
| 4 | Before compressing, the full original stdout is written to `.claude/hooks/.state/output/<sanitised-session>/NNNN.log` with dir mode 0700 and file mode 0600 (set explicitly, umask-independent). **If the save fails, the hook does not compress.** `session_id` is sanitised with the existing `_sanitize_session_id` logic (`pre_agent_step_limit.py:92`) — reused, not reinvented | D3; never elide what cannot be recovered |
| 5 | Each run prunes `.claude/hooks/.state/output/<session>/` folders older than 24 h: only folders matching the hook's own naming, never following symlinks, never touching `step_count_*` files or `stats.tsv`; a prune failure is ignored and the call still completes | D5 |
| 6 | Each compression appends one row to `.claude/hooks/.state/output/stats.tsv`: ISO timestamp, sanitised session, lines before, lines after, chars before, chars after. No command text and no output content ever appears in it | D6 |
| 7 | For **any** Bash stdout (any size), lines beginning with `.claude/hooks/.state/output/` or `./.claude/hooks/.state/output/` are removed and replaced by one line `… N matches inside saved outputs hidden …`; if nothing matches, stdout is untouched | D7 |
| 8 | Saved outputs can never ship or be committed: `.gitignore` still ignores `.claude/hooks/.state/` (test pins it), and the installer is checked — if `setup.sh`'s copy (`setup.sh:674`, `cp -r`) or `MANIFEST`'s `.claude/hooks` entry can carry `.state/`, add `!.claude/hooks/.state` to `MANIFEST` with a test | D3 |
| 9 | Fail-open: malformed stdin, missing fields, any internal exception → exit 0 with no stdout, so Claude sees the original output. The hook never emits `decision`, `permissionDecision`, or exit 2 | never break a Bash call |
| 10 | New `docs/claude-md/token-economy.md` documents: compression rules (threshold, what is kept), how to recover full output (Read the saved log at the printed line numbers, or `CLAUDE_FULL_OUTPUT=1`), the verbatim-preserve list (code, exact error text, file paths, commands, security warnings), and that sub-agent final reports **point to evidence by path/line** instead of pasting logs, while the Evidence table still carries full pasted output (Hard-Stop Gate 5 unchanged). `CLAUDE.md` gets a one-line pointer; the bodies are not duplicated into `CLAUDE.md`, the template or any role guide | D9; T082 delivery pattern |
| 11 | The Response Standard gains exactly **one** verbatim-preserve rule line, byte-identical in `CLAUDE.md` and `agents/general-agent-template.md`; `tests/test_response_standard.py` stays green with its "six" wording/count updated to seven | D9 |
| 12 | `skills/code-review/SKILL.md` gains a conditional `over-engineering-reviewer` persona with a concrete activation condition, checking the diff for: new abstraction with one caller, new dependency replacing ≤ 10 lines, speculative config/flags, duplication of an existing helper or stdlib. It cites "Search Before You Build" by name and does **not** copy the seven rungs | D10 |
| 13 | Size budgets are measured, not reframed: `test_agent_guide_dedup.py` AC7 stays green; if the one template line breaches a role's floor, repoint **only** that role with before/after numbers in the comment, exactly as T082/T100 did | Surgical Changes |
| 14 | No existing test is modified except the count/wording/baseline edits AC11 and AC13 require, each named with its reason in the TASK_REVIEW | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The implementing agent must NOT be the sole author of its own acceptance test. The Supervisor owns
> the mutation controls M1–M7 and re-runs them independently at Stage 4.

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | Bash `tool_response` with 1,000-line stdout, `FAILED test_x` at line 517 | `updatedToolOutput.stdout` has lines 1–40, a marker with `960` elided and the log path, `517: FAILED test_x`, lines 941–1000; log file holds all 1,000 lines byte-identical | pytest via subprocess, real stdin/stdout JSON |
| 2 | Same input with extra keys in `tool_response` | every non-stdout key/value identical in the output | pytest |
| 3 | 200-line stdout; 201-line stdout | 200 → no output; 201 → compressed | pytest (boundary) |
| 4 | 5,000 lines of `warning: x` | at most 60 matched lines shown + "N more matches in saved log" | pytest |
| 5 | Command `CLAUDE_FULL_OUTPUT=1 pytest`; non-UTF-8 bytes; empty stdout; `tool_name: "Read"`; malformed JSON | exit 0, empty stdout | pytest |
| 6 | Output dir made unwritable | exit 0, empty stdout (original shown), no crash | pytest |
| 7 | Saved log + dir | modes 0600 / 0700 under a permissive umask (`0o000`) | pytest |
| 8 | Session folder aged 25 h, one aged 1 h, a `step_count_x.txt`, `stats.tsv`, a symlink to a dir outside `.state/` | only the 25 h folder removed; the symlink target untouched | pytest (tmp dir) |
| 9 | Stdout containing a sentinel secret string | sentinel appears in the saved log, **never** in `stats.tsv`; stats row has 6 fields | pytest |
| 10 | Stdout of `grep -r SENTINEL .` that includes `./.claude/hooks/.state/output/s/0001.log:SENTINEL` lines, at 5 lines and at 500 lines | those lines replaced by the "N matches … hidden" line in both cases | pytest |
| 11 | `session_id` of `../../etc` | log path stays under `.claude/hooks/.state/output/` | pytest |
| 12 | `git check-ignore .claude/hooks/.state/output/x/0001.log` | exit 0 (ignored) | pytest |
| 13 | Docs/structure | pointer present in `CLAUDE.md`, bodies absent; seven Response Standard lines byte-identical; persona row with activation condition and no rung text | `tests/test_token_economy_docs.py`, `tests/test_response_standard.py` |

**Mandatory mutation controls** (each must go RED, then be reverted; paste both runs):
- **M1** — drop matched-line keeping → SC1 RED (the failing test in the middle vanishes: the exact false-green hazard the docs warn about).
- **M2** — build a fresh `{"stdout": ...}` instead of copying `tool_response` → SC2 RED.
- **M3** — compress even when the save fails → SC6 RED.
- **M4** — make prune match `*` instead of the hook's naming → SC8 RED.
- **M5** — write the command string into `stats.tsv` → SC9 RED.
- **M6** — disable the path filter → SC10 RED.
- **M7** — paste the reference's verbatim-preserve paragraph into `CLAUDE.md` → SC13 no-duplication RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_post_bash_compress_output.py tests/test_response_standard.py tests/test_token_economy_docs.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -5      # full suite, no regressions
bash validate.sh && bash tests/smoke-install.sh               # paths as present at pickup
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T124.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T124.md`. BEFORE: a real >200-line command on `main`, full output
> reaches the agent. AFTER: the same command on the branch in a live Claude Code session, compressed,
> with the saved-log path, and the agent recovering a middle line via Read. DELTA: from `stats.tsv`.

---

## Approach

**Pattern reference**:
- `.claude/hooks/post_bash_memory_update.py` — a PostToolUse/`Bash` hook in this repo: stdin parsing, fail-open.
- `.claude/hooks/pre_agent_step_limit.py:92` — `_sanitize_session_id` for untrusted `session_id` in a path; and `.state/` file handling.
- `docs/claude-md/untrusted-content-boundary.md` + its `CLAUDE.md` pointer (T082) — reference-file-plus-one-line-pointer delivery.
- `tests/test_response_standard.py` — byte-identity pinned by reading both files at test time.

**Vital slice**: the compression hook (AC1–9) — it is the only part that changes what agents consume. The docs line, reference file and persona row are small and ride along.

**Cut list**:
- Content-type compressors (path B) — register only if `stats.tsv` shows one shape dominating.
- Env- or config-tunable thresholds — constants at the top of the hook file.
- Savings report skill; per-task stats aggregation.
- Advisory PreToolUse hook (D1 replaced it).
- Compressing Read/Grep/stderr.
- Moving `_sanitize_session_id` into `lib/` — import or copy minimal; if a move is needed, STOP and ask (shared with the step-limit gate).

**Design notes (Supervisor, with reasons):**
- **Save before you elide.** If the original can't be saved, nothing is elided (AC4, M3). Reversibility is what makes compression safe.
- **Error pattern is a floor, the tail is the backstop.** The regex will miss some formats (`panic:`, `FATAL`, `✗`); test-runner summaries live in the last 60 lines, and every elided line is in the saved log with its line number.
- **Copy the response, swap one key.** A shape mismatch is silently ignored by Claude Code, which would make the hook look like it works in unit tests while doing nothing live (M2 + the live Demonstration).
- **This hook fails toward showing more.** Every uncertainty (can't save, can't decode, unexpected shape) resolves to *no compression*. State this in the docstring.
- **Reports point, not paste.** A sub-agent's final message is Supervisor input; a path:line into `TASK_REVIEW_Txxx.md` replaces a pasted log in the *message*. The Evidence table still carries full pasted output.

---

## Edge Case Checklist

(From `BRAINSTORMING_LOG_token-economy.md`; each maps to an SC or AC above.)

- [ ] Shape: copy `tool_response`, swap only `stdout` (AC2, SC2)
- [ ] 200/201 boundary; trailing newline vs none; CRLF; a single 5 MB line with no newlines (add a char cap, e.g. > 50,000 chars also triggers, keeping head/tail by chars)
- [ ] Non-UTF-8 / binary → skip (SC5)
- [ ] Background / interrupted → skip (SC5)
- [ ] Matched-line flood capped (SC4)
- [ ] Opt-out false positive only means no compression — plain substring match is acceptable
- [ ] `session_id` sanitised (SC11); parallel calls must not collide on `NNNN` — `O_CREAT|O_EXCL` or a unique suffix
- [ ] Explicit 0700/0600 (SC7)
- [ ] Prune scope and symlinks (SC8); prune failure ignored
- [ ] Path filter at every size (SC10)
- [ ] Disk full / read-only → no compression (SC6)
- [ ] Coexistence: `post_bash_memory_update.py` and `post_tool_trace.py` still fire and still see the original `tool_response` (compression changes only what Claude sees)
- [ ] Sub-agent worktrees: path relative to `$CLAUDE_PROJECT_DIR`, so each worktree keeps and prunes its own logs
- [ ] Stats has counts only (SC9)
- [ ] `test_site_content.py` derives hook facts from the repo — check whether the new hook must appear on `site/index.html`; add it rather than weaken the test
- [ ] `tests/test_provider_adapters.py` / `AGENTS.md` / `.cursor/rules/agent-base.mdc` mirror `CLAUDE.md` non-negotiables — check whether the new Response Standard line must be mirrored
- [ ] Response Standard's scope sentence ("Replies only — Evidence, KANBAN rows, `memory/` and commit messages stay fully detailed") preserved exactly

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_bash_compress_output.py` | **New.** The compression hook |
| `.claude/settings.json` | Register under PostToolUse / `Bash` |
| `.claude/hooks/tests/test_post_bash_compress_output.py` | **New.** SC1–12 through the real stdin/stdout protocol |
| `docs/claude-md/token-economy.md` | **New.** AC10 |
| `CLAUDE.md` | One pointer line; one Response Standard line |
| `agents/general-agent-template.md` | The same Response Standard line only |
| `skills/code-review/SKILL.md` | `over-engineering-reviewer` persona row |
| `tests/test_token_economy_docs.py` | **New.** SC13 structural assertions |
| `tests/test_response_standard.py` | "six" → "seven" only (AC14) |
| `.claude/hooks/tests/test_agent_guide_dedup.py` | Only if AC13 breaches: per-role repoint with measured numbers |
| `MANIFEST` | `!.claude/hooks/.state` only if AC8's installer check shows it can ship |
| `site/index.html` | Only if `test_site_content.py` requires the new hook listed |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py`, `post_bash_memory_update.py`, `post_tool_trace.py` | Other Bash hooks; coexistence only |
| `.claude/hooks/pre_agent_step_limit.py` | Reuse its sanitiser; do not modify the step-limit gate |
| `.claude/hooks/.state/step_count_*` | Prune must never touch them |
| `agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md` | No rule bodies in role guides (T100 test) |
| `memory/*` | Supervisor-only writes |
| `.github/workflows/ci.yml` | T123's scope |

---

## Test Plan

1. Hook tests first (`tdd` skill): SC1–12 via `subprocess` with JSON on stdin and `CLAUDE_PROJECT_DIR` pointed at a tmp dir — **not** import-and-call (T085/T093: behavioural claims need the real protocol).
2. Structural tests SC13 read every file at test time; no hardcoded copies of production text.
3. Implement until green; record full-suite count before/after.
4. Run M1–M7; paste RED then reverted-GREEN for each.
5. Measure AC13 per role before touching `test_agent_guide_dedup.py`; paste the numbers.
6. Stage 5 `/verify` (user-run): in a live session, run a >200-line command (e.g. `seq 1 1000; echo FAILED demo`) and show that the agent sees the compressed form with the path, recovers a middle line via Read, `CLAUDE_FULL_OUTPUT=1` shows everything, and `stats.tsv` gained a row. Report the real before/after numbers from `stats.tsv`, and say honestly if the live result differs from unit tests.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` — **mandatory (Medium)**; secrets-on-disk and path handling are in scope; scope manually to `main..<branch>` (built-in over-scopes to `origin/HEAD`)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T124.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M7 mutation controls pasted (RED then GREEN)
- [ ] `/verify` — user-run (Supervisor cannot run it)
- [ ] UI Evidence rows: ☐ N/A — no UI component (hook, docs and a skill file only)
- [ ] Supervisor notified: task ready for Stage 4 review
