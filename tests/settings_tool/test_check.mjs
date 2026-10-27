// T186: logic tests for the Settings tool Check mode. Zero dependencies (node:test).
// Same harness as test_generate.mjs: the core block is read out of site/index.html
// and run in node:vm. Every fixture here is synthetic: no real user file is copied.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "..", "site", "index.html"), "utf8");
const fixtureDir = join(here, "fixtures");
const fixture = (name) => readFileSync(join(fixtureDir, name), "utf8");

function block(id) {
  const m = html.match(new RegExp('<script[^>]*id="' + id + '"[^>]*>([\\s\\S]*?)</script>'));
  assert.ok(m, "missing <script id=\"" + id + "\">");
  return m[1];
}

const ctx = vm.createContext({});
vm.runInContext(block("settings-tool-core"), ctx);
const core = ctx.SettingsCore;
const plain = (x) => JSON.parse(JSON.stringify(x));
const catalog = core.loadCatalog(block("settings-catalog"));

const run = (obj, target = "user") => plain(core.check(catalog, typeof obj === "string" ? obj : JSON.stringify(obj), target));
const ids = (res) => res.findings.map((f) => f.id);
const only = (res, id) => res.findings.filter((f) => f.id === id);
// A file that satisfies I1, so tests can look at one rule at a time.
const SAFE_DENY = ["Read(./.env)", "Read(~/.ssh/**)"];
const withDeny = (obj) => ({ ...obj, permissions: { deny: SAFE_DENY, ...(obj.permissions || {}) } });

test("core exposes the Check mode functions", () => {
  for (const name of ["check", "format", "fromSettings", "maskSecrets", "parseSettings"]) {
    assert.equal(typeof core[name], "function", name);
  }
});

test("clean file gives zero findings", () => {
  const res = run({ permissions: { deny: SAFE_DENY, ask: ["Bash(rm -rf *)"] }, model: "opus", worktree: { baseRef: "head" } }, "project");
  assert.deepEqual(res.findings, []);
});

test("empty paste gives a hint and no findings", () => {
  for (const t of ["", "   \n "]) {
    const res = run(t);
    assert.deepEqual(res.findings, []);
    assert.equal(res.empty, true);
    assert.equal(res.tree, null);
  }
});

// ---- errors ------------------------------------------------------------

test("E1: invalid JSON names line 1, column 2 for {,}", () => {
  const res = run("{,}");
  assert.deepEqual(ids(res), ["E1"]);
  assert.equal(res.findings[0].severity, "error");
  assert.equal(res.findings[0].line, 1);
  assert.equal(res.findings[0].column, 2);
  assert.match(res.findings[0].problem, /line 1, column 2/);
  assert.equal(res.tree, null);
});

test("E1: line and column on a later line, and at end of input", () => {
  const a = run('{\n  "a": 1,\n}').findings[0];
  assert.deepEqual([a.id, a.line, a.column], ["E1", 3, 1]);
  const b = run('{"a":\n1').findings[0];
  assert.equal(b.id, "E1");
  assert.equal(b.line, 2);
});

test("E1: comments (JSONC) and a BOM are named as the cause", () => {
  assert.match(run('{\n // note\n "model": "opus"\n}').findings[0].problem, /comment/i);
  assert.match(run('{ /* x */ }').findings[0].problem, /comment/i);
  assert.match(run("﻿{}").findings[0].problem, /byte order mark/i);
});

test("E1: the message never echoes the pasted text", () => {
  const res = run('{"env": {"T": "ghp_SECRETSECRET"},}');
  assert.equal(res.findings[0].id, "E1");
  assert.ok(!JSON.stringify(res).includes("ghp_"));
});

test("E2: top level must be an object", () => {
  for (const t of ["[]", "1", "\"x\"", "null", "true"]) assert.deepEqual(ids(run(t)), ["E2"], t);
});

test("E3: wrong type, enum outside values, number outside min/max", () => {
  const res = run(withDeny({ cleanupPeriodDays: 0, effortLevel: "turbo", alwaysThinkingEnabled: "yes", autoCompactWindow: 50 }));
  assert.deepEqual(only(res, "E3").map((f) => f.path).sort(), ["alwaysThinkingEnabled", "autoCompactWindow", "cleanupPeriodDays", "effortLevel"]);
  assert.match(only(res, "E3").find((f) => f.path === "effortLevel").problem, /low, medium, high, xhigh/);
});

