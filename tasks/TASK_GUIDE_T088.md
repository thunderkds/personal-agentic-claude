# TASK_GUIDE — T088: All five `PACK.md` files document a `--pack` form `setup.sh` rejects
**Date**: 2026-08-21
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` — harness scope
2. Read `memory/MEMORY.md` in full
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C1 → apply the C1 row of the Complexity matrix

---

## Requirement (Pillar 1)

Surfaced by the T087 implementer and **empirically reproduced by the Supervisor** — this is a measured
defect, not an inherited claim. Every one of the five `packs/*/PACK.md` files documents:

```sh
sh ~/.supervisor/setup.sh --pack <name>     # space-separated
```

`setup.sh:87` parses only `--pack=*`, and `setup.sh:88` is a catch-all:

```sh
--pack=*) pack_val="${arg#--pack=}"; PACKS="$PACKS $pack_val" ;;
*) log_error "Unknown flag: $arg. Valid flags: --copy, --pack=<name>"; exit 1 ;;
```

Reproduced by replicating the arg loop in isolation (the installer itself was never run):

```
--pack mobile   → Unknown flag: --pack. Valid flags: --copy, --pack=<name>   exit=1
--pack=mobile   → OK packs: mobile                                          exit=0
```

Anyone following a `PACK.md` verbatim gets an immediate hard failure and installs nothing. This has
presumably been true since packs shipped; it survived because the pre-slim `README.md` had the `=`
form right throughout, so the two documents disagreed and only the README was ever read.

**Restated intent**:
> Every command a `PACK.md` tells a user to run is a command `setup.sh` actually accepts, and a test
> fails if that stops being true.

**Out of scope**:
- Changing `setup.sh` to *also* accept the space form. The `=` form is documented in the script's own
  usage line and used correctly everywhere else; widening the parser to match five wrong docs is the
  tail wagging the dog. If you believe otherwise, stop and say so rather than doing it.
- `site/index.html` — T087 already uses the correct `=` form there.
- `README.md` — already correct, and it is now 55 lines with no pack commands in it.
- Any other content in the `PACK.md` files.

**Requirement Refs**: N/A — defect found during T087 review, reproduced above.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-08-21, reproduced the failure directly)
- [x] Domain terms align with `PROJECT_SPEC.md`
- [x] Every AC traces to the Requirement
- [x] Requirement Refs recorded N/A with reason

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `setup.sh --pack=<name>` — the literal flag form the parser accepts.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | All five `packs/*/PACK.md` use `--pack=<name>` (with `=`) in every `setup.sh` invocation | the defect |
| 2 | No other content in those files is changed — this is a one-token fix per file, not a docs rewrite | Surgical Changes |
| 3 | `tests/test_pack_docs_flags.py` asserts that **every** `setup.sh` invocation found in any `packs/*/PACK.md` uses a flag form `setup.sh`'s own `case` statement accepts | the whole task |
| 4 | That test derives the valid flag forms from `setup.sh` **at test time** — it does not hardcode `--pack=`. If someone later adds a `--foo` flag to the script, the test must not need editing to know about it | drift constraint |
| 5 | The test also fails if a `PACK.md` invokes `setup.sh` with a flag that does not exist in the script at all (e.g. a typo'd `--packs=`) | AC3's real purpose |
| 6 | Full suite passes, 0 regressions against the 701 baseline | repo convention |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Each of the 5 `PACK.md` files | its `setup.sh` line uses `--pack=` | automated test |
| 2 | The flag forms parsed out of `setup.sh` | every documented flag is among them | automated test |
| 3 | **Mutation control M1** — revert one `PACK.md` to the space form `--pack mobile` | the test goes **RED** naming that file; revert after observing | Supervisor re-runs |
| 4 | **Mutation control M2** — change one `PACK.md` to a flag that exists nowhere (`--packs=mobile`) | the test goes **RED** naming the unknown flag; revert after observing | Supervisor re-runs |
| 5 | **Mutation control M3** — delete the `--pack=*` case line from `setup.sh` | the test goes **RED**, because the documented flag is no longer accepted by the script; revert after observing | Supervisor re-runs |

> M1–M3 mandatory. **Confirm each mutation changed bytes** (grep the mutated string back, or
> `git diff`) before concluding anything from a green result — a no-op mutation and a vacuous
> assertion both produce a green suite and are otherwise indistinguishable. This has bitten this
> project three times this session.
>
> M3 is the one that proves AC4: if the test hardcodes `--pack=` rather than reading `setup.sh`, M3
> stays green and the test is measuring a constant, not an agreement between two files.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_pack_docs_flags.py -q && python3 -m pytest .claude/hooks/tests/ tests/ -q
```

> Use the two-path form. `python3 -m pytest tests/ -q` collects a handful of tests, not 701 — the
> harness suite lives in the hidden `.claude/hooks/tests/`, which bare pytest skips.

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T088.md`.

---

## UI / Design Acceptance Criteria

**N/A — documentation and test only.** No UI component; all three Gate 6 rows are ☐ N/A for this reason.

---

## Approach

**Pattern reference**: `tests/test_site_content.py` (T083/T087) — the same shape applies here: parse the
source of truth at test time, assert the document agrees with it, never hardcode the expected value.
That file is the house style for this kind of two-file agreement test.

**Vital slice**: the test. The five one-token edits take a minute; without AC3–AC5 this silently
reverts, because nothing in this repo reads `PACK.md` against `setup.sh` today — which is exactly why
it went unnoticed for so long.

**Cut list**: no rewording of the surrounding prose; no unification of the five files' structure; no
check of `update.sh` invocations (none appear in `PACK.md` today — if you find one, report it rather
than expanding scope).

Parse `setup.sh`'s `case "$arg" in` block for the literal patterns it matches (`--copy`, `--pack=*`),
then extract every `setup.sh …` invocation from the `PACK.md` files and check each flag token against
those patterns. Treat `--pack=*` as a glob, not a literal.

---

## Edge Case Checklist

- [ ] The `case` block matches globs (`--pack=*`), not literals — a naive string compare of `--pack=mobile` against `--pack=*` will not match. Use `fnmatch`
- [ ] `packs/*/PACK.md` also contains a bare backtick-quoted `` `setup.sh` `` mention with no flags — that is prose, not an invocation, and must not be flagged
- [ ] Do not match `setup.sh` inside a URL (e.g. a `curl …/setup.sh | sh` line) as a local invocation with flags
- [ ] Five files, five identical edits — check all five actually changed; a `sed` that silently matched four is the obvious failure here
- [ ] `setup.sh` may gain flags later; AC4 exists so the test learns them without being edited

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `packs/mobile/PACK.md` | `--pack mobile` → `--pack=mobile` |
| `packs/data/PACK.md` | `--pack data` → `--pack=data` |
| `packs/devops/PACK.md` | `--pack devops` → `--pack=devops` |
| `packs/ai-agent/PACK.md` | `--pack ai-agent` → `--pack=ai-agent` |
| `packs/api/PACK.md` | `--pack api` → `--pack=api` |
| `tests/test_pack_docs_flags.py` | New — AC3–AC5 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | The script is correct; the docs are wrong. Changing the parser to match wrong docs inverts the fix |
| `site/index.html`, `README.md` | Already use the correct form |
| `PROJECT_KANBAN*.md`, `memory/**` | Supervisor-only |

---

## Test Plan

`tests/test_pack_docs_flags.py`:
1. `_valid_flag_patterns()` — parse `setup.sh`'s `case "$arg" in` block, return the glob patterns.
2. `test_every_pack_doc_flag_is_accepted_by_setup_sh` — for each `packs/*/PACK.md`, extract each `setup.sh` invocation's flag tokens, assert each matches one pattern via `fnmatch`.
3. Sanity assertions so the fixture cannot silently find nothing: assert 5 PACK.md files were scanned and at least one invocation was extracted from each.

Then the full suite, then M1–M3 with byte-change confirmation.

---

## Completion Checklist

- [ ] Test written first and observed RED against the current (wrong) docs — this task starts red, which is unusual and useful: paste that first failure
- [ ] All five files edited; confirm five, not four
- [ ] M1, M2, M3 each observed RED with the failing assertion pasted, **and the mutation confirmed to have changed bytes**
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: **N/A** — Low risk, docs + test only
- [ ] Tests pass — output pasted into `tasks/TASK_REVIEW_T088.md` (Gate 5)
- [ ] UI/Design rows: ☐ N/A ×3 (Gate 6)
- [ ] Report whether any `PACK.md` also documents `update.sh` with flags
- [ ] Supervisor notified: ready for Stage 4 review
