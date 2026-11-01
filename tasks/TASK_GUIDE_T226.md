# TASK_GUIDE — T226: Stage 1 offers the optional companion MCP servers
**Date**: 2026-11-01
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
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-01, verbatim: "from the kit, I don't see the kit ask for the easy-verifier mcp, easy-memory mcp and easy-ui mcp for the options to choose" — then, after the Stage 1 proposal: "let investigate and update to the kit, include the document also, [auto]".

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> At Stage 1 the Supervisor shows the user which companion MCP servers exist, which are already on this machine, what each adds and what it needs. The user can pick any or skip; skip is the default and changes nothing. The kit never installs a server. The docs say all of this.

**Out of scope** (what this task explicitly does NOT do):
- The kit running any install, `docker`, `sudo`, `uv`, `npm` or `claude mcp add`
- A menu or question in `setup.sh`
- Any network call in the skill's script
- Offering easy-context (no kit integration, no site card)
- Fixing the dead GitHub links on the site's `#mcps` cards, or changing any repo's visibility (registered as a follow-up; T194 edits the same section)
- The memory search script from the 2026-11-01 experiment

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):
- None in `PRD.md`: stand-in Requirements (`PROJECT_SPEC.md` `## Readiness`). Direct user request above.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor))
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "Companion" as in Companion score
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above (no refs: direct request)

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `companion-setup`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `skills/companion-setup/companions.json` has one entry each for `easy-verifier`, `easy-ui`, `easy-memory`, `easy-personal`: id, what it adds, required tools, install link, access (`public` or `private`). easy-context has no entry | "options to choose" |
| 2 | `skills/companion-setup/scripts/check_companions.py --installed <ids>` prints, for each public server not installed, a choice line with what it adds, what it needs and which tools are missing; each installed server as already installed, private or public | "options to choose" |
| 3 | A private server not installed is printed as one line saying it needs repo access, and is not a choice | honest offer: three repos answer 404 without a login |
| 4 | The script makes no network call, starts no process, writes no file, and exits 0 when tools are missing or `--installed` is empty | "optional" |
| 5 | `skills/companion-setup/SKILL.md` runs the script, shows its output, defaults to skip, shows only the install link and missing tools on a pick, and states the kit never installs, starts or runs `sudo`. It warns that the easy-verifier server listens on `127.0.0.1:8766` with no authentication. Auto mode: asks nothing, one `Not done:` line | "update to the kit" |
| 6 | Stage 1 item 1 in `docs/claude-md/pipeline-stages.md` names the skill; `CLAUDE_LEGACY.md` Stage 1 and skill list do too; `docs/claude-md/tracks.md` table row 5 names its auto rule | "update to the kit" |
| 7 | `setup.sh` prints one `log_info` line after the Pack catalog line naming the companion offer at Stage 1. No new prompt, and no check | "from the kit, I don't see" |
| 8 | README names the offer and stays within its line cap; the site's `#mcps` section says the Supervisor offers them at Stage 1; the site's skill count is right | "include the document also" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | No server installed; `PATH` without `docker` | easy-ui and easy-verifier are choices marked missing `docker`; easy-memory and easy-personal are non-choice lines; exit 0 | automated test |
| 2 | `--installed easy-memory` | easy-memory shows as already installed, not as needing access | automated test |
| 3 | `--installed unknown-id` | the unknown id is ignored with no crash | automated test |
| 4 | Script source | imports no network module and no `subprocess` | automated test |
| 5 | `companions.json` | every server the site's `#mcps` cards name has an entry, and each `access: public` link is not a `github.com` link of a private repo | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_companion_setup.py tests/test_site_content.py tests/test_readme_slim.py tests/test_docs_match_installer.py -q
python3 skills/companion-setup/scripts/check_companions.py --installed easy-memory,easy-personal
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T226.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T226.md`.

---

## Approach

**Pattern reference**: `skills/settings-setup/SKILL.md` + `skills/settings-setup/profiles.json` — a Stage 1 skill driven by a data file, with a stdlib script and a `### Auto mode` section. `skills/score/SKILL.md` — "You never install, start or upgrade the verifier".

**Vital slice**: the data file, the read-only script and the skill, plus the Stage 1 pointer.
**Cut list**: live access checks at setup (the list is static); `claude mcp list` from the script (it is slow and checks health over the network: the Supervisor passes what it sees as `--installed`); re-prompting on Update (`/companion-setup` works on demand); a CI check for repo visibility.

Link rather than copy install commands, so a server's install change cannot make the kit stale. easy-verifier's link is its public Docker image or site, never its repo.

---

## Edge Case Checklist

- [ ] `README.md` is exactly at its 75-line cap: replace or merge a line, never raise the cap
- [ ] `tests/test_site_content.py` bans the substring `required` in `#mcps` (`HONESTY_PHRASES`) and says the kit does not ship these tools: keep the new sentence honest
- [ ] `tests/test_site_content.py` compares the site's skill count with the `skills/` folders
- [ ] Prose must not imply the kit needs a server; the normal flow runs without them
- [ ] `setup.sh`'s Update path returns before the Pack catalog line: leave it as is
- [ ] The word `sudo` in the skill must only ever say the kit does not run it

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/companion-setup/SKILL.md` | new skill |
| `skills/companion-setup/companions.json` | new data file |
| `skills/companion-setup/scripts/check_companions.py` | new read-only script |
| `tests/test_companion_setup.py` | new tests |
| `docs/claude-md/pipeline-stages.md` | Stage 1 item 1 bullet and auto-mode line |
| `docs/claude-md/tracks.md` | table row 5 |
| `CLAUDE_LEGACY.md` | Stage 1 pointer and skill list |
| `setup.sh` | one `log_info` line |
| `README.md` | one line, within the cap |
| `site/index.html` | `#mcps` sentence, skill count |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/settings-setup/` | its rules limit it to the project settings file |
| `skills/score/` | unchanged behaviour |
| `AGENTS.md` | Stage index edit is the Supervisor's after review |
| `.claude/settings.json` | no hook or permission change |
| `memory/` | Supervisor-only |

---

## Test Plan

New `tests/test_companion_setup.py` covers the Success Criteria with a controlled `PATH`. Then the full suite: `python3 -m pytest tests/ .claude/hooks/tests/ -q`, and `bash scripts/validate.sh`.

---

## Questions Log

- 2026-11-01 DEBATE How should the kit offer the companion servers, and what happens on a pick? → New Stage 1 skill, link only, the kit never installs, plus one `setup.sh` log line (Advocate 1: Stage 1 prompt-only skill `companion-setup`, `setup.sh` unchanged; Advocate 2: skill `companions` with a data file, plus one `log_info` line in `setup.sh`) ⚠ decided for you — please review
- 2026-11-01 DEBATE Which servers may the kit list, and how does it treat one the user cannot install? → List easy-ui and easy-verifier as choices; easy-memory and easy-personal as "needs repo access" unless installed; leave out easy-context (Advocate 1: offer easy-ui, easy-verifier and easy-context, private ones a neutral skipped line, already-installed shown; Advocate 2: offer easy-ui and easy-verifier, leave out easy-context, never attempt an install) ⚠ decided for you — please review

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T226.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
