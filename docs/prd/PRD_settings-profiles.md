# PRD — Settings Profiles (site profiles + Supervisor default settings)
**Last updated**: 2026-10-29
**Status**: In Review (Stage 0.5a done — grilling decisions D1–D4 below; brainstorming next)
**Owner**: quannhm1604@gmail.com

> **Scope of this document**: *What* to build and *why*. Architecture and task state go to the
> spec/board files at Stage 2.
> Source: Stage 0.5 `grill-with-docs mode=requirement`, 2026-10-29. Each FR cites the grilling decision it came from.

---

## Overview

The site's settings tool (`site/index.html#settings-tool`, T185 Build + T187 Check) lets a user pick
from 63 keys and 4 presets (`safe-baseline`, `solo-engineer`, `team-project`, `empty`), and checks a
pasted `settings.json`. The installer (`setup.sh` → `install_settings`) only copies or merges the
kit's hook entries plus 2 harness-anchor deny rules. The page states: "The kit installs no settings
of its own."

User request (2026-10-29, verbatim): "we should provide more options for users to pick, by the way,
if the users do not choose from the settings setup, the agents supervisor should generate the default
settings with the high security and map with good approach for starting or the legacy following the
options pick, or if needed, ask for question from settings up the app to generate the suitable
settings following."

## Grilling decisions

| ID | Question | Decision (user) |
|----|----------|-----------------|
| D1 | What does "more options" mean on the page? | **More profiles** — named starting profiles that fill many keys at once. Not a page wizard, not more catalog keys. |
| D2 | Where is the default made when the user picked nothing? | **Supervisor at Stage 1** — a Stage 1 step (small skill). It asks 2–3 setup questions, or applies High security when the user skips. It shows the diff and writes only after approval. `setup.sh` is unchanged. |
| D3 | What is the "Legacy" profile? | **Today's kit settings** — the kit's hooks plus its 2 harness-anchor deny rules, nothing more. |
| D4 | Which file does the Supervisor write? | **Project settings** `.claude/settings.json` — merged with the kit's hooks and the user's own entries, never overwritten. |
| D5 | How strict is High security? | **Rules only** — deny reads of secrets (`.env`, `.env.*`, `*.pem`, `*.key`, `~/.ssh`, `~/.aws`, `~/.config/gh`), ask before `git push --force`/`-f`, `git reset --hard`, `rm -rf`, and `permissions.disableBypassPermissionsMode: "disable"`. No sandbox, no network allowlist. |

## Personas

| ID | Name | Pain point |
|----|------|-----------|
| P1 | New kit user on the site | 4 presets do not say which one is "secure" or "what the kit does by default" |
| P2 | User starting a project with the Supervisor | Gets no security rules unless they build a file by hand |
| P3 | Existing kit user | Wants the old behavior; must not be forced into stricter rules |

## Functional requirements

- **FR-001** (D1) The page offers named profiles, at least: High security, Legacy, plus the existing Solo engineer, Team project and Empty. Each profile has a one-line description of who it is for.
- **FR-002** (D5) High security fills exactly the D5 rule set. It sets no sandbox key and no `permissions.defaultMode`.
- **FR-003** (D3) Legacy fills exactly the kit's shipped `permissions.deny` (the 2 harness-anchor rules from `.claude/settings.json`). The page notes that the hooks are added by the installer, not by this file.
- **FR-004** (D1, D2) One source of profile values. The page profiles and the Stage 1 step use the same values; a test fails if they drift.
- **FR-005** (D2) A Stage 1 Supervisor step: if the project's `.claude/settings.json` has no profile rules yet, the Supervisor offers the profiles. It may ask up to 3 setup questions (e.g. solo or team; secrets in the repo; wants the old behavior). If the user skips or does not answer, the default is High security.
- **FR-006** (D2) The Stage 1 step shows the exact change (keys added) before it writes, and writes only after the user approves. In `[auto]` mode it writes nothing and records the recommendation in the final report.
- **FR-007** (D4) The write merges into `.claude/settings.json`: keeps every existing key, hook and rule; adds only missing rules (list union, no duplicates); never removes an entry. A file the merge cannot parse is left byte-identical and the step reports why.
- **FR-008** The page copy "The kit installs no settings of its own" is updated to say what is true after this change.

## Non-functional requirements

- **NFR-001** Security: no profile lowers safety (no `bypassPermissions`, no `allow` wildcard). A test asserts this.
- **NFR-002** The page stays one file, no external requests, no build step (T083/T089 rules).
- **NFR-003** The Stage 1 step needs only `python3` (already a hard prerequisite of the kit hooks).

## Out of scope

- A question wizard on the page (D1).
- New catalog keys (D1).
- Sandbox or network allowlist in any profile (D5).
- `setup.sh` changes (D2).
- Writing `~/.claude/settings.json` or `.claude/settings.local.json` (D4).

## Open questions

None open. Brainstorming decides the shared-source mechanism (FR-004) and the merge helper (FR-007).
