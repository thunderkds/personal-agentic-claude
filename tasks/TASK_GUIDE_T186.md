# TASK_GUIDE — T186: Site Settings tool, part 2 — Check mode: paste a `settings.json`, format it, validate it against the catalog and target file, visualize it, load it into Build
**Date**: 2026-10-27
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN_SITE.md` (site scope, Hard-Stop Gate 4) — spec `PROJECT_SPEC_SITE.md` § "Settings tool"

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md` in full — § "Settings tool" holds the five hard rules
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/frontend.md`
6. Read `tasks/TASK_GUIDE_T185.md` — the catalog shape, core/UI script split and Build mode you extend

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27, verbatim: "… by the way support they paste their current settings and we check the settings following, it will looks like the support for the pick/format/visualize the settings".

**Restated intent**:
> A developer pastes their current `settings.json`, picks which file it is, and the tool (a) formats it, (b) lists problems with a plain fix for each, (c) shows the settings as a grouped visual tree, and (d) loads it into Build mode so they can edit and copy a corrected file. Nothing they paste leaves their browser.

**Out of scope**: fixing files on disk; checking hook scripts' contents beyond the command string; `~/.claude.json` (global config) as an input type; managed-settings policy analysis.

**Requirement Refs**: none (site request, user-originated 2026-10-27).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-27)
- [ ] T185 merged (catalog + core block exist)
- [x] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: T185 — `#settings-tool` section, `#settings-catalog` JSON, `settings-tool-core` script block, Build mode
**Entry point**: the "Check" tab inside `<section id="settings-tool">`

---

## Design (layout and behaviour)

```
┌ Settings tool ─ [ Build ] [ Check ] ─────────────────────────────────────────┐
│ This is my: (•) User  ( ) Project  ( ) Local settings file                   │
│ ┌ paste here ───────────────────────────────┐  [Format] [Check] [Edit in Build]│
│ │ { "permissions": { "allow": ["Bash(git *)"│  Runs in your browser only.    │
│ └───────────────────────────────────────────┘  Nothing is sent or saved.     │
├ Findings (2 errors · 3 warnings · 1 tip) ────────────────────────────────────┤
│ ● error  autoMode           Ignored in a project file. Move it to ~/.claude/… │
│ ▲ warn   permissions.allow  "Bash(git *)" pre-approves git push and reset.   │
│ ▲ warn   env.GITHUB_TOKEN   Looks like a secret (value hidden). Remove it.   │
│ ○ tip    permissions.deny   No rule blocks reading .env. [Add in Build]      │
├ Map ─────────────────────────────────────────────────────────────────────────┤
│ Permissions  deny → ask → allow  (first match wins)                          │
│   deny 2 │ ask 0 │ allow 14 ▲                                                │
│ Hooks  PreToolUse ▸ Bash ▸ python3 …/pre_bash_block_unsafe_merge.py          │
│ Model & effort  effortLevel: low                                             │
│ Other keys (kept as-is)  enabledPlugins, extraKnownMarketplaces              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Check rules (exact; each finding = severity · path · one-sentence problem · one-sentence fix)

| ID | Severity | Rule |
|----|----------|------|
| E1 | error | Not valid JSON → show line and column of the parse error |
| E2 | error | Top level is not an object |
| E3 | error | Known key with wrong type, enum value outside `values`, or number outside `min`/`max` |
| E4 | error | Key in catalog `removed` (no effect) |
| E5 | error | Key ignored by the chosen file: in `managedOnly`; user-only key in project/local; `globalConfigOnly` key (belongs in `~/.claude.json`); `permissions.defaultMode` `auto`/`bypassPermissions` outside the user file |
| W1 | warn | Key in `deprecated` → name the replacement |
| W2 | warn | Key not in `knownKeys` → "did you mean …" (edit distance ≤ 2 to a known key), else "unknown key, kept as-is" |
| W3 | warn | Broad allow rule: `Bash`, `Bash(*)`, `Bash(git *)`, `Bash(bash *)`, `Bash(sh *)`, `Bash(python3 *)`, `Bash(python *)`, `Bash(node *)`, `Bash(cat *)` — "pre-approves nearly any command of that kind" |
| W4 | warn | Same rule in `allow` and in `deny` or `ask` → explain precedence (deny → ask → allow, first match wins); duplicate rules inside one list |
| W5 | warn | `env` value looks like a secret (prefixes `sk-`, `ghp_`, `gho_`, `github_pat_`, `xox`, `AKIA`, or ≥ 32 chars of `[A-Za-z0-9+/=_-]`) → value masked everywhere in the UI; fix: use `apiKeyHelper` or the shell |
| W6 | warn | Hook command copies input to a world-readable path (`tee /tmp`, `> /tmp`) |
| W7 | warn | A `lowersSafety` key is set to its unsafe value (`disableAllHooks: true`, `enableAllProjectMcpServers: true`, `defaultMode: "bypassPermissions"`) |
| I1 | tip | No deny rule matches `.env` / `~/.ssh` → offer the T185 suggestions with "Add in Build" |
| I2 | tip | `since` version on a key → "needs Claude Code ≥ X" |

### Visual map
Group keys by catalog category (unknown keys under "Other keys (kept as-is)"). Permissions render as three counted columns in precedence order. Hooks render as event ▸ matcher ▸ command (read-only). Every node carries its finding badge; clicking a finding scrolls to and highlights its node.

### Format and Edit in Build
- **Format**: pretty-print 2-space, keep the user's key order, keep unknown keys. If JSON is invalid, Format does nothing and E1 shows.
- **Edit in Build**: known keys fill Build controls; unknown / non-editable keys (e.g. `hooks`, `enabledPlugins`) go into a passthrough block that Build emits unchanged, so a round trip never drops data. Masked secrets: Build output keeps the original value only if the user ticks "keep secret values" (default off → key emitted with the value removed and a W5 note).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Check tab enabled; paste area, target-file choice, Format / Check / Edit in Build buttons; privacy line "Runs in your browser only. Nothing is sent or saved." | "they paste their current settings" |
| 2 | Pure `check(text, target) -> {findings, tree}` implements every rule E1–E5, W1–W7, I1–I2 exactly as tabled; one node test per rule (positive) plus a clean-file test with zero findings | "we check the settings" |
| 3 | `format(text)` pretty-prints, preserves key order and unknown keys; invalid input returns the E1 finding and no output | "format" |
| 4 | Visual map renders categories, permission columns in precedence order, hooks tree, finding badges; finding → node navigation works | "visualize the settings" |
| 5 | Round trip: `generate(fromSettings(parsed))` deep-equals the parsed input for any input with no secrets (unknown keys and `hooks` preserved) | "pick/format" — edit without data loss |
| 6 | Secret values (W5) are masked in the findings, the map and the formatted view; never written to the DOM unmasked unless "keep secret values" is ticked | Pasted secrets safety |
| 7 | Spec hard rules 1–5 still hold (no network/storage APIs; no submitting form; inline; no package.json; no-script fallback) — the existing T185 grep test covers the new code | `PROJECT_SPEC_SITE.md` § Settings tool |
| 8 | Fixture: the shape of this repo's own `.claude/settings.local.json` problems (broad `Bash(git *)` / `Bash(bash *)` allows) and a `tee /tmp/...` hook command yields W3 and W6 — fixture is synthetic, no real user file copied into the repo | Real-world check |
| 9 | Negative: 1 MB pasted text and deeply nested (depth 200) JSON do not freeze the page (> 2 s) or throw uncaught | Robustness |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `{"permissions":{"allow":["Bash(git *)"]}}`, target Local | Exactly one W3 on `permissions.allow[0]` + I1 | node test |
| 2 | `{"autoMode":{"soft_deny":["x"]}}`, target Project | E5 | node test |
| 3 | `{"env":{"GITHUB_TOKEN":"ghp_abc…"}}` | W5; rendered text contains no `ghp_` | node test + DOM-free render test of the masker |
| 4 | `{"includeCoAuthoredBy":false}` | W1 naming `attribution` | node test |
| 5 | `{ "permisions": {} }` | W2 "did you mean permissions" | node test |
| 6 | `{,}` | E1 with line 1, column 2 | node test |
| 7 | Mutation: delete the W3 rule | Success 1 fails | node test (run once, paste) |
| 8 | 375 / 768 / 1280 px, light + dark, with a 30-finding fixture | No page-wide horizontal scroll; findings readable | screenshots (Gate 6) |

### Verification Command (exact, runnable)

```bash
node --test tests/settings_tool/ && python3 -m pytest tests/test_site_content.py -q
```

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| Check mode with the AC 8 fixture | LLM-vision screenshot, 1280px | Matches the Design wireframe: paste area, findings list, map |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | Diff audit | Severity uses existing tag tokens (`tag-block` / `tag-advise` style) — no new literals |
| Typography matches spec | Visual | Existing body / `code` styles |
| Spacing / layout matches spec | Visual | New CSS scoped under `#settings-tool` |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | Playwright / screenshot | Paste area full width; findings stack; map scrolls inside its own container |
| Tablet (768px) | screenshot | No overflow |
| Desktop (1280px) | screenshot | Findings and map full width under the paste area |

