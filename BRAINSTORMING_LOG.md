# BRAINSTORMING_LOG.md
**Generated**: 2026-08-17
**Task / Context**: Hook wiring drift — a `settings.json` entry pointing at a hook file that does not exist bricks every Bash call, and the resulting error gives no direction to fix
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (moderate ambiguity; resolved by one user-supplied error report + empirical probing of all 8 hooks)

> Supersedes the 2026-08-05 Demonstration-block log (T053/T054 subject, shipped and closed).
> Recoverable from git history.

---

## The Problem Space

### What actually happened

A machine running this framework reported:

> *Broken hook: `.claude/settings.json` wires `pre_bash_block_dangerous_git.py` into every Bash call's
> PreToolUse, but that file doesn't exist on disk — so right now all Bash commands fail, not just git
> ones.*

The user's complaint was not that the hook blocked something. It was that **the error carried no
direction to fix and no explanation of what the hook was for**.

### Verified facts (claim-verification gate)

Every assertion below was checked against the actual files, not recalled:

| Claim | Verification | Result |
|---|---|---|
| The 8 framework hooks crash on a foreign machine | Ran all 8 as subprocesses under 3 conditions: home repo, bare project (hooks copied, no `tasks/`/KANBAN/`memory/`), `CLAUDE_PROJECT_DIR` unset — 24 runs | **False.** 0 non-zero exits, 0 tracebacks. All fail open silently by design |
| `pre_bash_block_dangerous_git.py` is shipped by this repo | `find`, `grep` over `MANIFEST*`, `setup.sh`, `update.sh`, `scripts/` | **Never shipped.** Matches no file in repo history |
| The guardrails skill creates that filename | Read `.claude/skills/git-guardrails-claude-code/SKILL.md` | **No.** It installs `block-dangerous-git.sh` — shell, not Python, different stem |
| The bundled guardrail script exists | `ls .claude/skills/git-guardrails-claude-code/scripts/` | Yes — `block-dangerous-git.sh`, 507 bytes, executable |
| This machine has the same drift | Cross-checked every wired path in 3 settings files against disk | **No.** 8/8 framework + 22/22 machine-level all resolve |
| All 8 hooks are wired | Parsed `.claude/settings.json` | Yes, all 8, correct events |

### The real root cause

The failing filename was **invented by pattern-matching**. The framework's real hooks are named
`pre_bash_block_unsafe_merge.py`, `pre_agent_step_limit.py`, … so `pre_bash_block_dangerous_git.py`
*looks* exactly like a framework hook. Something wrote the `settings.json` entry using that
convention without ever creating the file.

The guardrails skill's own step order makes this easy to hit:

- **Step 2** — place the script (`block-dangerous-git.sh`)
- **Step 3** — register it in `settings.json`
- **Step 5** — "Verify": `echo '{...}' | .claude/hooks/block-dangerous-git.sh`

Run step 3 without step 2, or let the name drift between them, and Bash is dead. **Step 5 verifies the
script in isolation and never verifies that `settings.json` points at a path that resolves.** The one
check that would have caught this is the one check the skill does not do.

### Why it was unfixable-feeling, and the constraint that dominates every option

**The broken tool is the tool you need to fix it.** When a `PreToolUse/Bash` hook is unresolvable,
every Bash call fails — including `ls`, including `cat settings.json`, including any repair script we
might ship. A `scripts/doctor.sh` is worthless in the exact moment it is needed.

Any viable remedy must therefore be reachable **without Bash** — i.e. via `Read`/`Edit` on a known
path, or via a *different* hook event that still fires, or printed pre-emptively before the breakage.

### Non-negotiable constraints

1. No remedy may depend on Bash working.
2. Framework hooks must keep failing **open** (silent exit 0) — that property is load-bearing and
   deliberately chosen; do not trade it away.
3. `pre_bash_block_unsafe_merge.py` must keep failing **closed** (it emits `decision: block` and exits
   0 by design — see its guarded import). These two rules are not in conflict; they are per-hook.
4. Whatever we add must survive `setup.sh` / `update.sh` deployment into other projects.

---

## Questions for the User

1. Should the remedy also cover **third-party** hooks (`~/.claude/settings.json` — `orca`,
   `supervisor-viz`, `node-terminal`)? They are outside this framework but they are wired into the
   same session, and one of them is emitting `[null] 📁 null` on every prompt in this very session.
2. Is the priority **prevention** (never break again) or **recovery** (a clear path out when it does)?
   Option D below is the only one that seriously buys both.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | The Doctor Script | `scripts/hook-doctor.sh` cross-checks wiring vs. disk | Low | ~80 lines | Low | |