test("E3: permissions present but null, and a non-string rule", () => {
  const res = run({ permissions: null });
  assert.deepEqual(only(res, "E3").map((f) => f.path), ["permissions"]);
  const res2 = run({ permissions: { deny: [...SAFE_DENY, 5] } });
  assert.deepEqual(only(res2, "E3").map((f) => f.path), ["permissions.deny"]);
});

test("E3: statusLine must be a command object; attribution may be false", () => {
  assert.deepEqual(only(run(withDeny({ statusLine: "~/bin/x.sh" })), "E3").map((f) => f.path), ["statusLine"]);
  assert.deepEqual(only(run(withDeny({ statusLine: { type: "command", command: "~/bin/x.sh" } })), "E3"), []);
  assert.deepEqual(only(run(withDeny({ attribution: false })), "E3"), []);
});

test("E4: removed key has no effect", () => {
  const res = run(withDeny({ taskOutputMaxChars: 1000 }));
  assert.deepEqual(ids(res), ["E4"]);
  assert.equal(res.findings[0].path, "taskOutputMaxChars");
});

test("E5: autoMode in a Project file is ignored", () => {
  const res = run(withDeny({ autoMode: { soft_deny: ["x"] } }), "project");
  assert.deepEqual(ids(res), ["E5"]);
  assert.equal(res.findings[0].path, "autoMode");
  assert.equal(ids(run(withDeny({ autoMode: { soft_deny: ["x"] } }), "user")).length, 0);
});

test("E5: managed-only, user-only, global-config keys and user-only defaultMode values", () => {
  const p = (obj, t) => only(run(withDeny(obj), t), "E5").map((f) => f.path);
  assert.deepEqual(p({ requiredMinimumVersion: "2.1.0" }, "user"), ["requiredMinimumVersion"]);
  assert.deepEqual(p({ spellcheck: true }, "local"), ["spellcheck"]);
  assert.deepEqual(p({ spellcheck: true }, "user"), []);
  assert.deepEqual(p({ useAutoModeDuringPlan: false }, "project"), ["useAutoModeDuringPlan"]);
  assert.deepEqual(p({ useAutoModeDuringPlan: false }, "local"), []);
  assert.deepEqual(p({ copyOnSelect: true }, "user"), ["copyOnSelect"]);
  assert.match(only(run(withDeny({ copyOnSelect: true })), "E5")[0].fix, /~\/\.claude\.json/);
  for (const v of ["auto", "bypassPermissions"]) {
    assert.deepEqual(p({ permissions: { defaultMode: v } }, "project"), ["permissions.defaultMode"], v);
  }
  assert.deepEqual(p({ permissions: { defaultMode: "plan" } }, "project"), []);
});

// ---- warnings ----------------------------------------------------------

test("W1: deprecated key names its replacement", () => {
  const res = run(withDeny({ includeCoAuthoredBy: false }));
  assert.deepEqual(ids(res), ["W1"]);
  assert.match(res.findings[0].fix, /attribution/);
});

test("W2: misspelled key gets did-you-mean; a far key is kept as-is", () => {
  const res = run('{ "permisions": {} }');
  const w2 = only(res, "W2");
  assert.equal(w2.length, 1);
  assert.match(w2[0].problem + " " + w2[0].fix, /did you mean permissions/i);
  const far = only(run(withDeny({ zzzzQqq: 1 })), "W2")[0];
  assert.match(far.problem, /unknown key, kept as-is/i);
  const nested = only(run({ permissions: { deny: SAFE_DENY, alow: [] } }), "W2")[0];
  assert.equal(nested.path, "permissions.alow");
  assert.match(nested.fix, /permissions\.allow/);
});

test("W2: valid keys outside the catalog are known (full reference index)", () => {
  const res = run(withDeny({ enabledPlugins: { "a@b": true }, apiKeyHelper: "/bin/k", hooks: {}, extraKnownMarketplaces: {}, remote: { defaultEnvironmentId: "env_1" }, sandbox: { credentials: { envVars: [] } }, worktree: { location: "x" } }));
  assert.deepEqual(only(res, "W2"), []);
  assert.ok(catalog.knownKeys.length >= 247, "knownKeys holds " + catalog.knownKeys.length);
});

