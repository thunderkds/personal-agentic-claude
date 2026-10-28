# TASK_REVIEW — T197: The push gate checks the task being pushed, not every task on the board

> Sibling of `tasks/TASK_GUIDE_T197.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. A branch whose one task ID is not on the board (`feat/t999-x`) checks the whole board. D3 also says "absent from the board is allowed"; D2 and the Edge Case line both say global, and global is the safe side — RULE: `tasks/TASK_GUIDE_T197.md:164`
2. Every scoped push also needs the directory it runs in to be a git repo with a branch checked out, and no push config that can move the destination (`remote.*.push`, `remote.*.mirror`, a `push.default` other than simple/current). Otherwise the whole board — RULE: `tasks/TASK_GUIDE_T197.md:11`
3. A destination must name the same one task as the source (`feat/t900-x:feat/t900-x` scopes; `HEAD:main`, `feat/t900-x:release/1.0`, `HEAD:feat/t901-x` are global), and a source or destination rooted at `release/` or `integration/` is global even with one ID — RULE: `tasks/TASK_GUIDE_T197.md:161`
4. In a chain, each `git push` is resolved; two pushes of different tasks, or any unresolved one, are global — RULE: `tasks/TASK_GUIDE_T197.md:163`
5. D4 (merge/rebase never scoped) is enforced by the segment allowlist: `merge`/`rebase` are not in `SAFE_GIT_SUBCOMMANDS`, pinned by `test_d4_merge_rebase_and_branch_moves_are_never_read_only_subcommands`. A separate merge regex was written, then removed because no mutation could make a test fail without it — RULE: `.claude/hooks/tests/test_merge_gate_guard.py:8`
6. The command is tokenized with stdlib `shlex` and comments are switched off, because shlex drops the rest of a line after a mid-word `#` and could hide a second push — RULE: `tasks/TASK_GUIDE_T197.md:145`
7. How strict the allowlist is: only `cd <dir> &&`, `git add/commit/status/log/diff/show` (each with its own option allowlist, `fetch` removed by decision 12), and `tail/head/cat/grep/wc` reading the push's output through a pipe may share a command with a scoped push; anything else (e.g. `python3 -m pytest && git push origin feat/t900-x`) checks the whole board — DEBATED: keep the strict allowlist as built (Advocate 1: strict allowlist, confidence high — B is a denylist and a script can switch the branch or call `git merge` where the regex sees none, `pre_bash_block_unsafe_merge.py:611`; Advocate 2: any non-push command, confidence low — it could not defend its own option, a `checkout` earlier in the chain moves the `HEAD` the resolver already read; Advocate 3: bare `git push` only after `cd`, confidence medium — safest, but it concedes `tasks/TASK_GUIDE_T197.md:163` wants `commit && push` scoped and sends nearly every real push back to the whole board). Decided by the safer-option order in `skills/resolve-question/SKILL.md` § Debate (A is the smaller change than B and meets the guide's own edge case; C is safer but drops a case the guide lists). Known residual: `git commit` can run repo hooks that run code, which no name check sees — the same trust boundary as the branch name. ⚠ decided for you — please review
8. `git -C <dir> push` is not seen by `BLOCKED_PATTERNS` at all (a gap that existed before T197). Not fixed here; reported to the Supervisor — RULE: `agents/common-infrastructure.md:35`
9. No pre-existing test was edited: every earlier merge-gate test sends an event with no `cwd`, so it stays on the whole-board path, and the T190 oracle is still byte-identical — FACT: .claude/hooks/tests/test_merge_gate_companion_rows.py:196 "event = json.dumps"
10. The two `docs/claude-md/tracks.md` lines that said the gate "blocks every push" are reworded, and one paragraph documents the scoping — RULE: `tasks/TASK_GUIDE_T197.md:179`
11. Decision labels follow the written report shape (`RULE`/`FACT`/`DEBATED`/`SAFER OPTION`), not the `RULE/DEBATE/FLAG` wording in the coordinator's message — RULE: `docs/claude-md/tracks.md` `### Final report`
12. Stage 4 `security-review` found four bypasses; the Supervisor reproduced each against the real hook, then the implementing agent fixed them test first: the remote name must fullmatch `[A-Za-z0-9._-]+` (closes `git push {origin,--all}`); `&` anywhere makes the command unresolved (closes a backgrounded `cd`); each read-only git subcommand takes only its own option list and `fetch` is dropped (closes `--upload-pack` and `--output`) — RULE: `docs/claude-md/tracks.md` `### Final report`
13. The push narrows only to a task whose row is in `### In Progress` or `### Ready for Review`; Todo, Done, Blocked and absent tasks check the whole board. This changes the guide's D3 — DEBATED: narrow only for In Progress or Ready for Review (Advocate 1: narrow only for In Progress or Ready for Review, medium — Todo/Done branches over-block, which is visible and safe; Advocate 2: keep it as built, any board task narrows, medium — it is what D3 says, but it admits the gap is silent and a Done-task branch name bypasses the gate; Advocate 3: drop the narrowing, low — safest, but it undoes the user's request and it would itself pick X over Z). Decided by the safer-option order in `skills/resolve-question/SKILL.md` § Debate: X over-blocks where Y under-blocks, and it is a one-line membership test, so it is the smaller change than Z. ⚠ decided for you — please review
14. The implementing agent closed two more gaps of finding 3's kind (brace expansion into an option, and a glob in a path argument), and in `online` mode the push narrows only to a task the online filters kept — RULE: `tasks/TASK_GUIDE_T197.md:11` "Every doubt must still resolve to today's behaviour: check the whole board."
15. P3 findings from `code-review` (the plural name `pushed_task_ids` for a one-ID return, the lane size) are left as suggestions — RULE: `skills/code-review/SKILL.md` § Phase 4
Checks: tests `python3 -m pytest .claude/hooks/tests/test_merge_gate_push_scope.py -q && python3 -m pytest .claude/hooks/tests/ -q && sh scripts/validate.sh` — 103 passed; 1089 passed, 25 subtests passed; `validate.sh: PASS` (auto-checked, not /verify); tests `python3 -m pytest tests/ -q` — 889 passed (auto-checked, not /verify); mutation check of the resolver — 12 mutations (each guard removed in turn on a copy of the hook), all 12 killed (auto-checked, not /verify); reviews: `code-review` (Supervisor: 14 probes of the real hook, all as designed; P3 only — `pushed_task_ids` returns one ID though named plural because the guide fixes the entry point; the diff is 1215 lines against a 500-line lane, 718 of them tests) and `security-review` (sub-task: 5 findings, 4 reproduced by the Supervisor against the real hook — `git push {origin,--all}`, `cd x && git status & git push origin`, `git fetch --upload-pack='git merge …' ; git push …`, `git push origin feat/t001-x` with T001 Done — all four fixed test first in `96bbc32`/`b379c3e` and re-probed: each now checks the whole board; the fifth, a symlink with `git -C link/..`, is confidence 6 and not fixed) (auto-checked, not /verify); after the fixes: `test_merge_gate_push_scope.py` 131 passed, `.claude/hooks/tests/` 1117 passed, `tests/` 889 passed, `validate.sh: PASS`, mutation check 19 of 19 killed (auto-checked, not /verify); process slip: the three Advocate prompts for decision 13 named the guide path, so the spawn hook attributed those calls to T197 (a warning, not a block); real run `sh t197_demo.sh /home/hungnguyenhuu/workspace/pets/wt-t197` (the real hook on stdin, constructed repo) — printed `exit 0, empty stdout -> ALLOWED` for `git push origin feat/t900-x` and `BLOCKED ... T901 (no evidence row)` for `git push origin main` and `git merge feat/t900-x` (auto-checked, not /verify)
Not done: merge (yours); auto verify: running (T182)

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_merge_gate_push_scope.py` (new, 131 tests: AC 1-12 + Edge Case checklist + online mode + the four Stage 4 security-review findings + anti-vacuity), oracle `.claude/hooks/tests/data/t197_pre_change_gate_output.txt` captured from the unchanged hook and committed in `83f5891` before the hook edit (`9b295e9`). First RED at `83f5891`: `67 failed, 27 passed in 1.45s` (2026-10-28T08:09:38Z), GREEN `103 passed`. Findings RED at `96bbc32` (hook unchanged since `9b295e9`): `25 failed, 106 passed in 1.90s` (2026-10-28T08:33:07Z); GREEN at `b379c3e`: `131 passed in 1.37s` |
| Verification command run | ☑ pass | 2026-10-28T08:35:52Z at `b379c3e`, exact command from the guide: `131 passed in 1.37s` / `1117 passed, 25 subtests passed in 23.01s` / `validate.sh: PASS`. Also `python3 -m pytest tests/ -q` → `889 passed in 62.42s` |
| Negative cases hold | ☑ pass | AC 4-11 each have a test that asserts the whole-board answer (`T901 (no evidence row)`): two IDs, own In Progress row, own `☑ fail` companion row, not-a-repo / detached / no `cwd`, merge and rebase, `--all`/`--mirror`/tag/`--tags`/delete, `cat900`/`t900x`/`t900_x`, heredoc/echo/`bash -c`/comment/`$(...)`/backtick/env prefix/wrapper. Stage 4 security-review findings, each a test that failed before `b379c3e`: (1) `git push {origin,--all}` / `{origin,--mirror}` / `{origin,--tags}` and path/URL remotes; (2) `cd <T-branch repo> && git status & git push origin` from `main`, and any `&`; (3) `git fetch --upload-pack='git merge feat/t901-y' . ; git push origin feat/t900-x`, `git diff/log --output=`, unknown options, `-m -x`, `{--stat,--output=.git/HEAD}`, `git log *`; (4) a branch named after a Todo / Done / lane-less task, and online a teammate's task the filter drops. Mutation check (each guard removed in turn on a copy of the hook): 19 mutations, all 19 killed |
| verify | ☑ pass | auto-run by hook, session 20b506d2-6f3c-431e-8b7c-bf91de59156c, commit a37754d5a42d99304ae59b5b7bfe66dcff0cbf57, log .claude/verify-runs/T197-a37754d5a42d.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | For the Stage 4 reviewer. Blast radius: `pre_bash_block_unsafe_merge.py` (new `pushed_task_ids` section + the narrowing in `main()`), the guard allowlist (`merge_gate_guard.py`, `test_merge_gate_guard.py`), `docs/claude-md/tracks.md` (two sentences + one paragraph). Every gate caller is this one hook |
| Full smoke suite still green (no regression) | ☑ pass | `.claude/hooks/tests/` `1117 passed, 25 subtests passed`; `tests/` `889 passed`; no pre-existing test edited except the allowlist pin in `test_merge_gate_guard.py` |
| **Companion score (easy-verifier)** | ☑ N/A | neither companion tool was run by the implementing agent |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component: a hook and its tests |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured against the unchanged hook (branch head `c8c863c`, no implementation commit yet).
The demo script copies the worktree's `.claude/hooks/` into a throwaway git repo on branch `feat/t900-x`,
writes a board with T900 (filled `verify` row + pytest trace record) and T901 (no evidence) both in Ready
for Review, and pipes a real `PreToolUse` event (`tool_name`, `cwd`, `tool_input.command`) into
`pre_bash_block_unsafe_merge.py`. Command: `sh <scratchpad>/t197_demo.sh /home/hungnguyenhuu/workspace/pets/wt-t197`
(the ATTRIBUTION_REMEDY note is cut from each reason for length).

```
captured 2026-10-28T08:04:54Z
hook: /home/hungnguyenhuu/workspace/pets/wt-t197/.claude/hooks/pre_bash_block_unsafe_merge.py @ c8c863c