| B | The Self-Describing Hook | Every hook gains `--explain`; errors cite a `docs/hooks.md` registry | Medium | ~250 lines | Medium | |
| C | The Source Fix | Reorder the guardrails skill; add wiring check to `setup.sh`/`update.sh` | Low | ~40 lines | Low | |
| D | **Preflight + Docs** | SessionStart validator that names the bad entry and the Read/Edit fix, plus a README troubleshooting section | Low-Med | ~120 lines | Low | ✅ Yes |

### Option A — The Doctor Script
**Approach**: Ship `scripts/hook-doctor.sh` that parses all settings files, resolves every wired hook
path, and reports `OK` / `MISSING` per entry (exactly the probe I ran above).

**Pros**: Trivially simple; reuses a script already proven in this session; useful for third-party hooks too.

**Cons**: Purely reactive. Requires the user to know it exists.

**Why it might fail**: **Fatal — it is a Bash script, and the failure mode it diagnoses is "Bash does not
work."** It can never run at the moment of breakage. It would only ever be useful preventatively, which
is Option C's job done worse.

### Option B — The Self-Describing Hook
**Approach**: Every framework hook gains an `--explain` flag printing its purpose, trigger, and remedy.
Add `docs/hooks.md` as a registry. Every block message ends with `See docs/hooks.md#<anchor>`.

**Pros**: Genuinely improves the eight real hooks' messages; the registry is a good artifact regardless;
helps the *legitimate block* case (missing TASK_GUIDE, step limit) as well as the broken case.

**Cons**: Large surface — touches all 8 hooks plus docs. Solves the wrong problem for the reported
incident: a hook that does not exist cannot print its own `--explain` text.

**Why it might fail**: Effort concentrated where the pain was not. The reported failure had **no hook**
to describe itself. Also risks the T041/T066 trap — writing explanatory prose into a channel that never
reaches the reader who needs it.

### Option C — The Source Fix
**Approach**: Reorder `git-guardrails-claude-code` so registration cannot precede file placement; make
its step 5 verify the *wired path* resolves, not just the script; add a wiring-vs-disk check to
`setup.sh` and `update.sh`.

**Pros**: Kills the root cause at its origin. Smallest diff. Directly targets the mechanism proven above.

**Cons**: Does nothing for a machine already broken — including, possibly, the user's other machine
right now. Only covers drift introduced *by the skill*; a hand-edited or model-invented entry
(which is what actually happened here) bypasses it entirely.

**Why it might fail**: The incident was **not** caused by the skill running incorrectly — the filename
never existed in any version. So the fix addresses a plausible path that was not the actual path taken.

### Option D — Preflight Validation + Troubleshooting Docs ✅
**Approach**: Three small, complementary pieces:

1. **A `SessionStart` hook** (`session_validate_hook_wiring.py`) that parses every settings file,
   resolves each wired hook command's script path, and — if any is missing — prints a precise,
   actionable block **at session start, before any Bash call is attempted**:
   ```
   ⚠️  BROKEN HOOK WIRING — Bash will fail on every call until fixed.
     .claude/settings.json → PreToolUse/Bash
       wired:   .claude/hooks/pre_bash_block_dangerous_git.py
       on disk: MISSING
     This is not a framework hook — no such file has ever shipped.
     FIX (no Bash required — use Read/Edit):
       Edit .claude/settings.json and delete that hooks entry,
       OR run /git-guardrails-claude-code to install the real
       guardrail (block-dangerous-git.sh) and wire it correctly.
   ```
   `SessionStart` still fires when `PreToolUse/Bash` is broken, so the message arrives **through a
   channel the failure cannot block**, and names a `Read`/`Edit` remedy that works without Bash.

2. **A README troubleshooting section** — the two stale hook rows corrected (see below), plus
   "when a hook misbehaves": how to tell a framework hook from a machine-level one, what each
   `[hook:...]` tag means, and the wiring-drift symptom and cure.

3. **Fold in Option C's cheap half** — the guardrails skill verifies the wired path resolves.

**Pros**: Recovery arrives before the breakage bites, through an unblockable channel. Prevention and
recovery both covered. Small, additive, no existing hook modified — so the fail-open/fail-closed
properties are untouched.

**Why it might fail**: A ninth hook is more surface, and a validator that itself crashes would be
ironic and bad — so it must be aggressively `try/except`-wrapped and fail open (never block a session
start). Risk that `SessionStart` output is easy to scroll past; mitigated by printing only on failure,
never on success. If the harness ever changes settings-file precedence, the parser drifts.

---

## 50% Rule Check

