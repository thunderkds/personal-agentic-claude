#!/usr/bin/env python3
"""Round 4 (T171): does the combined rule beat grep-only? Keep-or-drop decision.

    python3 scripts/bench_hybrid.py --yes          # real agents, both repos, costs tokens
    python3 scripts/bench_hybrid.py --analyze-only # rebuild the report from stored runs (free)

Methods (real agents, `claude -p`):
  grep_only  tools Grep, Glob, Read; the round-2/3 prompt.
  hybrid     the same tools + search_semantic + get_slice; the same prompt + ROUTING_RULE.
Every question of both repos is run 2 times per method, interleaved (q1 grep, q1 hybrid, ...).

The decision rule is PRE-REGISTERED (see `verdict`). Per question, d = hybrid - grep_only on the
mean of that method's runs; the 95% bootstrap CI resamples questions (10,000, seed 171).
KEEP / DROP / INCONCLUSIVE is computed by code; nothing here is tuned after a run.
Exit codes: 0 ok, 2 bad setup.
"""
import argparse
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_context_search as b  # noqa: E402

ROOT = b.ROOT
DATE = "2026-10-22"
OUT_MD = os.path.join(ROOT, "reports", f"context-search-hybrid-{DATE}.md")
OUT_JSON = os.path.join(ROOT, "reports", f"context-search-hybrid-{DATE}.json")
SPEND_JSON = os.path.join(ROOT, "reports", f"context-search-hybrid-{DATE}.spend.json")
CAP = 20.0
RUNS_PER_METHOD = 2
BOOT_N, BOOT_SEED = 10000, 171
METHODS = ("grep_only", "hybrid")
HYBRID_TOOLS = ["Grep", "Glob", "Read", "mcp__easy-context__search_semantic", "mcp__easy-context__get_slice"]
SEMANTIC = "mcp__easy-context__search_semantic"

ROUTING_RULE = ("How to search: use Grep/Glob and ranged Reads by default — for names, exact text, callers, "
                "a file and its tests, and checking that something does not exist. Use `search_semantic` first "
                "only for a question in plain words about intent, docs or decisions (\"where is X done\", "
                "\"why did we choose X\") when you have no good keyword; then confirm with a ranged Read.")

REPOS = {
    "this_repo": {"root": "/home/hungnguyenhuu/workspace/pets/personal-agentic-claude",
                  "questions": os.path.join(ROOT, "tests", "fixtures", "context_search_questions.json"),
                  "ignore": ("Ignore memory/event-trace/ and tasks/TASK_*_T171.md, tasks/TASK_*_T172.md: "
                             "they log this benchmark.")},
    "tapchat": {"root": "/home/hungnguyenhuu/workspace/project/beautifly/github/tapchat-apis",
                "questions": os.path.join(ROOT, "tests", "fixtures", "context_search_questions_tapchat.json"),
                "ignore": "Ignore dist/, coverage/, reports/ and node_modules/: they are build output, not source."},
}


# ---------------------------------------------------------------- commands and stream parsing

def hybrid_prompt(question, ignore):
    return b.agent_prompt(question).replace(b.PROMPT_IGNORE, ignore) + "\n\n" + ROUTING_RULE


def grep_prompt(question, ignore):
    return b.agent_prompt(question).replace(b.PROMPT_IGNORE, ignore)


def command(method, root, url=b.DEFAULT_URL):
    """`claude -p` argv; same flags as rounds 2-3, stream-json so tool calls are recorded."""
    base = ["claude", "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--setting-sources", "user", "--disable-slash-commands", "--strict-mcp-config",
            "--max-budget-usd", str(b.PER_RUN_BUDGET)]
    if method == "grep_only":
        return base + ["--tools", ",".join(b.OLD_TOOLS), "--allowedTools", ",".join(b.OLD_TOOLS)]
    mcp = {"mcpServers": {"easy-context": {"type": "http", "url": url, "headers": {"X-Easy-Context-Root": root}}}}
    return base + ["--mcp-config", json.dumps(mcp), "--tools", ",".join(b.OLD_TOOLS),
                   "--allowedTools", ",".join(HYBRID_TOOLS)]


