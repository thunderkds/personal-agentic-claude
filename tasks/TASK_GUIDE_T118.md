# TASK_GUIDE — T118: Fixture repos carry what `update.sh` hard-requires, and CI is green again
**Date**: 2026-09-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1, but multi-file: skim `memory/codebase-map.md` for the `tests/` layout

---

## Requirement (Pillar 1 — Adapt the requirement)

Two CI-wired suites went red the moment T111 merged to `main` at `4f766dd`:

```
tests/test_t098_harness_presence.sh   8 passed, 7 failed   (ci.yml:46)
tests/test_harness_projection.sh     35 passed, 3 failed   (ci.yml:28)
```

Every failure is the same line, from `setup.sh:421` / `update.sh:109`:

```
[error] Could not merge Easy Kit hooks into ./.claude/settings.json:
        the fetched Easy Kit has no lib/merge-settings.py
[error] Update finished, but Easy Kit hooks were NOT merged   (exit 2)
```

T111 made `lib/merge-settings.py` a hard prerequisite of both installers, run from the temp clone.
Both suites build **synthetic fixture repos** (`$WORK/fixture-repo`) holding only a hand-listed set
of files — `agents/`, `skills/`, `.claude/hooks`, `templates`, `MANIFEST`, `CLAUDE.md`,
`CLAUDE_LEGACY.md`, `settings.json`. Neither builder was taught about the new helper, so every
`update.sh` call against a fixture now aborts.

**Restated intent**:
> A fixture repo must be a believable Easy Kit. It has to carry the files the installers hard-require,
> so these suites test what they claim to test instead of failing at a missing prerequisite — and
> `main`'s CI goes green again.

**Out of scope** (explicitly NOT this task):
- Changing `merge_settings`, `settings_merge_refused`, or the hard-fail contract in `setup.sh` /
  `update.sh`. **See the Approach section — this is a settled decision, not an open question.**
- `tests/test_install_update_smoke.sh` — it clones the real repo, it already passes, leave it alone.
- T111's two recorded follow-ups (silent removal of a user entry matching the kit path pattern; a
  shared `merge_settings` helper once T112/T113 land). Different tasks.

**Requirement Refs**: none — this is a defect repair, registered from observed CI breakage on
`main`, not from a `PRD.md` line.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the observed failure (Supervisor, reproduced 2026-09-17 on `4f766dd`)
- [x] Domain terms align with `PROJECT_SPEC.md` (fixture repo, temp clone, kit)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] No Requirement Refs to check

---

## Dependencies & Reachability

**Depends on**: None — T111 is already merged; this repairs it.

**Entry point**: `lib/merge-settings.py` — the literal path both installers test for at
`setup.sh:418` and `update.sh:106`, and the string the fixture builders must satisfy.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `bash tests/test_t098_harness_presence.sh` exits 0, with all 15 checks passing and none skipped | "CI goes green again" |
| 2 | `bash tests/test_harness_projection.sh` exits 0, with all 38 checks passing and none skipped | "CI goes green again" |
| 3 | Each fixture repo contains `lib/merge-settings.py` **copied from the real repo**, not a stub or an empty file, and the copy is committed into the fixture's git history alongside the other fixture files | "a believable Easy Kit" |
| 4 | Anti-drift, both directions: deleting `lib/merge-settings.py` from a fixture makes that suite **fail by name** (proving the copy is load-bearing), and the suites still pass with it present | "test what they claim to test" |
| 5 | `bash tests/test_install_update_smoke.sh`, `tests/test_settings_merge.sh`, `tests/test_setup.sh`, `tests/test_update.sh` and `python3 tests/test_ci_wires_shell_suites.py` still pass unchanged | Out-of-scope guard |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `tests/test_t098_harness_presence.sh` on a clean checkout | exit 0, `15 passed, 0 failed` | automated test |
| 2 | `tests/test_harness_projection.sh` on a clean checkout | exit 0, `38 passed, 0 failed` | automated test |
| 3 | Fixture built, then `lib/merge-settings.py` deleted from it before the installer runs | the suite FAILS and names the missing prerequisite — it must not pass silently | mutation, run by hand, output pasted |
| 4 | `grep -c 'settings_merge_refused' setup.sh update.sh` | unchanged from `4f766dd` — the hard-fail contract was not softened | automated grep |
| 5 | Full suite sweep (AC5 list) | every suite exits 0 | automated test |

### Verification Command (exact, runnable)

