// T213: headless-Chrome check of the sidebar scroll-spy on site/index.html.
// Zero dependencies: node:test, node:http and raw CDP over Node's built-in WebSocket.
// Skips with a clear message when no Chrome binary is found (set CHROME to point at one).
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { existsSync, readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, extname } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "site");
const chromePath = [process.env.CHROME, "/usr/bin/google-chrome", "/usr/bin/chromium",
  "/snap/bin/chromium", "/usr/bin/chromium-browser"].find((p) => p && existsSync(p));
const skip = chromePath ? false : "no Chrome binary found (set CHROME=/path/to/chrome)";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const MIME = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml" };

let server, chrome, profile, ws, nextId = 1, sessionId;
const pending = new Map();
let baseUrl;

function send(method, params = {}, withSession = true) {
  const id = nextId++;
  const msg = { id, method, params };
  if (withSession && sessionId) { msg.sessionId = sessionId; }
  ws.send(JSON.stringify(msg));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

async function evaluate(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) { throw new Error(JSON.stringify(r.exceptionDetails)); }
  return r.result.value;
}

async function open(width, height) {
  await send("Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: baseUrl + "/index.html" });
  for (let i = 0; i < 100; i++) {
    if (await evaluate("document.readyState === 'complete'")) { break; }
    await sleep(50);
  }
  // Smooth scrolling never settles under headless automation (memory/learnings.md).
  await evaluate("document.documentElement.style.scrollBehavior = 'auto'");
  await sleep(300);
}

const activeLinks = () => evaluate(
  "[...document.querySelectorAll('#site-nav a.active')].map(a => a.getAttribute('href').slice(1))");
const navIds = () => evaluate(
  "[...document.querySelectorAll('#site-nav a[href^=\"#\"]')].map(a => a.getAttribute('href').slice(1))");

before(async () => {
  if (skip) { return; }
  server = createServer((req, res) => {
    const name = req.url.split("?")[0] === "/" ? "/index.html" : req.url.split("?")[0];
    const file = join(siteDir, name);
    if (!file.startsWith(siteDir) || !existsSync(file)) { res.writeHead(404).end(); return; }
    res.writeHead(200, { "content-type": MIME[extname(file)] || "application/octet-stream" });
    res.end(readFileSync(file));
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  baseUrl = "http://127.0.0.1:" + server.address().port;

  profile = mkdtempSync(join(tmpdir(), "t213-chrome-"));
  chrome = spawn(chromePath, ["--headless=new", "--disable-gpu", "--no-first-run",
    "--remote-debugging-port=0", "--user-data-dir=" + profile, "about:blank"],
  { stdio: "ignore" });
  const portFile = join(profile, "DevToolsActivePort");
  for (let i = 0; i < 100 && !existsSync(portFile); i++) { await sleep(100); }
  const [port, path] = readFileSync(portFile, "utf8").trim().split("\n");
  ws = new WebSocket("ws://127.0.0.1:" + port + path);
  await new Promise((r) => ws.addEventListener("open", r, { once: true }));
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? p.reject(new Error(JSON.stringify(msg.error))) : p.resolve(msg.result);
    }
  });
  const { targetId } = await send("Target.createTarget", { url: "about:blank" }, false);
  ({ sessionId } = await send("Target.attachToTarget", { targetId, flatten: true }, false));
});

after(async () => {
  if (ws) { ws.close(); }
  if (chrome) {
    const exited = new Promise((r) => chrome.once("exit", r));
    chrome.kill();
    await exited;
  }
  if (server) { server.close(); }
  if (profile) { rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }); }
});

test("AC1: after a click on any sidebar link, only that link is active (fresh page per link)",
  { skip }, async () => {
    await open(1440, 900);
    const ids = await navIds();
    assert.ok(ids.length >= 15, "expected the full sidebar, got " + ids.length);
    const wrong = [];
    for (const id of ids) {
      await open(1440, 900);
      await evaluate("document.querySelector('#site-nav a[href=\"#" + id + "\"]').click()");
      await sleep(400);
      const active = await activeLinks();
      if (active.length !== 1 || active[0] !== id) {
        wrong.push(id + " -> active: [" + active.join(", ") + "]");
      }
    }
    assert.deepEqual(wrong, [], "links whose click leaves a different link active:\n" + wrong.join("\n"));
  });

test("AC1: clicking every link in order on one page keeps the clicked link the only active one",
  { skip }, async () => {
    await open(1440, 900);
    const wrong = [];
    for (const id of await navIds()) {
      await evaluate("document.querySelector('#site-nav a[href=\"#" + id + "\"]').click()");
      await sleep(400);
      const active = await activeLinks();
      if (active.length !== 1 || active[0] !== id) {
        wrong.push(id + " -> active: [" + active.join(", ") + "]");
      }
    }
    assert.deepEqual(wrong, [], "sequential clicks that mis-highlight:\n" + wrong.join("\n"));
  });

