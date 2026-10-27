// T185: logic tests for the Settings tool core. Zero dependencies (node:test).
// The core block is read out of site/index.html and run in node:vm, so the
// page stays one file with no build step.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "..", "site", "index.html"), "utf8");

function block(id) {
  const m = html.match(new RegExp('<script[^>]*id="' + id + '"[^>]*>([\\s\\S]*?)</script>'));
  assert.ok(m, "missing <script id=\"" + id + "\">");
  return m[1];
}

const ctx = vm.createContext({});
vm.runInContext(block("settings-tool-core"), ctx);
const core = ctx.SettingsCore;
const catalog = core.loadCatalog(block("settings-catalog"));

test("core exposes the pure functions", () => {
  for (const name of ["loadCatalog", "applyPreset", "generate", "validateValue", "initialValue"]) {
    assert.equal(typeof core[name], "function", name);
  }
});

test("catalog is version-stamped and every entry has the required shape", () => {
  assert.equal(catalog.version, "2.1.311");
  for (const s of catalog.settings) {
    for (const f of ["key", "category", "type", "scopes", "why"]) assert.ok(s[f], s.key + " missing " + f);
    assert.ok(catalog.categories.includes(s.category), s.key + " category unknown");
    if (s.type === "enum") assert.ok(Array.isArray(s.values) && s.values.length, s.key + " enum needs values");
    assert.ok(catalog.knownKeys.includes(s.key), s.key + " not in knownKeys");
  }
});

test("Team project preset on Project target gives the exact JSON", () => {
  const sel = core.applyPreset(catalog, "team-project");
  const out = core.generate(catalog, sel, "project");
  const expected = {
    permissions: {
      deny: ["Read(./.env)", "Read(./.env.*)", "Read(./**/*.pem)", "Read(./**/*.key)", "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.config/gh/**)"],
      ask: ["Bash(git push --force *)", "Bash(git push -f *)", "Bash(git reset --hard *)", "Bash(rm -rf *)"],
    },
    worktree: { baseRef: "head", symlinkDirectories: ["node_modules", ".venv"] },
  };
  assert.deepEqual(JSON.parse(out.json), expected);
  assert.equal(out.json, JSON.stringify(expected, null, 2));
  assert.deepEqual(out.removed, []);
});

test("preset key sets are exact and never select a lowersSafety key", () => {
  const keys = (id) => Object.keys(core.applyPreset(catalog, id)).sort();
  assert.deepEqual(keys("safe-baseline"), ["permissions.ask", "permissions.deny"]);
  assert.deepEqual(keys("solo-engineer"), ["autoUpdatesChannel", "cleanupPeriodDays", "permissions.ask", "permissions.deny"]);
  assert.deepEqual(keys("team-project"), ["permissions.ask", "permissions.deny", "worktree.baseRef", "worktree.symlinkDirectories"]);
  assert.deepEqual(keys("empty"), []);
  const risky = new Set(catalog.settings.filter((s) => s.lowersSafety).map((s) => s.key));
  for (const p of catalog.presets) for (const k of Object.keys(core.applyPreset(catalog, p.id))) assert.ok(!risky.has(k), p.id + " selects " + k);
  const solo = core.applyPreset(catalog, "solo-engineer");
  assert.equal(solo.autoUpdatesChannel, "stable");
  assert.equal(solo.cleanupPeriodDays, 90);
});

test("two keys under one parent share one object", () => {
  const out = JSON.parse(core.generate(catalog, { "permissions.deny": ["Read(./.env)"], "permissions.ask": ["Bash(rm -rf *)"] }, "user").json);
  assert.deepEqual(Object.keys(out), ["permissions"]);
  assert.deepEqual(Object.keys(out.permissions).sort(), ["ask", "deny"]);
});

test("output follows catalog order, not selection order", () => {
  const a = core.generate(catalog, { cleanupPeriodDays: 40, "permissions.deny": ["Read(./.env)"] }, "user").json;
  assert.ok(a.indexOf("permissions") < a.indexOf("cleanupPeriodDays"));
});

test("empty list is omitted", () => {
  const out = core.generate(catalog, { "permissions.deny": [] }, "user");
  assert.equal(out.json, "{}");
});

test("autoMode.soft_deny removed on Project target with a one-line note", () => {
  const out = core.generate(catalog, { "autoMode.soft_deny": ["$defaults"] }, "project");
  assert.deepEqual(out.removed, ["autoMode.soft_deny"]);
  assert.equal(out.note, "1 key removed: not read from .claude/settings.json");
  assert.equal(out.json, "{}");
  const user = core.generate(catalog, { "autoMode.soft_deny": ["$defaults"] }, "user");
  assert.deepEqual(user.removed, []);
  assert.equal(user.note, "");
});

