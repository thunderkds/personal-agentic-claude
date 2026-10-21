# TASK_REVIEW — T171: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T171.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_bench_context_search.py` (17 tests: hit@k rank 3 -> hit@1=0/hit@5=1, `./a/b` normalisation, grep ranking, zero-match grep, token estimate, SSE parse + session id against a fake server, report rendering, closed port exit 2, `claude` missing exit 2, live test skips when server down). Fixture `tests/fixtures/context_search_questions.json` (19 questions: 8 conceptual, 7 symbol, 4 doc). Output: `17 passed in 0.82s` |
| Verification command run | pass | `python3 -m pytest tests/test_bench_context_search.py -q` -> 17 passed; `python3 scripts/bench_context_search.py` -> report written, 19 questions, both rows each; `--agent --limit 5 --yes` -> 10 runs with real usage and cost. Reports pasted below. |
| Negative cases hold | pass | closed port -> exit 2 + `easy-context server not reachable at http://127.0.0.1:1/mcp`; no `claude` on PATH -> exit 2 |
| verify | pass | script mode and real-agent mode ran end to end against the live server and the real CLI; full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> 1426 passed, 25 subtests passed |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | New files only, plus a one-line `.gitignore` negation so the report can be committed. No hub file touched. |
| Full smoke suite still green (no regression) | pass | 1426 passed, 25 subtests passed |
| **UI: Visual regression (diff or verdict pasted)** | N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | no UI |
| **UI: Responsiveness at target viewports** | N/A | no UI |

### Generated report (`reports/context-search-benchmark-2026-10-21.md`)

# easy-context search vs grep + Read: benchmark (T171)


<!-- section:script -->
## Script mode

| id | kind | ctx s | old s | ctx hit@1 | old hit@1 | ctx hit@5 | old hit@5 | ctx tok (est) | old tok (est) |
|---|---|---|---|---|---|---|---|---|---|
| c01 | conceptual | 0.115 | 0.021 | 0 | 0 | 1 | 0 | 1412 | 461121 |
| c02 | conceptual | 0.182 | 0.011 | 0 | 0 | 0 | 1 | 1840 | 8790 |
| c03 | conceptual | 0.183 | 0.022 | 0 | 0 | 0 | 1 | 2073 | 9914 |
| c04 | conceptual | 0.131 | 0.019 | 0 | 0 | 0 | 1 | 1702 | 40670 |
| c05 | conceptual | 0.117 | 0.014 | 0 | 0 | 0 | 0 | 2186 | 41973 |
| c06 | conceptual | 0.141 | 0.020 | 0 | 0 | 1 | 0 | 2211 | 14966 |
| c07 | conceptual | 0.115 | 0.014 | 0 | 0 | 1 | 0 | 915 | 6445 |
| c08 | conceptual | 0.137 | 0.015 | 0 | 1 | 0 | 1 | 1590 | 23305 |
| s01 | symbol | 0.129 | 0.020 | 0 | 0 | 0 | 0 | 921 | 423980 |
| s02 | symbol | 0.127 | 0.012 | 1 | 1 | 1 | 1 | 1261 | 1422 |
| s03 | symbol | 0.148 | 0.012 | 1 | 0 | 1 | 1 | 1045 | 4250 |
| s04 | symbol | 0.106 | 0.013 | 1 | 1 | 1 | 1 | 1542 | 2969 |
| s05 | symbol | 0.160 | 0.010 | 0 | 1 | 1 | 1 | 3028 | 6902 |
| s06 | symbol | 0.114 | 0.010 | 0 | 0 | 0 | 0 | 1089 | 6869 |
| s07 | symbol | 0.149 | 0.011 | 1 | 0 | 1 | 1 | 1385 | 4089 |
| d01 | doc | 0.121 | 0.011 | 1 | 1 | 1 | 1 | 1777 | 1373 |
| d02 | doc | 0.142 | 0.015 | 0 | 0 | 1 | 0 | 2276 | 46632 |
| d03 | doc | 0.118 | 0.016 | 1 | 0 | 1 | 0 | 1768 | 461226 |
| d04 | doc | 0.135 | 0.011 | 1 | 0 | 1 | 1 | 2119 | 5188 |

| method | median time (s) | hit@1 | hit@5 | total tokens (est) |
|---|---|---|---|---|
| context (search_semantic + get_slice) | 0.131 | 7/19 | 12/19 | 32140 |
| old (grep + Read) | 0.014 | 5/19 | 11/19 | 1572084 |

