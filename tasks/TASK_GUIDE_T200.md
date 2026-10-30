# TASK_GUIDE — T200: `settings-setup` skill — the Supervisor offers settings profiles at Stage 1 and writes High security by default, add-only
**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `docs/prd/PRD_settings-profiles.md` (decisions D1–D5, FR-001..FR-008) and `docs/brainstorming/BRAINSTORMING_LOG_settings-profiles.md` (Path A, Edge Case Checklist)
7. Read `lib/merge-settings.py` `merge_permission_denies()` — the add-only union rule this task follows (do not import or change it; `lib/` is not shipped to user projects)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-29, verbatim: "if the users do not choose from the settings setup, the agents supervisor should generate the default settings with the high security and map with good approach for starting or the legacy following the options pick, or if needed, ask for question from settings up the app to generate the suitable settings following."

**Restated intent**:
> A new skill `settings-setup` runs as a Stage 1 checklist step. If the project's `.claude/settings.json` holds none of a profile's rules, the Supervisor offers the profiles, may ask up to 3 setup questions, and uses High security when the user skips. It shows the exact keys it will add and writes only after the user approves. The write is add-only into `.claude/settings.json`: it keeps every key, hook and rule already there. In `[auto]` mode it writes nothing and puts the recommendation in the final report.

**Out of scope** (what this task explicitly does NOT do):
- `setup.sh` changes (D2); `lib/merge-settings.py` changes.
- Sandbox or network keys in any profile (D5).
- Writing `~/.claude/settings.json` or `.claude/settings.local.json` (D4).
- The site's Build-tab profiles (T201). Only the `#skills` roster entry for the new skill is in scope here (the roster drift test in `tests/test_site_content.py:532` requires it).

**Requirement Refs**: `docs/prd/PRD_settings-profiles.md` FR-002, FR-003, FR-004 (source half), FR-005, FR-006, FR-007, NFR-001, NFR-003.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-29; D1–D5 + Path A chosen by the user)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

---

## Dependencies & Reachability