test("defaultMode auto and bypassPermissions are user-only values", () => {
  for (const v of ["auto", "bypassPermissions"]) {
    assert.equal(core.generate(catalog, { "permissions.defaultMode": v }, "local").removed.length, 1);
    assert.equal(core.generate(catalog, { "permissions.defaultMode": v }, "user").removed.length, 0);
  }
  assert.equal(core.generate(catalog, { "permissions.defaultMode": "plan" }, "local").removed.length, 0);
});

test("plural note wording and local file name", () => {
  const out = core.generate(catalog, { "autoMode.soft_deny": ["x"], "autoMode.hard_deny": ["y"] }, "local");
  assert.equal(out.note, "2 keys removed: not read from .claude/settings.local.json");
});

test("number validation: out-of-range values are flagged and never emitted", () => {
  const entry = (k) => catalog.settings.find((s) => s.key === k);
  assert.equal(core.validateValue(entry("cleanupPeriodDays"), 0).ok, false);
  assert.equal(core.validateValue(entry("cleanupPeriodDays"), 1.5).ok, false);
  assert.equal(core.validateValue(entry("cleanupPeriodDays"), 1).ok, true);
  assert.equal(core.validateValue(entry("autoCompactWindow"), 99999).ok, false);
  assert.equal(core.validateValue(entry("autoCompactWindow"), 1000001).ok, false);
  assert.equal(core.validateValue(entry("autoCompactWindow"), 100000).ok, true);
  assert.equal(core.validateValue(entry("bashOutputMaxChars"), 3999).ok, false);
  assert.equal(core.validateValue(entry("bashOutputMaxChars"), 128000).ok, true);
  assert.equal(core.validateValue(entry("skillListingBudgetFraction"), 0).ok, false);
  assert.equal(core.validateValue(entry("skillListingBudgetFraction"), 1).ok, true);
  assert.equal(core.validateValue(entry("skillListingBudgetFraction"), 1.01).ok, false);
  assert.equal(core.validateValue(entry("feedbackSurveyRate"), 0).ok, true);
  assert.equal(core.validateValue(entry("feedbackSurveyRate"), 1.1).ok, false);
  assert.equal(core.validateValue(entry("cleanupPeriodDays"), NaN).ok, false);
  const out = core.generate(catalog, { cleanupPeriodDays: 0, autoUpdatesChannel: "stable" }, "user");
  assert.deepEqual(JSON.parse(out.json), { autoUpdatesChannel: "stable" });
  assert.deepEqual(out.invalid, ["cleanupPeriodDays"]);
});

test("enum, bool and string validation", () => {
  const entry = (k) => catalog.settings.find((s) => s.key === k);
  assert.equal(core.validateValue(entry("effortLevel"), "max").ok, false);
  assert.equal(core.validateValue(entry("maxEffortLevel"), "max").ok, true);
  assert.equal(core.validateValue(entry("sandbox.enabled"), "yes").ok, false);
  assert.equal(core.validateValue(entry("model"), "").ok, false);
  assert.equal(core.validateValue(entry("attribution.commit"), "").ok, true);
});

test("statusLine is emitted as a command object", () => {
  const out = JSON.parse(core.generate(catalog, { statusLine: "~/bin/line.sh" }, "user").json);
  assert.deepEqual(out, { statusLine: { type: "command", command: "~/bin/line.sh" } });
});

test("output always round-trips through JSON.parse with 2-space indent", () => {
  const sel = {};
  for (const s of catalog.settings) sel[s.key] = core.initialValue(s);
  for (const t of ["user", "project", "local"]) {
    const out = core.generate(catalog, sel, t);
    assert.equal(out.json, JSON.stringify(JSON.parse(out.json), null, 2));
  }
});

test("unknown selection keys are ignored", () => {
  assert.equal(core.generate(catalog, { notAKey: 1 }, "user").json, "{}");
});

test("tool script source holds no network or storage API (spec rule 1)", () => {
  const src = block("settings-tool-core") + (html.match(/<script id="settings-tool-ui">([\s\S]*?)<\/script>/) || ["", ""])[1];
  for (const bad of ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "localStorage", "sessionStorage", "indexedDB", "document.cookie"]) {
    assert.ok(!src.includes(bad), "tool script contains " + bad);
  }
});
