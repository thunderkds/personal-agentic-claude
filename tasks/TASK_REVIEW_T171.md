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


---

## Round 3 evidence (T1-T6, tapchat-apis)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_bench_context_search.py` (T6: `--questions` selection, tracked-only grep ignores ignored/untracked files, per-target exclude dirs, `git grep` leaves the repo untouched, read-only upkeep never touches a file, comparison section, labelled report paths) and fixture `tests/fixtures/context_search_questions_tapchat.json` (49 questions: 9 conceptual, 8 symbol, 6 doc, 7 multi_hop, 7 exact_text, 7 callers, 5 negative; 2 lifecycle chains). Output: `40 passed in 0.91s` |
| Verification command run | pass | script mode, `--upkeep --no-probe`, `--lifecycle --no-expiry-wait`, `--agent` against tapchat-apis with `--grep-tracked --grep-exclude-dir dist/coverage/reports --cap 10`; spend $6.48 over 140 runs (cap $10) |
| Negative cases hold (T4 read-only) | pass | `git -C tapchat-apis status --short` before: `M  tsconfig.json` / `?? reports/`; after: identical (diffed, empty). No staleness probe, no touch. All negative ground truth confirmed with zero `git grep` matches. |
| verify | pass | full suite `1449 passed, 25 subtests passed in 33.10s`; all modes ran end to end |
| Full smoke suite still green (no regression) | pass | `1449 passed, 25 subtests passed in 33.10s` |

Grading: no rule changed after seeing round-3 results (the round-2 rule, "negative answer opens with NOT FOUND", was applied from the start). The one wrong agent answer (d05, old agent) named `src/rooms/entities/room.entity.ts` for a rooms-table question whose ground truth is `DATABASE_README.md`; it was left as scored.

Limits: lifecycle ran 2 chains with no expiry wait, so there are no "resume after cache expiry" rows. Tracked-only `git grep` is the old-way scope here (ignored `dist`, `coverage`, `node_modules` and untracked `reports/` never count); the semantic index also holds only the 588 tracked files.

### Generated report (per-question rows omitted; all rows in `reports/context-search-benchmark-tapchat-2026-10-22.md` and `.json`)

# easy-context search vs grep + Read: benchmark (T171, 2026-10-22)

## Recommendation

On 44 scored questions in script mode, the context way hit@5 32/44 against 44/49 (grep + whole-file Read) and 44/49 (bounded grep + ranged Read). Estimated tokens: 85781 vs 172329 vs 24339; median time 0.154s vs 0.005s vs 0.006s. With real agents the context agent was right 49/49 times and the grep+Read agent 48/49; total tokens 1067225 vs 976491, cost $2.74 vs $1.80, median time 6.4s vs 7.3s. Context search was more accurate on: doc. Upkeep: a full re-index takes 5.0s and a no-op one 0.2s. Recommendation: use Grep/Glob/Read by default, with ranged reads: it cost $1.80 against $2.74 and was right 48/49 times against 49/49. Reach for context search first when you have no keyword to grep - a natural-language question about intent or a decision. By real-agent tokens, context search was cheaper and at least as accurate on: conceptual, doc, multi_hop; grep + Read was cheaper or more accurate on: symbol, exact_text, callers, negative. Session lifecycle: context: Q2 cost $0.145 resumed in the same session vs $0.073 in a closed + fresh one (cache_creation 5638 vs 7548 tokens); old: Q2 cost $0.070 resumed in the same session vs $0.038 in a closed + fresh one (cache_creation 774 vs 3273 tokens).

Real-agent spend this round: **$6.48** over 140 `claude -p` runs (cap $10).

## Script mode

| id | kind | ctx s | old s | bnd s | ctx h1 | old h1 | bnd h1 | ctx h5 | old h5 | bnd h5 | ctx tok | old tok | bnd tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Tokens are estimated (chars / 4). h1 / h5 = hit@1 / hit@5. n/a = not scored (semantic search on a negative question always returns hits; agent mode grades it).

| method | median time (s) | hit@1 | hit@5 | total tokens (est) |
|---|---|---|---|---|
| context (search_semantic + get_slice) | 0.154 | 21/44 | 32/44 | 85781 |
| old (grep -n + Read whole top file) | 0.005 | 23/49 | 44/49 | 172329 |
| old, bounded (file list capped 50 + Read +-40 lines) | 0.006 | 23/49 | 44/49 | 24339 |

**Accuracy per question kind (script mode, hit@1 / hit@5)**

| kind | n | context | old | old, bounded |
|---|---|---|---|---|
| conceptual | 9 | 4/9 , 9/9 | 1/9 , 7/9 | 1/9 , 7/9 |
| symbol | 8 | 7/8 , 7/8 | 0/8 , 7/8 | 0/8 , 7/8 |
| doc | 6 | 2/6 , 6/6 | 5/6 , 5/6 | 5/6 , 5/6 |
| multi_hop | 7 | 4/7 , 4/7 | 6/7 , 6/7 | 6/7 , 6/7 |
| exact_text | 7 | 3/7 , 6/7 | 6/7 , 7/7 | 6/7 , 7/7 |
| callers | 7 | 1/7 , 0/7 | 0/7 , 7/7 | 0/7 , 7/7 |
| negative | 5 | n/a | 5/5 , 5/5 | 5/5 , 5/5 |

