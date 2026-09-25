# BRAINSTORMING_LOG.md
**Generated**: 2026-09-24
**Task / Context**: T124 — token economy (headroom → input, ponytail → coding, caveman → output); this log covers the **compression hook** only
**Skill**: `Skill({ skill: "brainstorming" })` — tier **Standard** (direction locked by `grill-with-docs`; the open question is how to build it)

---

## The Problem Space

Large Bash output (test runs, logs, recursive searches) costs input tokens every time an agent reads
it, and most of it is repetition. headroom solves this with a proxy; the user excluded installing it.
**Proven live on Claude Code 2.1.281 (2026-09-24 probe):** a PostToolUse hook's
`hookSpecificOutput.updatedToolOutput` replaces a Bash result before Claude sees it, and
`additionalContext` reaches Claude. So the same idea fits in one local hook.

Locked by grilling (user decisions, 2026-09-24):

| # | Decision |
|---|---|
| Q1 | Bash **stdout** only, only when > **200 lines**; keep first 40 + last 60 + every error/fail/warn/Traceback/assert line; **stderr verbatim**; Read/Grep untouched |
| Q2 | Originals saved **inside the repo**: `.claude/hooks/.state/output/<session>/NNNN.log`, dir 0700 / file 0600 (user overrode the outside-repo recommendation for manageability) |
| Q3 | `CLAUDE_FULL_OUTPUT=1` command prefix skips compression for that call; otherwise Read the saved log |
| Q4 | The hook itself prunes session folders older than 24 h (user asked "who will delete" → the hook) |
| Q5 | Append-only `.state/output/stats.tsv` — timestamp, session, lines/chars before→after; **no command text, no content** |

Non-negotiables: compression changes only what Claude *sees* (the command already ran); an error line
must never be dropped; the hook must never break a Bash call (fail-open → original output).

Verified against the repo (claim gate):
- `.gitignore:52` ignores `.claude/hooks/.state/`.
- `MANIFEST` ships `.claude/hooks` whole and excludes only `!.claude/hooks/tests`; `setup.sh:674` does a `cp -r` — whether `.state/` can ride along is **unverified** and becomes an AC.
- `pre_agent_step_limit.py:92` `_sanitize_session_id()` already reduces an untrusted `session_id` to a file-name-safe fragment — **reuse, do not reinvent** (session_id reaches a path here too).
- Existing Bash PostToolUse hooks (`post_bash_memory_update.py`, `post_tool_trace.py`) do not gate on stdout content, so compression cannot alter the merge gate or memory prompt.
- Shell `grep -r` from the repo root **does** descend into `.claude/hooks/.state/` (measured); the built-in Grep tool (ripgrep) honours `.gitignore`.

---

## Questions for the User

**All resolved 2026-09-24:** user selected **Option A**, and grep fix **(a) filter**.

1. ~~**grep -r pollution fix**~~ → (a) filter (the one open design choice — see *Adversarial Review → all options*):
   recommended **(a) filter**: strip lines that start with the `.claude/hooks/.state/output/` path
   from *any* Bash stdout (only recursive grep/find listings print that prefix), with a one-line
   "N matches inside saved outputs hidden" note. Alternative **(b) gzip** the saved logs (`NNNN.log.gz`)
   so `grep -r` sees binary noise instead of text — but then the agent must `zcat` instead of Read.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Line selector | One stdlib Python hook: count lines, keep head/tail/matched lines, save original, emit `updatedToolOutput` | Low | ~150 lines + tests | Low | ✅ Yes |
| B | Content router | headroom-style: detect pytest / JSON / diff / plain and apply a per-type compressor | Medium | ~400 lines + tests | Medium | |
| C | Truncate only | Head/tail cut with no matched-line keep and no saved original | Low | ~50 lines | High (drops errors) | |

### Option A — Line selector
**Approach**: `.claude/hooks/post_bash_compress_output.py`, registered PostToolUse/`Bash`. Read stdin →
skip unless stdout > 200 lines and no opt-out → copy the original `tool_response` dict, replace only
`stdout` with: head 40 · `… N lines elided — full output: <path> …` · matched lines (capped, each
with its original line number) · tail 60 → save original, append stats, prune old sessions → print JSON.
Any exception → exit 0, no stdout (Claude sees the original).
**Pros**: one file, stdlib only, same shape as the repo's other hooks; the output keeps line numbers so
the agent can `Read` the saved log at exactly the right offset.
**Cons**: generic — a pytest run keeps its "N passed" tail but not a structured failure summary.
**Why it might fail**: a noisy build prints thousands of `warning` lines → matched lines re-flood
the output (**mitigation: cap matched lines, e.g. 60, and say how many more exist**); a keyword the
regex misses (`panic:`, `FATAL`, `✗`, `E   ` pytest prefix) is elided (**mitigation: the saved log +
tail 60 — pytest/jest summaries live in the tail**).