**Depends on**: none. T201 (site profiles) depends on this task's `profiles.json`.
**Entry point**: `Skill({ skill: "settings-setup" })`; script `python3 skills/settings-setup/scripts/apply_profile.py <profile-id> [--dry-run] [--settings PATH]`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `skills/settings-setup/profiles.json` holds profiles `high-security`, `legacy`, `solo-engineer`, `team-project`, `empty`, each with `id`, `label`, `for` (one line: who it is for) and `values` (dotted keys → values, lists fully written out, no `$suggest`) | FR-004 |
| 2 | `high-security.values` is exactly: `permissions.deny` = `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`, `Read(~/.ssh/**)`, `Read(~/.aws/**)`, `Read(~/.config/gh/**)`; `permissions.ask` = `Bash(git push --force *)`, `Bash(git push -f *)`, `Bash(git reset --hard *)`, `Bash(rm -rf *)`; `permissions.disableBypassPermissionsMode` = `"disable"`. No other key | FR-002, D5 |
| 3 | `legacy.values.permissions.deny` equals this repo's `.claude/settings.json` `permissions.deny` (asserted by a test that reads that file, not a hardcoded copy) | FR-003, D3 |
| 4 | `solo-engineer` and `team-project` equal today's page presets with `$suggest` expanded (`site/index.html:801`) | FR-004 |
| 5 | `apply_profile.py <id>` merges add-only into `.claude/settings.json`: lists are unioned (existing order first, no duplicates); a scalar is set only if the key is absent; nothing is removed or reordered; `hooks` and every other key are byte-for-byte equal after a JSON round trip | FR-007 |
| 6 | No file → the script creates it with the profile only. File unparseable, `permissions` not an object, or a target list not a list → exit 2, file byte-identical, reason on stderr | FR-007 |
| 7 | `--dry-run` prints the keys and rules it would add (one per line, `+ <key>: <value>`) and the existing keys it keeps that differ (`= kept <key>: <theirs>`), writes nothing, exit 0. A second real run after a first prints `no change` and does not rewrite the file (mtime unchanged) | FR-006, idempotence |
| 8 | NFR-001 test: no profile contains `bypassPermissions`, an `allow` key, or a `permissions.defaultMode` | NFR-001 |
| 9 | `skills/settings-setup/SKILL.md` (≤ 8,192 bytes, Codex cap) gives the flow: detect (dry-run per profile; "already has profile X" if a dry-run adds nothing) → offer profiles with their `for` lines → up to 3 questions (solo or team; secret files in the repo; keep today's kit behavior → Legacy) → skip or no answer = `high-security` → show dry-run → write on approval. `[auto]` mode: dry-run only, recommendation goes under the final report | FR-005, FR-006 |
| 10 | `docs/claude-md/pipeline-stages.md` Stage 1 checklist item 1 lists `Skill({ skill: "settings-setup" })` with its auto-mode line; the AGENTS.md stage index `1=` list names `settings-setup` | FR-005 |
| 11 | `site/index.html` `#skills` roster has a `settings-setup` entry so the roster drift test stays green | roster test |
| 12 | Mutations, each turns a test RED then green on revert: **M1** remove the "never remove" guard (assign the profile list instead of union); **M2** set a scalar even when present; **M3** add `"permissions.allow": ["Bash(*)"]` to a profile; **M4** drop one rule from `legacy` | guarantees asserted |
| 13 | Full suites pass: `python3 -m pytest tests -q`, hook tests, `bash tests/test_readme_current.sh`, `./validate.sh` (if present) | regression |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | tmp dir with a kit-shaped `settings.json` (hooks + 2 deny) | `apply_profile.py high-security` adds 7 deny + 4 ask + 1 scalar; hooks unchanged; 2nd run `no change` | pytest |
| 2 | JSONC file with a comment | exit 2, sha256 unchanged | pytest |
| 3 | User has `disableBypassPermissionsMode` absent but `ask` containing one of the 4 rules | that rule not duplicated | pytest |
| 4 | A real `claude -p` session in a scratch project runs Stage 1 step and the user answers "skip" | Supervisor shows the dry-run, asks to write, writes High security on "yes" | Supervisor `/verify` |

### Verification Command

```bash
python3 -m pytest tests/test_settings_setup.py -q && python3 -m pytest tests -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T200.md`.

---

## UI / Design Acceptance Criteria

N/A — no UI beyond one roster entry that reuses the existing roster markup. All three UI Evidence rows ☐ N/A (justification: copy-only roster line, covered by the roster drift test).

---

## Approach

**Pattern reference**: `skills/wake/scripts/memory_sections.py` (skill-local script, stdlib only); `lib/merge-settings.py:136` (add-only union, `write_atomic`).

**Vital slice**: `profiles.json` (high-security + legacy) + `apply_profile.py` with dry-run + tests for AC 5–8 + SKILL.md.
**Cut list**:
- More than 3 setup questions; any question that maps to a sandbox key.
- A "remove profile" / downgrade command.
- Writing user or local settings files.

Writing: SKILL.md text the user reads follows AGENTS.md Writing Principles (ASD-STE100).

---

## Edge Case Checklist

See `docs/brainstorming/BRAINSTORMING_LOG_settings-profiles.md` → Edge Case Checklist. Plus:
- [ ] Write is atomic (temp file + rename), like `merge-settings.py write_atomic`
- [ ] Existing file keeps its indentation style if cheap; otherwise 2-space indent, trailing newline — document which
- [ ] Unknown profile id → exit 2 with the list of valid ids

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/settings-setup/SKILL.md` | new |
| `skills/settings-setup/profiles.json` | new |
| `skills/settings-setup/scripts/apply_profile.py` | new |
| `tests/test_settings_setup.py` | new |
| `docs/claude-md/pipeline-stages.md` | Stage 1 item 1 |
| `AGENTS.md` | stage index `1=` only |
| `site/index.html` | `#skills` roster entry only |
| `.claude/skills` | nothing — it is a relative symlink onto `skills/`; check the new skill resolves through it |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `lib/merge-settings.py` | D2 |
| `.claude/settings.json` (this repo) | the kit's own file; Legacy reads it |
| `site/index.html` `#settings-tool` | T201 |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Red first: write `tests/test_settings_setup.py` for AC 1–8, see it fail. Build `profiles.json`, then `apply_profile.py`. Run M1–M4 by hand and paste each RED and green. Then the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T200.md` (Hard-Stop Gate 5)
- [ ] `security-review` run (Risk Medium)
- [ ] `Skill({ skill: "verify" })` run (user only)
- [ ] Supervisor notified: task ready for Stage 4 review
