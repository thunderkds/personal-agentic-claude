# BRAINSTORMING_LOG.md — Settings Profiles (site profiles + Supervisor default settings)
**Date**: 2026-10-29 · **Tier**: Standard · **Input**: `PRD_settings-profiles.md` (FR-001..FR-008, decisions D1–D5)

---

## The Problem Space

D1–D5 fix *what* ships: named profiles on the page, a Stage 1 Supervisor step that defaults to High
security (rules only), Legacy = today's kit file, writes to `.claude/settings.json` by add-only merge.
Two things are open: **where the profile values live** (FR-004, one source for page and step) and
**what does the merge** (FR-007).

Verified facts (read 2026-10-29):

- The page keeps its catalog in `<script type="application/json" id="settings-catalog">`
  (`site/index.html:731`); presets are its `presets` array (`:801`). `"$suggest"` expands to the
  key's `suggest` list (`:883`). Node tests in `tests/settings_tool/` run the `settings-tool-core`
  block in `node:vm`.
- The current `safe-baseline` preset = `permissions.deny` + `permissions.ask` suggestions. It lacks
  `permissions.disableBypassPermissionsMode` (`:741`, value `"disable"`), so it is not yet D5.
- `lib/merge-settings.py` already unions the kit's `permissions.deny` add-only (T148, `:136`) and
  never copies `allow`/`ask`. It handles hook entries too.
- **The installer ships `skills/` and `templates/`, not `site/` and not `lib/`** (`MANIFEST:45,53`;
  `setup.sh:359` runs `lib/merge-settings.py` from the temp clone only). So in a user's project the
  Stage 1 step cannot read the page or `lib/`. The source must live in a shipped folder.
- Precedent for a skill-local script: `skills/wake/scripts/memory_sections.py`.

## The Alternatives

### Path A — Shipped profiles file + skill script, page embeds a copy (Recommended)
- `skills/settings-setup/profiles.json`: the one source (ids, labels, one-line "for whom", values).
- `skills/settings-setup/SKILL.md`: Stage 1 step — detect, ask ≤3 questions, show diff, write on approval.
- `skills/settings-setup/scripts/apply_profile.py <profile> [--dry-run]`: add-only merge into
  `.claude/settings.json` — list union for `deny`/`ask`, set a scalar only if absent, never remove;
  unparseable file → exit 2, file byte-identical.
- Page: `presets` gains `high-security` (replaces `safe-baseline`) and `legacy`, each with a
  description line. A pytest drift test asserts page presets == `profiles.json` for shared ids.
- **Pros**: works offline in any installed project; testable; one merge rule in code. **Cons**: two
  copies (page + file) held equal by a test, not by construction.

### Path B — Page is the source; the step fetches it from the live site
- **Pros**: one copy by construction. **Cons**: needs network at Stage 1; fetched page text is
  untrusted content; a site deploy silently changes every project's defaults. Rejected.

### Path C — 50% less code: profiles as prose in SKILL.md, the Supervisor edits by hand
- No script. SKILL.md lists the rules; the Supervisor uses Edit on `.claude/settings.json`.
  A test greps SKILL.md against the page.
- **Pros**: ~half the code. **Cons**: the never-remove / no-duplicate / byte-identical-on-error
  guarantees (FR-007) rest on the model's care, not on a test; no dry-run output for the diff (FR-006).

## Adversarial Review

| Path | Why it might fail |
|------|-------------------|
| A | Drift test only compares ids it knows; a new profile added on one side only slips through → test asserts the **id sets** are equal too. `apply_profile.py` duplicates part of `merge-settings.py` → keep it to permissions only (no hooks), and test both never-remove and idempotence. |
| B | Offline machine = no default; site compromise = every new project's settings. |
| C | One bad Edit drops a user's hook entry; the kit's own hooks break every tool call (T074 learning). |

## Edge Case Checklist (for both TASK_GUIDEs)

- [ ] No `.claude/settings.json` → create it with the profile only (installer adds hooks later or already did).
- [ ] File is JSONC / invalid / `permissions` not an object → exit 2, byte-identical, reason printed.
- [ ] User already has `disableBypassPermissionsMode` or a `defaultMode` → keep theirs, report it.
- [ ] User has an `allow` rule that a new deny covers → keep both (deny wins in Claude Code); report it.
- [ ] Run twice → second run changes nothing (idempotent).
- [ ] Legacy on a kit-installed project → no-op ("already Legacy").
- [ ] `[auto]` mode → `--dry-run` only; recommendation goes in the final report (FR-006).
- [ ] Page: a user who edited keys then picks a profile → existing Replace / Keep mine confirm (T185).
- [ ] Page: no profile emits `bypassPermissions` or an `allow` wildcard (NFR-001).

## Surgical Scope

**Should touch**: `skills/settings-setup/` (new), `site/index.html` (catalog `presets`, profile
description line, the "installs no settings" sentence), `tests/settings_tool/`, a new pytest for
drift + merge, `docs/claude-md/pipeline-stages.md` (Stage 1 checklist line), the AGENTS.md stage index
(`1=` list), `PROJECT_KANBAN.md`, `PROJECT_KANBAN_SITE.md`.
**Must not touch**: `setup.sh` (D2), `lib/merge-settings.py`, `.claude/settings.json` of this repo,
the Check-tab rules (T187).

## Recommended Path

**Path A.** Two tasks:
1. **T200** (harness board) — `settings-setup` skill + `profiles.json` + `apply_profile.py` + Stage 1 wiring. C2 / Risk Medium (writes a security file in user projects).
2. **T201** (site board) — page profiles High security + Legacy with descriptions, copy fix, drift test against `profiles.json`. C1 / Risk Low, UI. Depends on T200.