### Option B — Content router
**Approach**: detect output type, e.g. pytest (keep `FAILED`/`E ` blocks + summary), JSON (collapse
repeated array items), `git diff` (keep hunks for changed files only), else Option A.
**Pros**: higher savings on the exact shapes headroom benchmarks (JSON 60–95% per its README — their claim).
**Cons**: 3–4 compressors, each its own failure mode and test matrix; speculative until Option A's stats show which shape dominates.
**Why it might fail**: a misdetected type gets the wrong compressor and drops the one line that mattered — the most dangerous silent failure available here; also directly against Simplicity First (no measured need yet).

### Option C — Truncate only
**Approach**: keep head + tail, drop the middle, no saved file.
**Pros**: smallest possible.
**Cons**: violates locked Q1 (error lines kept) and Q2 (reversibility).
**Why it might fail**: a failing test in the middle of a 2,000-line run disappears and the agent reports green — exactly the false-assumption hazard the Claude Code docs warn about for `updatedToolOutput`.

---

## 50% Rule Check

Option A at ~75 lines: drop stats (Q5) and pruning (Q4), keep a single fixed log path overwritten per
call. Rejected — both were explicit user decisions, and without pruning the in-repo folder grows forever
while holding secrets. The achievable cut is *within* A: no config file, no env-tunable thresholds
(constants at the top of the file), no per-type logic.

---

## Recommended Path

**Option A — Line selector.** It meets every locked decision with the least code, keeps error lines by
construction, and produces the stats that would justify Option B later on evidence rather than on
headroom's numbers. Option B is recorded as a follow-up to register only if stats show one output
shape dominating the saving.

---

## Surgical Scope

Files that **should** be touched:
- `.claude/hooks/post_bash_compress_output.py` — new hook
- `.claude/settings.json` — register under PostToolUse/`Bash`
- `.claude/hooks/tests/test_post_bash_compress_output.py` — new, real stdin/stdout protocol
- `MANIFEST` — `!.claude/hooks/.state` **only if** the installer check shows it can ship
- `.gitignore` — none expected (line 52 already covers it); a test pins that

Files that **must not** be touched:
- `.claude/hooks/pre_bash_block_unsafe_merge.py`, `post_bash_memory_update.py`, `post_tool_trace.py` — other Bash hooks; ordering-independent coexistence only
- `.claude/hooks/pre_agent_step_limit.py` — reuse `_sanitize_session_id` by import or a tiny move into `lib/`; if moving, STOP and ask (shared with the step-limit gate)
- `.claude/hooks/.state/step_count_*` — cleanup must never touch these

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Replacement copies the original `tool_response` and swaps only `stdout` — a shape mismatch is **silently ignored** by Claude Code (docs), so a test must assert all original keys survive.
- [ ] Output of exactly 200 / 201 lines; trailing newline vs none; CRLF; a single 5 MB line with no newlines (line count 1 — needs a char cap too).
- [ ] Non-UTF-8 / binary stdout → skip compression, never crash.
- [ ] `run_in_background` / interrupted commands → no stdout yet → skip.
- [ ] Matched-line flood capped; count of un-shown matches stated.
- [ ] Opt-out: `CLAUDE_FULL_OUTPUT=1 cmd` skips; a false positive (the string appearing in data) only means *no* compression — the safe direction, so plain substring detection is acceptable.
- [ ] `session_id` sanitised before it becomes a path (reuse `_sanitize_session_id`); `NNNN` counter race between parallel calls → use `O_CREAT|O_EXCL` or a unique suffix.
- [ ] Permissions 0700/0600 set explicitly (umask-independent), asserted by test.
- [ ] Prune: only `.state/output/<session>/` dirs matching the naming pattern, older than 24 h, never follows symlinks, never touches `step_count_*` or `stats.tsv`; prune failure is ignored.
- [ ] grep -r pollution: a planted sentinel in a saved log must not reach Claude via `grep -r` from repo root (per the chosen fix).
- [ ] Disk full / read-only FS → can't save original → **do not compress** (never elide what can't be recovered).
- [ ] Coexistence: the other Bash PostToolUse hooks still fire and still see the original `tool_response`.
- [ ] Sub-agent worktrees: path is relative to `$CLAUDE_PROJECT_DIR`, so each worktree keeps its own logs.
- [ ] Stats row carries counts only — test asserts no command text / stdout substring appears in `stats.tsv`.
