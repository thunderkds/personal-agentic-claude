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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_pre_tool_sensitive_path.py` (new, 28 tests): AC1 shipped list; AC2/SC1–SC2 Edit/Write; AC3/SC3–SC5 Bash via `shell_data`; AC4/SC6 predicted paths (silent — see Assumption check §2); AC5/SC7 missing list, malformed stdin, import failure; AC6 MANIFEST + `lib/merge-settings.py` merge; SC8 (a)/(b) mutation controls. Output (2026-10-17T03:30:57Z): `28 passed, 11 subtests passed in 0.89s` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_pre_tool_sensitive_path.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q` → `28 passed, 11 subtests passed in 0.89s` then `1025 passed, 11 subtests passed in 18.85s`, exit=0 (implementing agent, 2026-10-17T03:30:57Z) — reviewer to re-run |
| Negative cases hold | ☑ pass | `.env.example`, quoted data (`echo "edit .env later"`), heredoc-body mention, ordinary paths (`docs/infra.md`, `envoy.yaml`) stay silent; unpredicted sibling `infra/other.tf` and an unpredicted token in a mixed Bash command still ask. SC8 mutants: naive quoted-strip waves SC4 through, allow-on-failure waves SC7 through — both asserted RED |
| verify | ☐ pending — user runs `/verify`; SC9 (live permission prompt on Write `.env`) is checked there | not yet run — awaiting the user's `/verify` |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `tests/ .claude/hooks/tests/` 1025 passed (first run caught `tests/test_site_content.py::test_every_wired_hook_appears_in_hook_table` — fixed by adding the hook's row to `site/index.html`); `bash scripts/validate.sh` → `validate.sh: PASS`; `tests/test_settings_merge.sh`, `tests/test_setup.sh`, `tests/test_manifest_exclusions.sh` exit=0 |
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
