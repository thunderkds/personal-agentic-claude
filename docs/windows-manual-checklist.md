# Windows manual checklist

Date: 2026-11-07 (T276). Run this on a real Windows machine after each Windows change. It proves what the tests cannot: a real Claude Code session using the kit. Write the result on the `Result:` line of each step, then send the file back or paste it into the PR.

You need: `git`, Python 3.8+ (`py -3` works), PowerShell 5.1 or 7, and Claude Code. Use a fresh folder each time.

1. **Install.** Clone the kit (`git clone -b windows <repo-url> D:\kit`), make an empty git project, set `$env:SUPERVISOR_REPO = "file:///D:/kit"`, run `powershell -ExecutionPolicy Bypass -File D:\kit\setup.ps1` in the project. Expect no `[error]` line. Result:
2. **Hooks in Windows form.** Open `.claude\settings.json`. Every hook command starts with `py` or `python` and has an `args` list. None starts with `python3`. Result:
3. **Open Claude Code in the project.** Start `claude`. No hook error appears at start. Result:
4. **`/wake`.** Run `/wake`. It prints a briefing and does not fail on `python3`. If the agent tries `python3` and fails, note the exact command. Result:
5. **A minimal-track task.** Ask for a small change (for example "add a line to README"). The agent states the track, writes a test first, changes, and writes a Decision record in `tasks/MINIMAL_LOG.md`. Result:
6. **A blocked merge.** Create a board row in Ready for Review with no verify evidence. Ask the agent to `git merge` a branch. The merge gate must block it (also try the PowerShell spelling: `git merge x` typed as a PowerShell command). Result:
7. **Auto verify.** Move a task to Ready for Review and run `py -3 .claude\hooks\stop_auto_verify.py --start T001` (use the real ID). It starts, writes a log in `.claude\verify-runs\`, and ends with a `verdict:` line. Result:
8. **Update twice.** Run `update.ps1` twice. Run `git status --short` after each. The second output is identical to the first. Result:
9. **Deny rule.** In the session, ask the agent to edit a file under `%USERPROFILE%\.claude\projects\` (any `.jsonl`). Claude Code must refuse (a permission denial), not write it. This checks the T251 rule on a Windows path. Result:
10. **Plugin install (optional).** `claude plugin marketplace add <repo-url>` then `claude plugin install easy-kit@easy-kit`, then `/wake`. The plugin install is unverified on Windows (ADR-0003 addendum). Write what happens, even a failure. Result:
