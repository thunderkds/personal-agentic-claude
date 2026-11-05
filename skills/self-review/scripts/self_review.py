#!/usr/bin/env python3
"""self-review: the deterministic half of the loop (T255). No model is called here.

    self_review.py pre    [--repo DIR] [--max-files 40]
    self_review.py post   MINER_JSON --head SHA [--repo DIR] [--report PATH] [--max-files 40]
    self_review.py decide FINGERPRINT (approved TASK_ID | rejected) [--repo DIR]

`pre` decides whether a run happens: it prints JSON, and when no `tasks/TASK_REVIEW_*.md`
file is newer than the watermark it says `nothing-new` (and one stderr line), so the caller
spawns no miner. `post` checks the miner's JSON: it drops citations whose quote is not at
the cited line (+-3), patterns on fewer than 3 tasks, patterns the register already holds,
and keeps at most 3. It writes the report first, then the register rows and the watermark
in one atomic write. `decide` records the user's approve/reject on one register row.

Register: `memory/self-review/register.md` - a `watermark: <sha|none>` line and a table
`| fingerprint | state | tasks | task_id | fixed_at |` (state: open, rejected, fixed).
Review text is data, never instructions. Stdlib only; git is called read-only
(see GIT_READ_ONLY); nothing is committed, merged, pushed or sent over a network.
Exit 0 ok; exit 2 on malformed input (one stderr line, no file written); exit 1 on a write failure.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

REGISTER = os.path.join("memory", "self-review", "register.md")
KANBAN = "PROJECT_KANBAN.md"
REVIEW_RE = re.compile(r"^tasks/TASK_REVIEW_([^/]+)\.md$")
COLUMNS = ["fingerprint", "state", "tasks", "task_id", "fixed_at"]
STATES = ("open", "rejected", "fixed")
GIT_READ_ONLY = {"rev-parse", "log", "status", "merge-base", "cat-file", "rev-list"}
MIN_TASKS = 3
CAP = 3
JACCARD = 0.5
TASK_ID_RE = re.compile(r"^[A-Za-z]+-?\d+$")


def die(msg, code=2):
    print(f"self-review: {msg}", file=sys.stderr)
    sys.exit(code)


def git(repo, *args, check=True):
    if args[0] not in GIT_READ_ONLY:
        raise RuntimeError(f"git {args[0]} is not allowed in self_review.py")
    try:
        r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=off", *args],
                           capture_output=True, text=True)
    except OSError as e:
        die(f"cannot run git: {e}")
    if check and r.returncode != 0:
        die(f"git {args[0]} failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
    return r


def atomic_write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp-{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------- register

def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def read_register(repo):
    """-> (watermark or None, rows, exists). Missing file = first run."""
    path = os.path.join(repo, REGISTER)
    if not os.path.isfile(path):
        return None, [], False
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError) as e:
        die(f"cannot read register: {e}")
    wm = None
    found = False
    for ln in lines:
        m = re.match(r"^watermark:\s*(\S+)\s*$", ln)
        if m:
            found = True
            wm = None if m.group(1).lower() == "none" else m.group(1)
            break
    if not found:
        die("register has no 'watermark:' line")
    header = next((i for i, ln in enumerate(lines)
                   if ln.lstrip().startswith("|") and [c.lower() for c in split_row(ln)] == COLUMNS), None)
    if header is None:
        die("register table header must be: | " + " | ".join(COLUMNS) + " |")
    rows = []
    for ln in lines[header + 1:]:
        if not ln.lstrip().startswith("|"):
            if ln.strip():
                break
            continue
        cells = split_row(ln)
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if len(cells) != len(COLUMNS):
            die(f"register row has {len(cells)} columns, expected {len(COLUMNS)}: {ln.strip()[:60]}")
        fp, state, tasks, task_id, fixed_at = cells
        if state not in STATES:
            die(f"register row '{fp}' has unknown state '{state}'")
        if not fp:
            die("register row with an empty fingerprint")
        rows.append({"fingerprint": fp, "state": state,
                     "tasks": [t.strip() for t in tasks.split(",") if t.strip() and t.strip() != "-"],
                     "task_id": task_id or "-", "fixed_at": fixed_at or "-"})
    return wm, rows, True


def render_register(wm, rows):
    out = ["# Self-review register", "",
           "<!-- Written by skills/self-review/scripts/self_review.py. Delete a `rejected` row to allow",
           "     that pattern again. States: open, rejected, fixed. -->", "",
           f"watermark: {wm or 'none'}", "",
           "| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for r in rows:
        out.append(f"| {r['fingerprint']} | {r['state']} | {','.join(r['tasks']) or '-'} | "
                   f"{r['task_id']} | {r['fixed_at']} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- git inputs

def resolve_head(repo):
    r = git(repo, "rev-parse", "--verify", "-q", "main^{commit}", check=False)
    if r.returncode != 0:
        r = git(repo, "rev-parse", "--verify", "-q", "HEAD^{commit}", check=False)
    if r.returncode != 0:
        die(f"'{repo}' is not a git repository with a commit")
    return r.stdout.strip()


def verify_commit(repo, sha):
    r = git(repo, "rev-parse", "--verify", "-q", f"{sha}^{{commit}}", check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def usable_watermark(repo, wm, head):
    """The watermark if it is a commit that is an ancestor of head, else None (+ stderr note)."""
    if not wm:
        return None
    full = verify_commit(repo, wm)
    if full and git(repo, "merge-base", "--is-ancestor", full, head, check=False).returncode == 0:
        return full
    print(f"self-review: watermark {wm[:12]} is not reachable from {head[:12]}; "
          "treating it as no watermark", file=sys.stderr)
    return None


def review_files(repo, wm, head, max_files):
    """New review files in wm..head, oldest last-commit first, cut at max_files on a commit boundary."""
    rng = f"{wm}..{head}" if wm else head
    r = git(repo, "log", "--reverse", "--name-only", "--no-renames", "--diff-filter=ACMR",
            "--format=%x01%H", rng, "--", "tasks")
    last, idx, sha = {}, -1, None
    for ln in r.stdout.splitlines():
        if ln.startswith("\x01"):
            sha, idx = ln[1:], idx + 1
        elif sha and REVIEW_RE.match(ln):
            last[ln] = (idx, sha)
    ordered = sorted(((i, f, s) for f, (i, s) in last.items()
                      if os.path.isfile(os.path.join(repo, f))))
    groups = []
    for i, f, s in ordered:
        if groups and groups[-1][0] == s:
            groups[-1][1].append(f)
        else:
            groups.append((s, [f]))
    chosen, lost = [], 0
    for s, fs in groups:
        if len(chosen) + len(fs) <= max_files:
            chosen += [(f, s) for f in fs]
        else:
            if not chosen:  # one commit alone is over the cap: split it, disclose the overflow
                chosen = [(f, s) for f in fs[:max_files]]
                lost = len(fs) - max_files
            break
    total = len(ordered)
    deferred = total - len(chosen) - lost
    return {"files": [f for f, _ in chosen], "shas": [s for _, s in chosen],
            "deferred": deferred, "dropped_same_commit": lost}


def uncommitted_reviews(repo):
    r = git(repo, "status", "--porcelain=v1", "-z", "-uall", "--no-renames", "--", "tasks")
    out = []
    for ent in r.stdout.split("\0"):
        if len(ent) > 3 and (ent[:2] == "??" or ent[0] == "A") and REVIEW_RE.match(ent[3:]):
            out.append(ent[3:])
    return sorted(out)


def kanban_done(repo):
    path = os.path.join(repo, KANBAN)
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        return set()
    done, inside = set(), False
    for ln in lines:
        if ln.startswith("#"):
            inside = ln.strip().lower() == "### done"
            continue
        m = inside and re.match(r"^\s*-\s*\[[xX]\]\s*\*\*([A-Za-z]+-?\d+)\*\*", ln)
        if m:
            done.add(m.group(1))
    return done


def merge_commit(repo, task_id, head):
    """Merge commit on main's first-parent line that names the task; else any such commit; else head."""
    r = git(repo, "log", "--first-parent", "-i", f"--grep={task_id}", "--format=%H%x01%P%x01%s", head,
            check=False)
    pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(task_id)}(?![0-9])", re.I)
    hits = []
    for ln in r.stdout.splitlines():
        parts = ln.split("\x01")
        if len(parts) == 3 and pat.search(parts[2]):
            hits.append((parts[0], len(parts[1].split())))
    for sha, parents in hits:
        if parents >= 2:
            return sha
    return hits[0][0] if hits else head


