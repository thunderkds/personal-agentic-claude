#!/usr/bin/env python3
"""Token meter (T124) — spend and agent focus, measured from Claude Code session transcripts.

Read-only, stdlib only, stdout only: it never opens a file for writing and never
creates a directory (same rule as `scripts/memory_usage_report.py`, T063).
Method and baseline: `docs/token-focus-finding-2026-09-25.md`, DDR-0009.

**Aggregates only.** Transcripts hold everything a session saw, secrets included.
Text is only ever measured (`len`) or compared in memory (recall risk); output
holds counts, sizes, costs, task IDs, transcript basenames, tool names and
attachment types — never transcript text, commands, file contents or prompts.

Usage::

    token_meter.py [--projects-dir DIR] [--task Txxx] [--bash-lines N] [--json]
    token_meter.py --session PATH [--json]
    token_meter.py --current [--cwd DIR] [--projects-dir DIR] [--json]
    (both take --price-in / --price-out, $ per MTok)

Transcript root: `--projects-dir`, else `$CLAUDE_CONFIG_DIR/projects`, else
`~/.claude/projects`; `*.jsonl` recursively (sub-agents live under
`<session>/subagents/`). Symlinked directories are not followed and files that
resolve outside the root are skipped.

Rules
-----
* **API call** — an assistant entry whose `message.usage` has integer
  `input_tokens`, `output_tokens`, `cache_read_input_tokens`,
  `cache_creation_input_tokens`. De-duplicated by `message.id` (streamed chunks
  share one; the last entry wins; an entry without an id is its own call). Summary totals de-duplicate across files too
  (a continued session re-records history); per-transcript views are per file.
* **Cost** — (input + 2 x 1h-write + 1.25 x 5m-write + 0.1 x read) x input price
  + output x output price. With no `cache_creation` split, all writes are 5m.
* **Context** of a call — input + cache writes + cache reads.
* **Tokens from text** — characters / 3.5 (estimate, not calibrated).
* **Carry cost** — a content item is first sent by the next API call after it
  appears; it costs one cache write at that call's write rate (2x if it wrote
  nothing) plus 0.1x on every later call of the transcript. Assumes no
  compaction, so savings are upper bounds.
* **Content kinds** (session view) — `tool_result:<tool>`, `tool_input`
  (json of the tool-call input), `assistant_text`, `user_text` (prompts, skill
  bodies), `attachment:<type>` (its `rendered` text; attachments without
  `rendered` count 0). `prompt_snapshot` is excluded — it copies the system
  prompt, already in the fixed prefix. Thinking blocks and images count 0.
* **Spawned agent** — a transcript whose first non-meta user message names
  `TASK_GUIDE_T<digits>`. Pre-edit reading = tool results received before the
  first `Edit`/`Write`/`MultiEdit` call; an agent that never edits reports its
  whole session as pre-edit (`edited: false`). Spawns with < 3 calls are listed
  but excluded from medians.
* **Counterfactual** (`--bash-lines N`) — every Bash stdout (`toolUseResult.stdout`;
  the tool_result text when that is absent) over N lines is replayed as first 40
  + error lines (cap 60) + last 60; the elided characters are the saving,
  carry-weighted. **Recall risk**: an elided line of >= 25
  characters appears in the agent's next 3 outputs (text + tool inputs).
* **Loud on drift** — malformed lines are skipped and counted; a file with
  assistant entries but no parseable usage is `unparsed` and listed by basename;
  if no API call parses at all the meter exits 2 naming the expected keys.

JSON (`--json`), stable keys
----------------------------
Directory mode::

    {"projects_dir": str,
     "prices": {"input_per_mtok": float, "output_per_mtok": float},
     "summary": {"transcripts", "main", "sub", "api_calls", "spend_usd",
                 "components": {"input"|"cache_write"|"cache_read"|"output":
                                {"usd", "share_pct"}},
                 "malformed_lines", "unparsed": [basename, ...]},
     "spawns": {"items": [{"transcript", "task", "calls", "spawn_prompt_chars",
                           "fixed_prefix_tokens", "pre_edit_tokens",
                           "calls_before_edit", "context_at_edit" (null if no edit),
                           "edited", "cost_usd", "pre_edit_carry_share_pct",
                           "in_medians"}],
                "median": {same numeric keys, over spawns with >= 3 calls} | null,
                "excluded_short": int},
     "counterfactual": null | {"bash_lines", "bash_outputs", "qualifying",
                               "saved_tokens", "saving_usd", "saving_share_pct",
                               "recall_risk", "recall_risk_pct"}}

Session mode (`--session PATH`)::

    {"prices": {...},
     "session": {"transcript", "calls", "spend_usd", "latest_context_tokens",
                 "composition": {kind: {"tokens", "carry_usd", "share_pct"}},
                 "malformed_lines"}}

Session mode adds `context_now` (context of the last call), `context_peak`,
`calls_over_150k` and `top_content_kinds` ([{"kind", "share_pct"}], top 3 by carry share).

`--current` (T126) analyses the running session: the most recently modified
top-level `*.jsonl` in `<root>/<slug>/`, `<slug>` = the absolute working directory
(`--cwd`, default cwd) with every `/` and `.` replaced by `-`. Newest-modified is a
heuristic — with two sessions open in one project it may pick the other one. Never
looks at other projects or at `subagents/`. Not found -> exit 2 naming the directory.

Exit codes: 0 ok; 2 no transcripts, no parseable API call, or bad arguments.
"""
import argparse
import json
import os
import re
import statistics
import sys