## Real-agent mode (claude -p)

| id | kind | ctx s | old s | ctx tokens | old tokens | ctx $ | old $ | ctx ok | old ok |
|---|---|---|---|---|---|---|---|---|---|

| method | median time (s) | correct | total tokens (real) | total cost (USD) |
|---|---|---|---|---|
| context agent (easy-context tools only) | 6.4 | 49/49 | 1067225 | 2.739 |
| old agent (Grep, Glob, Read only) | 7.3 | 48/49 | 976491 | 1.800 |

**Correctness and cost per question kind (real agents)**

| kind | n | ctx correct | old correct | ctx tokens | old tokens | ctx $ | old $ |
|---|---|---|---|---|---|---|---|
| conceptual | 9 | 9/9 | 9/9 | 187680 | 240593 | 0.483 | 0.534 |
| symbol | 8 | 8/8 | 8/8 | 134779 | 115540 | 0.326 | 0.193 |
| doc | 6 | 6/6 | 5/6 | 97445 | 157401 | 0.269 | 0.335 |
| multi_hop | 7 | 7/7 | 7/7 | 142695 | 150636 | 0.465 | 0.284 |
| exact_text | 7 | 7/7 | 7/7 | 143747 | 115132 | 0.350 | 0.166 |
| callers | 7 | 7/7 | 7/7 | 197485 | 90716 | 0.452 | 0.164 |
| negative | 5 | 5/5 | 5/5 | 163394 | 106473 | 0.394 | 0.124 |

**Run-to-run spread (3 repeats per method; min / median / max)**

| question | method | tokens | cost (USD) | time (s) | correct |
|---|---|---|---|---|---|

## Session lifecycle: same session, resume after cache expiry, closed + fresh

Mean per step over the chains. `cache_read` = prompt tokens re-read from cache; `cache_creation` = prompt tokens written to cache (reload cost).

| step | method | n | correct | input | output | cache_read | cache_creation | cost (USD) | time (s) |
|---|---|---|---|---|---|---|---|---|---|
| Q1 (cold start, new session) | context | 2 | 2/2 | 4 | 328 | 5464 | 9882 | 0.0867 | 7.5 |
| Q1 (cold start, new session) | old | 2 | 2/2 | 6 | 438 | 17435 | 5032 | 0.0525 | 8.1 |
| Q2 same session (resume right away) | context | 2 | 2/2 | 6 | 309 | 34524 | 5638 | 0.1449 | 6.9 |
| Q2 same session (resume right away) | old | 2 | 2/2 | 5 | 309 | 23486 | 774 | 0.0696 | 6.0 |
| Q2 closed + fresh session (re-find) | context | 2 | 2/2 | 7 | 381 | 26274 | 7548 | 0.0733 | 8.5 |
| Q2 closed + fresh session (re-find) | old | 2 | 2/2 | 6 | 424 | 17741 | 3273 | 0.0382 | 14.7 |

## Index upkeep and staleness

| operation | seconds |
|---|---|
| full re-index (force, 588 files / 3771 slices) | 5.03 |
| re-index, nothing changed | 0.24 |

Timing only: no file was touched or added in the target (read-only run), so there is no incremental or staleness measurement here.

Target `git status` unchanged afterwards: **yes**.

## Grep scope used for the old way

`git grep` over git-tracked files only; skipped directories: .git, __pycache__, node_modules, .pytest_cache, event-trace, dist, coverage, reports.

## This repo vs tapchat-apis

| measure | this repo (Markdown-heavy) | tapchat-apis (code-heavy) |
|---|---|---|
| script hit@5, context | 16/34 | 32/44 |
| script hit@5, old | 28/39 | 44/49 |
| script hit@5, old_bounded | 28/39 | 44/49 |
| script est. tokens, context | 62103 | 85781 |
| script est. tokens, old | 365769 | 172329 |
| script est. tokens, old_bounded | 37332 | 24339 |
| agent correct, context | 38/39 | 49/49 |
| agent tokens, context | 1097720 | 1067225 |
| agent cost USD, context | 2.72 | 2.74 |
| agent correct, old | 39/39 | 48/49 |
| agent tokens, old | 792769 | 976491 |
| agent cost USD, old | 1.34 | 1.80 |
| agent cost ratio context / old | 2.02x | 1.52x |
| full re-index (s) | 6.7 (623 files) | 5.0 (588 files) |


---

