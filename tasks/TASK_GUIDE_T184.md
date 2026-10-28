# TASK_GUIDE — T184: Kit settings defaults from the Claude Code settings reference — credential read-denies, destructive-command `ask` rules (merged add-only), worktree base ref, skill-listing budget check
**Status**: CLOSED 2026-10-27, will not do — user: "the config should go by the taste, we no need to update as initial". Kept as the content source (evaluation table) for T185/T187.
**Date**: 2026-10-27
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27: "checking all of these config from here https://code.claude.com/docs/en/settings-reference, depend on my work style and as senior engineer, which settings should be add in the initial, and we should have" → follow-up: "let investigate for clearly more, evaluate setting if needed, create the task guide automate".

**Restated intent**:
> The kit's shipped `.claude/settings.json` (copied on fresh install, merged on existing projects by `lib/merge-settings.py`) gains the small set of settings-reference keys that close real gaps in the kit's safety and Stage 3 worktree flow — and nothing speculative. Every key is justified by a concrete failure it prevents in this kit.

**Evaluation summary (Supervisor, from the full settings reference, CLI 2.1.311)** — keys considered and REJECTED for the shared kit file, with reason (do not re-add):

| Key | Why not in the kit file |
|---|---|
| `env.CLAUDE_STEP_LIMIT` | `pre_agent_step_limit.py:64` already defaults to 90; shipping it is a no-op |
| `minimumVersion` | Only constrains auto-updates; does not stop an old CLI starting (`requiredMinimumVersion` is managed-only) |
| `permissions.disableBypassPermissionsMode` | Deny rules and hooks still apply in bypass mode; locking it removes a user choice for no gate benefit |
| `permissions.blockReadsOutsideWorkingDirectories` | Breaks the Supervisor reading sibling worktrees (`../wt-tNNN`) and `~/.claude` memory |
| `sandbox.*` for the main session | Needs `bubblewrap` + `socat`; `failIfUnavailable` would brick installs without them. Sub-agent sandbox already exists: `templates/subagent-sandbox.settings.json` (T147) |
| `attribution`, `model`, `effortLevel`, `cleanupPeriodDays`, `autoUpdatesChannel`, `statusLine` | Personal preference → user settings, never a shipped project file |
| `plansDirectory`, `enableAllProjectMcpServers`, `includeGitInstructions`, `respectGitignore` | Defaults already correct for the kit, or no request for them |

**Out of scope**:
- The user's own `~/.claude/settings.json` and `.claude/settings.local.json` (personal cleanup — separate, user-run; see plan artifact)
- `templates/subagent-sandbox.settings.json` and `scripts/gen_sandbox_profile.py`
- Any hook script under `.claude/hooks/`
- Main-session sandboxing

**Requirement Refs**: none in `PRD.md` (kit-maintenance request, user-originated 2026-10-27).

### Decisions (resolved 2026-10-27 — user: "update as initial", i.e. take the Supervisor recommendation for each)

- **D1 = union `ask` add-only** (like `deny`); `allow` stays never-copied.
- **D2 = fill-if-absent per `worktree` sub-key**; never overwrite a project value.
- **D3 = leave `autoMemoryEnabled` unset**; document the overlap with the kit's `memory/` tier in one line (in the `merge-settings.py` docstring is NOT the place — put it where T185 documents the defaults on the site).

Follow-up: T185 (site board, `PROJECT_KANBAN_SITE.md`) documents these shipped defaults on `site/index.html` and depends on this task.

Original options as recorded at Stage 2:

- **D1 — Merge `permissions.ask` add-only.** T148 rule: kit `allow`/`ask` are never copied. `ask` only narrows (it adds a prompt, never removes one), so it belongs with `deny`, not `allow`. Recommend: union `ask` add-only exactly like `deny`; `allow` stays never-copied. Without D1, existing projects never receive the `ask` rules.
- **D2 — `worktree` block merge policy.** Recommend: fill-if-absent per sub-key (`baseRef`, `symlinkDirectories`) — never overwrite a project value. Alternative: copy on fresh install only.
- **D3 — `autoMemoryEnabled`.** The kit has its own Supervisor-only `memory/` tier; Claude Code auto memory is a second, uncoordinated store. Recommend: leave unset (user choice) and document the overlap in one line; alternative: ship `false`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user accepted the plan 2026-10-27)
- [x] D1–D3 answered by the user and recorded in this file
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `merge_permission_denies` (in `lib/merge-settings.py`, called by `setup.sh` `install_settings` / `update.sh`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Kit `.claude/settings.json` `permissions.deny` adds credential read-denies: `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`, `Read(./**/secrets/**)`, `Read(~/.ssh/**)`, `Read(~/.aws/**)`, `Read(~/.config/gh/**)` — existing `harness-anchors` entries kept | Safety gap: today nothing blocks reading secrets (the sensitive-path hook covers Edit/Write/Bash only, not Read) |
| 2 | `.env.example` stays readable despite `Read(./.env.*)` (deny is first-match, so either an explicit test proves it is readable, or the pattern is narrowed so it does not match) | Matches `.claude/sensitive-paths.txt` `!.env.example` intent |
| 3 | Kit `permissions.ask` ships: `Bash(git push --force *)`, `Bash(git push -f *)`, `Bash(git reset --hard *)`, `Bash(rm -rf *)` | Destructive-command confirmation |
| 4 | (D1) `lib/merge-settings.py` unions kit `ask` into project `ask` add-only (project order first, no duplicates); kit `allow` still never copied; a project `allow` rule identical to a kit `ask` rule is left in place and reported on stderr as a warning (allow and ask conflict — ask wins by precedence, but the user should know) | Existing projects must receive AC 3 |
| 5 | (D2) Kit ships `"worktree": {"baseRef": "head", "symlinkDirectories": ["node_modules", ".venv"]}`; merge fills absent sub-keys only, never overwrites a project value | Default `baseRef: "fresh"` branches from `origin/<default>`, so a sub-agent worktree misses TASK_GUIDEs committed locally but not pushed — the Stage 3 spawn reads a stale or missing guide |
| 6 | AC 5 is proven live: an `Agent(isolation: "worktree")` spawn (or `EnterWorktree`) from a repo whose local `main` is 1 commit ahead of `origin/main` creates a worktree that contains that commit; and a missing `node_modules` in the source repo does not fail worktree creation | Proves the key does what the docs say for the kit's actual spawn path |
| 7 | `/doctor` skill-listing usage measured with the kit's full skill roster installed; if descriptions are being dropped at the 0.01 default, ship `skillListingBudgetFraction` at the lowest value that keeps every kit skill description (record the measured numbers); else ship nothing and record the numbers | Kit ships ~40 skills; dropped descriptions silently stop skills from triggering |
| 8 | Merge stays idempotent: install + update run twice → byte-identical `settings.json` (existing SC5 still passes with the new keys) | Regression guard |
| 9 | Negative: a project `settings.json` whose `permissions.ask` or `worktree` is the wrong type (string, number) → refused, nothing written, exit 2 (same as existing invalid-shape handling) | Merge safety contract |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fresh install into empty repo | `settings.json` has all AC 1 denies, AC 3 asks, AC 5 worktree block | `tests/test_settings_merge.sh` new case |
| 2 | Existing project with user `ask: ["Bash(npm publish *)"]` and `worktree.baseRef: "fresh"` | After update: user ask first, kit asks appended; `baseRef` still `"fresh"`; `symlinkDirectories` added | automated test |
| 3 | Project `permissions.ask` is `"x"` | exit 2, file byte-identical | automated test |
| 4 | Merge with D1 change reverted (mutation control) | Case 2 fails | automated test (mutation, like existing M1) |
| 5 | `Read(.env)` in a kit-installed scratch repo | Denied; `Read(.env.example)` allowed | manual live check in a scratch repo, transcript pasted |
| 6 | AC 6 scenario | Worktree contains the local-only commit | manual live check, `git -C <wt> log -1` pasted |

### Verification Command (exact, runnable)

```bash
bash tests/test_settings_merge.sh && sh scripts/validate.sh && sh scripts/smoke-install.sh && python3 -m pytest .claude/hooks/tests/ -q
```

---

## Approach

**Pattern reference**: `lib/merge-settings.py` `merge_permission_denies` (T148) — add-only union, project order first, die on wrong type. Mirror it for `ask`; write a small sibling for the `worktree` fill-if-absent rule. Tests: `tests/test_settings_merge.sh` T148 case and M1 mutation control.

**Vital slice**: AC 1 + AC 3 + AC 4 (credential denies and destructive `ask` rules reaching both fresh and existing projects).
**Cut list**:
- Main-session sandbox (see evaluation table)
- Merging any top-level scalar key beyond `worktree`
- A version check in `setup.sh` (no request; separate task if wanted)

Update the `merge-settings.py` module docstring "Permissions (T148)" paragraph to state the new `ask` and `worktree` rules — it is the ownership contract other tasks read.

---

## Edge Case Checklist

- [ ] `Read(./.env.*)` matches `.env.example` (AC 2)
- [ ] Deny path prefixes: in Read rules `./` is project-relative and `~/` is home — do not use the sandbox path semantics (`/path` absolute) by mistake
- [ ] Project `allow` contains `Bash(git *)` (this repo's own local file does): `ask` still wins by precedence — confirm with the live check, do not edit the user's local file
- [ ] Background sub-agents cannot answer an `ask` prompt; confirm a sub-agent hitting `git push --force` is blocked, not hung (`dontAsk` turns ask into deny)
- [ ] `symlinkDirectories` entry that does not exist in the source repo
- [ ] `worktree` present in project but `null`
- [ ] Older CLI that does not know `worktree` keys — must not reject the whole file (unknown keys are tolerated; verify on 2.1.311 only, note version)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/settings.json` | Add AC 1 denies, AC 3 `ask`, AC 5 `worktree`, AC 7 budget key if measured needed |
| `lib/merge-settings.py` | `ask` add-only union (D1), `worktree` fill-if-absent (D2), docstring |
| `tests/test_settings_merge.sh` | New cases for AC 1–5, 8, 9 + mutation control |
| `tasks/TASK_REVIEW_T184.md` | Evidence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py` | Out of scope; hooks already enforce gates |
| `templates/subagent-sandbox.settings.json` | T147 profile, generated from `sensitive-paths.txt` |
| `.claude/settings.local.json`, `~/.claude/settings.json` | User's personal files |
| `.claude/sensitive-paths.txt` | Hook input; changing it changes the sub-agent sandbox |

---

## Test Plan

Extend `tests/test_settings_merge.sh` (offline, real `setup.sh`/`update.sh`) with the SC1–SC4 cases above plus a mutation control. Live checks (AC 2, 6, Success 5–6) run in a scratch repo; paste transcripts into the review file.

---

## Completion Checklist

- [x] D1–D3 recorded
- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T184.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows: N/A (no UI)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