test("AC2: a section scrolled to just below the header is the active one",
  { skip }, async () => {
    await open(1440, 900);
    const wrong = [];
    const ids = await navIds();
    let reachable = 0;
    for (const id of ids) {
      // The same offset an anchor jump uses, read from CSS rather than hard-coded.
      const fits = await evaluate(`(() => {
        const s = document.getElementById(${JSON.stringify(id)});
        const off = parseFloat(getComputedStyle(s).scrollMarginTop);
        const y = s.getBoundingClientRect().top + scrollY - off;
        const max = document.documentElement.scrollHeight - innerHeight;
        if (y > max) { return false; }
        scrollTo(0, y);
        return true;
      })()`);
      if (!fits) { continue; }
      reachable++;
      await sleep(300);
      const active = await activeLinks();
      if (active.length !== 1 || active[0] !== id) {
        wrong.push(id + " -> active: [" + active.join(", ") + "]");
      }
    }
    assert.ok(reachable >= 10, "too few sections reachable to be a meaningful check: " + reachable);
    assert.deepEqual(wrong, [], "sections at the top of the view with another link active:\n" + wrong.join("\n"));
  });

test("AC3: after clicking a last section, a manual scroll up hands the highlight back to the scroll",
  { skip }, async () => {
    await open(1440, 900);
    const ids = await navIds();
    const wrong = [];
    for (const id of ids.slice(-3)) {
      await evaluate("document.querySelector('#site-nav a[href=\"#" + id + "\"]').click()");
      await sleep(400);
      // Real wheel input, as a user scrolls by hand.
      await send("Input.dispatchMouseEvent",
        { type: "mouseWheel", x: 700, y: 400, deltaX: 0, deltaY: -1500 });
      await sleep(900);
      const result = await evaluate(`(() => {
        const secs = [...document.querySelectorAll('main > section[id]')];
        const off = parseFloat(getComputedStyle(secs[0]).scrollMarginTop);
        const top = secs.find((s) => s.getBoundingClientRect().bottom > off) || secs[0];
        const active = [...document.querySelectorAll('#site-nav a.active')].map(a => a.getAttribute('href').slice(1));
        return { expected: top.id, active };
      })()`);
      if (result.expected === id) { wrong.push(id + ": wheel did not move the page away"); continue; }
      if (result.active.length !== 1 || result.active[0] !== result.expected) {
        wrong.push(id + " -> after wheel up expected " + result.expected + ", active [" + result.active.join(", ") + "]");
      }
    }
    assert.deepEqual(wrong, [], wrong.join("\n"));
  });

test("375px: opening the drawer and clicking a link makes that link the only active one",
  { skip }, async () => {
    await open(375, 700);
    const wrong = [];
    for (const id of ["skills", "hooks", "agent-focus", "options"]) {
      await open(375, 700);
      await evaluate("document.querySelector('.nav-toggle').click()");
      await sleep(150);
      await evaluate("document.querySelector('#site-nav a[href=\"#" + id + "\"]').click()");
      await sleep(400);
      const active = await activeLinks();
      if (active.length !== 1 || active[0] !== id) {
        wrong.push(id + " -> active: [" + active.join(", ") + "]");
      }
    }
    assert.deepEqual(wrong, [], "drawer clicks that mis-highlight:\n" + wrong.join("\n"));
  });

// Round 2: the hold releases on ANY scroll away from where the click landed,
// however the scroll was caused, and the jump itself never releases it.
const topSectionId = () => evaluate(`(() => {
  const secs = [...document.querySelectorAll('main > section[id]')];
  const off = parseFloat(getComputedStyle(secs[0]).scrollMarginTop);
  return (secs.find((s) => s.getBoundingClientRect().bottom > off) || secs[0]).id;
})()`);
const click = (id) => evaluate("document.querySelector('#site-nav a[href=\"#" + id + "\"]').click()");

test("round 2: a scroll with no wheel, touch or key event releases the hold",
  { skip }, async () => {
    await open(1440, 900);
    await click("settings-tool");
    await sleep(600);
    assert.deepEqual(await activeLinks(), ["settings-tool"]);
    await evaluate("scrollBy(0, 2500)"); // settings-tool is ~1930px tall; scrollbar drag, find-in-page, autoscroll: no input events
    await sleep(600);
    const expected = await topSectionId();
    assert.notEqual(expected, "settings-tool", "scrollBy did not leave the section");
    assert.deepEqual(await activeLinks(), [expected]);
  });

test("round 2: a smooth-scroll jump does not release the hold",
  { skip }, async () => {
    await open(1440, 900);
    await evaluate("document.documentElement.style.scrollBehavior = 'smooth'");
    await click("hooks");
    // Sample during the animation, then after it settles.
    await sleep(120);
    const midway = await evaluate("scrollY");
    await sleep(1800);
    const landed = await evaluate("scrollY");
    assert.ok(landed > 1000, "smooth scroll did not move the page: " + landed);
    assert.ok(midway < landed, "expected an animated jump (midway " + midway + ", landed " + landed + ")");
    assert.deepEqual(await activeLinks(), ["hooks"]);
  });

test("round 2: a click on the last section, where the page cannot scroll, stays held",
  { skip }, async () => {
    await open(1440, 900);
    await evaluate("scrollTo(0, document.documentElement.scrollHeight)");
    await sleep(500);
    await click("options");
    await sleep(800); // longer than the settle debounce, with no scroll event at all
    assert.deepEqual(await activeLinks(), ["options"]);
    await sleep(500);
    assert.deepEqual(await activeLinks(), ["options"]);
  });