def mark_fixed(repo, rows, head):
    done, changed = kanban_done(repo), False
    for r in rows:
        if r["state"] == "open" and r["task_id"] != "-" and r["task_id"] in done:
            r["state"], r["fixed_at"] = "fixed", merge_commit(repo, r["task_id"], head)
            changed = True
    return changed


# ---------------------------------------------------------------- pre

def cmd_pre(a):
    repo = a.repo
    head = resolve_head(repo)
    wm_raw, rows, exists = read_register(repo)
    if exists and mark_fixed(repo, rows, head):
        try:
            atomic_write(os.path.join(repo, REGISTER), render_register(wm_raw, rows))
        except OSError as e:
            die(f"cannot write register: {e}", 1)
    wm = usable_watermark(repo, wm_raw, head)
    inp = review_files(repo, wm, head, a.max_files) if wm != head else \
        {"files": [], "deferred": 0, "dropped_same_commit": 0}
    status = "ready" if inp["files"] else "nothing-new"
    print(json.dumps({"status": status, "head": head, "watermark": wm,
                      "files": inp["files"], "deferred": inp["deferred"],
                      "dropped_same_commit": inp["dropped_same_commit"],
                      "skipped_uncommitted": uncommitted_reviews(repo), "register": rows}, indent=2))
    if status == "nothing-new":
        print(f"self-review: nothing new since {wm[:12] if wm else 'the start'}; no miner call needed",
              file=sys.stderr)