---

## Approach

**Pattern reference**: T185's `settings-tool-core` block and `tests/settings_tool/test_generate.mjs` — add `check`, `format`, `fromSettings`, `maskSecrets` to the same core block, tests beside it (`tests/settings_tool/test_check.mjs`).

Parse with `JSON.parse` inside try/catch; derive line/column from the error position (engines differ — compute from the `position N` in the message, fallback "line unknown"). Render all pasted values with `textContent`, never `innerHTML` (pasted text is untrusted).

**Vital slice**: `check()` with E1, E3, E5, W3, W5 + findings list + Format.
**Cut list**:
- Auto-fix buttons per finding (only "Add in Build" for I1)
- Diff view between pasted and generated
- Checking `~/.claude.json`

---

## Edge Case Checklist

- [ ] Pasted text with BOM or comments (JSONC) → E1 that names comments as the cause
- [ ] Duplicate keys in the JSON text (last one wins in `JSON.parse`) → W4-style warning if detectable cheaply, else documented as a limit
- [ ] `permissions` present but `null`
- [ ] Rule strings with `<script>` in them render as text (XSS — `textContent` only)
- [ ] Secret inside a hook command string (e.g. `TOKEN=ghp_…`) also masked
- [ ] Empty paste → hint, no findings

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | Check mode UI, core functions, scoped CSS |
| `tests/settings_tool/test_check.mjs` | One test per rule, round trip, masking, robustness |
| `tests/settings_tool/fixtures/*.json` | Synthetic fixtures (no real user files) |
| `tasks/TASK_REVIEW_T186.md` | Evidence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/settings.local.json`, `~/.claude/settings.json` | Real user files — never copied into fixtures |
| `.claude/settings.json`, `lib/merge-settings.py` | Kit installs no defaults |
| `PROJECT_KANBAN.md` | Harness board |

---

## Test Plan

TDD per rule in `tests/settings_tool/test_check.mjs`; round-trip property test over the fixtures; masking test asserts no secret substring in rendered strings; robustness test with generated 1 MB / depth-200 input. Screenshots at 375 / 768 / 1280 light + dark. Medium risk → `security-review` focuses on XSS via pasted text and any path that could persist or transmit it.

---

## Completion Checklist

- [ ] T185 merged (dependency)
- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T186.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
