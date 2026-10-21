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