```bash
bash tests/test_t098_harness_presence.sh && \
bash tests/test_harness_projection.sh && \
bash tests/test_install_update_smoke.sh && \
bash tests/test_settings_merge.sh && \
bash tests/test_setup.sh && \
bash tests/test_update.sh && \
python3 tests/test_ci_wires_shell_suites.py
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled at Stage 4/5 in `tasks/TASK_REVIEW_T118.md`, copied from `templates/TASK_REVIEW_template.md`.

---

## Approach

**Pattern reference**: `tests/test_settings_merge.sh` — T111's own suite, the one place in this repo
that already builds a fixture kit which satisfies `merge_settings`. Imitate how it provisions the
helper; do not invent a second convention.

**The design question is settled — fixture-side, not product-side.** Both readings were considered:

1. *Teach the fixtures to carry the helper* — **chosen.**
2. *Make the installers degrade when the fetched kit can't merge hooks* — **rejected.** The hard
   fail is deliberate (ADR-0002; `setup.sh:413-414`): every wired hook runs as `python3 …`, so a kit
   that cannot merge hooks produces an install with no working hooks. Softening it re-introduces the
   silently-unhooked install T111 existed to prevent, and would be an unrequested behaviour change
   to a just-merged, just-reviewed contract. A real fetched kit always contains the helper; a fixture
   without it is simulating an impossible kit, so the fixture is what is wrong.

If implementation turns up evidence that (2) is actually correct, **STOP and ask the Supervisor** —
do not switch approach unilaterally.

**Vital slice**: AC1–AC3 — the two fixture builders provisioning the real helper. That is the whole
repair and it is what makes CI green.
**Cut list**:
- A general "fixture completeness" framework that diffs every fixture against the installers'
  full prerequisite set. Two suites and one prerequisite today; AC4's targeted mutation covers the
  recurrence risk at a fraction of the surface.

**Copy the real file; do not write a stub.** A stub would drift from `lib/merge-settings.py` and the
suites would go on passing against merge logic that no longer exists — the same class of defect as
this one, one level down.

---

## Edge Case Checklist

- [ ] The fixture's `MANIFEST` must NOT start shipping `lib/` into target projects — the helper runs
      from the temp clone and is deliberately never installed (`setup.sh:412-413`). Provisioning it
      into the fixture repo is not the same as adding it to `MANIFEST`. Check the installed file
      list in both suites is unchanged.
- [ ] `tests/test_harness_projection.sh` sources `lib/harness-fetch.sh` from `$REPO_ROOT` at :461
      and :473 — a different mechanism from the fixture clone. Don't conflate the two.
- [ ] The fixture is committed with `git -C "$FIXTURE" add -A` before the installer clones it; a
      file written after that commit is invisible to a clone. Provision before the commit.
- [ ] `test_t098_harness_presence.sh` builds its fixture once and reuses it across ~10 cases —
      fix the builder, not each call site.
- [ ] Both suites run under `sh`-compatible shellcheck rules; match the surrounding style exactly.
- [ ] Do not `chmod +x` the copied helper if the original isn't — mode changes have bitten this
      repo before (T111's own P2 was a mode-losing atomic write).

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `tests/test_t098_harness_presence.sh` | Fixture builder (~:41-63) also provisions `lib/merge-settings.py` from the real repo, before the fixture's `git add -A`/commit |
| `tests/test_harness_projection.sh` | Same, in its fixture builder (~:44-91) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh` | The hard-fail contract is the settled decision above — out of scope |
| `lib/merge-settings.py` | The thing under test; changing it invalidates the fixtures |
| `MANIFEST` | The helper is deliberately not installed into target projects |
| `.github/workflows/ci.yml` | Both suites are already wired (:28, :46); the T109 drift guard will fail if wiring changes |
| `tests/test_install_update_smoke.sh` | Clones the real repo, already green |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-owned — report status, don't edit the board |

---

## Test Plan

No new test file. The repair is proven by two existing suites going from red to green, plus the
AC4 mutation run by hand in both directions:

1. Baseline: run both suites, paste the current 7-fail / 3-fail output as BEFORE.
2. Fix both fixture builders.
3. Re-run: both exit 0, every case passing — paste as AFTER.
4. Mutation: delete `lib/merge-settings.py` from a built fixture, confirm the suite fails and names
   the prerequisite, restore, confirm green. Paste both.
5. Sweep the AC5 suites to prove nothing adjacent regressed.

> Hard-Stop Gate 5 note: this task writes no new test file, and that is correct here — the
> acceptance evidence is two previously-red CI-wired suites going green plus a mutation proving the
> fix is load-bearing. Record exactly that in the Evidence table's "New test(s) cover acceptance
> criteria" row, with pasted output for all three runs.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Low risk) — mark N/A
- [ ] shellcheck passes on both changed suites
- [ ] BEFORE / AFTER / mutation output pasted into `tasks/TASK_REVIEW_T118.md`'s Evidence table
- [ ] `Skill({ skill: "verify" })` run (user-invoked)
- [ ] All three UI/Design Evidence rows marked ☐ N/A — pure-infrastructure task, no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
