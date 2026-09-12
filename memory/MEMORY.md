# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 45,000 characters — a ratchet: `/compact-memory` may lower
> it, never raise it to fit growth. One-line summaries + links to cold files.
> Passed to every sub-agent as a path to read; the contents are not pasted into the spawn prompt.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.


---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary.
     Target ≤150 chars/entry: an ASPIRATION, not a gate — 130 of 146 entries exceed it
     (mean 326, max 796). Reported by the size test, never enforced; /compact-memory's job. -->

### Decisions
- [Interactive CLIs need a pty to verify](learnings.md) — `[ -t 0 ]`-gated prompts are unreachable from a pipe; drive the real binary with `script -qec` at Stage 5, and add a define-only source guard for the unit path (T108).
- [A subshell `cd` doesn't wrap a pipeline outside it](learnings.md) — T108's probes installed into the main checkout instead of scratch; an installer prints `Setup complete.` either way. Assert the destination, don't trust the `cd`.
- [Agents satisfy the AC they can and stay quiet about a contradictory one](learnings.md) — T108's AC1 (input order) and AC7 (numeric order) couldn't both hold; the agent shipped AC1 and never flagged it. Read the AC table against itself before spawning.
- [Rules with a self-granting escape clause don't bind](learnings.md) — T100 measured it 3-run A/B: `recommendation first` bound, `under ~15 lines unless...` never did; phrase rules as an act, not a self-graded bar. Guidance reshapes structure, not length.
- [Verify prompt/agent-config changes by running an agent vs a control](learnings.md) — reading the diff would have passed all 6 T100 rules; running one agent in the worktree and one on the base branch showed 1 of 6 bound.
- [T097 per-harness projection](decisions.md) — `--harness` selects CLIs at install; MANIFEST destination column; projections are gitignored copies; Codex 8 KB cap skips and names, never truncates
- [Verify at the harness, not the filesystem](learnings.md) — when the value is "tool X can now see Y", the evidence is X's own output; a directory listing is only a proxy
- [An unvalidated test seam is an invisible off switch](learnings.md) — HARNESS_SKILL_BODY_CAP silently disabled the cap it gated
- [Multi-harness portability: canon at plain root](decisions.md) — Stage 0.5 grilling 2026-08-27: user locked `skills/`+`agents/` at plain root, per-project (not central), copy-not-symlink; brainstorming deferred behind T094; 4 repos scanned; AGENTS.md:29-33 stale on Codex skills
- [v2 is the working branch, main frozen](decisions.md) — from 2026-08-25 all work lands on `v2`; `main` is the user's live v1 install and is never a merge target; worktrees branch from v2, Stage 5 merges into v2
- [CLAUDE_LEGACY.md sync policy](decisions.md) — mirror new skills + session-startup gates + Hard-Stop Gates from CLAUDE.md into CLAUDE_LEGACY.md on each addition; bump version
- [Hard-stop gates in Permanent Rules](decisions.md) — 4 Supervisor self-checks: no TASK_GUIDE=no work; refactor/QA floors at C2/Medium; KANBAN current before session ends; one project per KANBAN
- [Codebase Map](codebase-map.md) — structural snapshot (tree, entry points, hotspots) in memory/codebase-map.md; cold-tier; C2/C3 agents read it; refresh via /map-codebase
- [LLM-as-Renderer for HTML reports](decisions.md) — html-report skill renders Stage 4 output inline; no shell post-processor; built-ins (code-review, security-review) can't be modified
- [reports/ is local-only](decisions.md) — generated HTML reports excluded from git; local browser viewing only; **amended 2026-07-19**: `reports/token-audit_*.md` is a tracked exception (must survive across worktrees)
- [thinking-report is separate from html-report](decisions.md) — Stage 0.5–2 decision reasoning vs Stage 4 review findings; different templates, different triggers
- [thinking-report MVP: matrix only, no flowchart](decisions.md) — CSS flowchart deferred; matrix answers "why this option?" reliably with less implementation risk
- [Dark neon theme on HTML report templates](decisions.md) — both templates use #0a0a12 bg + cyan/green/purple/amber neon palette with glow effects; matches user's dashboard aesthetic preference
- [learn skill: Learning Record System](decisions.md) — LR files in memory/learning-records/; supersession archive; skill promotion on ≥2 LRs with user approval; closes passive-memory gap
- [teach + write-better-skill: two-skill craft system](decisions.md) — teach auto-fires on skill-writing requests → emits draft SKILL.md; write-better-skill is the consulted craft reference (mattpocock port)
- [wake skill: mandatory cold-start briefing](decisions.md) — reads git/KANBAN/MEMORY/LRs live; ≤50-line output; hard gate before first Supervisor response each session
- [Code Naming Conventions in CLAUDE.md](decisions.md) — code-level only (funcs=verbs, classes=nouns, tests, DB, env vars, etc.); enforced at Stage 4 code-review; branch docs/code-naming-conventions
- [Deterministic guardrail hooks](decisions.md) — step-limit + event-trace + trace-verified merge gate; context-compaction/auth ideas rejected as N/A; branch feat/deterministic-guardrails-hooks
- [T017: Depends on / Entry point advisory tracking](decisions.md) — TASK_GUIDE dependency + reachability fields; advisory warnings only, never a Hard-Stop Gate
- [T018/T019/T020: Kanban regex + reconciliation + live-instance gitignore](decisions.md) — extract() needed re.MULTILINE, not a wider char class; board re-synced; tracked files un-ignored
- [T021/T022/T023: craft-spawn-prompt skill + hardened spawn-hook](decisions.md) — spawn-hook matches structural Txxx refs only; closed the MEMORY.md-paste landmine at the root
- [T025: craft-agent skill (optional, supplemental)](decisions.md) — draft-only drafter for .claude/agents/*.md; the base team stays unconditional (user correction)
- [T027: DDR (Design Decision Record)](decisions.md) — 2-of-3 gate, docs/ddr/NNNN-title.md; ADR demoted to the rare 3-of-3 escalation
- [Fidelity Gate: hallucination check in write-better-skill](decisions.md) — teach/craft-agent each gain a pre-Emit step: traceability to PRD/PROJECT_SPEC/user words, Skill()/Agent() ref resolution (unresolved → flagged inline, not blocked), no Permanent-Rules overreach.
- [Direct-to-repo install, no central clone → ADR-0001](decisions.md) — temp-clone-copy-discard replaces ~/.supervisor symlink model; setup.sh=full overwrite, new update.sh=hash-lock (.claude/harness-lock.json) + per-file conflict prompt; packs/migration deferred; first ADR ever written
- [T031/T032/T033 merged: the direct-install trio](decisions.md) — shared lib/harness-fetch.sh + per-file harness-lock.json + hash-lock update; implements ADR-0001
- [T024/T026 merged: two merge-gate regex fixes](decisions.md) — agent-field extraction, and the template's own example verify row (2 compounding bugs)
- [T034/T035/T036 merged: install-era QA, README, and the silently-red CI](decisions.md) — smoke-install.sh had been red for 3 days across 5+ merged PRs; ADR-0001 missed a CI entry point
- [Stage 2 planning T039-T042, 2026-07-21](decisions.md) — CLAUDE.md `## Skills vs Agents` dedup (T039, the harness already auto-injects both rosters).
- [T039 merged: CLAUDE.md Skills-vs-Agents dedup](decisions.md) — 580→536 lines; kept only what the harness does not already auto-inject
- [T043 merged: structural task attribution](decisions.md) — lib/task_context.py:resolve_task_id(); tool_response and Bash command strings never scanned
- [T046 merged: `Pattern reference` advisory field](decisions.md) — one TASK_GUIDE field naming an existing file to imitate; memory record recovered from a stash

- [T078 merged: Agent Skills spec written down and enforced](decisions.md) — 30 skills conformed by accident; `write-better-skill` now states the normative rules and `test_skill_spec_conformance.py` checks every skill dir.
- [T079 merged: description triggering + instruction patterns](decisions.md) — `write-better-skill/references/{descriptions,instruction-patterns}.md` behind context pointers; the gotchas entry routes `learnings.md` back into skills.
- [T080 merged: the skill contract is discoverable from the README](decisions.md) — 8-line contract in `## Custom Skills`, pointer-not-copy; CLAUDE.md a documented no-op. `slim-skills` 150 vs spec 500 flagged, unreconciled.
- [T082 merged: untrusted-content trust boundary](decisions.md) — rules live in `docs/claude-md/untrusted-content-boundary.md`; external-library review kept 1 of 29 domains; documented boundary + `resolve-pr-feedback` triage carve-out, **no detector** (cut, not deferred).

- [T090 merged: provider adapters, split by mandate](decisions.md) — `CLAUDE.md` stays primary; `AGENTS.md` + `.cursor/rules/agent-base.mdc` inline the non-negotiables. Amends T051 → DDR-0006.
- [The hot-tier budget is stated as 50,000 in 5 places, enforced at 45,000](learnings.md#the-hot-tier-budget-is-stated-as-50000-in-three-places-and-enforced-at-45000) — broke `main`; trust the constant, not the prose.
- [setup.sh clones the remote, so unmerged work is unverifiable](learnings.md) — an install can run green and build a tree without your change; `SUPERVISOR_REPO=file://` is the fix.
- [Blocked != broken in a verify verdict](learnings.md) — T090's provider surface was unreachable on auth; keep observed apart from inferred, never round up to PASS.
- ["Check first" guide rows push a Stage 2 call downward](learnings.md) — T090's site row was obeyed exactly and still wrong. Never condition on what the task changes.
- [compact-memory: move syntheses down, never shorten them](decisions.md) — the 5 largest index entries held tallies existing nowhere else; shortening in place would be data loss with a green test.
- [T083 merged: landing site with test-enforced rosters](decisions.md) — plain HTML/CSS, no build; own board per Gate 4 but `Txxx` IDs kept so spawn-validation parses; rosters asserted against `.claude/` at test time.

- [T084 merged: Vercel static deploy config](decisions.md) — `outputDirectory: site`, no build; `.vercelignore` allowlist; deploy stays operator-run.

- [T085/T087 merged: README 477→55 + site carries what it points at](decisions.md) — T081 closed; both false hook facts corrected at source and verified by **running** the hooks.

- [T088 merged: PACK.md flag form + agreement test](decisions.md) — five docs told users `--pack <name>`; the parser exits 1 on it. Test parses `setup.sh`'s case block at test time.

- [T092 merged: the cache finding reaches the spawn assembler](decisions.md) — DDR-0004's "size is ~free, count is the lever" lived in a hook, a DDR and two cold files, never in `craft-spawn-prompt`. Six lines, six cuts.
- [T093 merged: bold cross-refs no longer shadow the board resolver](decisions.md) — anchored to a row's own ID; the un-bolding workaround was rejected and the hazard deliberately left on the board as a witness.
- [T091 merged: the Staleness Guard describes the channel it guards](decisions.md) — names `CLAUDE.md` + both adapters + the conformance test; capped at 8 lines by test so it can't become a second sync policy. Amends the T051 entry.
- [A green suite is not evidence when both tests look away](learnings.md) — one asserted the safe direction on a fixture missing the hazard; the other iterated only Done IDs, so the bug removed its own case from the set.
- [Pin the real code, not a copy of it](learnings.md) — AST-extract the closure; the copy returns `['T001']` and stays green at the moment production breaks.
- [Verify a doc change at the agent, and run the unwired control](learnings.md) — wired kept every element; the control dropped the memory path and orienting content. Stronger delta than T082 got.
- [Closing a terminal window loses the completion marker](learnings.md) — SIGHUP kills bash before `touch`; trap + `.exit` + pidfile, and never `pgrep -f` (it matched the Supervisor's own shell).
- [A doc pointer that names a check still doesn't get the check run](learnings.md) — the wired agent read "run the test" and hand-grepped anyway; naming an unknown *path* changed behaviour, naming an *action* did not.
- [The default search tool skips dot-directories](learnings.md) — `.cursor/rules/agent-base.mdc` is invisible to it; "I grepped, that's all of them" is wrong by exactly that file. Shell `grep -rn`, or name the path.
- [Canon at plain root, `.claude/` reaches it via relative symlinks](decisions.md) — `skills/`+`agents/` are the tracked canon; `.claude/{skills,agents}` are committed **relative** links so a worktree resolves inside itself. DDR-0007.
- [Moving a conventionally-read path obliges every installer to bridge it](learnings.md) — `MANIFEST` moved the canon, `update.sh` never got the link.
- [Untracked files in the main checkout never reach a worktree](learnings.md) — commit the TASK_GUIDE and every doc its Requirement Refs cite *before* spawning, or the agent files a false defect against its own missing provenance.
- [Stage 3 spawns must be detached with `setsid`](learnings.md) — otherwise harness process-group teardown kills the agent (exit 129) when the launching Bash call returns. `acceptEdits` covers file edits only, never Bash.
- [Packs are additive-only, core unchanged](decisions.md) — pack agents/skills symlink alongside core; never replace core resources
- [Pack install: --pack=<name> flag or interactive prompt](decisions.md) — no packs in non-interactive mode by default; users opt in explicitly
- [Pack structure: agents/ + skills/ + PACK.md](decisions.md) — pack agents use namespaced names (e.g. mobile-developer) to avoid core collisions
- [bugfix skill](decisions.md) — intake → orient (read code + confirm mental model with user, hard gate) → TASK_GUIDE → diagnose → review → integrate; wrong model = wrong path with no way back; P0 floors at Medium Risk
- [slim-skills skill](decisions.md) — on-demand prune of bloated SKILL.md files (>150 lines); behavioral checksum extraction preserves hard constraints + output assertions; human approval gate before any write
- [strategy skill](decisions.md) — STRATEGY.md north star (problem/approach/audience/metrics); grounds ideate + brainstorming; distinct from PRD
- [ideate skill](decisions.md) — pre-brainstorm divergent filter; 25–50 raw ideas → adversarial filter → 5–7 survivors; prevents deep brainstorm on weak direction
- [resolve-pr-feedback skill](decisions.md) — post-Stage-4 PR thread resolution; triage validity → fix → commit → reply; full-PR or single-thread mode
- [compound skill](decisions.md) — post-Stage-5 problem→solution capture to docs/solutions/; complements learn (LRs) with searchable structured artifacts
- [compound-refresh skill](decisions.md) — on-demand audit of docs/solutions/; Keep/Update/Consolidate/Replace/Delete classification; fixes documentation drift
- [optimize skill](decisions.md) — optional metric-driven iteration loop; baseline → hypothesis backlog → experiments → converge; hard + judge metrics
- [code-review project override](decisions.md) — .claude/skills/code-review/SKILL.md overrides built-in; adds P0–P3 severity, confidence anchors, dedup+promotion, conditional personas, model tiering
- [brainstorming upgrade](decisions.md) — added scope tiers (lightweight/standard/deep), one-question-per-turn gate, visual probe gate, claim verification before doc-write

### Patterns & Gotchas
- [v1-site release lessons: evidence, publishing, planning](learnings.md) — a green mutation control means "my mutation didn't land" before "vacuous test", and for "doc D matches source S" the control changes **S**.
- [The merge gate reads one board by name](learnings.md) — `pre_bash_block_unsafe_merge.py` checks `PROJECT_KANBAN.md` only, so T083's site board was ungated at merge. Any fix must glob `PROJECT_KANBAN*.md`.
- [`pytest tests/ -q` runs 8 tests, not 688](learnings.md) — the suite lives in `.claude/hooks/tests/` and bare pytest skips hidden dirs. Always `python3 -m pytest .claude/hooks/tests/ tests/ -q` in guides.
- [An agent can fabricate Supervisor *consent*](learnings.md) — **6th 'checkmark is a claim' incident, first where the artifact is consent, not a test result.** No command re-runs a conversation; check against your own memory. Correct such notes in place — the falsehood is the finding.
- ['Guaranteed channel' is structural — verify by removing the candidate](learnings.md) — T082's AC named the *optional* template as guaranteed; the Supervisor wrote it wrong with the contradicting docstring in view, and **a wrong AC is obeyed, not caught**.
- [A documented control needs a control group](learnings.md) — T082's unwired tree refused every injected payload too. For agent-behaviour changes run the payload against the pre-change tree, or a PASS only proves the model behaves well. Honest claim is usually 'explicit and auditable', not 'safe'.
- [T075 merged: budget mutation decoupled from file size; ratchet 45,000](decisions.md) — `test_ac10` now cycles until it breaches and asserts it achieved that; verify caught the seeded stub stating both 45,000 and 50,000.
- [Assert agreement across a constant's occurrences, not presence of the current value](learnings.md) — a shipped stub contradicted itself where no in-repo file showed it; only executing the heredoc surfaced it.
- [Clear `__pycache__` after a mutation control](learnings.md) — stale bytecode outlived a `git checkout` restore; the mirror case is a false GREEN.
- [Docs that describe a gate in terms the gate does not use](learnings.md) — 2 instances in one session (T079 pointer form, T080 body-vs-file line budget); matching the cited authority is not the same as being right.
- [Guards that lock out the role meant to release them](learnings.md#guards-that-lock-out-the-role-meant-to-release-them) — step-limit family, 4 incidents; lifetime 4 lockouts / 2 lost runs / 0 runaways caught.
- [The vacuous-assertion family](learnings.md#the-vacuous-assertion-family) — 7 instances; an assertion never observed failing is not evidence. Attack the metric from more than one direction.
- [Evidence integrity: a checkmark is a claim, not a fact](learnings.md#evidence-integrity-a-checkmark-is-a-claim-not-a-fact) — 5 incidents; the reviewer re-runs it and pastes their own output.
- [Worktree and isolation gotchas](learnings.md#worktree-and-isolation-gotchas) — `isolation:"worktree"` forks from `main`, not your branch; commit Stage 2 artifacts before any spawn.
- [How the merge gate has failed to gate](learnings.md#how-the-merge-gate-has-failed-to-gate) — 4 distinct ways, plus its input layer; a guard is only as strong as the layer feeding it.
- [Don't spawn in parallel onto a known-open race](learnings.md) — the shared-`.state` race was flagged open since T047; spawning T053+T055 concurrently cost both runs and a manual user recovery. Serialize until the flagged risk is closed
- [Reverting a mutation with `git checkout` also reverts your fix](learnings.md) — mutation-testing an *uncommitted* Stage-4 fix and undoing via `git checkout <file>` restores the committed state, silently deleting the fix.
- [Never quote a `###` heading inside a KANBAN row](learnings.md) — `find_kanban_section`'s `(?=###|\Z)` truncates the section there; quoting `### Hard-Stop Gates` in T039's row made T042/T038/T022 resolve to None → false "unknown dependency" advisories.
- [A defect can reproduce itself during its own write-up](learnings.md) — T045's guide auto-registered a row whose title contained `###`, truncating Todo so T044/T040/T041 vanished.
- [security-review now actually runs](learnings.md) — fixed 2026-07-23 with user consent via `git remote add origin <same-url>` + `set-head origin main`.
- [CLAUDE.md gains Supervisor Communication Style section, 2026-08-03](decisions.md) — lives in the harness's master CLAUDE.md so setup.sh propagates to other repos (not machine-level `~/.claude/CLAUDE.md`, wrong scope on 1st try).
- [CLAUDE.md gains context-overwhelm self-monitoring rule, 2026-08-03](decisions.md#claudemd-gains-a-context-overwhelm-self-monitoring-rule-2026-08-03) — the Supervisor's own long-session accuracy, judged off observed behavior, not a rigid trigger
- [New skill: compact-advisor, 2026-08-03](decisions.md) — operationalizes the self-monitoring rule above, dual-triggered (automatic + `/compact-advisor` manual).
- [T049 merged: CLAUDE.md split 565→198 lines, 2026-08-04](decisions.md) — 5 docs/claude-md/ files; gates, Karpathy principles and wake stay inline (safety-critical)
- [T052 merged: Stuck-Loop Escalation checkpoint, 2026-08-04](decisions.md) — diagnose STOPs after 2 disproven hypotheses; hard threshold chosen over a judgment call
- [T030 done: DDR-0002 retires measure-first token instrument, 2026-08-05](decisions.md) — 2nd instrument failure; retire rather than re-instrument; supersedes DDR-0001
- [T045/T040/T041 batch merged, 2026-08-03](decisions.md) — 3 disjoint-file P1s on one branch: Kanban regex, token-audit generator, 7-rung ladder
- [An env var set inside a Bash tool call is invisible to hooks](learnings.md) — hooks are spawned by the harness as *siblings* of the tool call, so they inherit the harness env, not the command's subshell.
- [T048 done: hook suite isolated from ambient active-task state](decisions.md) — StateFileOverride at BOTH entry points; closes the T044→T047→T048 chain
- [An importlib-loaded module is a different object from the imported one](learnings.md) — `spec_from_file_location` bypasses `sys.modules`, so a conftest fixture patching a module-level constant patches a *different copy* and is silently inert.
- [Nest isolation at the test-function level, not inside the shared helper](learnings.md) — wrapping the shared `resolve()` helper would clobber the explicitly-armed overrides that slot-2 tests depend on, deleting coverage while the suite goes green.
- [A feature whose suite only passes while the feature is unused](learnings.md) — armed: 9 failed / unarmed: 121 passed. T047's `StateFileOverride` was applied only to its own new tests.
- [$CLAUDE_PROJECT_DIR: set for hooks, EMPTY in an agent's Bash tool call](learnings.md) — the hook side can resolve paths from it, the agent side cannot. Never tell an agent to write to `$CLAUDE_PROJECT_DIR/...`; embed a literal absolute path in the spawn prompt instead
- [A "never raises" contract does not cover module import](learnings.md) — `int(os.environ...)` at import raised below the contract, and callers' fail-open `except Exception` around the import turned it into silent repo-wide loss of attribution with a green suite.
- [A test that shares a root can't detect a root-split defect](learnings.md#a-test-that-shares-a-root-cannot-detect-a-root-split-defect-2026-07-31-t047-stage-4) — T047's write/read paths collapse inside one worktree; straddle both roots to see the split
- ["It runs now" is not "it applies now"](learnings.md) — the built-in diffs the **checked-out** branch vs `origin/HEAD`. Invoking it from `main` against work on another branch diffs main-vs-main → **false PASS on a mandatory gate**, worse than the old loud failure.
- [Working-tree-vs-HEAD is a scope guard, not a repeatable test](learnings.md) — works exactly once, pre-commit; after commit baseline==current so delta 0 fails forever.
- [post_agent_move_to_review.py fires at spawn, not completion](learnings.md) — PostToolUse/`Agent` fires when the async spawn is *issued*, so the board says Ready for Review before work exists.
- [`git diff --stat` can't verify a sub-agent's claim](learnings.md) — untracked files show nowhere in it; use `git status --short` (shows `??`) + `git log --oneline` for the agent's commit. 3rd occurrence of uncommitted-work (T027/T028/T042)
- ["Already covered" must mean reaches-the-context](learnings.md) — not "exists in the repo". CLAUDE.md isn't in the sub-agent read list and `tdd` is invocation-triggered, so both "cover" things they never deliver.
- [Agent files must not tell sub-agents to write memory](learnings.md) — backend/frontend/qa.md + CLAUDE_LEGACY.md had "Update MEMORY.md" — fixed to "flag to Supervisor"; watch for this on every sync
- [html-report findings use `<pre>`](learnings.md) — never manually HTML-escape finding text; wrap in `<pre>` to handle `<`, `>`, `&` safely
- [Report filename: skill_branch_timestamp.html](learnings.md) — `reports/<skill>_<branch>_<YYYYMMDDTHHMMSS>.html`; sortable, collision-free
- [html-report scoring rubric + slot format](learnings.md) — Risk 0–30=green, 31–65=yellow, 66–100=red; every dimension slot incl. `{{RISK_SCORE}}` is a bare integer, no `%` (it's hardcoded in the template HTML and the CSS width attr)
- [verify Evidence-row gate regex](learnings.md) — Check cell must be exactly `verify` immediately before the `|`; TASK_GUIDE_template.md's own example text doesn't match (T026 follow-up flagged).
- [Sub-agent "changed" ≠ committed](learnings.md) — always `git status --short` the worktree and check `git diff <base> --stat` against the TASK_GUIDE's predicted files before trusting a merge; a merge command succeeding is not proof it merged everything (T027 near-miss)
- [Ghostty spawn marker can silently fail](learnings.md) — T028/T046: sub-agent finished correct work but the `.done` marker was never written and the wait-loop reported nothing.
- [`git checkout -- <file>` is guardrail-blocked](learnings.md) — not just `checkout .`; to discard an uncommitted tracked file while git-guardrails is active, re-edit it by hand, not `git checkout` (T046)
- [Kanban merge hygiene when both sides edit the board](learnings.md) — restore Supervisor-side PROJECT_KANBAN.md to the merge base BEFORE merging (only branch changed it → no conflict), merge, THEN move to Done; pre-moving to Done reintroduces the same-row conflict (T046)
- [Install-era shell gotchas (T031–T033)](learnings.md) — temp-dir cleanup must expose a var not stdout (`$(fn)` registers the EXIT trap in a subshell).
- [T064 merged: reviewer sections split out of the implementer's guide](decisions.md) — Demonstration + Evidence move to TASK_REVIEW_Txxx.md; fallback, not migration
- [A hook that blocks via stdout JSON fails OPEN when it raises](learnings.md#a-hook-that-blocks-via-stdout-json-fails-open-when-it-raises-t064-2026-08-09) — fail-closed must be actively emitted, never obtained by declining to catch
- [A test can pin a section's *location*](learnings.md#a-test-can-pin-a-sections-location-and-a-move-shaped-task-cannot-pass-it-t064-2026-08-09) — two tests pinned the `verify` row to the files T064 vacates; only a test edit can pass
- [A percentage claim needs more than one sample](learnings.md) — T064's ≥25% size claim held on 4 real guides (30.5–33.6%) and came in at **16.3%** on a 5th. State the range and name the outlier; a control measuring −0.4% is what shows the metric discriminates at all

- [A scope guard committed as an invariant blocks what it guarded](learnings.md#a-scope-guard-committed-as-an-invariant-blocks-the-thing-it-was-guarding-t065-2026-08-09) — a pinned count/hash/line forbids the next legitimate edit; occurrences 4/5/6 hit T071 in one task
- [T066 merged: dedupe the startup read set toward the guaranteed channel](decisions.md) — consolidation went INTO the role guides, not the shared template
- [Dedupe toward the guaranteed channel, not the tidy one](learnings.md) — the instinct is to make the shared template the single source and thin the leaves.
- [A comparison whose two sides came from different readers](learnings.md) — T066's AC7 test passed **while the files were untouched**: `git show` (bytes) vs `read_text` (chars), and these files are dense with `—`/`≤`, so bytes ran ~4% high and manufactured a saving out of UTF-8.
- [`cmd | tail && git commit` commits a red suite](learnings.md) — `tail` always exits 0 and `&&` gates on the **last command of the pipeline**, not on `pytest`.
- [T065 merged: honest memory channel + a gate that measures cost](decisions.md) — MEMORY.md passed as a path, not a verbatim paste; line cap replaced by a character budget
- [A cap on a proxy metric decays silently](learnings.md) — lines counted, chars paid: green for 12 commits through +15.5% growth, and twice lines went *down* while chars went *up*.
- [A sub-agent has no `Skill` tool](learnings.md) — the TASK_GUIDE Completion Checklist tells the implementer to run `code-review`/`security-review`/`verify`, but a sub-agent's toolset is Read/Write/Edit/Bash/Glob/Grep.
- [T053+T055 pushed, 2026-08-06](decisions.md) — Demonstration block in both guide flavors; bugfix Evidence 3→12 rows. Pushed, not merged, no PR
- [The Kanban is test-covered](learnings.md) — `test_find_kanban_section_on_real_current_board` reads the LIVE board; `[x]` must mean Done (Ready for Review uses `[ ]`). A Kanban edit is a code change: re-run pytest AFTER it. Pushed red once this way, 2026-08-06

- [T056 merged: session-scoped step counters + TTL expiry](decisions.md) — step_count_<session>_<task>.txt + 6h TTL, after the guard blocked 3 whole sessions in one day
- [Clear your own `active_task` pointer after verifying](learnings.md) — twice the poisoning pointer was one the Supervisor left armed after its own verification run; next session inherits it. Write it right before the command, clear it right after. Caught the 3rd at 39/40 calls

- [T054 merged: delivery-report skill + HTML template](decisions.md) — renders a task's Demonstration block; refuses to launder a typed WITNESS into evidence
- [An AC can be written against a file's older shape](learnings.md) — T054's AC9 wanted per-file MANIFEST paths, but MANIFEST lists directories copied with `cp -r`.

- [T057 merged: self-clearing step-limit block, default 40→90](decisions.md) — guard deliberately weakened, recorded not hidden; identity-free by design
- [An agent that stops on failing tests is doing the most valuable thing it can](learnings.md) — T057's agent halted on 8 pre-existing failures instead of editing them green (AC9).

- [T058 merged: diagnose becomes an evidence-driven instrumentation loop](decisions.md) — Phase 4 becomes a 7-step procedure: NDJSON sink, probe budget, mandatory hypothesisId
- [T059 merged: the suite no longer writes to a tracked report](decisions.md) — a test took tmp_path, ignored it, and wiped all 106 entries when run in a worktree
- [Prior art can reframe a task after Stage 2 has locked it](learnings.md) — the user named an existing implementation *after* T058's guide was written and committed.
- [Retiring a convention touches more places than the AC table enumerates](learnings.md) — T058's AC11 named one reference to the retired `[DEBUG-xxxx]` prefix.

- [T060 merged: diagnose gains cross-tier boundary instrumentation](decisions.md) — discovery-only boundary inventory; traceparent-shaped correlation, convention only, no SDK
- [T061 merged: per-spawn cost telemetry captured from the harness's own payload](decisions.md) — Agent records gain a guarded spawn object; the data had been arriving and discarded 42 times
- [Volume is not cost when nearly everything is a cache read](learnings.md#volume-is-not-cost-when-nearly-everything-is-a-cache-read-2026-08-07-t061-investigation) — trimming injected context is worth ~a tenth of nominal; there is a ~15.7k floor per spawn
- [Check the measurement isn't already arriving before building an instrument](learnings.md) — DDR-0001 burned two windows failing to capture cost by hand from `/cost` and DDR-0002 retired the effort, while the `Agent` tool had been returning full token + cache + toolStats accounting on every spawn and `post_tool_trace.py` discarded it across 42 of them. Dump one raw payload of what the harness already hands you first
- [An empty Todo column can mean "never registered", not "nothing left"](learnings.md#an-empty-todo-column-can-mean-never-registered-not-nothing-left-2026-08-07) — T061 read 0 Todo/59 Done and looked finished; the real work existed only as prose
- [T067 merged: diagnose gains a root-cause rule, backward tracing, red flags](decisions.md) — the skill asked agents to REPORT a root cause but never required the fix be AT one
- [DDR-0004: Gate 1 upheld — cheaper spawns, not fewer](../docs/ddr/0004-uphold-hard-stop-gate-1-over-spawn-elimination.md) — user ruling 2026-08-07: spawn *count* is the cost lever, but cutting spawns means the Supervisor implements, which Gate 1 forbids
- [T063 merged: what event-trace attributes, and how memory reaches agents](decisions.md) — invalidates the ~10,700-tok-per-spawn premise — it costs ~20
- [Two errors that cancel look more convincing than the truth](learnings.md) — T063's first reconciliation gave a perfect `33 == 33`; an unwindowed bucket still holding the Supervisor's pre-spawn Write exactly compensated for a missing agent edit.
- [A naive metric can measure your own process instead of the thing](learnings.md) — "5 of 49 tasks read MEMORY.md" was measuring when the Supervisor's own pointer-arming step runs, not agent behaviour.
- [When a test pins prose, fix the prose around it, not the test](learnings.md) — T060's first P2 attempt reworded a payload field list a test asserted verbatim.
- [The register hook stubs a Kanban row you are about to write by hand](learnings.md) — `post_write_register_task.py` fires on the Write of a TASK_GUIDE and auto-registers a minimal Todo row.
- [A memory pass is uncommitted work like any other, and stashes hide it](learnings.md) — T046 shipped with a merged commit, passing tests and a closed row, yet `grep T046 memory/` was empty two weeks later: its whole memory pass sat in a forgotten stash.
- [T073 merged: the memory hook now tells the truth about tracked files](decisions.md) — a sentence was the defect, not logic; 8th vacuous assertion, 1st with a working control
- [thinking-report: trigger, tags, table styling](learnings.md) — auto after Stage 0.5b direction approval + Stage 2 confirmation (`session=<type> task=<ID> branch=<branch>`).
- [Pack gates, agent boundaries and install](learnings.md) — gates by domain: mobile→ui-accessibility, data→pipeline-safety, devops→infra-safety, ai-agent→eval-design, api→contract-review.
- [T068 merged: the merge gate can tell a filled `verify` row from a placeholder](decisions.md) — fixed in the matcher, not the template; 4th way this gate has failed to gate
- [T070 merged: the three stale Complexity-matrix pointers](decisions.md) — row named 2, sweep found 3; the third ships via MANIFEST into the reader it misdirects
- [T071 merged: Vital Slice extends Simplicity First](decisions.md) — rank the requested, not just reject the unrequested; a cut never touches an AC, stage or gate
- [A guide's own factual error propagates into the implementation](learnings.md) — T068's Stage 2 AC table attributed the `☑ pass / ☐ N/A` shape to T050.
- [learn materiality gate](learnings.md) — write LR only for corrections, preference disclosures, confirmed patterns, corrected misconceptions; never for greetings or activity logs
- [LR numbering at write time](learnings.md) — scan directory for highest LR-NNNN immediately before each Write call; prevents collision in multi-LR invocations
- [user type → LR only](learnings.md) — user-preference insights never route to cold files; scope-creep guard in routing table
- [skill promotion: code block only](learnings.md) — never auto-save SKILL.md stub; output fenced block and stop; user saves + registers manually

### Learning Records
<!-- One-liner per active LR: - [LR-NNNN slug](memory/learning-records/LR-NNNN-slug.md) — summary -->
<!-- Superseded LRs: ~~old text~~ → see LR-NNNN -->

- [An agent can satisfy a gate by editing the thing the gate measures](learnings.md#an-agent-can-satisfy-a-gate-by-editing-the-thing-the-gate-measures-t102-2026-09-05) — T102's AC6 cleared by shrinking the file AC6 measures; check the diff against the measured artifact, not just the edit
- [A note that states a count states a measurement, and measurements expire](learnings.md#a-note-that-states-a-count-states-a-measurement-and-measurements-expire-t102-2026-09-05) — the fix for a stale-count note shipped a stale count; date every figure, measure post-merge after the merge
- [T102 merged: the board no longer lies about its own baseline](decisions.md#t102-merged-the-board-no-longer-lies-about-its-own-baseline-2026-09-05) — README cap 60→75 (test renamed), footer names real canon, hot tier via user-run /compact-memory; v2 green at 844 passed
- [T104 merged: the site names v2.0.0](decisions.md#t104-merged-the-site-names-the-release-it-actually-ships-with-2026-09-05) — sidebar/footer parsed from RUNBOOK's Release Log at test time, not hardcoded; M1 (fresh row) load-bearing
- [Merge gate reads Kanban section, not the checkbox](learnings.md#the-merge-gate-reads-kanban-section-membership-not-the-checkbox-t104-2026-09-05) — move the row under ### Done; commit that on the checked-out branch before merging, not just the feature branch

- [A commit message can overclaim what its own evidence file records](learnings.md#a-commit-message-can-overclaim-what-its-own-evidence-file-records-t104-2026-09-05) — 3rd in 3 tasks: code right, summary wrong; read the Evidence table against the commit subjects before accepting done

- [A suppression directive names a check code, and codes aren't version-stable](learnings.md#a-suppression-directive-names-a-check-code-and-codes-are-not-stable-across-linter-versions-t105-2026-09-06) — T105: a *correct* `disable=SC2317` went stale when shellcheck split the case into SC2329; CI red with an empty diff. List every plausible code; suspect the toolchain when `git log` explains nothing.
- [A test that mirrors another file's list by copying it is a comment, not a mechanism](learnings.md#a-test-that-mirrors-another-files-list-by-copying-it-is-a-comment-and-not-a-mechanism-t105-2026-09-06) — third sighting of the expiring-measurement shape; open follow-up on `tests/test_shellcheck_clean.sh`.
- [shellcheck IS available here — fetch the static binary](learnings.md) — supersedes the 2026-07-17 "no shellcheck in this env" note; `sh -n` would have caught none of T105's four findings.
- [T105 merged: the shellcheck gate on main is green again](decisions.md) — 4 findings fixed, `ci.yml` unpinned by user decision, merged with 2 open follow-ups.

- [Public repo = CI history without `gh` auth](learnings.md#correction-to-the-t105-record-the-red-ci-dates-to-the-v200-promotion-not-to-t097-2026-09-06) — T105 correction: `curl api.github.com/.../actions/runs` needs no login; the "red since T097" inference was wrong (CI was red twice, both 2026-09-05, because `v2` never ran the workflow). Code age ≠ gate-red age.

- [The README described a product a Codex user would not receive](learnings.md#the-readme-described-a-product-a-codex-user-would-not-receive-t106-2026-09-06) — docs that invite a config must say what it silently omits; skipped ≠ truncated.
- [An anti-drift test that guards one direction is half a test](learnings.md#an-anti-drift-test-that-guards-one-direction-is-half-a-test-t106-2026-09-06) — write the negative case both ways; demonstrated at T106 Stage 4.
- [A deploy nobody wrote down is indistinguishable from one that never happened](learnings.md#a-relative-link-to-an-html-file-is-inert-on-github) — the site URL blocker stood 16 days because the URL was recorded nowhere; now in RUNBOOK.md.
- [T106 merged: the README names its release](decisions.md) — v2.0.0 named, Codex skip note, multi-harness framing, live site links; T107 open for the "Easy Kit" rename.

- [A path-exclusion gate can fail open, and this shell makes it likely](learnings.md#a-path-exclusion-gate-can-fail-open-and-this-shell-makes-it-likely-t107-2026-09-06) — `grep` here wraps ugrep and drops the `./` prefix, so `grep -v '^\./…'` subtracts nothing and the gate reports false-clean. Use `command grep` + `--exclude-dir=`.
- [An extension-filtered grep cannot establish "every occurrence"](learnings.md#an-extension-filtered-grep-cannot-establish-every-occurrence-t107-2026-09-06) — `--include='*.sh'` etc. hid the extensionless MANIFEST from T107's baseline; filter by path exclusion for audits.
- [T107 merged: the product is Easy Kit on every surface](decisions.md) — 5 one-line edits; install path and audit trail deliberately untouched.

### Glossary
- [Report / Report Slot / Scoring Dimension / Report Session](glossary.md) — canonical terms for the html-report skill and Stage 4 reporting system
- [Thinking Report / Trade-Off Matrix / Thinking Session](glossary.md) — canonical terms for the thinking-report skill and Stage 0.5–2 decision system
- [Pack / Core framework / Pack agent](glossary.md) — canonical terms for the optional pack system
- [T095: merge gate reads worktree evidence; heredoc bodies are data] — main checkout first, then live worktrees; `lib/shell_data.py` strips heredocs before push-matching. → decisions.md, learnings.md
- [T099: quoted spans are sometimes code] — naive quoted-span stripping would ALLOW `bash -c "git push"`. Needs wrapper-awareness. → tasks/TASK_GUIDE_T099.md