def parse_stream(stdout, expected=()):
    """(result row, [tool names called in order]) from `stream-json --verbose` output."""
    tools, result = [], None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for block in (ev.get("message") or {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tools.append(block.get("name", ""))
        elif ev.get("type") == "result":
            result = ev
    if result is None:
        raise ValueError("no result event in stream")
    return b.parse_agent_json(json.dumps(result), list(expected)), tools


def run_one(method, repo, q, budget, url=b.DEFAULT_URL):
    cfg = REPOS[repo]
    budget.check()
    prompt = (hybrid_prompt if method == "hybrid" else grep_prompt)(q["question"], cfg["ignore"])
    try:
        done = subprocess.run(command(method, cfg["root"], url), input=prompt, cwd=cfg["root"],
                              capture_output=True, text=True, timeout=900)
        row, tools = parse_stream(done.stdout, q["expected_paths"])
    except (subprocess.SubprocessError, ValueError, OSError) as err:
        row = {"seconds": 0, "input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "tokens": 0,
               "cost": 0.0, "turns": None, "hit": 0, "error": True, "session_id": None, "answer": f"run failed: {err}"}
        tools = []
        print(f"  {repo} {q['id']} {method}: run failed: {err}", file=sys.stderr)
    row["correct"] = b.grade_answer(q, row["answer"]) if not row["error"] else 0
    row.update(repo=repo, qid=q["id"], kind=q["kind"], method=method, tools=tools)
    budget.add(row["cost"])
    return row


# ---------------------------------------------------------------- statistics

def per_question(runs, field):
    """{(repo, qid): {method: mean of field over that method's runs}}."""
    acc = {}
    for r in runs:
        acc.setdefault((r["repo"], r["qid"]), {}).setdefault(r["method"], []).append(r[field])
    return {k: {m: statistics.mean(v) for m, v in by.items()} for k, by in acc.items()}


def paired_diffs(runs, field, repo=None, kind=None):
    """d = hybrid - grep_only per question (questions with both methods)."""
    kinds = {(r["repo"], r["qid"]): r["kind"] for r in runs}
    out = []
    for key, by in per_question(runs, field).items():
        if "hybrid" in by and "grep_only" in by and (repo is None or key[0] == repo) \
                and (kind is None or kinds[key] == kind):
            out.append(by["hybrid"] - by["grep_only"])
    return out


def bootstrap_ci(values, n=BOOT_N, seed=BOOT_SEED):
    """(mean, lo, hi): mean and 95% percentile bootstrap CI, resampling the values."""
    if not values:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(values[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return (sum(values) / k, means[int(0.025 * n)], means[int(0.975 * n) - 1])


def correctness(runs):
    """{repo: {method: [correct runs, total runs]}}."""
    out = {}
    for r in runs:
        c = out.setdefault(r["repo"], {}).setdefault(r["method"], [0, 0])
        c[0] += r["correct"]
        c[1] += 1
    return out


def verdict(cost_ci, grep_mean_cost, corr):
    """PRE-REGISTERED rule. cost_ci = (mean, lo, hi) of pooled d for cost; corr = correctness().

    KEEP: hybrid correctness >= grep_only on both repos AND (pooled cost CI hi <= 0, OR hybrid strictly
          higher on at least one repo with pooled cost CI hi <= +10% of grep_only's mean cost).
    DROP: pooled cost CI lo > 0 AND hybrid not strictly higher on either repo.
    else INCONCLUSIVE (the lean is reported: the sign of the mean cost difference).
    """
    mean, lo, hi = cost_ci
    ge_all = all(v["hybrid"][0] >= v["grep_only"][0] for v in corr.values())
    strict_any = any(v["hybrid"][0] > v["grep_only"][0] for v in corr.values())
    if ge_all and (hi <= 0 or (strict_any and hi <= 0.10 * grep_mean_cost)):
        return "KEEP"
    if lo > 0 and not strict_any:
        return "DROP"
    return "INCONCLUSIVE (leans " + ("keep" if mean < 0 else "drop") + ")"


def route_adherence(runs):
    """{kind: [hybrid runs that called search_semantic, hybrid runs]}."""
    out = {}
    for r in runs:
        if r["method"] == "hybrid":
            c = out.setdefault(r["kind"], [0, 0])
            c[0] += int(SEMANTIC in r["tools"])
            c[1] += 1
    return out


def overhead(runs):
    """Hybrid runs that never called search_semantic vs grep_only on the same questions."""
    gq = per_question([r for r in runs if r["method"] == "grep_only"], "cost")
    plain = [r for r in runs if r["method"] == "hybrid" and SEMANTIC not in r["tools"]]
    pairs = [(r["cost"], gq[(r["repo"], r["qid"])]["grep_only"]) for r in plain if (r["repo"], r["qid"]) in gq]
    if not pairs:
        return {"n": 0}
    return {"n": len(pairs), "hybrid_mean": statistics.mean(p[0] for p in pairs),
            "grep_mean": statistics.mean(p[1] for p in pairs),
            "diff": statistics.mean(p[0] - p[1] for p in pairs)}


def analyze(runs):
    res = {"totals": {}, "paired": {}, "correctness": correctness(runs), "route": route_adherence(runs),
           "overhead": overhead(runs)}
    for repo in sorted({r["repo"] for r in runs}):
        res["totals"][repo] = {m: {"runs": sum(1 for r in runs if r["repo"] == repo and r["method"] == m),
                                   "cost": sum(r["cost"] for r in runs if r["repo"] == repo and r["method"] == m),
                                   "tokens": sum(r["tokens"] for r in runs if r["repo"] == repo and r["method"] == m)}
                               for m in METHODS}
    for field in ("cost", "tokens"):
        res["paired"][field] = {"pooled": bootstrap_ci(paired_diffs(runs, field))}
        for repo in res["totals"]:
            res["paired"][field][repo] = bootstrap_ci(paired_diffs(runs, field, repo=repo))
        kinds = [k for k in b.KIND_ORDER if paired_diffs(runs, field, kind=k)]
        res["paired"][field]["kinds"] = {k: bootstrap_ci(paired_diffs(runs, field, kind=k)) for k in kinds}
    gm = statistics.mean(v["grep_only"] for v in per_question(runs, "cost").values() if "grep_only" in v) if runs else 0
    res["grep_mean_cost"] = gm
    res["verdict"] = verdict(res["paired"]["cost"]["pooled"], gm, res["correctness"]) if runs else "INCONCLUSIVE"
    return res


# ---------------------------------------------------------------- report

def _ci(c, fmt):
    return f"{fmt.format(c[0])} [{fmt.format(c[1])}, {fmt.format(c[2])}]"


def render(a, extra=None):
    out = [f"# Round 4: hybrid vs grep-only (T171, {DATE})", "", f"**VERDICT: {a['verdict']}**", ""]
    out += ["Pre-registered rule: KEEP if hybrid correctness >= grep_only on both repos AND (pooled cost CI upper "
            "bound <= 0, OR hybrid strictly higher on one repo with the bound <= +10% of grep_only's mean cost). "
            "DROP if the pooled cost CI lower bound > 0 and hybrid is not strictly higher on either repo. "
            "Otherwise INCONCLUSIVE.", ""]
    out += ["## Totals per repo (all runs)", "", "| repo | method | runs | cost (USD) | tokens | correct |", "|---|---|---|---|---|---|"]
    for repo, by in a["totals"].items():
        for m in METHODS:
            c = a["correctness"][repo][m]
            out.append(f"| {repo} | {m} | {by[m]['runs']} | {by[m]['cost']:.3f} | {by[m]['tokens']} | {c[0]}/{c[1]} |")
    for field, fmt, label in (("cost", "{:+.4f}", "cost (USD)"), ("tokens", "{:+.0f}", "tokens")):
        p = a["paired"][field]
        out += ["", f"## Paired mean d = hybrid - grep_only, {label} per question (95% bootstrap CI, 10,000 resamples, seed 171)",
                "", "| scope | mean d [CI] |", "|---|---|", f"| pooled | {_ci(p['pooled'], fmt)} |"]
        out += [f"| {r} | {_ci(p[r], fmt)} |" for r in a["totals"]]
        out += [f"| kind: {k} | {_ci(v, fmt)} |" for k, v in p["kinds"].items()]
    out += ["", f"Mean grep_only cost per question: ${a['grep_mean_cost']:.4f}.", "",
            "## Route adherence (hybrid runs that called `search_semantic`)", "", "| kind | called / runs |", "|---|---|"]
    out += [f"| {k} | {v[0]}/{v[1]} ({100 * v[0] / v[1]:.0f}%) |" for k, v in a["route"].items() if v[1]]
    o = a["overhead"]
    out += ["", "## Fixed overhead of carrying the tools", ""]
    if o["n"]:
        out.append(f"{o['n']} hybrid runs never called `search_semantic`. They cost ${o['hybrid_mean']:.4f} on average against "
                   f"${o['grep_mean']:.4f} for grep_only on the same questions (difference {o['diff']:+.4f}).")
    else:
        out.append("Every hybrid run called `search_semantic`.")
    for line in (extra or []):
        out += ["", line]
    return "\n".join(out) + "\n"


def save(runs, extra=None):
    a = analyze(runs)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"date": DATE, "runs": runs, "analysis": a, "notes": extra or []}, fh, indent=1)
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write(render(a, extra))
    return a


def dump_runs(runs, notes):
    """Cheap checkpoint: raw runs only (the bootstrap runs at the end)."""
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"date": DATE, "runs": runs, "notes": notes}, fh)


