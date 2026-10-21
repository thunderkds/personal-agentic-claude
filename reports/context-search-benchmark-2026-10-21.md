# easy-context search vs grep + Read: benchmark (T171, 2026-10-21)

## Recommendation

On 34 scored questions in script mode, the context way hit@5 16/34 against 28/39 (grep + whole-file Read) and 28/39 (bounded grep + ranged Read). Estimated tokens: 62103 vs 365769 vs 37332; median time 0.119s vs 0.010s vs 0.010s. With real agents the context agent was right 38/39 times and the grep+Read agent 39/39; total tokens 1097720 vs 792769, cost $2.72 vs $1.34, median time 8.0s vs 8.4s. Grep + Read was more accurate on: exact_text. Upkeep: a full re-index takes 6.7s and an incremental one 0.2s for 10 touched files; after an edit, search returned the old text until the file was re-indexed. Recommendation: use Grep/Glob/Read by default, with ranged reads, because it was as accurate and cheaper overall. Reach for context search first only when you have no keyword to grep - a natural-language question about intent or a decision. By real-agent tokens, context search was cheaper and at least as accurate on: symbol, doc; grep + Read was cheaper or more accurate on: conceptual, multi_hop, exact_text, callers, negative. Session lifecycle: context: Q2 cost $0.078 resumed in the same session vs $0.071 in a closed + fresh one (cache_creation 2080 vs 7722 tokens); old: Q2 cost $0.061 resumed in the same session vs $0.047 in a closed + fresh one (cache_creation 1171 vs 4050 tokens). A resume after the 5-minute cache window still read most of its prompt from cache, so the cache did not visibly expire; parallel chains share one prompt prefix and keep it warm, which this test cannot separate from expiry.

Real-agent spend this round: **$6.80** over 142 `claude -p` runs (cap $12).

## Script mode