**Verdict.** Over 19 questions the context way found the expected file first 7 times and in the top 5 12 times; the old way 5 and 11. The context way was slower (median 0.131s vs 0.014s) and returned 32140 estimated tokens against 1572084 (48.9x the old way's). Tokens are chars / 4, an estimate.
<!-- /section:script -->

<!-- section:agent -->
## Real-agent mode (claude -p)

| id | ctx s | old s | ctx tokens | old tokens | ctx $ | old $ | ctx hit | old hit |
|---|---|---|---|---|---|---|---|---|
| c01 | 7.9 | 7.4 | 25583 | 20599 | 0.0578 | 0.0334 | 1 | 1 |
| c02 | 14.3 | 18.8 | 55435 | 28505 | 0.1141 | 0.0473 | 1 | 1 |
| c03 | 7.0 | 10.7 | 16354 | 27984 | 0.0574 | 0.0401 | 1 | 1 |
| c04 | 8.2 | 8.5 | 16432 | 29375 | 0.0588 | 0.0415 | 1 | 1 |
| c05 | 7.0 | 7.8 | 26560 | 23164 | 0.0641 | 0.0479 | 1 | 1 |

| method | median time (s) | answers naming an expected path | total tokens (real) | total cost (USD) |
|---|---|---|---|---|
| context agent (easy-context tools only) | 7.9 | 5/5 | 140364 | 0.352 |
| old agent (Grep, Glob, Read only) | 8.5 | 5/5 | 129627 | 0.210 |

**Verdict.** Over 5 questions the context agent named an expected path 5 times and the grep+Read agent 5 times. Median time 7.9s vs 8.5s; total tokens 140364 vs 129627; total cost $0.352 vs $0.210. Both runs carry the same fixed prompt overhead, so compare the difference, not the absolute size.
<!-- /section:agent -->


---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured before any implementation commit.

```
2026-10-21T10:52:47Z
$ ls scripts/bench_context_search.py tests/fixtures/context_search_questions.json tests/test_bench_context_search.py
ls: cannot access 'scripts/bench_context_search.py': No such file or directory
ls: cannot access 'tests/fixtures/context_search_questions.json': No such file or directory
ls: cannot access 'tests/test_bench_context_search.py': No such file or directory
$ python3 scripts/bench_context_search.py
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t171/scripts/bench_context_search.py': [Errno 2] No such file or directory
exit=2
```

**AFTER**:

```
2026-10-21T10:59:02Z
scripts/bench_context_search.py
tests/fixtures/context_search_questions.json
tests/test_bench_context_search.py
.................                                                        [100%]
17 passed in 0.95s
```

Script mode summary (from the report above): context 7/19 hit@1, 12/19 hit@5, median 0.131s, ~32k est. tokens; old way 5/19, 11/19, median 0.014s, ~1.57M est. tokens. Real-agent (5 questions): 5/5 vs 5/5 correct, 140,364 vs 129,627 real tokens, $0.352 vs $0.210.

**DELTA**: A maintainer can now run one command and get time, correctness and token numbers comparing easy-context search with grep + Read on 19 fixed questions, plus a 5-question real-agent comparison.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T171.jsonl`, never the
implementing agent alone]

---

## Round 2 evidence (R1-R7, amendment of 2026-10-21)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_bench_context_search.py`: 31 tests incl. multi_hop all-needed scoring, negative scoring, bounded old way (window + 50-line cap), budget abort, lifecycle record parsing and wait logic, spread, regrade, upkeep probe leaves checkout clean. Output: `31 passed in 0.80s` |
| Verification command run | pass | `python3 scripts/bench_context_search.py` (script, 39 questions, 3 methods); `--upkeep`; `--agent --yes` ($4.81, 108 runs); `--lifecycle --yes` (32 runs, $1.99; cumulative $6.80, cap $12); `--regrade` (free). Report and JSON below / in `reports/`. |
| Negative cases hold | pass | cap check refuses a run that would pass the cap (unit test); main checkout `git status --short` identical before and after `--upkeep` (probe file `zz_staleness_probe.md` created, edited, removed); touching used mtime only |
| verify | pass | all four modes ran end to end against the live server and CLI; full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> 1440 passed, 25 subtests passed |
| Full smoke suite still green (no regression) | pass | 1440 passed, 25 subtests passed |

Grading note: `negative` agent answers were first graded by a heuristic that also rejected any file path in the answer; it marked "NOT FOUND ... the closest file is X, unrelated" wrong. After seeing 3 such answers the rule became "the answer opens with NOT FOUND" (the instruction the agents were given), applied to every row with `--regrade`, no new runs. Before the change: context 36/39, old 38/39; after: 38/39 and 39/39.

Other caveats: `memory/event-trace/` is excluded from the grep methods and the agent prompt tells both agents to ignore it, because that log quotes every benchmark question. The `new untracked file` and `touch` probes ran against the main checkout's index only. The lifecycle chains ran in parallel, so they share one prompt prefix and keep the prompt cache warm: the "after cache expiry" rows cannot show a true expiry.

### Generated report (per-question rows omitted here; all rows are in `reports/context-search-benchmark-2026-10-21.md` and `.json`)

# easy-context search vs grep + Read: benchmark (T171, 2026-10-21)

## Recommendation

On 34 scored questions in script mode, the context way hit@5 16/34 against 28/39 (grep + whole-file Read) and 28/39 (bounded grep + ranged Read). Estimated tokens: 62103 vs 365769 vs 37332; median time 0.119s vs 0.010s vs 0.010s. With real agents the context agent was right 38/39 times and the grep+Read agent 39/39; total tokens 1097720 vs 792769, cost $2.72 vs $1.34, median time 8.0s vs 8.4s. Grep + Read was more accurate on: exact_text. Upkeep: a full re-index takes 6.7s and an incremental one 0.2s for 10 touched files; after an edit, search returned the old text until the file was re-indexed. Recommendation: use Grep/Glob/Read by default, with ranged reads, because it was as accurate and cheaper overall. Reach for context search first only when you have no keyword to grep - a natural-language question about intent or a decision. By real-agent tokens, context search was cheaper and at least as accurate on: symbol, doc; grep + Read was cheaper or more accurate on: conceptual, multi_hop, exact_text, callers, negative. Session lifecycle: context: Q2 cost $0.078 resumed in the same session vs $0.071 in a closed + fresh one (cache_creation 2080 vs 7722 tokens); old: Q2 cost $0.061 resumed in the same session vs $0.047 in a closed + fresh one (cache_creation 1171 vs 4050 tokens). A resume after the 5-minute cache window still read most of its prompt from cache, so the cache did not visibly expire; parallel chains share one prompt prefix and keep it warm, which this test cannot separate from expiry.

Real-agent spend this round: **$6.80** over 142 `claude -p` runs (cap $12).

## Script mode

| id | kind | ctx s | old s | bnd s | ctx h1 | old h1 | bnd h1 | ctx h5 | old h5 | bnd h5 | ctx tok | old tok | bnd tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Tokens are estimated (chars / 4). h1 / h5 = hit@1 / hit@5. n/a = not scored (semantic search on a negative question always returns hits; agent mode grades it).

| method | median time (s) | hit@1 | hit@5 | total tokens (est) |
|---|---|---|---|---|
| context (search_semantic + get_slice) | 0.119 | 7/34 | 16/34 | 62103 |
| old (grep -n + Read whole top file) | 0.010 | 15/39 | 28/39 | 365769 |
| old, bounded (file list capped 50 + Read +-40 lines) | 0.010 | 15/39 | 28/39 | 37332 |

**Accuracy per question kind (script mode, hit@1 / hit@5)**

| kind | n | context | old | old, bounded |
|---|---|---|---|---|
| conceptual | 8 | 0/8 , 3/8 | 1/8 , 4/8 | 1/8 , 4/8 |
| symbol | 7 | 4/7 , 5/7 | 5/7 , 5/7 | 5/7 , 5/7 |
| doc | 4 | 3/4 , 4/4 | 1/4 , 2/4 | 1/4 , 2/4 |
| multi_hop | 5 | 0/5 , 1/5 | 0/5 , 2/5 | 0/5 , 2/5 |
| exact_text | 5 | 0/5 , 3/5 | 3/5 , 5/5 | 3/5 , 5/5 |
| callers | 5 | 0/5 , 0/5 | 0/5 , 5/5 | 0/5 , 5/5 |
| negative | 5 | n/a | 5/5 , 5/5 | 5/5 , 5/5 |

## Real-agent mode (claude -p)

| id | kind | ctx s | old s | ctx tokens | old tokens | ctx $ | old $ | ctx ok | old ok |
|---|---|---|---|---|---|---|---|---|---|

| method | median time (s) | correct | total tokens (real) | total cost (USD) |
|---|---|---|---|---|
| context agent (easy-context tools only) | 8.0 | 38/39 | 1097720 | 2.718 |
| old agent (Grep, Glob, Read only) | 8.4 | 39/39 | 792769 | 1.344 |

**Correctness and cost per question kind (real agents)**

| kind | n | ctx correct | old correct | ctx tokens | old tokens | ctx $ | old $ |
|---|---|---|---|---|---|---|---|
| conceptual | 8 | 8/8 | 8/8 | 215617 | 203232 | 0.586 | 0.382 |
| symbol | 7 | 7/7 | 7/7 | 122425 | 136114 | 0.321 | 0.225 |
| doc | 4 | 4/4 | 4/4 | 63340 | 100971 | 0.205 | 0.177 |
| multi_hop | 5 | 5/5 | 5/5 | 183412 | 89657 | 0.411 | 0.161 |
| exact_text | 5 | 4/5 | 5/5 | 160241 | 87679 | 0.393 | 0.156 |
| callers | 5 | 5/5 | 5/5 | 234309 | 63409 | 0.478 | 0.099 |
| negative | 5 | 5/5 | 5/5 | 118376 | 111707 | 0.325 | 0.143 |

**Run-to-run spread (3 repeats per method; min / median / max)**

| question | method | tokens | cost (USD) | time (s) | correct |
|---|---|---|---|---|---|

## Session lifecycle: same session, resume after cache expiry, closed + fresh

Mean per step over the chains. `cache_read` = prompt tokens re-read from cache; `cache_creation` = prompt tokens written to cache (reload cost).

| step | method | n | correct | input | output | cache_read | cache_creation | cost (USD) | time (s) |
|---|---|---|---|---|---|---|---|---|---|
| Q1 (cold start, new session) | context | 4 | 4/4 | 4 | 282 | 10114 | 5446 | 0.0513 | 7.1 |
| Q1 (cold start, new session) | old | 4 | 4/4 | 6 | 370 | 16876 | 3670 | 0.0402 | 11.1 |
| Q2 same session (resume right away) | context | 4 | 4/4 | 4 | 306 | 20722 | 2080 | 0.0782 | 6.4 |
| Q2 same session (resume right away) | old | 4 | 4/4 | 6 | 354 | 24140 | 1171 | 0.0614 | 7.4 |
| Q2 closed + fresh session (re-find) | context | 4 | 4/4 | 5 | 297 | 15248 | 7722 | 0.0708 | 7.5 |
| Q2 closed + fresh session (re-find) | old | 4 | 4/4 | 7 | 500 | 21862 | 4050 | 0.0468 | 10.3 |
| Q2 resumed after 3720s wait | context | 1 | 1/1 | 2 | 207 | 9056 | 0 | 0.0462 | 4.8 |
| Q2 resumed after 3720s wait | old | 1 | 1/1 | 6 | 367 | 28355 | 426 | 0.0611 | 7.6 |
| Q2 resumed after 372s wait | context | 4 | 4/4 | 3 | 276 | 15321 | 637 | 0.0650 | 4.8 |
| Q2 resumed after 372s wait | old | 4 | 4/4 | 6 | 367 | 24456 | 618 | 0.0573 | 8.1 |

## Index upkeep and staleness

| operation | seconds |
|---|---|
| full re-index (force, 623 files / 7213 slices) | 6.69 |
| re-index, nothing changed | 0.24 |
| re-index after touching 1 file (mtime only) | 0.24 |
| re-index after touching 10 files (mtime only) | 0.24 |
| re-index after adding 1 new file | 0.26 |

Touching changes only the file's mtime, so the index skips the unchanged content: those rows show the cost of the scan alone.

**Staleness probe** (a new untracked file is indexed, edited, searched before re-index, then removed):

- new file found by search after indexing: **yes**
- after edit, before re-index: search still returns the OLD text: **yes**
- after edit, before re-index: search finds the NEW text: **no**
- after re-index: search finds the new text: **yes**
- after delete, before re-index: deleted file still returned: **yes**
- after delete and re-index: deleted file still returned: **no**

Main checkout `git status` unchanged afterwards: **yes**.