PRICE_IN_PER_MTOK = 5.0     # claude-opus-5, $ per million input tokens
PRICE_OUT_PER_MTOK = 25.0   # claude-opus-5, $ per million output tokens
WRITE_1H = 2.0
WRITE_5M = 1.25
READ = 0.1
CHARS_PER_TOKEN = 3.5

USAGE_KEYS = ("input_tokens", "output_tokens", "cache_read_input_tokens",
              "cache_creation_input_tokens")
EDIT_TOOLS = ("Edit", "Write", "MultiEdit")
EXCLUDED_ATTACHMENTS = ("prompt_snapshot",)
SPAWN_PATTERN = re.compile(r"TASK_GUIDE_(T\d+)")
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
ERROR_LINE = re.compile(r"error|fail|exception|traceback|fatal|panic", re.IGNORECASE)
KEEP_HEAD, KEEP_TAIL, ERROR_CAP = 40, 60, 60
RECALL_WINDOW, RECALL_MIN_CHARS = 3, 25
MIN_CALLS_FOR_MEDIAN = 3
REFERENCE_CONTEXT = 150_000
TOP_KINDS = 3


class Prices:
    def __init__(self, price_in, price_out):
        self.inp = price_in / 1e6
        self.out = price_out / 1e6


def safe_name(name):
    """Tool names and attachment types are printed; anything unexpected is not."""
    return name if isinstance(name, str) and SAFE_NAME.match(name) else "other"


def text_len(value):
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(text_len(item) for item in value)
    if isinstance(value, dict):
        if value.get("type") in ("image", "thinking", "redacted_thinking"):
            return 0
        return text_len(value.get("text", value.get("content")))
    return 0