test("W3: broad allow rule, exactly one W3 plus I1 (Success 1)", () => {
  const res = run({ permissions: { allow: ["Bash(git *)"] } }, "local");
  assert.deepEqual(ids(res), ["W3", "I1"]);
  assert.equal(res.findings[0].path, "permissions.allow[0]");
  assert.match(res.findings[0].problem, /pre-approves nearly any command of that kind/);
});

test("W3: every listed broad rule is flagged, a narrow one is not", () => {
  const broad = ["Bash", "Bash(*)", "Bash(git *)", "Bash(bash *)", "Bash(sh *)", "Bash(python3 *)", "Bash(python *)", "Bash(node *)", "Bash(cat *)"];
  const res = run({ permissions: { deny: SAFE_DENY, allow: [...broad, "Bash(git status)"] } });
  assert.deepEqual(only(res, "W3").map((f) => f.path), broad.map((_, i) => "permissions.allow[" + i + "]"));
});

test("W4: rule in allow and deny/ask, and duplicates inside one list", () => {
  const res = run({ permissions: { deny: [...SAFE_DENY, "Bash(curl *)"], ask: ["Bash(npm *)", "Bash(npm *)"], allow: ["Bash(curl *)", "Bash(npm *)"] } });
  const w4 = only(res, "W4").map((f) => f.path);
  assert.deepEqual(w4, ["permissions.ask[1]", "permissions.allow[0]", "permissions.allow[1]"]);
  assert.match(only(res, "W4")[1].problem, /deny → ask → allow/);
});

test("W5: secret-looking env values; masked everywhere (Success 3)", () => {
  const secret = "ghp_abcdefghijklmnopqrstuvwxyz0123456789";
  const res = run({ env: { GITHUB_TOKEN: secret, OK: "1" }, permissions: { deny: SAFE_DENY } });
  assert.deepEqual(ids(res), ["W5"]);
  assert.equal(res.findings[0].path, "env.GITHUB_TOKEN");
  assert.match(res.findings[0].fix, /apiKeyHelper/);
  assert.ok(!JSON.stringify(res).includes("ghp_"), "findings or tree hold the secret");
  for (const v of ["sk-ant-123", "gho_x", "github_pat_x", "xoxb-1", "AKIAIOSFODNN7EXAMPLE", "a".repeat(32)]) {
    assert.deepEqual(ids(run({ env: { X: v }, permissions: { deny: SAFE_DENY } })), ["W5"], v);
  }
  assert.deepEqual(ids(run({ env: { X: "short-plain-value" }, permissions: { deny: SAFE_DENY } })), []);
});

test("W6: hook command copies input to /tmp", () => {
  const hooks = { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: "tee /tmp/in.json | ./h.sh" }, { type: "command", command: "cat > /tmp/x" }, { type: "command", command: "./safe.sh" }] }] };
  const res = run(withDeny({ hooks }));
  assert.deepEqual(only(res, "W6").map((f) => f.path), ["hooks.PreToolUse[0].hooks[0].command", "hooks.PreToolUse[0].hooks[1].command"]);
});

test("W7: lowersSafety key set to its unsafe value", () => {
  const res = run(withDeny({ disableAllHooks: true, enableAllProjectMcpServers: true }));
  assert.deepEqual(only(res, "W7").map((f) => f.path), ["disableAllHooks", "enableAllProjectMcpServers"]);
  const bypass = run({ permissions: { deny: SAFE_DENY, defaultMode: "bypassPermissions" } }, "user");
  assert.deepEqual(only(bypass, "W7").map((f) => f.path), ["permissions.defaultMode"]);
  assert.deepEqual(only(run(withDeny({ disableAllHooks: false })), "W7"), []);
});

// ---- tips --------------------------------------------------------------

test("I1: no deny rule for .env / ~/.ssh offers the Build suggestions", () => {
  const res = run({ model: "opus" });
  assert.deepEqual(ids(res), ["I1"]);
  const add = res.findings[0].action.add["permissions.deny"];
  assert.ok(add.includes("Read(./.env)") && add.includes("Read(~/.ssh/**)"));
  assert.equal(res.findings[0].action.label, "Add in Build");
  assert.deepEqual(ids(run({ permissions: { deny: ["Read(./.env)"] } })), ["I1"]);
});

