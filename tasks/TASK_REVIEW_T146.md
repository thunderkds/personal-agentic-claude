# TASK_REVIEW — T146: An edit or command that touches a sensitive path asks a human first

> Sibling of `tasks/TASK_GUIDE_T146.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_pre_tool_sensitive_path.py` (new, 28 tests): AC1 shipped list; AC2/SC1–SC2 Edit/Write; AC3/SC3–SC5 Bash via `shell_data`; AC4/SC6 predicted paths (silent — see Assumption check §2); AC5/SC7 missing list, malformed stdin, import failure; AC6 MANIFEST + `lib/merge-settings.py` merge; SC8 (a)/(b) mutation controls. Output (2026-10-17T03:30:57Z): `28 passed, 11 subtests passed in 0.89s`. **Fix round 1** added 4 tests (quoted redirect target asks / ordinary redirect silent / bare `dir/**` directory asks / lookalikes silent) — 9 subtests RED before the fix; after (2026-10-17T03:49:14Z): `32 passed, 25 subtests passed in 1.08s` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q` → fix round 1 (2026-10-17T03:49:14Z): `32 passed, 25 subtests passed in 1.08s` then `1041 passed, 25 subtests passed in 16.78s`, exit=0 (implementing agent) — reviewer to re-run. Round 0: `28 passed` / `1025 passed`, 2026-10-17T03:30:57Z |
| Negative cases hold | ☑ pass | `.env.example`, quoted data (`echo "edit .env later"`), heredoc-body mention, ordinary paths (`docs/infra.md`, `envoy.yaml`) stay silent; unpredicted sibling `infra/other.tf` and an unpredicted token in a mixed Bash command still ask. SC8 mutants: naive quoted-strip waves SC4 through, allow-on-failure waves SC7 through — both asserted RED |
| verify | ☑ pass | user's `/verify` 2026-10-17 (commit ad7af97): live Claude Code 2.1.302 sessions — headless Write `.env` refused by `[hook:sensitive-path]`; SC9 interactive `Write(.env)` prompts, `Write(notes.txt)` does not; Bash `> secrets.key` asks — pass. Full record in `## Stage 5 — /verify` below |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `main..feat/t146-t147-harness-hardening`, then fix-round delta `9a04675..7426c92` — see `## Stage 4 — code-review` sections below |
| Full smoke suite still green (no regression) | ☑ pass | Fix round 1 (2026-10-17T03:49Z): `tests/ .claude/hooks/tests/` 1041 passed; `bash scripts/validate.sh` → `validate.sh: PASS` exit=0; `python3 scripts/gen_sandbox_profile.py --check` exit=0 (T147 imports the hook's brace expansion). Round 0: `tests/ .claude/hooks/tests/` 1025 passed (first run caught `tests/test_site_content.py::test_every_wired_hook_appears_in_hook_table` — fixed by adding the hook's row to `site/index.html`); `bash scripts/validate.sh` → `validate.sh: PASS`; `tests/test_settings_merge.sh`, `tests/test_setup.sh`, `tests/test_manifest_exclusions.sh` exit=0 |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by the implementing agent at HEAD `29dcd16`, before any T146 implementation
commit):

```text
2026-10-17T03:27:48Z
$ echo {"tool_name":"Write","tool_input":{"file_path":".env"}} | python3 .claude/hooks/pre_tool_sensitive_path.py
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t146-t147/.claude/hooks/pre_tool_sensitive_path.py': [Errno 2] No such file or directory
exit=2
$ ls .claude/sensitive-paths.txt
ls: cannot access '.claude/sensitive-paths.txt': No such file or directory
$ grep -c sensitive_path .claude/settings.json
0

2026-10-17T03:27:51Z
$ python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q
ERROR: file or directory not found: .claude/hooks/tests/test_pre_tool_sensitive_path.py

no tests ran in 0.00s
exit=4
```

Nothing stands between Edit/Write/Bash and `.env`: no hook, no pattern list, no registration.

**AFTER** (implementing agent, after the implementation, before the T146 commit):

```text
2026-10-17T03:31:44Z
$ echo {"tool_name":"Write","tool_input":{"file_path":".env","content":"x"}} | python3 .claude/hooks/pre_tool_sensitive_path.py
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "[hook:sensitive-path] This Write call touches a sensitive path: .env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it."}}
exit=0
$ ls .claude/sensitive-paths.txt
.claude/sensitive-paths.txt
$ grep -c sensitive_path .claude/settings.json
1

2026-10-17T03:30:57Z
$ python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q
28 passed, 11 subtests passed in 0.89s
```