def text_of(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(text_of(item) for item in value)
    if isinstance(value, dict):
        return text_of(value.get("text", value.get("content")))
    return ""


def parse_usage(usage):
    if not isinstance(usage, dict) or not all(isinstance(usage.get(k), int) for k in USAGE_KEYS):
        return None
    split = usage.get("cache_creation")
    if isinstance(split, dict):
        w1h = split.get("ephemeral_1h_input_tokens") or 0
        w5m = split.get("ephemeral_5m_input_tokens") or 0
    else:
        w1h, w5m = 0, usage["cache_creation_input_tokens"]
    return {"input": usage["input_tokens"], "w1h": w1h, "w5m": w5m,
            "read": usage["cache_read_input_tokens"], "output": usage["output_tokens"]}


def call_components(u, prices):
    return {"input": u["input"] * prices.inp,
            "cache_write": (WRITE_1H * u["w1h"] + WRITE_5M * u["w5m"]) * prices.inp,
            "cache_read": READ * u["read"] * prices.inp,
            "output": u["output"] * prices.out}


def compress_elided(lines):
    """Lines the rule would drop: all but head, tail and (capped) error lines."""
    middle = lines[KEEP_HEAD:len(lines) - KEEP_TAIL]
    kept_errors = 0
    elided = []
    for line in middle:
        if kept_errors < ERROR_CAP and ERROR_LINE.search(line):
            kept_errors += 1
        else:
            elided.append(line)
    return elided


class Transcript:
    """One streaming pass over one JSONL file."""

    def __init__(self, path, bash_lines=None):
        self.path = path
        self.basename = os.path.basename(path)
        self.malformed = 0
        self.assistant_entries = 0
        self.calls = []            # parsed usage dicts, in order
        self.call_ids = []
        self._index = {}           # message.id -> call index
        self.content = {}          # (kind, first_call_index) -> chars
        self.first_user_chars = None
        self.task = None
        self.pre_edit = {}         # first_call_index -> chars of tool results before first edit
        self.edited = False
        self.edit_call = None
        self.bash_outputs = 0
        self.bash_saved = {}       # first_call_index -> elided chars
        self.qualifying = 0
        self.recall_hits = 0
        self._pending = []         # [start_index, elided lines, hit]
        self._tool_names = {}
        self._bash_lines = bash_lines
        self._parse()

    def _add(self, kind, chars):
        if chars:
            key = (kind, len(self.calls))
            self.content[key] = self.content.get(key, 0) + chars

    def _parse(self):
        with open(self.path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    self.malformed += 1
                    continue
                if not isinstance(entry, dict):
                    self.malformed += 1
                    continue
                kind = entry.get("type")
                if kind == "assistant":
                    self._assistant(entry)
                elif kind == "user":
                    self._user(entry)
                elif kind == "attachment":
                    self._attachment(entry)
        for pending in self._pending:
            self.recall_hits += pending[2]

    def _assistant(self, entry):
        self.assistant_entries += 1
        message = entry.get("message")
        if not isinstance(message, dict):
            return
        usage = parse_usage(message.get("usage"))
        if usage is None:
            return
        mid = message.get("id")
        if mid is not None and mid in self._index:
            index = self._index[mid]
            self.calls[index] = usage
        else:
            index = len(self.calls)
            if mid is not None:
                self._index[mid] = index
            self.calls.append(usage)
            # an entry without an id is its own call, never merged (here or across files)
            self.call_ids.append(mid if mid is not None else (self.path, index))
        output_text = []
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                self._add("assistant_text", text_len(block.get("text")))
                output_text.append(text_of(block.get("text")))
            elif block.get("type") == "tool_use":
                serialized = json.dumps(block.get("input"))
                self._add("tool_input", len(serialized))
                output_text.append(serialized)
                self._tool_names[block.get("id")] = block.get("name")
                if block.get("name") in EDIT_TOOLS and not self.edited:
                    self.edited = True
                    self.edit_call = index
        self._check_recall(index, "\n".join(output_text))

    def _check_recall(self, index, output):
        if not output:
            return
        for pending in self._pending:
            start, elided, hit = pending
            if not hit and start <= index < start + RECALL_WINDOW:
                if any(line in output for line in elided):
                    pending[2] = 1
        self._pending = [p for p in self._pending if index < p[0] + RECALL_WINDOW or p[2]]

    def _user(self, entry):
        message = entry.get("message")
        if not isinstance(message, dict):
            return
        content = message.get("content")
        blocks = content if isinstance(content, list) else [content]
        user_chars = 0
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                self._tool_result(block, entry.get("toolUseResult"))
            else:
                user_chars += text_len(block)
        self._add("user_text", user_chars)
        if self.first_user_chars is None and user_chars and not entry.get("isMeta"):
            self.first_user_chars = user_chars
            match = SPAWN_PATTERN.search(text_of(content))
            self.task = match.group(1) if match else None

    def _tool_result(self, block, tool_use_result):
        name = self._tool_names.get(block.get("tool_use_id"))
        chars = text_len(block.get("content"))
        self._add("tool_result:" + safe_name(name), chars)
        if not self.edited and chars:
            index = len(self.calls)
            self.pre_edit[index] = self.pre_edit.get(index, 0) + chars
        if name == "Bash" and self._bash_lines is not None:
            stdout = tool_use_result.get("stdout") if isinstance(tool_use_result, dict) else None
            self._bash(stdout if isinstance(stdout, str) else text_of(block.get("content")))

    def _bash(self, output):
        self.bash_outputs += 1
        lines = output.split("\n")
        if len(lines) <= self._bash_lines:
            return
        self.qualifying += 1
        elided = compress_elided(lines)
        index = len(self.calls)
        self.bash_saved[index] = self.bash_saved.get(index, 0) + sum(len(l) + 1 for l in elided)
        quotable = {l.strip() for l in elided if len(l.strip()) >= RECALL_MIN_CHARS}
        self._pending.append([index, quotable, 0])

    def _attachment(self, entry):
        attachment = entry.get("attachment")
        atype = attachment.get("type") if isinstance(attachment, dict) else None
        if atype in EXCLUDED_ATTACHMENTS:
            return
        self._add("attachment:" + safe_name(atype), text_len(entry.get("rendered")))

    # --- derived numbers -------------------------------------------------------

    def cost(self, prices):
        return sum(sum(call_components(u, prices).values()) for u in self.calls)

    def carry(self, chars, index, prices):
        """$ carried by `chars` first sent at call `index` until the transcript ends."""
        if index >= len(self.calls):
            return 0.0
        u = self.calls[index]
        written = u["w1h"] + u["w5m"]
        rate = (WRITE_1H * u["w1h"] + WRITE_5M * u["w5m"]) / written if written else WRITE_1H
        reads = len(self.calls) - 1 - index
        return chars / CHARS_PER_TOKEN * prices.inp * (rate + READ * reads)

    def unparsed(self):
        return self.assistant_entries > 0 and not self.calls


def context_of(u):
    return u["input"] + u["w1h"] + u["w5m"] + u["read"]


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def find_transcripts(root):
    real_root = os.path.realpath(root)
    found = []
    for directory, subdirs, files in os.walk(real_root, followlinks=False):
        subdirs.sort()
        for name in sorted(files):
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(directory, name)
            if os.path.commonpath([os.path.realpath(path), real_root]) == real_root:
                found.append(path)
    return found


def default_root():
    config = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    base = config if config else os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "projects")


def current_transcript(root, cwd):
    directory = os.path.join(root, re.sub(r"[/.]", "-", os.path.abspath(cwd)))
    if not os.path.isdir(directory):
        fail("no session directory: looked in %s" % directory)
    files = [os.path.join(directory, n) for n in os.listdir(directory)
             if n.endswith(".jsonl") and os.path.isfile(os.path.join(directory, n))]
    if not files:
        fail("no top-level *.jsonl transcript in %s" % directory)
    return max(files, key=lambda f: (os.path.getmtime(f), f))


def spawn_row(t, prices):
    cost = t.cost(prices)
    carry = sum(t.carry(chars, index, prices) for index, chars in t.pre_edit.items())
    edit_call = t.edit_call if t.edited else None
    return {
        "transcript": t.basename,
        "task": t.task,
        "calls": len(t.calls),
        "spawn_prompt_chars": t.first_user_chars,
        "fixed_prefix_tokens": context_of(t.calls[0]),
        "pre_edit_tokens": round(sum(t.pre_edit.values()) / CHARS_PER_TOKEN),
        "calls_before_edit": edit_call if t.edited else len(t.calls),
        "context_at_edit": context_of(t.calls[edit_call]) if t.edited else None,
        "edited": t.edited,
        "cost_usd": cost,
        "pre_edit_carry_share_pct": pct(carry, cost),
        "in_medians": len(t.calls) >= MIN_CALLS_FOR_MEDIAN,
    }


MEDIAN_KEYS = ("calls", "spawn_prompt_chars", "fixed_prefix_tokens", "pre_edit_tokens",
               "calls_before_edit", "context_at_edit", "cost_usd", "pre_edit_carry_share_pct")


def medians(rows):
    rows = [r for r in rows if r["in_medians"]]
    if not rows:
        return None
    result = {}
    for key in MEDIAN_KEYS:
        values = [r[key] for r in rows if r[key] is not None]
        result[key] = statistics.median(values) if values else None
    return result


def analyse_directory(root, prices, task=None, bash_lines=None):
    paths = find_transcripts(root)
    if not paths:
        fail("no transcripts (*.jsonl) under %s" % root)
    transcripts = [Transcript(p, bash_lines) for p in paths]

    seen = set()
    components = {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    calls = 0
    for t in transcripts:
        for mid, u in zip(t.call_ids, t.calls):
            if mid in seen:
                continue
            seen.add(mid)
            calls += 1
            for key, value in call_components(u, prices).items():
                components[key] += value
    unparsed = sorted(t.basename for t in transcripts if t.unparsed())
    if calls == 0:
        fail("no parseable API call in %d transcript(s); expected assistant entries with "
             "message.usage {%s} — transcript format may have changed. Unparsed: %s"
             % (len(transcripts), ", ".join(USAGE_KEYS), ", ".join(unparsed) or "none"))
    spend = sum(components.values())
    sub = sum(1 for p in paths if os.sep + "subagents" + os.sep in p)

    spawn_rows = [spawn_row(t, prices) for t in transcripts if t.task and t.calls]
    if task:
        spawn_rows = [r for r in spawn_rows if r["task"] == task]

    counterfactual = None
    if bash_lines is not None:
        saved_chars = sum(sum(t.bash_saved.values()) for t in transcripts)
        saving = sum(t.carry(chars, index, prices)
                     for t in transcripts for index, chars in t.bash_saved.items())
        qualifying = sum(t.qualifying for t in transcripts)
        recall = sum(t.recall_hits for t in transcripts)
        counterfactual = {
            "bash_lines": bash_lines,
            "bash_outputs": sum(t.bash_outputs for t in transcripts),
            "qualifying": qualifying,
            "saved_tokens": round(saved_chars / CHARS_PER_TOKEN),
            "saving_usd": saving,
            "saving_share_pct": pct(saving, spend),
            "recall_risk": recall,
            "recall_risk_pct": pct(recall, qualifying),
        }

    return {
        "projects_dir": root,
        "summary": {
            "transcripts": len(transcripts),
            "main": len(transcripts) - sub,
            "sub": sub,
            "api_calls": calls,
            "spend_usd": spend,
            "components": {k: {"usd": v, "share_pct": pct(v, spend)} for k, v in components.items()},
            "malformed_lines": sum(t.malformed for t in transcripts),
            "unparsed": unparsed,
        },
        "spawns": {
            "items": spawn_rows,
            "median": medians(spawn_rows),
            "excluded_short": sum(1 for r in spawn_rows if not r["in_medians"]),
        },
        "counterfactual": counterfactual,
    }


def analyse_session(path, prices):
    if not os.path.isfile(path):
        fail("no such transcript: %s" % path)
    t = Transcript(path)
    if not t.calls:
        fail("no parseable API call in %s; expected assistant entries with message.usage {%s}"
             % (t.basename, ", ".join(USAGE_KEYS)))
    spend = t.cost(prices)
    composition = {}
    for (kind, index), chars in t.content.items():
        row = composition.setdefault(kind, {"tokens": 0.0, "carry_usd": 0.0, "share_pct": 0.0})
        row["tokens"] += chars / CHARS_PER_TOKEN
        row["carry_usd"] += t.carry(chars, index, prices)
    for row in composition.values():
        row["tokens"] = round(row["tokens"])
        row["share_pct"] = pct(row["carry_usd"], spend)
    ranked = sorted(composition.items(), key=lambda kv: -kv[1]["carry_usd"])
    return {"session": {
        "transcript": t.basename,
        "calls": len(t.calls),
        "spend_usd": spend,
        "latest_context_tokens": context_of(t.calls[-1]),
        "context_now": context_of(t.calls[-1]),
        "context_peak": max(context_of(u) for u in t.calls),
        "calls_over_150k": sum(1 for u in t.calls if context_of(u) > REFERENCE_CONTEXT),
        "top_content_kinds": [{"kind": k, "share_pct": row["share_pct"]}
                              for k, row in ranked[:TOP_KINDS]],
        "composition": dict(ranked),
        "malformed_lines": t.malformed,
    }}


# --- text rendering ---------------------------------------------------------------

def num(value):
    if value is None:
        return "-"
    if isinstance(value, float) and not value.is_integer():
        return "{:,.1f}".format(value)
    return "{:,}".format(int(value))


def render_directory(data):
    s = data["summary"]
    prices = data["prices"]
    out = ["token_meter - %d transcripts (%d main, %d sub) under %s"
           % (s["transcripts"], s["main"], s["sub"], data["projects_dir"]),
           "API calls: %s (de-duplicated by message.id) | malformed lines skipped: %d"
           % (num(s["api_calls"]), s["malformed_lines"]),
           "Spend (billed-equivalent @ $%g in / $%g out per MTok): $%.2f"
           % (prices["input_per_mtok"], prices["output_per_mtok"], s["spend_usd"])]
    for key, label in (("input", "input"), ("cache_write", "cache write"),
                       ("cache_read", "cache read"), ("output", "output")):
        c = s["components"][key]
        out.append("  %-12s $%10.2f  %5.1f%%" % (label, c["usd"], c["share_pct"]))
    out.append("Unparsed transcripts (assistant entries, no usage): %s"
               % (", ".join(s["unparsed"]) or "none"))

    sp = data["spawns"]
    out.append("")
    out.append("Spawned agents (first user message names TASK_GUIDE_Txxx): %d (%d with < %d calls, "
               "excluded from medians)" % (len(sp["items"]), sp["excluded_short"], MIN_CALLS_FOR_MEDIAN))
    if sp["items"]:
        header = ("task", "calls", "prompt_ch", "prefix_tok", "pre_edit_tok", "calls_pre",
                  "ctx_at_edit", "cost_$", "carry_%", "transcript")
        out.append("  %-6s %6s %10s %10s %12s %9s %11s %8s %7s  %s" % header)
        for r in sp["items"]:
            out.append("  %-6s %6s %10s %10s %12s %9s %11s %8.2f %7.1f  %s%s" % (
                r["task"], num(r["calls"]), num(r["spawn_prompt_chars"]),
                num(r["fixed_prefix_tokens"]), num(r["pre_edit_tokens"]),
                num(r["calls_before_edit"]), num(r["context_at_edit"]), r["cost_usd"],
                r["pre_edit_carry_share_pct"], r["transcript"],
                "" if r["edited"] else "  (no edit: whole session is pre-edit)"))
        m = sp["median"]
        if m:
            out.append("  %-6s %6s %10s %10s %12s %9s %11s %8.2f %7.1f" % (
                "median", num(m["calls"]), num(m["spawn_prompt_chars"]),
                num(m["fixed_prefix_tokens"]), num(m["pre_edit_tokens"]),
                num(m["calls_before_edit"]), num(m["context_at_edit"]), m["cost_usd"],
                m["pre_edit_carry_share_pct"]))

    cf = data["counterfactual"]
    if cf:
        out.append("")
        out.append("Counterfactual --bash-lines %d (keep first %d + error lines (cap %d) + last %d):"
                   % (cf["bash_lines"], KEEP_HEAD, ERROR_CAP, KEEP_TAIL))
        out.append("  Bash outputs: %s | qualifying: %s | elided: ~%s tokens"
                   % (num(cf["bash_outputs"]), num(cf["qualifying"]), num(cf["saved_tokens"])))
        out.append("  carry-weighted saving: $%.2f = %.2f%% of spend (upper bound, no compaction)"
                   % (cf["saving_usd"], cf["saving_share_pct"]))
        out.append("  recall risk: %d of %d (%.1f%%) - an elided line (>= %d chars) reappeared in "
                   "the next %d outputs" % (cf["recall_risk"], cf["qualifying"],
                                            cf["recall_risk_pct"], RECALL_MIN_CHARS, RECALL_WINDOW))
    return "\n".join(out)


def render_session(data):
    s = data["session"]
    out = ["token_meter --session %s" % s["transcript"],
           "context now: %s | peak: %s | calls over 150k: %s of %s | top: %s"
           % (num(s["context_now"]), num(s["context_peak"]), num(s["calls_over_150k"]),
              num(s["calls"]), ", ".join("%s %.0f%%" % (k["kind"], k["share_pct"])
                                         for k in s["top_content_kinds"]) or "-"),
           "API calls: %s | spend: $%.2f | latest context: %s tokens | malformed lines: %d"
           % (num(s["calls"]), s["spend_usd"], num(s["latest_context_tokens"]), s["malformed_lines"]),
           "Composition (carry-weighted share of this session's spend; prompt_snapshot excluded):",
           "  %-40s %10s %10s %7s" % ("kind", "tokens", "carry_$", "share")]
    for kind, row in s["composition"].items():
        out.append("  %-40s %10s %10.3f %6.1f%%" % (kind, num(row["tokens"]), row["carry_usd"],
                                                    row["share_pct"]))
    return "\n".join(out)


def fail(message):
    print("token_meter: " + message, file=sys.stderr)
    sys.exit(2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Token spend and agent focus from Claude Code "
                                                 "transcripts (aggregates only).")
    parser.add_argument("--projects-dir", help="transcript root (default: $CLAUDE_CONFIG_DIR/projects "
                                               "or ~/.claude/projects)")
    parser.add_argument("--session", help="report one transcript")
    parser.add_argument("--current", action="store_true",
                        help="report the running session (newest top-level transcript for --cwd)")
    parser.add_argument("--cwd", help="working directory whose session --current reports "
                                      "(default: cwd)")
    parser.add_argument("--task", help="only spawns for this task ID, e.g. T124")
    parser.add_argument("--bash-lines", type=int, help="replay the Bash compression rule at N lines")
    parser.add_argument("--price-in", type=float, default=PRICE_IN_PER_MTOK, help="$ per MTok input")
    parser.add_argument("--price-out", type=float, default=PRICE_OUT_PER_MTOK, help="$ per MTok output")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)
    if args.bash_lines is not None and args.bash_lines < 0:
        parser.error("--bash-lines must be >= 0")

    if args.current and args.session:
        parser.error("--current and --session are mutually exclusive")
    if args.cwd and not args.current:
        parser.error("--cwd only applies to --current")

    prices = Prices(args.price_in, args.price_out)
    price_info = {"input_per_mtok": args.price_in, "output_per_mtok": args.price_out}
    if args.session or args.current:
        path = args.session
        if args.current:
            root = args.projects_dir or default_root()
            path = current_transcript(root, args.cwd or os.getcwd())
        data = analyse_session(path, prices)
        data["prices"] = price_info
        render = render_session
    else:
        root = args.projects_dir or default_root()
        if not os.path.isdir(root):
            fail("no transcripts: %s is not a directory" % root)
        data = analyse_directory(root, prices, args.task, args.bash_lines)
        data["prices"] = price_info
        render = render_directory
    print(json.dumps(data, indent=2) if args.json else render(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