test("I2: since version on a key", () => {
  const res = run(withDeny({ bashOutputMaxChars: 8000 }));
  assert.deepEqual(ids(res), ["I2"]);
  assert.match(res.findings[0].problem, /2\.1\.261/);
});

// ---- format ------------------------------------------------------------

test("format pretty-prints with 2 spaces, keeps key order and unknown keys", () => {
  const out = plain(core.format('{"zeta":1,"model":"opus","aUnknown":{"b":2,"a":1}}'));
  assert.equal(out.ok, true);
  assert.equal(out.text, '{\n  "zeta": 1,\n  "model": "opus",\n  "aUnknown": {\n    "b": 2,\n    "a": 1\n  }\n}');
});

test("format of invalid JSON returns E1 and no output", () => {
  const out = plain(core.format("{,}"));
  assert.equal(out.ok, false);
  assert.equal(out.text, "");
  assert.equal(out.findings[0].id, "E1");
});

test("format masks secrets unless keepSecrets", () => {
  const text = JSON.stringify({ env: { T: "ghp_abc123" }, hooks: { Stop: [{ hooks: [{ type: "command", command: "TOKEN=ghp_abc123def ./x.sh" }] }] } });
  assert.ok(!core.format(text).text.includes("ghp_"));
  assert.ok(core.format(text, true).text.includes("ghp_abc123def"));
});

// ---- masking -----------------------------------------------------------

test("maskSecrets hides tokens inside hook commands and env values, keeps paths", () => {
  const masked = plain(core.maskSecrets({ env: { K: "sk-live-1234" }, hooks: { Stop: [{ hooks: [{ command: "TOKEN=ghp_abcdef123 python3 /home/u/.claude/hooks/a_very_long_script_name_here.py" }] }] } }));
  const s = JSON.stringify(masked);
  assert.ok(!s.includes("ghp_") && !s.includes("sk-live"), s);
  assert.ok(s.includes("/home/u/.claude/hooks/a_very_long_script_name_here.py"), "path was masked");
  assert.ok(!core.maskSecrets("run task-runner now").includes("hidden"), "word containing sk- was masked");
});

test("rule strings with <script> stay plain text in findings and tree", () => {
  const res = run({ permissions: { deny: SAFE_DENY, allow: ["Bash(<script>alert(1)</script>)", "Bash(<script>alert(1)</script>)"] } });
  assert.ok(JSON.stringify(res).includes("<script>"), "value should be carried as text, not dropped");
  assert.equal(only(res, "W4").length, 1);
});

// ---- tree --------------------------------------------------------------

test("tree groups keys by catalog category, permissions in precedence order, hooks, other", () => {
  const res = run({ effortLevel: "low", permissions: { allow: ["Bash(ls)"], deny: SAFE_DENY }, hooks: { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: "python3 h.py" }] }] }, enabledPlugins: {}, zzz: 1 });
  const t = res.tree;
  assert.deepEqual(t.categories.map((c) => c.name), ["Model & effort"]);
  assert.deepEqual(t.categories[0].items.map((i) => i.path), ["effortLevel"]);
  assert.deepEqual(Object.keys(t.permissions), ["deny", "ask", "allow"]);
  assert.equal(t.permissions.deny.length, 2);
  assert.equal(t.permissions.allow[0].path, "permissions.allow[0]");
  assert.deepEqual(t.hooks, [{ path: "hooks.PreToolUse[0].hooks[0].command", event: "PreToolUse", matcher: "Bash", command: "python3 h.py" }]);
  assert.deepEqual(t.other.map((o) => o.path), ["enabledPlugins", "zzz"]);
});

// ---- fromSettings / round trip ----------------------------------------

const roundTrip = (parsed, target = "user") => {
  const loaded = core.fromSettings(catalog, parsed, {});
  return JSON.parse(core.generate(catalog, loaded.selection, target, loaded.passthrough).json);
};

test("fromSettings fills Build selection for known keys and passes the rest through", () => {
  const parsed = { permissions: { deny: SAFE_DENY }, hooks: { Stop: [] }, enabledPlugins: { x: true }, cleanupPeriodDays: 0 };
  const loaded = plain(core.fromSettings(catalog, parsed, {}));
  assert.deepEqual(loaded.selection, { "permissions.deny": SAFE_DENY });
  assert.deepEqual(loaded.passthrough, { hooks: { Stop: [] }, enabledPlugins: { x: true }, cleanupPeriodDays: 0 });
});

