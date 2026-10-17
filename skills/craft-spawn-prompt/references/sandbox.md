# Sandboxed CLI spawn (T147)

For a `claude` CLI spawn, give the Supervisor this command, run from the task's worktree, with the
main checkout's literal absolute path (as in element 6) and the model from step 5:

```sh
claude --settings templates/subagent-sandbox.settings.json --add-dir <main-checkout>/.claude/hooks/.state --model <model> -p "<prompt>"
```

What the profile (`templates/subagent-sandbox.settings.json`) does:

- **Writes only inside the worktree.** `Edit(./**)` is the only edit allow rule. Sandboxed Bash can
  write to the cwd and the temp directory only. A linked worktree's shared `.git` stays writable,
  so `git commit` works.
- **No network.** `WebFetch` and `WebSearch` are denied. Bash runs in the OS sandbox with no allowed
  domains, `strictAllowlist` set and no unsandboxed retry. `failIfUnavailable` means `claude` will
  not start rather than run unsandboxed.
- **No sensitive paths.** Every `.claude/sensitive-paths.txt` pattern gets a `Read` and an `Edit`
  deny rule. `memory/` is edit-denied (Supervisor-only writes). T146's hook still runs from the
  project settings.
- **Never prompts.** `dontAsk` denies anything the rules don't pre-approve, including a T146 `ask`.
  A headless spawn therefore never waits for a human. The test runners the role guides use are
  pre-allowed.

Limits — say them, don't paper over them:

- `--add-dir` exists so element 6's state-file write can reach the main checkout. Without it, trace
  attribution breaks.
- The sandbox write-protects `.claude/` (settings, hooks, skills, agents). A task that edits the kit's
  own hooks cannot finish inside the profile, so spawn it unsandboxed and say so.
- On Linux, sandbox write rules with wildcards are skipped. Bash writes to sensitive *patterns*
  inside the worktree are therefore stopped by T146's hook, not by the OS.
- A `!` negation can't be expressed as a permission rule, so the profile is stricter than the list
  (`.env.example` is denied too).
- After editing `.claude/sensitive-paths.txt`, regenerate with
  `python3 scripts/gen_sandbox_profile.py`. `tests/test_subagent_sandbox_profile.py` fails until you
  do.

`Agent()` in-process spawns are **not** sandboxed. They run with the Supervisor's permissions,
whatever this profile says.