SC9 (the prompt really appears in a live session) is still **pending** — Stage 5, `/verify`.

**DELTA**: An agent's Edit, Write or Bash call that touches `.env*`, secrets, production configs or infra now stops at a confirmation prompt naming the path and pattern, unless the active task predicted that exact path.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T146.jsonl`, never the
implementing agent alone]

### Fix round 1 — BEFORE

Implementing agent, at HEAD `1c2bd1d`, before any fix-round-1 commit. Each command is sent to the
hook as a Bash PreToolUse event on stdin (`/tmp/t146_demo.sh`: `{"tool_name":"Bash","tool_input":{"command":…},"cwd":<worktree>}`,
`CLAUDE_PROJECT_DIR=<worktree>`, `CLAUDE_ACTIVE_TASK` unset):

```text
2026-10-17T03:48:10Z
$ Bash: echo x > ".env"
(silent — no decision)
exit=0
$ Bash: printf k > ".env.local"
(silent — no decision)
exit=0
$ Bash: rm -rf infra
(silent — no decision)
exit=0
$ Bash: mv secrets /tmp/x
(silent — no decision)
exit=0
$ Bash: rm -rf 'infra/'
(silent — no decision)
exit=0
$ Bash: echo "edit .env later"
(silent — no decision)
exit=0
```

The first five are the two P1s: each writes, removes or moves a sensitive path with no prompt. The
last is SC3 (quoted data) and must stay silent.

### Fix round 1 — AFTER

Implementing agent, same script, after the fix, before the fix commit:

```text
2026-10-17T03:49:33Z
$ Bash: echo x > ".env"
ask: [hook:sensitive-path] This Bash call touches a sensitive path: .env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it.
exit=0
$ Bash: printf k > ".env.local"
ask: [hook:sensitive-path] This Bash call touches a sensitive path: .env.local (pattern `.env.*`). Listed in .claude/sensitive-paths.txt and no active task predicts it.
exit=0
$ Bash: rm -rf infra
ask: [hook:sensitive-path] This Bash call touches a sensitive path: infra (pattern `infra/**`). Listed in .claude/sensitive-paths.txt and no active task predicts it.
exit=0
$ Bash: mv secrets /tmp/x
ask: [hook:sensitive-path] This Bash call touches a sensitive path: secrets (pattern `**/secrets/**`). Listed in .claude/sensitive-paths.txt and no active task predicts it.
exit=0
$ Bash: rm -rf 'infra/'
ask: [hook:sensitive-path] This Bash call touches a sensitive path: infra/ (pattern `infra/**`). Listed in .claude/sensitive-paths.txt and no active task predicts it.
exit=0
$ Bash: echo "edit .env later"
(silent — no decision)
exit=0
```

Verification run for this round:

```text
2026-10-17T03:49:14Z
$ python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
32 passed, 25 subtests passed in 1.08s
1041 passed, 25 subtests passed in 16.78s
exit=0
$ bash scripts/validate.sh
validate.sh: PASS
exit=0
$ python3 scripts/gen_sandbox_profile.py --check
exit=0
```

What changed (`.claude/hooks/pre_tool_sensitive_path.py` only; `lib/shell_data.py` untouched):

- **P1 quoted redirect target**: `command_tokens` collects every quoted word right after `>`, `>>`,
  `>|`, `&>` or `N>` (`QUOTED_REDIRECT_TARGET_PATTERN`) from the heredoc-stripped text, *before*
  `strip_quoted_spans` removes data spans, and checks each as a path. A quoted `>` target inside a
  data span (`echo "a > 'b'"`) is also collected — that can only over-ask.
- **P1 bare directory**: `_pattern_matches` tries each slash-pattern candidate as written and with a
  trailing `/`, so `infra/**` and `**/secrets/**` cover `infra` and `secrets` themselves. A plain
  *file* named `infra` now asks too — over-asks, the safe side.
- **P3**: `itertools.islice(glob.iglob(...), MAX_GLOB_MATCHES)` stops the walk at the cap.
- Tests (written first, 9 subtests RED before the fix): `test_bash_quoted_redirect_target_behind_data_command_asks`,
  `test_bash_quoted_redirect_to_ordinary_path_is_silent`, `test_bash_directory_named_by_dir_pattern_asks`,
  `test_directory_lookalikes_stay_silent`. The SC8a mutation anchor moved with the renamed line
  (`strip_quoted_spans(unheredoc)`); the control still asserts SC4 goes RED.

---

## Assumption check (implementing agent, 2026-10-17)

**Assumption**: PreToolUse can return an `ask` decision as
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "..."}}`.

**Result: holds.** Installed CLI: `claude --version` → `2.1.302 (Claude Code)`. Source:
https://code.claude.com/docs/en/hooks, "PreToolUse decision control" (fetched 2026-10-17), verbatim:

> `PreToolUse` hooks can control whether a tool call proceeds. Unlike other hooks that use a
> top-level `decision` field, PreToolUse returns its decision inside a `hookSpecificOutput` object.
> This gives it richer control: four outcomes (allow, deny, ask, or defer) …
>
> `"ask"` prompts the user to confirm. … `permissionDecisionReason`: For `"ask"`, shown to the user
> in the permission prompt. When Claude Code denies the call in a `-p` run where no one can answer
> that prompt, Claude reads the reason in the tool result instead.
>
> When multiple PreToolUse hooks return different decisions, precedence is `deny` > `defer` > `ask` > `allow`.
>
> A hook's `"ask"` also forces a permission prompt in auto mode: the classifier can still deny the
> tool call, but it can't approve the call silently.

Two consequences recorded for the Supervisor:

1. **Headless runs**: in a `-p` run nobody can answer the prompt, so `ask` becomes a **deny** with
   the reason shown to the agent. A headless sub-agent therefore cannot touch a sensitive path at
   all unless its guide predicted it — consistent with T147's intent.
2. **AC4 interpretation — the hook stays silent, it does not emit `allow`.** Per the same table,
   `"allow"` *"skips the permission prompt"* — i.e. it would auto-approve the whole tool call,
   granting more than this hook's concern (a predicted Bash path would wave through every other part
   of that command). So when the active task predicts the path, the hook emits **no decision** (exit
   0, empty stdout = "normal permission flow applies"): no prompt *from this hook*, and the
   session's own permission mode decides as it would without T146. Tests assert "no `ask`, empty
   stdout". If the Supervisor wants a literal `allow`, it is a one-line change in `main()`.

## Implementation notes (implementing agent)

- **Files beyond the prediction**: `site/index.html` (one hook-table row — `tests/test_site_content.py`
  requires every wired hook to appear there). `MANIFEST` gained only `.claude/sensitive-paths.txt`;
  the hook itself already ships under the existing `.claude/hooks` entry.
- **`guide_sections` heading quirk (not fixed — out of scope)**: `slice_section` appends `\b` after
  the heading, which can never match after a closing `)`, so
  `read_guide_section(id, "Files to Change (Predicted)", …)` always returns `None`. The hook asks for
  the prefix `Files to Change` instead (the slicer accepts a trailing qualifier). Any future caller
  looking up a `(…)`-suffixed heading will hit the same silent `None` — worth a follow-up task.
- **Path anchoring**: a `/` pattern is matched from the project dir *or* the call's `cwd` (a Stage 3
  agent's cwd is its worktree, while `$CLAUDE_PROJECT_DIR` is the main checkout). A path under
  neither is matched from any of its directories — over-asks rather than guessing an anchor.
- **Bash globs**: `cat .env*` is expanded against the filesystem the way the shell would.
- **Recorded limitations**: paths built from variables (`"$F"`) are not resolved; Bash *reads* of
  sensitive paths ask too.

## Stage 4 — code-review (Supervisor, 2026-10-17)

Scope: `main..feat/t146-t147-harness-hardening`. Startup-reads line present and complete. Entry point `pre_tool_sensitive_path.py` is registered in `.claude/settings.json`. Task suites: `40 passed, 11 subtests passed`; `gen_sandbox_profile.py --check` reports the profile is fresh.

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P1 | `.claude/hooks/pre_tool_sensitive_path.py` `command_tokens` | A **quoted redirect target behind a data command** is stripped as data, so the write goes through silently. Reproduced through the real stdin protocol: `echo x > ".env"` → silent and `printf k > ".env.local"` → silent, while `echo x > .env` → ask. | 100 | Before `strip_quoted_spans`, collect quoted redirect targets (`>`, `>>`, `>|`, `&>`, `2>` followed by a quoted word) from the heredoc-stripped text and check them as tokens. Keep SC3 (`echo "edit .env later"` → allow). |
| P1 | same, `_pattern_matches` | **A directory named by a `dir/**` pattern doesn't match itself**, so the whole tree can be removed or moved. Reproduced: `rm -rf infra` → silent, `mv secrets /tmp/x` → silent, `rm -rf 'infra/'` → silent. | 100 | Also try `path_string + "/"` against slash patterns, so `infra/**` covers `infra`. |
| P2 | hook (design) | The "predicted path" escape and the pattern list are read from files the agent itself can write: its worktree's `tasks/TASK_GUIDE_*.md`, `.claude/sensitive-paths.txt` (when `CLAUDE_PROJECT_DIR` is the worktree), and the shared `active_task` state file. So the hook guards against accidents, not against a misbehaving agent. | 75 | Not fixed in this round. Record it as a limitation; a follow-up could read predictions from `main`'s committed guide. |
| P2 | `templates/subagent-sandbox.settings.json` (T147) | `memory/` is denied for the Edit tool only. Sandboxed Bash can still write `memory/` inside the worktree. | 75 | Record as a limitation (the Supervisor reviews the diff before merge), or add a sandbox filesystem write-deny for `memory/` if the setting exists. |
| P3 | hook `command_tokens` | `glob.glob(..., recursive=True)` builds the full list before the 200-match cap, so a `**` token walks the whole tree on every Bash call. | 75 | Use `itertools.islice(glob.iglob(...), MAX_GLOB_MATCHES)`. |

Verdict: **2 × P1 must be fixed before merge** → sent back to the implementing agent (fix round 1).

### Fix round 1 — response (implementing agent, 2026-10-17)

- P1 quoted redirect target — **fixed**, see Demonstration "Fix round 1 — AFTER".
- P1 `dir/**` matching the directory itself — **fixed**, same.
- P3 full `glob.glob` list — **fixed** (`islice(iglob(...))`).
- Both P2s — **not fixed, recorded as limitations** below, per the work order.

### Recorded limitations (from the Stage 4 P2s)

1. **The hook guards against accidents, not a misbehaving agent.** The predicted-path escape
   (`tasks/TASK_GUIDE_*.md`, read from both the project dir and the call's `cwd`), the pattern list
   (`.claude/sensitive-paths.txt`, when `CLAUDE_PROJECT_DIR` is the worktree) and the shared
   `active_task` state file are all writable by the agent the hook is gating. An agent that edits
   its own guide's `## Files to Change (Predicted)` table or the list silences the prompt. The
   Supervisor's pre-merge diff review is the backstop. Follow-up candidate: read predictions from
   `main`'s committed guide instead of the working tree.
2. **T147: `memory/` is write-denied for the Edit tool only.** `templates/subagent-sandbox.settings.json`
   does not stop sandboxed Bash from writing `memory/` inside the worktree. The Supervisor reviews
   the diff before merge; a sandbox filesystem write-deny for `memory/` is the follow-up if the
   setting exists.

## Stage 5 — /verify (2026-10-17, run by the user's `/verify`)

**Verdict: PASS.** Real Claude Code 2.1.302 sessions, in a throwaway linked worktree of this branch:
- Headless `claude -p`, asked to Write `.env` → refused: `[hook:sensitive-path] This Write call touches a sensitive path: …/vt/.env (pattern `.env`). Listed in .claude/sensitive-paths.txt and no active task predicts it.` The `.env` file was not created.
- SC9, interactive with `--permission-mode acceptEdits` in a herdr pane: `Write(notes.txt)` → `Wrote 1 line to notes.txt` with no prompt; `Write(.env)` → `Do you want to create .env? ❯ 1. Yes 2. No`. Declined, and `.env` was not created.
- 🔍 Bash inside the sandboxed session: `echo "x" > secrets.key` → `[hook:sensitive-path] This Bash call touches a sensitive path: secrets.key (pattern `**/*.key`)`.

## Stage 4 — code-review, fix round 1 delta (Supervisor, 2026-10-17)

Scope: `9a04675..7426c92` (`pre_tool_sensitive_path.py` and its tests). Both P1s are confirmed closed through the real stdin protocol: `echo x > ".env"`, `echo x >".env"`, `echo x | tee ".env"`, `rm -rf infra`, `mv secrets /tmp/x` → ask; `echo "edit .env later"` → silent. No new P0/P1.

| Sev | Finding | Conf | Action |
|---|---|---|---|
| P2 | **Over-asking on plain words, and the dir fix made it worse.** Any bare token equal to a protected directory name now asks: `git commit -m "update infra docs"`, `git commit -m "rotate secrets handling"`, `docker build -t infra .`. In a headless spawn, `ask` resolves to deny, so a sub-agent's commit is refused whenever its message names one of these words. The implementing agent hit this live and worked around it with `git commit -F`. | 100 | Follow-up task: treat `git commit -m/--message` values as data, or match a bare `dir/**` token only when it ends in `/` or exists as a directory. |
| P3 | `QUOTED_REDIRECT_TARGET_PATTERN` also fires on a `>` *inside* quoted prose (`echo "a > '.env'"` → ask). | 100 | Accept: it errs toward asking. |