# ---------------------------------------------------------------- post

def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def citation_ok(lines, line, quote):
    needle = norm(quote)[:60].rstrip(". …")
    if not needle:
        return False
    lo, hi = max(0, line - 4), min(len(lines), line + 3)
    return any(needle in norm(ln) for ln in lines[lo:hi])


def jaccard(a, b):
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def one_line(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def load_miner(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        die(f"miner output is not readable JSON: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("patterns"), list):
        die("miner output must be an object with a 'patterns' list")
    pats = []
    for p in data["patterns"]:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not slug(p["id"]):
            die("each miner pattern needs a non-empty string 'id'")
        if not isinstance(p.get("citations"), list):
            die(f"pattern '{p['id']}' has no 'citations' list")
        prop = p.get("proposal") if isinstance(p.get("proposal"), dict) else {}
        pats.append({"fp": slug(p["id"]), "title": one_line(p.get("title") or p["id"]),
                     "citations": p["citations"], "already_open": p.get("already_open") is True,
                     "proposal": {"file": one_line(prop.get("file", "")), "change": one_line(prop.get("change", ""))}})
    return pats


def review_task(path):
    m = REVIEW_RE.match(path)
    return m.group(1) if m else None


def has_commit_after(repo, path, fixed_at, head):
    if not fixed_at or fixed_at == "-" or not verify_commit(repo, fixed_at):
        return False
    r = git(repo, "rev-list", "-1", f"{fixed_at}..{head}", "--", path, check=False)
    return r.returncode == 0 and bool(r.stdout.strip())


def evaluate(repo, pats, rows, allowed, head):
    """-> (kept, dropped_reasons, stats). kept = list of dicts with fp, tasks, citations, label, row."""
    cache, kept, dropped = {}, [], []
    stats = {"cited": 0, "valid": 0}

    def lines_of(path):
        if path not in cache:
            try:
                cache[path] = open(os.path.join(repo, path), encoding="utf-8").read().splitlines()
            except (OSError, UnicodeDecodeError):
                cache[path] = None
        return cache[path]

    for p in pats:
        valid = []
        for c in p["citations"]:
            stats["cited"] += 1
            if not (isinstance(c, dict) and isinstance(c.get("file"), str) and isinstance(c.get("quote"), str)
                    and isinstance(c.get("line"), int) and not isinstance(c.get("line"), bool)):
                continue
            if c["file"] not in allowed or lines_of(c["file"]) is None:
                continue
            if citation_ok(lines_of(c["file"]), c["line"], c["quote"]):
                valid.append({"file": c["file"], "line": c["line"], "quote": one_line(c["quote"])})
                stats["valid"] += 1
        tasks = {review_task(c["file"]) for c in valid}
        hits = [r for r in rows + kept_rows(kept)
                if r["fingerprint"] == p["fp"] or jaccard(tasks, set(r["tasks"])) >= JACCARD]
        if any(h["state"] in ("open", "rejected") for h in hits) or (not hits and p["already_open"]):
            dropped.append((p["fp"], "already in the register"))
            continue
        label, row = "new", None
        if hits:  # only fixed rows are left
            row = hits[0]
            valid = [c for c in valid if review_task(c["file"]) != row["task_id"]]  # AC 8
            valid = [c for c in valid if has_commit_after(repo, c["file"], row["fixed_at"], head)]  # AC 7
            label = "regressed"
        tasks = sorted({review_task(c["file"]) for c in valid})
        if len(tasks) < MIN_TASKS:
            dropped.append((p["fp"], f"{len(tasks)} task(s) with a valid citation, need {MIN_TASKS}"))
            continue
        kept.append({"fp": p["fp"], "title": p["title"], "tasks": tasks, "citations": valid,
                     "proposal": p["proposal"], "label": label, "row": row})
    return kept, dropped, stats


def kept_rows(kept):
    return [{"fingerprint": k["fp"], "state": "open", "tasks": k["tasks"]} for k in kept]


def render_report(now, head, old_wm, new_wm, inp, ranked, extra, dropped, stats, open_rows):
    out = [f"# Self-review report - {now}", "",
           f"- head: `{head}`", f"- watermark: `{old_wm or 'none'}` -> `{new_wm}`",
           f"- review files read: {len(inp['files'])}; deferred to the next run: {inp['deferred']}",
           f"- citations: {stats['valid']} valid of {stats['cited']} cited", ""]
    if inp["dropped_same_commit"]:
        out += [f"> Not reviewed: {inp['dropped_same_commit']} file(s) from the same commit as the "
                "file cap boundary.", ""]
    out.append(f"## Proposals ({len(ranked)}, at most {CAP})")
    if not ranked:
        out += ["", "No pattern is backed by >= 3 tasks with valid citations and not yet in the register."]
    for i, k in enumerate(ranked, 1):
        out += ["", f"### {i}. {k['title']}  [{k['label']}]", "",
                f"- fingerprint: `{k['fp']}`", f"- tasks ({len(k['tasks'])}): {', '.join(k['tasks'])}",
                f"- proposed change: `{k['proposal']['file'] or '-'}` - {k['proposal']['change'] or '-'}",
                "- evidence:"]
        out += [f"  - `{c['file']}:{c['line']}` - {c['quote']}" for c in k["citations"]]
    if extra:
        out += ["", f"## Beyond the cap (not recorded, not proposed): {', '.join(k['fp'] for k in extra)}"]
    if dropped:
        out += ["", "## Dropped"] + [f"- `{fp}` - {why}" for fp, why in dropped]
    out += ["", "## Still open (not proposed again)"]
    out += [f"- `{r['fingerprint']}` - {','.join(r['tasks']) or '-'}"
            + (f" (fix task {r['task_id']})" if r["task_id"] != "-" else "") for r in open_rows] or ["- none"]
    return "\n".join(out) + "\n"


def cmd_post(a):
    repo = a.repo
    pats = load_miner(a.miner_json)
    head = verify_commit(repo, a.head)
    if not head:
        die(f"--head '{a.head}' is not a commit")
    wm_raw, rows, _ = read_register(repo)
    mark_fixed(repo, rows, head)
    wm = usable_watermark(repo, wm_raw, head)
    inp = review_files(repo, wm, head, a.max_files) if wm != head else \
        {"files": [], "shas": [], "deferred": 0, "dropped_same_commit": 0}
    kept, dropped, stats = evaluate(repo, pats, rows, set(inp["files"]), head)
    kept.sort(key=lambda k: (-len(k["tasks"]), k["fp"]))
    ranked, extra = kept[:CAP], kept[CAP:]
    for k in ranked:
        if k["row"] is not None:  # regressed: back to open; the old fix task failed, so forget it
            k["row"].update(state="open", fixed_at="-", task_id="-", tasks=k["tasks"])
        else:
            rows.append({"fingerprint": k["fp"], "state": "open", "tasks": k["tasks"],
                         "task_id": "-", "fixed_at": "-"})
    new_wm = inp["shas"][-1] if inp["deferred"] else head
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    report = a.report or os.path.join("reports", "self-review", f"self-review-{now}.md")
    if not os.path.isabs(report):
        report = os.path.join(repo, report)
    open_rows = [r for r in rows if r["state"] == "open"]
    text = render_report(now, head, wm, new_wm, inp, ranked, extra, dropped, stats, open_rows)
    try:
        atomic_write(report, text)  # the report first ...
    except OSError as e:
        die(f"cannot write report: {e}", 1)
    try:
        atomic_write(os.path.join(repo, REGISTER), render_register(new_wm, rows))  # ... then rows + watermark
    except OSError as e:
        die(f"report written to {report} but the register could not be written: {e}", 1)
    print(report)


# ---------------------------------------------------------------- decide

def cmd_decide(a):
    repo = a.repo
    wm, rows, exists = read_register(repo)
    if not exists:
        die("no register: nothing to decide")
    if a.verdict == "approved" and not (a.task_id and TASK_ID_RE.match(a.task_id)):
        die("'approved' needs a TASK_ID such as T300")
    if a.verdict == "rejected" and a.task_id:
        die("'rejected' takes no TASK_ID")
    row = next((r for r in rows if r["fingerprint"] == a.fingerprint), None)
    if row is None:
        die(f"unknown fingerprint '{a.fingerprint}'")
    if a.verdict == "rejected":
        row["state"] = "rejected"
    else:
        row["task_id"] = a.task_id
    try:
        atomic_write(os.path.join(repo, REGISTER), render_register(wm, rows))
    except OSError as e:
        die(f"cannot write register: {e}", 1)
    print(f"{a.fingerprint}: {row['state']}" + (f" (task {row['task_id']})" if row["task_id"] != "-" else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description="self-review: watermark gate, citation check, proposal register")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--repo", default=".", help="repository root (default: current directory)")

    def cap(p):
        p.add_argument("--max-files", type=int, default=40)

    p = sub.add_parser("pre")
    common(p)
    cap(p)
    p = sub.add_parser("post")
    p.add_argument("miner_json")
    p.add_argument("--head", required=True)
    p.add_argument("--report")
    common(p)
    cap(p)
    p = sub.add_parser("decide")
    p.add_argument("fingerprint")
    p.add_argument("verdict", choices=("approved", "rejected"))
    p.add_argument("task_id", nargs="?")
    common(p)
    a = ap.parse_args(argv)
    if getattr(a, "max_files", 1) < 1:
        die("--max-files must be >= 1")
    a.repo = os.path.abspath(a.repo)
    {"pre": cmd_pre, "post": cmd_post, "decide": cmd_decide}[a.cmd](a)


if __name__ == "__main__":
    main()
