# TASK_REVIEW — T147: Spawned sub-agents run under a tighter sandbox profile than the Supervisor

> Sibling of `tasks/TASK_GUIDE_T147.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_subagent_sandbox_profile.py` (new, 12 tests): SC1/AC1 Read+Edit deny per pattern (re-derived independently of the generator), brace expansion, no network (sandbox + WebFetch/WebSearch), worktree-only edits + `memory/` deny, no `/`-anchored rule; AC3 generator `--check` + a grown list is caught; AC5 `dontAsk` + test runners pre-allowed; SC5/AC4 Supervisor settings carry no `permissions`/`sandbox` (also vs `git diff main`); AC2 skill → `references/sandbox.md` command carries `--settings` + `--add-dir`, `Agent()` stated unsandboxed; MANIFEST ships profile, generator, list. Output (2026-10-17T03:38:09Z): `12 passed in 0.05s` |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_subagent_sandbox_profile.py -q` → `12 passed in 0.05s`, exit=0 (implementing agent, 2026-10-17T03:38:09Z) — reviewer to re-run |
| Negative cases hold (automated part) | ☑ pass | Appending `vault/**` to the list without regenerating → `missing_denies` returns `['Read(vault/**)', 'Edit(vault/**)']`. **Live negatives SC2 (write `../outside.txt` refused), SC3 (`curl https://example.com` refused) and SC4 (`python3 -m pytest -q` runs with no prompt) are pending** — Supervisor/user run them at `/verify`; not faked here |
| verify | ☐ pending — user runs `/verify`, including live SC2–SC4 with a real `claude --settings templates/subagent-sandbox.settings.json` spawn in a scratch worktree | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests/ .claude/hooks/tests/ -q` → `1037 passed, 11 subtests passed in 18.47s`. At commit `e1002d9` (2026-10-17T03:39:04Z): install_update_smoke 9/0, settings_merge 40/0, setup 18/0, manifest_exclusions 8/0, harness_projection 41/0, update 38/0, update_removals 30/0, install_backups 17/0. (install_update_smoke clones the last commit, so it showed `FAIL: AC1: MANIFEST path 'scripts/gen_sandbox_profile.py' missing` until the generator was committed.) `bash scripts/validate.sh` → `PASS` |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by the implementing agent at `9d470d7` — T146 committed, no T147 change yet):

```text
2026-10-17T03:34:17Z
$ python3 -m pytest tests/test_subagent_sandbox_profile.py -q
ERROR: file or directory not found: tests/test_subagent_sandbox_profile.py

no tests ran in 0.00s
exit=4
$ ls templates/subagent-sandbox.settings.json scripts/gen_sandbox_profile.py
ls: cannot access 'templates/subagent-sandbox.settings.json': No such file or directory
ls: cannot access 'scripts/gen_sandbox_profile.py': No such file or directory
exit=2
$ grep -c -e "--settings" -e "sandbox" skills/craft-spawn-prompt/SKILL.md
0
$ git diff main -- .claude/settings.json | grep -c permissions
0
```

Prior content of the part of `skills/craft-spawn-prompt/SKILL.md` this task changes (`#### 6. Output`),
verbatim:

```markdown
#### 6. Output
Return: 1. the assembled prompt (fenced, ready for `Agent({ subagent_type, prompt })`); 2. the
pre-flight verdict; 3. the recommended spawn model as `<cli> · <Cn> → <model>` (or STOP-and-ask).

The Supervisor reads this output and issues the `Agent()` call itself; this skill never calls it.
```

No profile, no generator, no CLI spawn command and no word on sandboxing: a CLI-spawned sub-agent
ran with whatever permissions its terminal's `claude` picked up, the same as the Supervisor's.

**AFTER** (implementing agent, at `e1002d9`):

```text
2026-10-17T03:38:09Z
$ python3 -m pytest tests/test_subagent_sandbox_profile.py -q
............                                                             [100%]
12 passed in 0.05s
exit=0
$ python3 scripts/gen_sandbox_profile.py --check; echo $?
0
```

New content of `skills/craft-spawn-prompt/SKILL.md` `#### 6. Output`, verbatim:

```markdown
#### 6. Output
Return: 1. the assembled prompt (fenced, ready for `Agent({ subagent_type, prompt })`); 2. the
pre-flight verdict; 3. the recommended spawn model as `<cli> · <Cn> → <model>` (or STOP-and-ask); 4. for a `claude` CLI spawn, the sandboxed command in `references/sandbox.md` (T147). `Agent()` spawns are **not** sandboxed — they run with the Supervisor's permissions; say so whenever you pick that path.
```

with the command in `skills/craft-spawn-prompt/references/sandbox.md`:
`claude --settings templates/subagent-sandbox.settings.json --add-dir <main-checkout>/.claude/hooks/.state --model <model> -p "<prompt>"`.
Live behaviour (SC2–SC4) is **pending**, at `/verify`.

**DELTA**: The Supervisor can launch a CLI sub-agent under a generated profile. That agent can edit only inside its worktree, has no network, cannot read or edit any sensitive-path pattern or edit `memory/`, and never stops to ask. The Supervisor's own settings stay unchanged, and `Agent()` spawns are documented as unsandboxed.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T147.jsonl`, never the
implementing agent alone]

---

## Assumption check (implementing agent, 2026-10-17)

**Assumption**: `permissions` rule syntax (`Edit(<glob>)`, `Bash(<pattern>)`) and `sandbox` keys for
network exist. **Result: holds.** Installed CLI `2.1.302 (Claude Code)`; `bwrap` and `socat` present,
and `bwrap --unshare-net --unshare-user true` exits 0 on this machine (AppArmor has
`bwrap-userns-restrict`).

Sources (fetched 2026-10-17), verbatim excerpts:

- https://code.claude.com/docs/en/sandboxing — *"Network | No direct route out. Connections go
  through a proxy on your machine that checks each host against your allowed domains, which start
  empty."* · *"Strict allowlist: if you set `strictAllowlist` to `true` in user, managed, or CLI
  `--settings` settings, Claude Code denies sandboxed commands access to any host outside the
  allowlist instead of prompting."* · *"You can disable the unsandboxed retry by setting
  `"allowUnsandboxedCommands": false` … If you or your administrator disable the retry in managed
  settings or with the `--settings` flag, the sandbox becomes admin-required."* · *"Git worktrees:
  when the working directory is a linked git worktree, the sandbox also allows writes to the main
  repository's shared `.git` directory"* · *"The sandbox covers shell commands only. Claude's file
  tools, MCP servers, and hooks run outside it."*
- https://code.claude.com/docs/en/permissions — *"Rules are evaluated in order: deny, then ask, then
  allow. … An allow rule can't carve an exception out of a deny rule."* · path table: *"A file passed
  with `--settings <file>` | `<directory of file>/path`"* and *"`path` or `./path` | Path relative to
  current directory"* · *"Bare filenames follow gitignore semantics and match at any depth"* ·
  `dontAsk`: *"Auto-denies every call that would otherwise prompt; file reads in your working
  directories and other actions that need no approval still run, as do tools pre-approved via …
  `permissions.allow` rules"* · *"Claude Code checks file permissions against `Edit(path)` and
  `Read(path)` rules only. If you write a path rule for `Write` … Claude Code accepts the rule but
  never consults it"*.
- https://code.claude.com/docs/en/settings-reference, "Sandbox path prefixes" — *"`allowWrite` and
  `denyWrite`: … On Linux and WSL2, the sandbox mounts concrete paths, so Claude Code skips an entry
  that contains `*`, `?`, or `[` … Claude Code adds the paths from your `Edit` permission rules to
  these lists, so the same limit applies to them"* · *"`denyRead` and `allowRead`: wildcards work on
  every platform."*

## Implementation notes (implementing agent)

How each guide requirement is met, and where the docs forced a choice:

- **Never needs a human (AC5)**: `defaultMode: dontAsk`. Anything that would prompt is denied
  instead, including T146's `ask`. A headless spawn never stalls. To confirm live at SC2: the
  T146-`ask`→deny behaviour under `dontAsk` is inferred from the docs, not observed.
- **Writes only in the worktree**: `Edit(./**)` is the only edit allow, and it is cwd-relative.
  A `/path` rule would anchor at `templates/`, because a `--settings` file anchors at its own
  directory. Edits elsewhere would prompt, so `dontAsk` denies them. Bash writes are bounded by
  the OS sandbox (cwd + temp dir + the worktree's shared `.git`).
- **Sensitive paths**: a `Read(...)` and an `Edit(...)` deny per pattern, braces expanded,
  cwd-relative. **Deviation**: the `!` negation (`!.env.example`) cannot be expressed, so the profile
  denies `.env.example` too (stricter). Sensitive files *outside* the worktree are not covered by
  these rules. They are covered by `dontAsk` (the Read tool outside the working dirs would prompt, so
  it is denied) and by T146's hook for Edit/Write/Bash (floating-path matching).
- **Reads outside the worktree (decision b)**: allowed for Bash (the sandbox reads most of the
  machine). **Not** allowed for the Read tool: under `dontAsk`, a read outside the working dirs
  would prompt, so it is denied. A `Read(//**)` allow rule was considered and rejected. It would
  need matching `//**/…` deny rules, and the docs say Linux expands wildcard read entries to concrete
  paths, so a filesystem-wide pattern risks a full-disk walk at startup. **Question for the
  Supervisor**: is Bash-only reading outside the worktree acceptable? If not, `--add-dir <path>`
  per spawn is the narrow fix.
- **No network**: `WebFetch` and `WebSearch` are denied as whole tools. The sandbox has
  `allowedDomains: []`, `strictAllowlist: true` (honoured from `--settings`),
  `allowUnsandboxedCommands: false` and `failIfUnavailable: true`.
- **Trace attribution**: the state file lives in the main checkout, outside the worktree. The spawn
  command adds `--add-dir <main-checkout>/.claude/hooks/.state` so the sandboxed `printf >` lands.
- **Known limits**, recorded in `skills/craft-spawn-prompt/references/sandbox.md`:
  - The sandbox write-protects `.claude/` (settings, hooks, skills, agents), so kit-hook tasks such
    as T146 itself cannot run inside the profile.
  - On Linux, wildcard `Edit` denies don't reach the OS layer. Bash writes to sensitive patterns are
    stopped by T146's hook, not the kernel.
- **Files beyond the prediction**:
  - `skills/craft-spawn-prompt/references/sandbox.md` (new). The SKILL.md is capped at 80 lines by
    `.claude/hooks/tests/test_spawn_prompt_cache_note.py` (T092) and was already at 80, so the
    change there is net zero lines and the detail lives in the reference.
  - `MANIFEST` also ships `scripts/gen_sandbox_profile.py`. The profile ships under the existing
    `templates` entry.
- **Not touched**: `.claude/settings.json` (AC4) and `.claude/sensitive-paths.txt` (read only).