Option D's piece 1 is the only real code. The 50%-less version: **skip the parser entirely** and have
the validator simply `os.path.exists()` each `.py`/`.sh` token found by one regex over the raw settings
text — no JSON walk, no event/matcher modelling. It loses the ability to say *which event* is broken,
but keeps the part that matters: the missing path and the fix. That halves the code and removes the
JSON-schema-drift risk. **Adopt this** — the event name is a nice-to-have, and `grep` of the settings
file gives it to the user in one step if they want it.

Piece 2 (docs) has no code. Piece 3 is ~5 lines in a SKILL.md.

---

## Recommended Path

**Option D — Preflight Validation + Troubleshooting Docs**, with the 50%-rule simplification applied to
the validator (regex scan, not JSON walk).

It is the only option that satisfies the dominant constraint: **the remedy must not require the tool
that is broken.** A is fatally Bash-dependent; B invests where the pain was not; C cannot help an
already-broken machine and does not match the actual cause. D delivers the message through
`SessionStart`, names a Bash-free fix, and costs ~60 lines after the 50% cut.

The README work the user originally asked for rides along as piece 2 — and it now has real content:
two provably stale rows plus a genuine troubleshooting story.

---

## Surgical Scope

Files that **should** be touched:
- `.claude/hooks/session_validate_hook_wiring.py` — new; the validator
- `.claude/hooks/tests/test_hook_wiring_validation.py` — new; tests
- `.claude/settings.json` — register the `SessionStart` hook
- `README.md` — correct rows 407/408; add hook-troubleshooting section
- `.claude/skills/git-guardrails-claude-code/SKILL.md` — step 5 verifies the wired path
- `MANIFEST` — ship the new hook (T054 precedent: check whether directory-level `cp -r` already covers it **before** adding a line)

Files that **must not** be touched:
- The 8 existing hooks — their fail-open/fail-closed semantics are load-bearing and separately tested
- `.claude/hooks/lib/*.py` — unrelated to wiring
- `~/.claude/settings.json` — the user's machine-level third-party hooks; read-only to us, never edited
- `memory/MEMORY.md` — at 49,957 of its 50,000 ratchet; any entry needs `/compact-memory` first

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Validator must **never** block session start — wrap everything, exit 0 on any exception
- [ ] Settings file absent / malformed JSON / empty → silent exit 0, no traceback
- [ ] `$CLAUDE_PROJECT_DIR` unset, and `~` in a path → both must expand correctly (verified: hooks tolerate unset today)
- [ ] A wired command that is inline shell, not a script path (e.g. `touch /tmp/x`) → must not be reported missing
- [ ] Multi-hook `command` strings with pipes (`tee … | supervisor-viz …`) → must not false-positive
- [ ] Same script wired to several events → report once, not N times
- [ ] Report **only** on failure; a healthy session prints nothing
- [ ] Message must name a `Read`/`Edit` remedy, never a Bash command
- [ ] Distinguish framework hooks from third-party ones so the user knows whose problem it is
- [ ] Test must straddle the boundary: assert against a settings file with a genuinely missing path, not a mocked `exists()` (T047 root-split lesson)
- [ ] Do not assert the validator's prose exists — assert it against real on-disk state (T073 AC6 lesson)

---

## Next Actions

1. User selects a path (this document does not advance without it).
2. Stage 2: register **T074** on `PROJECT_KANBAN.md` and generate `tasks/TASK_GUIDE_T074.md`.
   Suggested labels: **C1 / Medium Risk / P1** — Medium because it touches `settings.json`, whose
   breakage mode is total Bash loss.
3. Stage 3: spawn `common-infrastructure` (owns hooks + settings + installer).
4. Pre-flight per T064/T071 lessons: grep the suite for pinned paths and **size invariants** before
   editing `README.md`.
5. Separately decide whether the two open T073 findings (merge gate `__file__` blindness; whole-string
   command scan) become their own task — they are unrelated to this one.

---

## User Selection

> **Approved direction**: Option D — Preflight Validation + Troubleshooting Docs, with the 50%-rule
> simplification applied to the validator (regex scan of the settings text, not a JSON walk).
> Approved by user on 2026-08-17.
>
> **Open question 1 resolved by the Supervisor, stated as an assumption**: the validator **does**
> scan machine-level hooks (`~/.claude/settings.json`) — the scan is the same code either way, and
> the user's own machine currently runs a third-party hook emitting `[null] 📁 null` on every prompt.
> It reports them **read-only**, labelled as not-ours, and never edits that file. Reversible: drop
> the second path from the scan list.
>
> **Open question 2**: answered implicitly by the choice — Option D was recommended precisely because
> it buys prevention *and* recovery; no further ruling needed.