## Round 4 evidence (H1-H5, hybrid vs grep-only)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_bench_hybrid.py` (12 tests: paired diff on run means, bootstrap CI with fixed seed and known input, the verdict function on KEEP / DROP / INCONCLUSIVE fixtures, tool-call extraction from a stream-json sample, route adherence and overhead, command and prompt construction, end-to-end analyze). Output with the round-2/3 file: `52 passed in 1.15s` |
| Verification command run | pass | `python3 scripts/bench_hybrid.py --yes`: 352 runs (88 questions x 2 methods x 2 runs, interleaved), 0 errors, no reruns; `VERDICT: KEEP`; spend $11.29 (cap $20) |
| Negative cases hold (H4 read-only) | pass | tapchat-apis `git status --short` before and after: `M  tsconfig.json` / `?? reports/` (identical, diffed) |
| verify | pass | full suite `1461 passed, 25 subtests passed in 33.94s` |
| Full smoke suite still green (no regression) | pass | `1461 passed, 25 subtests passed in 33.94s` |

The rule, prompts, routing text and graders were committed (0fe8311) before the first run and not changed afterwards.

Read the verdict with this caveat (from the numbers below): hybrid called `search_semantic` in only 4 of 176 runs (all `doc` questions). The agents followed "Grep by default" almost always, so hybrid behaved like grep-only with extra tools loaded. KEEP is reached through the rule's second branch: hybrid answered 1 more question correctly on tapchat (97/98 vs 96/98; the grep-only miss is e02 run 2), and the pooled cost CI upper bound (+$0.0004) is within 10% of grep-only's mean cost ($0.0329). Cost is not shown lower (the CI includes 0), and tokens are higher by about 4.8k per question (CI excludes 0), which is the tool-schema weight; cost stayed level because of cache pricing.

# Round 4: hybrid vs grep-only (T171, 2026-10-22)

**VERDICT: KEEP**

Pre-registered rule: KEEP if hybrid correctness >= grep_only on both repos AND (pooled cost CI upper bound <= 0, OR hybrid strictly higher on one repo with the bound <= +10% of grep_only's mean cost). DROP if the pooled cost CI lower bound > 0 and hybrid is not strictly higher on either repo. Otherwise INCONCLUSIVE.

## Totals per repo (all runs)

| repo | method | runs | cost (USD) | tokens | correct |
|---|---|---|---|---|---|
| tapchat | grep_only | 98 | 3.366 | 1934303 | 96/98 |
| tapchat | hybrid | 98 | 3.074 | 2371639 | 97/98 |
| this_repo | grep_only | 78 | 2.433 | 1558683 | 78/78 |
| this_repo | hybrid | 78 | 2.412 | 1970953 | 78/78 |

## Paired mean d = hybrid - grep_only, cost (USD) per question (95% bootstrap CI, 10,000 resamples, seed 171)

| scope | mean d [CI] |
|---|---|
| pooled | -0.0018 [-0.0040, +0.0004] |
| tapchat | -0.0030 [-0.0065, +0.0004] |
| this_repo | -0.0003 [-0.0028, +0.0022] |
| kind: conceptual | -0.0016 [-0.0085, +0.0051] |
| kind: symbol | -0.0034 [-0.0074, -0.0000] |
| kind: doc | +0.0014 [-0.0054, +0.0085] |
| kind: multi_hop | -0.0049 [-0.0124, +0.0018] |
| kind: exact_text | -0.0005 [-0.0041, +0.0040] |
| kind: callers | +0.0009 [+0.0000, +0.0016] |
| kind: negative | -0.0039 [-0.0116, +0.0010] |

## Paired mean d = hybrid - grep_only, tokens per question (95% bootstrap CI, 10,000 resamples, seed 171)

| scope | mean d [CI] |
|---|---|
| pooled | +4827 [+3889, +5803] |
| tapchat | +4463 [+3447, +5452] |
| this_repo | +5286 [+3558, +7145] |
| kind: conceptual | +6775 [+4240, +9302] |
| kind: symbol | +2861 [+1091, +4254] |
| kind: doc | +4630 [-64, +10530] |
| kind: multi_hop | +4746 [+2956, +6589] |
| kind: exact_text | +5003 [+3504, +6757] |
| kind: callers | +3661 [+2873, +4065] |
| kind: negative | +5950 [+3850, +8256] |

Mean grep_only cost per question: $0.0329.

## Route adherence (hybrid runs that called `search_semantic`)

| kind | called / runs |
|---|---|
| conceptual | 0/34 (0%) |
| symbol | 0/30 (0%) |
| doc | 4/20 (20%) |
| multi_hop | 0/24 (0%) |
| exact_text | 0/24 (0%) |
| callers | 0/24 (0%) |
| negative | 0/20 (0%) |

## Fixed overhead of carrying the tools

172 hybrid runs never called `search_semantic`. They cost $0.0307 on average against $0.0326 for grep_only on the same questions (difference -0.0020).

tapchat git status before: 'M  tsconfig.json\n?? reports/'; after: 'M  tsconfig.json\n?? reports/'; identical: True

Spend: $11.29 over 352 runs (cap $20).