test("round trip: generate(fromSettings(parsed)) deep-equals every fixture", () => {
  const files = readdirSync(fixtureDir).filter((f) => f.endsWith(".json"));
  assert.ok(files.length >= 3, "fixtures missing");
  for (const f of files) {
    const parsed = JSON.parse(fixture(f).replace(/ghp_\w+|sk-[\w-]+/g, "plain"));
    assert.deepEqual(roundTrip(parsed), parsed, f);
  }
  const edge = { statusLine: { type: "command", command: "x", padding: 1 }, permissions: { deny: [] }, env: {}, a: { b: { c: [1, { d: null }] } } };
  assert.deepEqual(roundTrip(edge), edge);
});

test("fromSettings removes secret values unless keepSecrets, and counts them", () => {
  const parsed = { env: { GITHUB_TOKEN: "ghp_abcdef123456", OK: "1" }, hooks: { Stop: [{ hooks: [{ type: "command", command: "T=ghp_zzzz1234 ./x" }] }] } };
  const off = core.fromSettings(catalog, parsed, {});
  const json = core.generate(catalog, off.selection, "user", off.passthrough).json;
  assert.ok(!json.includes("ghp_"), json);
  assert.equal(JSON.parse(json).env.GITHUB_TOKEN, "");
  assert.equal(off.masked, 2);
  const on = core.fromSettings(catalog, parsed, { keepSecrets: true });
  assert.deepEqual(JSON.parse(core.generate(catalog, on.selection, "user", on.passthrough).json), parsed);
});

test("own __proto__ key is kept as data and pollutes nothing", () => {
  const text = '{"__proto__": {"polluted": 1}, "model": "opus"}';
  const res = run(text);
  assert.ok(res.findings.some((f) => f.path === "__proto__"));
  const parsed = JSON.parse(text);
  const back = roundTrip(parsed);
  assert.equal(vm.runInContext("({}).polluted", ctx), undefined);
  assert.ok(Object.prototype.hasOwnProperty.call(back, "__proto__"));
  assert.ok(core.format(text).text.includes('"__proto__"'));
});

// ---- real-world shape and robustness ----------------------------------

test("AC8: local-file shape with broad git/bash allows and a tee /tmp hook yields W3 and W6", () => {
  const res = run(fixture("local_broad_allow.json"), "local");
  assert.deepEqual(only(res, "W3").map((f) => f.path), ["permissions.allow[0]", "permissions.allow[1]"]);
  assert.equal(only(res, "W6").length, 1);
});

test("30-finding fixture for the Gate 6 screenshots holds at least 30 findings", () => {
  const res = run(fixture("many_findings.json"), "project");
  assert.ok(res.findings.length >= 30, "only " + res.findings.length);
  for (const id of ["E3", "E4", "E5", "W1", "W2", "W3", "W4", "W5", "W6", "W7", "I1", "I2"]) assert.ok(ids(res).includes(id), id);
  assert.ok(!JSON.stringify(res).includes("ghp_"));
});

test("robustness: 1 MB paste and depth-200 nesting finish under 2 s without throwing", () => {
  const many = {};
  for (let i = 0; many && JSON.stringify(many).length < 1_000_000; i += 500) for (let j = i; j < i + 500; j++) many["key" + j] = "value-" + j;
  const big = JSON.stringify(many);
  let deep = "1";
  for (let i = 0; i < 200; i++) deep = '{"a":' + deep + "}";
  const deepAll = '{"permissions":' + deep + ',"hooks":' + deep + ',"env":' + deep + "}";
  const longStr = JSON.stringify({ env: { X: "a".repeat(1_000_000) } });
  for (const [name, text] of [["1 MB keys", big], ["depth 200", deep], ["depth 200 in known keys", deepAll], ["1 MB string", longStr]]) {
    const t0 = performance.now();
    const res = core.check(catalog, text, "user");
    const f = core.format(text);
    const loaded = core.fromSettings(catalog, JSON.parse(text), {});
    core.generate(catalog, loaded.selection, "user", loaded.passthrough);
    const ms = performance.now() - t0;
    console.log("# robustness " + name + ": " + text.length + " chars, " + res.findings.length + " findings, " + ms.toFixed(1) + " ms");
    assert.ok(f.ok);
    assert.ok(ms < 2000, name + " took " + ms + " ms");
  }
});