def git_status(root):
    return subprocess.run(["git", "-C", root, "status", "--short"], capture_output=True, text=True).stdout


# ---------------------------------------------------------------- main

def key(r):
    return (r["repo"], r["qid"], r["method"], r["rep"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions per repo")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--rerun-errors", action="store_true", help="re-run runs that errored; keep the rest")
    args = ap.parse_args(argv)

    runs = []
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as fh:
            runs = json.load(fh)["runs"]
    notes = []
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as fh:
            notes = json.load(fh).get("notes", [])
    if args.analyze_only:
        save(runs, notes)
        print(f"Report: {OUT_MD}")
        return 0
    if not shutil.which("claude"):
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2
    if args.rerun_errors:
        runs = [r for r in runs if not r["error"]]
    done = {key(r) for r in runs}
    budget = b.Budget(args.cap, SPEND_JSON)
    total = sum(len(b.load_questions(c["questions"], args.limit)) for c in REPOS.values()) * 2 * RUNS_PER_METHOD
    print(f"Round 4: up to {total} `claude -p` runs; cap ${args.cap:.2f} (spent ${budget.spent:.2f}).")
    if not args.yes and input("Continue? [y/N] ").strip().lower() != "y":
        return 0
    before = git_status(REPOS["tapchat"]["root"])
    lock, aborted = threading.Lock(), []

    def work(repo):
        try:
            for q in b.load_questions(REPOS[repo]["questions"], args.limit):
                for rep in range(1, RUNS_PER_METHOD + 1):
                    for method in METHODS:
                        row_key = (repo, q["id"], method, rep)
                        if row_key in done:
                            continue
                        row = run_one(method, repo, q, budget)
                        row["rep"] = rep
                        with lock:
                            runs.append(row)
                            if len(runs) % 20 == 0:
                                dump_runs(runs, notes)
                                print(f"  {len(runs)} runs, ${budget.spent:.2f} spent", file=sys.stderr)
        except b.BudgetExceeded as err:
            aborted.append(f"{repo}: {err}")

    threads = [threading.Thread(target=work, args=(r,)) for r in REPOS]
    [t.start() for t in threads]
    [t.join() for t in threads]
    after = git_status(REPOS["tapchat"]["root"])
    notes = [n for n in notes if not n.startswith(("tapchat git status", "ABORT"))]
    notes.append(f"tapchat git status before: {before.strip() or '(clean)'!r}; after: {after.strip() or '(clean)'!r}; "
                 f"identical: {before == after}")
    notes += [f"ABORT {a}" for a in aborted]
    notes.append(f"Spend: ${budget.spent:.2f} over {budget.runs} runs (cap ${args.cap:.0f}).")
    a = save(runs, notes)
    print(f"VERDICT: {a['verdict']}\nSpent ${budget.spent:.2f}. Report: {OUT_MD}\nJSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