| id | kind | ctx s | old s | bnd s | ctx h1 | old h1 | bnd h1 | ctx h5 | old h5 | bnd h5 | ctx tok | old tok | bnd tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c01 | conceptual | 0.111 | 0.015 | 0.014 | 0 | 0 | 0 | 1 | 0 | 0 | 1412 | 23091 | 865 |
| c02 | conceptual | 0.128 | 0.008 | 0.008 | 0 | 0 | 0 | 0 | 1 | 1 | 1840 | 7829 | 843 |
| c03 | conceptual | 0.119 | 0.018 | 0.017 | 0 | 0 | 0 | 0 | 1 | 1 | 2073 | 8908 | 1081 |
| c04 | conceptual | 0.167 | 0.017 | 0.016 | 0 | 0 | 0 | 0 | 1 | 1 | 1702 | 30093 | 860 |
| c05 | conceptual | 0.128 | 0.011 | 0.010 | 0 | 0 | 0 | 0 | 0 | 0 | 2186 | 32333 | 1813 |
| c06 | conceptual | 0.134 | 0.015 | 0.015 | 0 | 0 | 0 | 1 | 0 | 0 | 2211 | 8664 | 1346 |
| c07 | conceptual | 0.110 | 0.010 | 0.010 | 0 | 0 | 0 | 1 | 0 | 0 | 915 | 6143 | 907 |
| c08 | conceptual | 0.117 | 0.011 | 0.010 | 0 | 1 | 1 | 0 | 1 | 1 | 1590 | 19813 | 993 |
| s01 | symbol | 0.115 | 0.011 | 0.010 | 0 | 0 | 0 | 0 | 0 | 0 | 921 | 6211 | 1293 |
| s02 | symbol | 0.124 | 0.011 | 0.009 | 1 | 1 | 1 | 1 | 1 | 1 | 1261 | 973 | 661 |
| s03 | symbol | 0.137 | 0.009 | 0.010 | 1 | 1 | 1 | 1 | 1 | 1 | 1045 | 2115 | 731 |
| s04 | symbol | 0.147 | 0.011 | 0.010 | 1 | 1 | 1 | 1 | 1 | 1 | 1542 | 2652 | 858 |
| s05 | symbol | 0.117 | 0.008 | 0.008 | 0 | 1 | 1 | 1 | 1 | 1 | 3028 | 6902 | 826 |
| s06 | symbol | 0.116 | 0.008 | 0.008 | 0 | 0 | 0 | 0 | 0 | 0 | 1089 | 6635 | 824 |
| s07 | symbol | 0.132 | 0.010 | 0.010 | 1 | 1 | 1 | 1 | 1 | 1 | 1385 | 8331 | 741 |
| d01 | doc | 0.133 | 0.010 | 0.010 | 1 | 1 | 1 | 1 | 1 | 1 | 1777 | 1259 | 556 |
| d02 | doc | 0.115 | 0.014 | 0.013 | 0 | 0 | 0 | 1 | 0 | 0 | 2276 | 40268 | 1527 |
| d03 | doc | 0.123 | 0.014 | 0.013 | 1 | 0 | 0 | 1 | 0 | 0 | 1768 | 91704 | 6266 |
| d04 | doc | 0.117 | 0.009 | 0.009 | 1 | 0 | 0 | 1 | 1 | 1 | 2119 | 5074 | 659 |
| m01 | multi_hop | 0.125 | 0.014 | 0.015 | 0 | 0 | 0 | 1 | 1 | 1 | 2131 | 7147 | 2020 |
| m02 | multi_hop | 0.123 | 0.010 | 0.010 | 0 | 0 | 0 | 0 | 0 | 0 | 1224 | 6211 | 1293 |
| m03 | multi_hop | 0.118 | 0.010 | 0.010 | 0 | 0 | 0 | 0 | 1 | 1 | 1515 | 6424 | 1042 |
| m04 | multi_hop | 0.116 | 0.010 | 0.009 | 0 | 0 | 0 | 0 | 0 | 0 | 2380 | 5780 | 1215 |
| m05 | multi_hop | 0.125 | 0.009 | 0.010 | 0 | 0 | 0 | 0 | 0 | 0 | 2562 | 6054 | 1031 |
| e01 | exact_text | 0.116 | 0.009 | 0.010 | 0 | 1 | 1 | 0 | 1 | 1 | 2212 | 2079 | 958 |
| e02 | exact_text | 0.116 | 0.009 | 0.010 | 0 | 1 | 1 | 1 | 1 | 1 | 2222 | 2393 | 577 |
| e03 | exact_text | 0.125 | 0.008 | 0.009 | 0 | 0 | 0 | 1 | 1 | 1 | 979 | 2579 | 516 |
| e04 | exact_text | 0.115 | 0.008 | 0.008 | 0 | 1 | 1 | 0 | 1 | 1 | 405 | 2032 | 561 |
| e05 | exact_text | 0.117 | 0.009 | 0.010 | 0 | 0 | 0 | 1 | 1 | 1 | 1594 | 5343 | 741 |
| k01 | callers | 0.123 | 0.011 | 0.010 | 0 | 0 | 0 | 0 | 1 | 1 | 1178 | 2091 | 723 |
| k02 | callers | 0.130 | 0.008 | 0.009 | 0 | 0 | 0 | 0 | 1 | 1 | 2610 | 3477 | 757 |
| k03 | callers | 0.125 | 0.008 | 0.008 | 0 | 0 | 0 | 0 | 1 | 1 | 638 | 2130 | 990 |
| k04 | callers | 0.116 | 0.008 | 0.009 | 0 | 0 | 0 | 0 | 1 | 1 | 1215 | 896 | 516 |
| k05 | callers | 0.118 | 0.008 | 0.009 | 0 | 0 | 0 | 0 | 1 | 1 | 2071 | 2135 | 742 |
| n01 | negative | 0.112 | 0.012 | 0.012 | n/a | 1 | 1 | n/a | 1 | 1 | 778 | 0 | 0 |
| n02 | negative | 0.118 | 0.007 | 0.006 | n/a | 1 | 1 | n/a | 1 | 1 | 1258 | 0 | 0 |
| n03 | negative | 0.163 | 0.011 | 0.010 | n/a | 1 | 1 | n/a | 1 | 1 | 1046 | 0 | 0 |
| n04 | negative | 0.126 | 0.009 | 0.008 | n/a | 1 | 1 | n/a | 1 | 1 | 616 | 0 | 0 |
| n05 | negative | 0.109 | 0.013 | 0.013 | n/a | 1 | 1 | n/a | 1 | 1 | 1329 | 0 | 0 |

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
| c01 | conceptual | 14.2 | 7.8 | 48728 | 22139 | 0.1262 | 0.0513 | 1 | 1 |
| c02 | conceptual | 17.2 | 11.5 | 57758 | 22849 | 0.1104 | 0.0457 | 1 | 1 |
| c03 | conceptual | 6.8 | 12.6 | 16744 | 29998 | 0.0595 | 0.0536 | 1 | 1 |
| c04 | conceptual | 11.6 | 9.9 | 16342 | 24999 | 0.0561 | 0.0578 | 1 | 1 |
| c05 | conceptual | 9.1 | 13.9 | 28837 | 31410 | 0.0815 | 0.0547 | 1 | 1 |
| c06 | conceptual | 5.9 | 8.1 | 16624 | 20625 | 0.0584 | 0.0343 | 1 | 1 |
| c07 | conceptual | 5.0 | 7.2 | 14438 | 21425 | 0.0399 | 0.0375 | 1 | 1 |
| c08 | conceptual | 7.1 | 10.7 | 16146 | 29787 | 0.0543 | 0.0471 | 1 | 1 |
| s01 | symbol | 24.6 | 8.5 | 33669 | 20539 | 0.0680 | 0.0325 | 1 | 1 |
| s02 | symbol | 5.5 | 6.2 | 14435 | 12525 | 0.0389 | 0.0190 | 1 | 1 |
| s03 | symbol | 49.5 | 9.5 | 13823 | 19462 | 0.0340 | 0.0277 | 1 | 1 |
| s04 | symbol | 7.1 | 10.5 | 14472 | 19143 | 0.0391 | 0.0253 | 1 | 1 |
| s05 | symbol | 5.5 | 17.3 | 17124 | 29421 | 0.0609 | 0.0478 | 1 | 1 |
| s06 | symbol | 7.4 | 5.7 | 14319 | 15307 | 0.0393 | 0.0416 | 1 | 1 |
| s07 | symbol | 10.8 | 8.9 | 14583 | 19717 | 0.0411 | 0.0315 | 1 | 1 |
| d01 | doc | 6.6 | 17.2 | 15956 | 21058 | 0.0517 | 0.0408 | 1 | 1 |
| d02 | doc | 8.0 | 9.0 | 16524 | 21896 | 0.0575 | 0.0391 | 1 | 1 |
| d03 | doc | 5.2 | 11.2 | 14940 | 35131 | 0.0431 | 0.0568 | 1 | 1 |
| d04 | doc | 6.3 | 8.4 | 15920 | 22886 | 0.0526 | 0.0404 | 1 | 1 |
| m01 | multi_hop | 8.6 | 9.2 | 16611 | 21742 | 0.0587 | 0.0422 | 1 | 1 |
| m02 | multi_hop | 5.2 | 8.7 | 14565 | 20948 | 0.0401 | 0.0380 | 1 | 1 |
| m03 | multi_hop | 27.7 | 5.4 | 69278 | 12682 | 0.1257 | 0.0203 | 1 | 1 |
| m04 | multi_hop | 12.9 | 6.7 | 40485 | 20217 | 0.0852 | 0.0296 | 1 | 1 |
| m05 | multi_hop | 10.7 | 6.0 | 42473 | 14068 | 0.1010 | 0.0309 | 1 | 1 |
| e01 | exact_text | 7.8 | 7.5 | 13198 | 20550 | 0.0299 | 0.0354 | 1 | 1 |
| e02 | exact_text | 7.4 | 6.6 | 16229 | 12732 | 0.0535 | 0.0209 | 1 | 1 |
| e03 | exact_text | 13.4 | 8.5 | 44615 | 13682 | 0.1285 | 0.0299 | 0 | 1 |
| e04 | exact_text | 16.2 | 12.5 | 48231 | 21324 | 0.1026 | 0.0434 | 1 | 1 |
| e05 | exact_text | 12.3 | 7.5 | 37968 | 19391 | 0.0780 | 0.0267 | 1 | 1 |
| k01 | callers | 25.8 | 5.2 | 95104 | 12371 | 0.1659 | 0.0168 | 1 | 1 |
| k02 | callers | 12.0 | 6.4 | 27943 | 12931 | 0.0703 | 0.0226 | 1 | 1 |
| k03 | callers | 7.1 | 4.3 | 21964 | 12532 | 0.0403 | 0.0180 | 1 | 1 |
| k04 | callers | 8.3 | 5.4 | 27966 | 12540 | 0.0675 | 0.0189 | 1 | 1 |
| k05 | callers | 13.2 | 4.8 | 61332 | 13035 | 0.1338 | 0.0226 | 1 | 1 |
| n01 | negative | 8.9 | 6.5 | 35196 | 18800 | 0.1167 | 0.0219 | 1 | 1 |
| n02 | negative | 4.2 | 11.9 | 14470 | 33538 | 0.0393 | 0.0391 | 1 | 1 |
| n03 | negative | 5.1 | 6.7 | 13456 | 20944 | 0.0308 | 0.0311 | 1 | 1 |
| n04 | negative | 5.3 | 6.7 | 28240 | 19266 | 0.0702 | 0.0255 | 1 | 1 |
| n05 | negative | 6.6 | 9.0 | 27014 | 19159 | 0.0680 | 0.0251 | 1 | 1 |

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
| c02 | context | 15397 / 15780 / 28232 | 0.039 / 0.043 / 0.066 | 5.7 / 5.8 / 8.2 | 3/3 |
| c02 | old | 13715 / 23742 / 27238 | 0.021 / 0.031 / 0.044 | 6.6 / 9.6 / 11.4 | 3/3 |
| s03 | context | 12930 / 12944 / 13829 | 0.006 / 0.018 / 0.026 | 4.3 / 4.6 / 6.3 | 3/3 |
| s03 | old | 12452 / 12500 / 18885 | 0.010 / 0.010 / 0.014 | 5.7 / 5.9 / 7.3 | 3/3 |
| m01 | context | 16461 / 16513 / 16567 | 0.009 / 0.048 / 0.049 | 5.2 / 5.6 / 7.7 | 3/3 |
| m01 | old | 21437 / 21935 / 28865 | 0.028 / 0.031 / 0.037 | 9.5 / 9.8 / 12.9 | 3/3 |
| e02 | context | 16268 / 16280 / 16289 | 0.008 / 0.009 / 0.046 | 4.6 / 5.0 / 9.4 | 3/3 |
| e02 | old | 12844 / 12898 / 20621 | 0.014 / 0.014 / 0.026 | 5.9 / 6.7 / 7.7 | 3/3 |
| k04 | context | 16423 / 16436 / 16459 | 0.009 / 0.010 / 0.048 | 5.7 / 6.7 / 7.5 | 3/3 |
| k04 | old | 12579 / 12595 / 12596 | 0.008 / 0.011 / 0.011 | 4.3 / 4.9 / 5.4 | 3/3 |

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
