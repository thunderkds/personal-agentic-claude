# TASK_GUIDE — T185: Site Settings tool, part 1 — Build mode: pick settings from a catalog, choose the target file, generate and copy `settings.json`
**Date**: 2026-10-27
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN_SITE.md` (site scope, Hard-Stop Gate 4) — spec `PROJECT_SPEC_SITE.md` § "Settings tool"

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC_SITE.md` in full — § "Settings tool" holds the five hard rules (site scope — NOT `PROJECT_SPEC.md`)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/frontend.md`
6. Read `tasks/TASK_GUIDE_T184.md` "Evaluation summary" — the reasons for each setting come from there

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-27, verbatim: "design a section that user can click on the settings and we can generate the settings for users, by the way support they paste their current settings and we check the settings following, it will looks like the support for the pick/format/visualize the settings". Earlier: "the config should go by the taste, we no need to update as initial" (kit installs no defaults — T184 closed).

**Restated intent**:
> A developer opens the kit site, clicks the Claude Code settings they want, sets each value, chooses which file it is for (`~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`), and copies a valid, formatted JSON file. The tool explains each setting in one line and never offers a key that the chosen file ignores. This task is the **pick + generate** half; paste / check / visualize is T186.

**Out of scope** (T186 owns these): paste input, validation findings, the visual tree, "load pasted into Build".
Also out: installing anything into a project; the full ~250-key reference (catalog is curated, see below); managed-settings keys as pickable items.

**Requirement Refs**: none (site request, user-originated 2026-10-27).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-27)
- [x] Domain terms: "target file" = user / project / local settings file; "catalog" = the inline settings list; "preset" = a named starting selection
- [x] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `<section id="settings-tool">`

---

## Design (layout and behaviour)

```
┌ Settings tool ───────────────────────────────────────────────────────────────┐
│ [ Build ]  [ Check ]  ← mode tabs (Check is T186; until then shown disabled)│
│ Target file: (•) User ~/.claude/settings.json  ( ) Project  ( ) Local       │
│ Start from:  [Safe baseline] [Solo engineer] [Team project] [Empty]         │
├──────────────── catalog (left) ───────────────┬──── output (right) ────────┤
│ ▸ Safety & permissions (4 on)                 │ ~/.claude/settings.json    │
│   [x] permissions.deny        list  ⓘ         │ {                          │
│       + Read(./.env)  + Read(~/.ssh/**) [+add]│   "permissions": {         │
│   [x] permissions.ask         list            │     "deny": [ ... ],       │
│   [ ] permissions.defaultMode  ▾ acceptEdits  │     "ask":  [ ... ]        │
│ ▸ Worktrees                                   │   },                       │
│ ▸ Model & effort                              │   "autoUpdatesChannel":    │
│ ▸ Memory & context                            │     "stable"               │
│ ▸ Git & attribution                           │ }                          │
│ ▸ Hooks & MCP                                 │ [Copy]  4 keys · valid     │
│ ▸ Interface · Updates & privacy               │                            │
│ (filter: [ type to search keys ])             │                            │
└───────────────────────────────────────────────┴────────────────────────────┘
```

- Each catalog row: checkbox · key (code) · value control (toggle / select / number / list editor / text) · one-line "why" · scope badge (where it is honoured) · "lowers safety" badge when applicable · link icon to the key's anchor on the official settings reference.
- Switching **target file** hides keys that file ignores (e.g. `autoMode` and `permissions.defaultMode: "auto"|"bypassPermissions"` are user-only; `network.strictAllowlist` user/managed only) and drops them from the output with a one-line note "N keys removed: not read from <file>".
- Output updates live, 2-space indent, catalog order; shows key count and "valid" (the output is always produced from typed controls, so it must always be valid JSON).
- Presets only set checkboxes and values; the user can change everything afterwards. Presets never select a "lowers safety" key.
- At 375px: catalog and output stack (output below, sticky Copy button). Reuse existing page tokens, table/`details` styles; no new color literals.
- No script → static paragraph + link to https://code.claude.com/docs/en/settings-reference (spec rule 5).

## Catalog (seed content — curated from the settings reference, CLI 2.1.311)

Entry shape (inline `<script type="application/json" id="settings-catalog">`):
`{ "version": "2.1.311", "categories": [...], "settings": [ { "key", "category", "type": "bool|enum|string|number|stringList|object", "values"?, "min"?, "max"?, "default"?, "scopes": ["user","project","local"], "why", "lowersSafety"?: true, "since"?: "2.1.257", "suggest"?: [list items offered as one-click adds] } ], "knownKeys": [...all top-level/dotted keys from the reference, name only...], "deprecated": { "includeCoAuthoredBy": "attribution", "disableArtifact": "enableArtifact" }, "removed": ["taskOutputMaxChars","keybindingFlavor"], "globalConfigOnly": ["autoConnectIde","autoInstallIdeExtension","copyFullResponse","copyOnSelect","defaultToAgentsView","diffTool","externalEditorContext","leftArrowOpensAgents","prStatusFooterEnabled","claudeInChromeDefaultEnabled"], "managedOnly": [...] }`

Seed settings (each needs a `why`; facts from the reference — do not invent ranges):
- **Safety & permissions**: `permissions.deny` (suggest `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`, `Read(~/.ssh/**)`, `Read(~/.aws/**)`, `Read(~/.config/gh/**)`); `permissions.ask` (suggest `Bash(git push --force *)`, `Bash(git push -f *)`, `Bash(git reset --hard *)`, `Bash(rm -rf *)`); `permissions.allow` (lowersSafety); `permissions.defaultMode` enum `default|acceptEdits|plan|auto|dontAsk|bypassPermissions` (`auto`/`bypassPermissions` user-only; bypass lowersSafety); `permissions.additionalDirectories`; `permissions.disableBypassPermissionsMode` enum `disable`; `permissions.blockReadsOutsideWorkingDirectories` bool since 2.1.257; `autoMode.soft_deny` / `autoMode.hard_deny` (user only, `"$defaults"` keeps built-ins); `autoMode.classifyAllShell` (user only).
- **Sandbox**: `sandbox.enabled`, `sandbox.failIfUnavailable`, `sandbox.autoAllowBashIfSandboxed` (default true), `sandbox.allowUnsandboxedCommands` (default true), `sandbox.excludedCommands`, `sandbox.filesystem.denyRead`, `sandbox.filesystem.allowWrite`, `sandbox.network.allowedDomains`, `sandbox.network.strictAllowlist` (user only). Note in `why`: Linux needs `bubblewrap` + `socat`.
- **Worktrees**: `worktree.baseRef` enum `fresh|head` (default fresh = from `origin/<default>`); `worktree.symlinkDirectories` (suggest `node_modules`, `.venv`); `worktree.sparsePaths`.
- **Model & effort**: `model`; `effortLevel` enum `low|medium|high|xhigh`; `maxEffortLevel` adds `max`; `fallbackModel` (list); `alwaysThinkingEnabled`; `showThinkingSummaries`; `fastMode`; `promptCacheTtl` / `subagentPromptCacheTtl` enum `5m|1h`; `language`; `outputStyle`.
- **Memory & context**: `autoMemoryEnabled` (default true); `autoMemoryDirectory`; `autoCompactEnabled`; `autoCompactWindow` number 100000–1000000; `idleCompaction`; `claudeMdExcludes`; `bashOutputMaxChars` 4000–128000 since 2.1.261; `skillListingBudgetFraction` >0 ≤1 default 0.01; `fileCheckpointingEnabled`; `plansDirectory` (relative to project root).
- **Git & attribution**: `attribution.commit`, `attribution.pr` (strings, `""` hides), `attribution.sessionUrl` bool; `includeGitInstructions`; `prUrlTemplate`.
- **Hooks & MCP**: `disableAllHooks` (lowersSafety — also disables the kit's gates); `enableAllProjectMcpServers` (lowersSafety); `enabledMcpjsonServers`; `disabledMcpjsonServers`; `allowedHttpHookUrls`. (`hooks` itself: not editable in Build — shown read-only in T186.)
- **Interface**: `statusLine` (command string), `theme`, `showTurnDuration`, `preferredNotifChannel` enum `auto|terminal_bell|iterm2|iterm2_with_bell|kitty|ghostty|notifications_disabled`, `respectGitignore`.
- **Updates & privacy**: `autoUpdatesChannel` enum `latest|stable`; `minimumVersion`; `cleanupPeriodDays` integer ≥1 default 30; `feedbackSurveyRate` 0–1; `env` (object; `why` warns values are plain text — never put tokens here).

Presets:
- **Safe baseline** (any file): deny suggestions + ask suggestions.
- **Solo engineer** (user file): Safe baseline + `autoUpdatesChannel: "stable"`, `cleanupPeriodDays: 90`.
- **Team project** (project file): Safe baseline + `worktree.baseRef: "head"`, `worktree.symlinkDirectories: ["node_modules", ".venv"]`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `<section id="settings-tool">` with `<h2>Settings tool</h2>`, nav link under "Getting started" after "Update flow"; Build mode works; Check tab present but disabled with "coming soon" until T186 | "design a section" |
| 2 | Clicking a catalog row's checkbox adds/removes that key in the output; changing its control changes the value; nested keys (`permissions.deny`) are emitted as nested objects | "click on the settings and we can generate" |
| 3 | Output is always valid JSON (`JSON.parse` round-trips) with 2-space indent and a working Copy button (clipboard with select-text fallback) | "generate the settings" / "format" |
| 4 | Target-file switch hides and removes keys not honoured by that file and states how many were removed | Correct settings per file |
| 5 | Each of the three presets produces the exact key set listed above; no preset selects a `lowersSafety` key | "generate the settings for users" |
| 6 | Number controls clamp/flag out-of-range values (`autoCompactWindow`, `bashOutputMaxChars`, `cleanupPeriodDays`, `skillListingBudgetFraction`, `feedbackSurveyRate`) and never emit an invalid value | Valid output |
| 7 | Spec hard rules 1–5 hold: no network or storage API in the tool script, no submitting form, all inline, no package.json, no-script fallback | `PROJECT_SPEC_SITE.md` § Settings tool |
| 8 | Catalog drift/shape test: every entry has `key`, `category`, `type`, `scopes`, `why`; every `enum` has `values`; `version` stamp present; every `key` is in `knownKeys` | Spec source-of-truth row |
| 9 | Existing `tests/test_site_content.py` suite stays green (nav, inline scripts, no external assets) | Regression |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Preset "Team project", target Project | Output equals the preset's exact JSON | `node --test` on the pure `generate(selection, target)` function |
| 2 | Select `autoMode.soft_deny`, switch target to Project | Key removed, note "1 key removed: not read from .claude/settings.json" | node test |
| 3 | `cleanupPeriodDays` = 0 | Control flags it; output omits / keeps last valid value | node test |
| 4 | Tool script source | Contains none of `fetch(`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`, `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie` | pytest grep test |
| 5 | Catalog with one entry missing `why` | Shape test fails (mutation, run once, paste) | pytest |
| 6 | 375 / 768 / 1280 px, light + dark | No page-wide horizontal scroll; output readable | screenshots (Gate 6) |

### Verification Command (exact, runnable)

```bash
node --test "tests/settings_tool/*.mjs" && python3 -m pytest tests/test_site_content.py -q
```

---

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#settings-tool` Build mode, "Team project" preset | LLM-vision screenshot, 1280px | Matches the Design wireframe above; catalog left, output right |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors match design tokens | Diff audit: no new color literals | Only existing `var(--…)` tokens |
| Typography matches spec | Visual / computed style | Existing heading, body and `code` styles |
| Spacing / layout matches spec | Visual | Reuses `.table-wrap` / `details` patterns; new CSS scoped under `#settings-tool` |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (375px) | Playwright / screenshot | Catalog and output stacked; Copy button reachable; no page-wide horizontal scroll |
| Tablet (768px) | screenshot | Stacked or two columns without overflow |
| Desktop (1280px) | screenshot | Two columns |

---

## Approach

**Pattern reference**: `site/index.html` existing inline `<script>` blocks (style, no framework) and `#update-flow` markup; `tests/test_site_content.py` `test_all_scripts_are_inline` / `test_no_external_assets` for test style.

Split the script in two inline blocks: `<script id="settings-tool-core">` = pure functions only (`loadCatalog`, `applyPreset`, `generate(selection, target) -> {json, removed}`, `validateValue(entry, value)`), no DOM access; and a UI block that wires the DOM. Node tests read `site/index.html`, extract the `settings-tool-core` block text and run it in `node:vm` — this keeps one file, no build, no package.json. T186 adds its checker functions to the same core block.

**Vital slice**: catalog JSON + `generate()` + Safety & permissions and Model & effort categories rendered + target switch + Copy.
**Cut list**:
- Per-key deep links beyond one link per row to the reference page anchor
- Editing `hooks` in Build (read-only display arrives with T186)
- URL-hash sharing of a selection
- Managed-settings keys as pickable rows

Writing: page text follows AGENTS.md Writing Principles (ASD-STE100).

---

## Edge Case Checklist

- [ ] Two selected keys share a parent (`permissions.deny` + `permissions.ask`) → one `permissions` object
- [ ] An empty list (`deny: []`) is omitted, not emitted
- [ ] Preset applied after manual edits → replaces selection (confirm inline, no `confirm()` dialog)
- [ ] Clipboard API refused → fallback selects the output text
- [ ] Very long rule strings wrap inside the output pane, not the page
- [ ] Keyboard: every checkbox, control and tab reachable and labelled; focus visible

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `site/index.html` | `#settings-tool` section, nav link, inline catalog JSON, core + UI scripts, scoped CSS |
| `tests/settings_tool/test_generate.mjs` | Node built-in tests for core functions |
| `tests/test_site_content.py` | Catalog shape test, no-network/storage test, section/nav assertions |
| `tasks/TASK_REVIEW_T185.md` | Evidence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/settings.json`, `lib/merge-settings.py` | The kit installs no settings defaults (T184 closed) |
| `README.md` | Site scope only |
| `PROJECT_KANBAN.md` | Harness board |

---

## Test Plan

TDD: write `tests/settings_tool/test_generate.mjs` (presets, target filtering, value validation) red first, then the core block. Then pytest shape/no-network tests. Then UI + screenshots at 375 / 768 / 1280 in light and dark.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T185.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