$ git push origin feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git push origin feat/t901-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git push origin main   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git merge feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git add -A && git commit -m 'wip' && git push -u origin feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.
```

The verified task T900's own branch push is refused for T901, another session's task. The first
Verification Command step, at the same time:

```
$ python3 -m pytest .claude/hooks/tests/test_merge_gate_push_scope.py -q   # 2026-10-28T08:04:54Z
no tests ran in 0.00s
```

**AFTER**: same script, same fixture, against the changed hook after the Stage 4 security-review fixes
(`b379c3e`). The output is the same as the first AFTER run at `9b295e9` (2026-10-28T08:18:08Z). The four
bypass commands the security-review reproduced now all resolve to "unresolved" (the whole board): see
the `Negative cases hold` Evidence row.

```
captured 2026-10-28T08:37:26Z
hook: /home/hungnguyenhuu/workspace/pets/wt-t197/.claude/hooks/pre_bash_block_unsafe_merge.py @ b379c3e

$ git push origin feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
exit 0, empty stdout -> ALLOWED

$ git push origin feat/t901-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git push origin main   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git merge feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.

$ git add -A && git commit -m 'wip' && git push -u origin feat/t900-x   (cwd: fixture repo on branch feat/t900-x)
exit 0, empty stdout -> ALLOWED
```

The demo script, for a witness to rerun (`sh t197_demo.sh <worktree>`; it builds and deletes its own
fixture in `mktemp -d`):

```sh
#!/bin/sh
set -e
WT="$1"
FIX=$(mktemp -d)
trap 'rm -rf "$FIX"' EXIT
mkdir -p "$FIX/.claude" "$FIX/tasks" "$FIX/memory/event-trace"
cp -r "$WT/.claude/hooks" "$FIX/.claude/hooks"
rm -rf "$FIX/.claude/hooks/.state"
printf '# PROJECT_KANBAN\n\n### Todo\n\n### In Progress\n\n### Ready for Review\n- [ ] **T900** — verified fixture task | common-infrastructure | C2 | Risk: Medium | P0\n- [ ] **T901** — unverified fixture task (another session) | backend-developer | C1 | Risk: Low | P1\n\n### Done\n' > "$FIX/PROJECT_KANBAN.md"
printf '# TASK_GUIDE - T900\n\n### Evidence\n\n> Moved to tasks/TASK_REVIEW_T900.md.\n' > "$FIX/tasks/TASK_GUIDE_T900.md"
printf '# TASK_REVIEW - T900\n\n## Evidence\n\n| Check | Result | Notes |\n|---|---|---|\n| verify | ☑ pass | verify skill run, feature confirmed working — pass |\n' > "$FIX/tasks/TASK_REVIEW_T900.md"
python3 -c 'import json;print(json.dumps({"timestamp":"2026-10-28T00:00:00+00:00","tool_name":"Bash","summary":json.dumps({"command":"python3 -m pytest -q"}),"is_error":False}))' > "$FIX/memory/event-trace/T900.jsonl"
git -C "$FIX" init -q -b feat/t900-x
git -C "$FIX" -c user.email=d@example.com -c user.name=d commit -q --allow-empty -m fixture
run() {
  printf '\n$ %s   (cwd: fixture repo on branch %s)\n' "$1" "$(git -C "$FIX" rev-parse --abbrev-ref HEAD)"
  python3 -c 'import json,sys;print(json.dumps({"tool_name":"Bash","cwd":sys.argv[2],"tool_input":{"command":sys.argv[1]}}))' "$1" "$FIX" \
    | GIT_CONFIG_GLOBAL=/dev/null python3 "$FIX/.claude/hooks/pre_bash_block_unsafe_merge.py" \
    | python3 -c 'import json,sys;t=sys.stdin.read().strip();print("exit 0, empty stdout -> ALLOWED" if not t else "BLOCKED: "+json.loads(t)["reason"].split("\n  Note:")[0])'
}
date -u +"captured %Y-%m-%dT%H:%M:%SZ"
echo "hook: $WT/.claude/hooks/pre_bash_block_unsafe_merge.py @ $(git -C "$WT" rev-parse --short HEAD)"
run "git push origin feat/t900-x"
run "git push origin feat/t901-x"
run "git push origin main"
run "git merge feat/t900-x"
run "git add -A && git commit -m 'wip' && git push -u origin feat/t900-x"
```

(The script captured above wrote the board with a heredoc; this copy uses `printf` so the block has
no nested heredoc. The board text is the same.)

**DELTA**: A session can now push its own verified task's branch while another session's task sits
unverified in Ready for Review. `main`, merges, a branch named after a task that is not in In Progress or
Ready for Review, and any push the hook cannot tie to one task are still checked against the whole board.

**WITNESS**: pending. The implementing agent (common-infrastructure, T197) ran BEFORE at
2026-10-28T08:04:54Z and AFTER at 2026-10-28T08:18:08Z (`memory/event-trace/T197.jsonl`). An independent
witness is T182's headless `/verify T197` run or the user.

**Trust boundary (Edge Case checklist)**: the scoping trusts the branch name. A branch that lies about its
task (T901's work pushed on `feat/t900-x`) is checked against T900, and the push needs T900's own
evidence; it no longer needs T901's. Stated, not closed: closing it would need the gate to know which
task wrote which commit, which nothing records today.
