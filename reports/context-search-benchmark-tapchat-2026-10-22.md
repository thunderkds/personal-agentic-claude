# easy-context search vs grep + Read: benchmark (T171, 2026-10-22)

## Recommendation

On 44 scored questions in script mode, the context way hit@5 32/44 against 44/49 (grep + whole-file Read) and 44/49 (bounded grep + ranged Read). Estimated tokens: 85781 vs 172329 vs 24339; median time 0.154s vs 0.005s vs 0.006s. With real agents the context agent was right 49/49 times and the grep+Read agent 48/49; total tokens 1067225 vs 976491, cost $2.74 vs $1.80, median time 6.4s vs 7.3s. Context search was more accurate on: doc. Upkeep: a full re-index takes 5.0s and a no-op one 0.2s. Recommendation: use Grep/Glob/Read by default, with ranged reads: it cost $1.80 against $2.74 and was right 48/49 times against 49/49. Reach for context search first when you have no keyword to grep - a natural-language question about intent or a decision. By real-agent tokens, context search was cheaper and at least as accurate on: conceptual, doc, multi_hop; grep + Read was cheaper or more accurate on: symbol, exact_text, callers, negative. Session lifecycle: context: Q2 cost $0.145 resumed in the same session vs $0.073 in a closed + fresh one (cache_creation 5638 vs 7548 tokens); old: Q2 cost $0.070 resumed in the same session vs $0.038 in a closed + fresh one (cache_creation 774 vs 3273 tokens).

Real-agent spend this round: **$6.48** over 140 `claude -p` runs (cap $10).

## Script mode

| id | kind | ctx s | old s | bnd s | ctx h1 | old h1 | bnd h1 | ctx h5 | old h5 | bnd h5 | ctx tok | old tok | bnd tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c01 | conceptual | 0.157 | 0.005 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 2356 | 6075 | 536 |
| c02 | conceptual | 0.122 | 0.006 | 0.006 | 1 | 0 | 0 | 1 | 0 | 0 | 1870 | 9926 | 1111 |
| c03 | conceptual | 0.159 | 0.005 | 0.006 | 0 | 0 | 0 | 1 | 1 | 1 | 1269 | 756 | 480 |
| c04 | conceptual | 0.119 | 0.007 | 0.007 | 0 | 1 | 1 | 1 | 1 | 1 | 1665 | 2501 | 568 |
| c05 | conceptual | 0.133 | 0.005 | 0.006 | 0 | 0 | 0 | 1 | 1 | 1 | 854 | 5173 | 455 |
| c06 | conceptual | 0.175 | 0.005 | 0.006 | 0 | 0 | 0 | 1 | 1 | 1 | 1627 | 5694 | 415 |
| c07 | conceptual | 0.155 | 0.005 | 0.006 | 1 | 0 | 0 | 1 | 1 | 1 | 2577 | 6218 | 330 |
| c08 | conceptual | 0.154 | 0.006 | 0.007 | 0 | 0 | 0 | 1 | 0 | 0 | 1568 | 18984 | 1021 |
| c09 | conceptual | 0.151 | 0.005 | 0.006 | 1 | 0 | 0 | 1 | 1 | 1 | 2666 | 5573 | 568 |
| s01 | symbol | 0.126 | 0.005 | 0.006 | 1 | 0 | 0 | 1 | 1 | 1 | 1583 | 1224 | 359 |
| s02 | symbol | 0.138 | 0.004 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 1502 | 6434 | 861 |
| s03 | symbol | 0.115 | 0.004 | 0.006 | 1 | 0 | 0 | 1 | 1 | 1 | 1183 | 9090 | 745 |
| s04 | symbol | 0.161 | 0.004 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 1795 | 3128 | 439 |
| s05 | symbol | 0.164 | 0.005 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 894 | 877 | 317 |
| s06 | symbol | 0.110 | 0.005 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 1281 | 596 | 481 |
| s07 | symbol | 0.159 | 0.005 | 0.006 | 1 | 0 | 0 | 1 | 0 | 0 | 1563 | 5704 | 842 |
| s08 | symbol | 0.120 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 1193 | 6075 | 536 |
| d01 | doc | 0.147 | 0.010 | 0.008 | 0 | 1 | 1 | 1 | 1 | 1 | 837 | 1273 | 508 |
| d02 | doc | 0.144 | 0.008 | 0.008 | 1 | 1 | 1 | 1 | 1 | 1 | 1238 | 5691 | 402 |
| d03 | doc | 0.142 | 0.005 | 0.007 | 0 | 1 | 1 | 1 | 1 | 1 | 1157 | 1589 | 585 |
| d04 | doc | 0.117 | 0.005 | 0.007 | 1 | 1 | 1 | 1 | 1 | 1 | 883 | 1639 | 691 |
| d05 | doc | 0.177 | 0.008 | 0.008 | 0 | 0 | 0 | 1 | 0 | 0 | 2237 | 8866 | 808 |
| d06 | doc | 0.123 | 0.005 | 0.005 | 0 | 1 | 1 | 1 | 1 | 1 | 1101 | 4165 | 266 |
| m01 | multi_hop | 0.154 | 0.010 | 0.007 | 0 | 1 | 1 | 0 | 1 | 1 | 1921 | 3011 | 396 |
| m02 | multi_hop | 0.127 | 0.005 | 0.006 | 1 | 1 | 1 | 1 | 1 | 1 | 3267 | 2188 | 466 |
| m03 | multi_hop | 0.140 | 0.005 | 0.005 | 0 | 0 | 0 | 1 | 0 | 0 | 1931 | 10253 | 882 |
| m04 | multi_hop | 0.200 | 0.005 | 0.006 | 1 | 1 | 1 | 1 | 1 | 1 | 1292 | 877 | 317 |
| m05 | multi_hop | 0.162 | 0.005 | 0.006 | 1 | 1 | 1 | 1 | 1 | 1 | 2994 | 1960 | 364 |
| m06 | multi_hop | 0.127 | 0.005 | 0.005 | 1 | 1 | 1 | 0 | 1 | 1 | 2063 | 4945 | 432 |
| m07 | multi_hop | 0.107 | 0.005 | 0.006 | 0 | 1 | 1 | 0 | 1 | 1 | 2483 | 3128 | 439 |
| e01 | exact_text | 0.156 | 0.005 | 0.006 | 0 | 1 | 1 | 1 | 1 | 1 | 2068 | 412 | 368 |
| e02 | exact_text | 0.174 | 0.005 | 0.006 | 0 | 1 | 1 | 0 | 1 | 1 | 1086 | 694 | 638 |
| e03 | exact_text | 0.156 | 0.005 | 0.005 | 1 | 0 | 0 | 1 | 1 | 1 | 1522 | 1933 | 597 |
| e04 | exact_text | 0.094 | 0.005 | 0.007 | 0 | 1 | 1 | 1 | 1 | 1 | 1382 | 715 | 600 |
| e05 | exact_text | 0.118 | 0.005 | 0.006 | 0 | 1 | 1 | 1 | 1 | 1 | 1906 | 581 | 371 |
| e06 | exact_text | 0.149 | 0.004 | 0.005 | 1 | 1 | 1 | 1 | 1 | 1 | 1925 | 4778 | 726 |
| e07 | exact_text | 0.177 | 0.004 | 0.005 | 1 | 1 | 1 | 1 | 1 | 1 | 3021 | 6592 | 637 |
| k01 | callers | 0.173 | 0.005 | 0.005 | 0 | 0 | 0 | 0 | 1 | 1 | 2613 | 1169 | 473 |
| k02 | callers | 0.163 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 2698 | 1145 | 353 |
| k03 | callers | 0.172 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 1897 | 2059 | 473 |
| k04 | callers | 0.156 | 0.005 | 0.006 | 1 | 0 | 0 | 0 | 1 | 1 | 1527 | 4038 | 702 |
| k05 | callers | 0.163 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 1968 | 660 | 469 |
| k06 | callers | 0.170 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 1610 | 1977 | 676 |
| k07 | callers | 0.155 | 0.005 | 0.006 | 0 | 0 | 0 | 0 | 1 | 1 | 2970 | 1963 | 636 |
| n01 | negative | 0.166 | 0.005 | 0.005 | n/a | 1 | 1 | n/a | 1 | 1 | 1280 | 0 | 0 |
| n02 | negative | 0.097 | 0.007 | 0.010 | n/a | 1 | 1 | n/a | 1 | 1 | 1312 | 0 | 0 |
| n03 | negative | 0.162 | 0.005 | 0.005 | n/a | 1 | 1 | n/a | 1 | 1 | 1196 | 0 | 0 |
| n04 | negative | 0.128 | 0.006 | 0.007 | n/a | 1 | 1 | n/a | 1 | 1 | 727 | 0 | 0 |
| n05 | negative | 0.132 | 0.006 | 0.008 | n/a | 1 | 1 | n/a | 1 | 1 | 2223 | 0 | 0 |

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
| c01 | conceptual | 12.9 | 6.5 | 56235 | 13504 | 0.1046 | 0.0290 | 1 | 1 |
| c02 | conceptual | 5.5 | 8.8 | 14641 | 27215 | 0.0441 | 0.0859 | 1 | 1 |
| c03 | conceptual | 5.8 | 5.0 | 14196 | 12667 | 0.0388 | 0.0216 | 1 | 1 |
| c04 | conceptual | 6.6 | 10.5 | 14302 | 20253 | 0.0390 | 0.0306 | 1 | 1 |
| c05 | conceptual | 4.9 | 7.3 | 14573 | 25145 | 0.0411 | 0.0752 | 1 | 1 |
| c06 | conceptual | 7.5 | 22.4 | 15138 | 68685 | 0.0475 | 0.1012 | 1 | 1 |
| c07 | conceptual | 6.9 | 9.0 | 15957 | 22991 | 0.0536 | 0.0466 | 1 | 1 |
| c08 | conceptual | 6.1 | 10.4 | 14699 | 28082 | 0.0432 | 0.0988 | 1 | 1 |
| c09 | conceptual | 9.3 | 7.6 | 27939 | 22051 | 0.0711 | 0.0447 | 1 | 1 |
| s01 | symbol | 3.7 | 6.2 | 13344 | 12504 | 0.0310 | 0.0200 | 1 | 1 |
| s02 | symbol | 8.8 | 4.5 | 13402 | 12267 | 0.0320 | 0.0176 | 1 | 1 |
| s03 | symbol | 5.4 | 6.0 | 13783 | 12331 | 0.0362 | 0.0200 | 1 | 1 |
| s04 | symbol | 3.9 | 9.4 | 13736 | 19969 | 0.0343 | 0.0347 | 1 | 1 |
| s05 | symbol | 4.2 | 5.4 | 12314 | 12734 | 0.0236 | 0.0216 | 1 | 1 |
| s06 | symbol | 3.6 | 3.7 | 17506 | 12178 | 0.0654 | 0.0172 | 1 | 1 |
| s07 | symbol | 4.2 | 5.7 | 12761 | 20134 | 0.0266 | 0.0331 | 1 | 1 |
| s08 | symbol | 7.7 | 7.1 | 37933 | 13423 | 0.0773 | 0.0284 | 1 | 1 |
| d01 | doc | 4.7 | 7.9 | 13851 | 21237 | 0.0364 | 0.0432 | 1 | 1 |
| d02 | doc | 4.1 | 5.8 | 15841 | 20921 | 0.0522 | 0.0341 | 1 | 1 |
| d03 | doc | 6.4 | 8.2 | 14887 | 21644 | 0.0444 | 0.0414 | 1 | 1 |
| d04 | doc | 8.4 | 11.4 | 23356 | 32653 | 0.0483 | 0.0589 | 1 | 1 |
| d05 | doc | 6.2 | 8.9 | 16328 | 21871 | 0.0568 | 0.0446 | 1 | 0 |
| d06 | doc | 4.0 | 11.4 | 13182 | 39075 | 0.0308 | 0.1129 | 1 | 1 |
| m01 | multi_hop | 9.3 | 9.9 | 30753 | 21797 | 0.0955 | 0.0429 | 1 | 1 |
| m02 | multi_hop | 7.3 | 6.2 | 16185 | 13022 | 0.0553 | 0.0242 | 1 | 1 |
| m03 | multi_hop | 5.3 | 6.5 | 20198 | 19760 | 0.0881 | 0.0287 | 1 | 1 |
| m04 | multi_hop | 6.3 | 7.3 | 16945 | 19123 | 0.0614 | 0.0266 | 1 | 1 |
| m05 | multi_hop | 5.3 | 13.1 | 15302 | 32711 | 0.0474 | 0.0636 | 1 | 1 |
| m06 | multi_hop | 5.4 | 11.5 | 15400 | 22148 | 0.0487 | 0.0530 | 1 | 1 |
| m07 | multi_hop | 6.9 | 8.0 | 27912 | 22075 | 0.0683 | 0.0453 | 1 | 1 |
| e01 | exact_text | 4.0 | 7.3 | 15639 | 21080 | 0.0498 | 0.0356 | 1 | 1 |
| e02 | exact_text | 10.4 | 8.7 | 32431 | 12290 | 0.0548 | 0.0178 | 1 | 1 |
| e03 | exact_text | 6.5 | 7.1 | 15395 | 19796 | 0.0483 | 0.0291 | 1 | 1 |
| e04 | exact_text | 4.3 | 4.1 | 14558 | 12115 | 0.0422 | 0.0164 | 1 | 1 |
| e05 | exact_text | 10.6 | 6.2 | 35570 | 19041 | 0.0647 | 0.0263 | 1 | 1 |
| e06 | exact_text | 6.5 | 7.5 | 14701 | 18587 | 0.0421 | 0.0233 | 1 | 1 |
| e07 | exact_text | 5.1 | 5.6 | 15453 | 12223 | 0.0486 | 0.0174 | 1 | 1 |
| k01 | callers | 7.1 | 3.8 | 21938 | 12502 | 0.0422 | 0.0194 | 1 | 1 |
| k02 | callers | 6.3 | 7.0 | 27081 | 12755 | 0.0661 | 0.0218 | 1 | 1 |
| k03 | callers | 7.3 | 5.7 | 28169 | 12889 | 0.0662 | 0.0224 | 1 | 1 |
| k04 | callers | 10.3 | 6.4 | 37777 | 14922 | 0.0761 | 0.0408 | 1 | 1 |
| k05 | callers | 8.7 | 9.0 | 29724 | 12674 | 0.0768 | 0.0213 | 1 | 1 |
| k06 | callers | 6.1 | 6.1 | 24768 | 12221 | 0.0556 | 0.0173 | 1 | 1 |
| k07 | callers | 7.7 | 8.3 | 28028 | 12753 | 0.0693 | 0.0214 | 1 | 1 |
| n01 | negative | 6.4 | 7.2 | 23226 | 18260 | 0.0497 | 0.0194 | 1 | 1 |
| n02 | negative | 11.2 | 11.7 | 41170 | 25374 | 0.0890 | 0.0316 | 1 | 1 |
| n03 | negative | 6.1 | 8.9 | 26459 | 19332 | 0.0650 | 0.0268 | 1 | 1 |
| n04 | negative | 7.9 | 8.8 | 26718 | 25312 | 0.0758 | 0.0276 | 1 | 1 |
| n05 | negative | 10.5 | 5.5 | 45821 | 18195 | 0.1142 | 0.0187 | 1 | 1 |

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
| c02 | context | 14629 / 14635 / 14651 | 0.010 / 0.011 / 0.036 | 5.0 / 5.5 / 6.6 | 3/3 |
| c02 | old | 21653 / 27208 / 31422 | 0.025 / 0.043 / 0.078 | 9.7 / 12.1 / 16.3 | 3/3 |
| s03 | context | 13757 / 13765 / 13766 | 0.008 / 0.008 / 0.028 | 4.2 / 4.9 / 5.1 | 3/3 |
| s03 | old | 13462 / 19156 / 19219 | 0.019 / 0.020 / 0.021 | 5.3 / 5.7 / 7.0 | 3/3 |
| m01 | context | 30791 / 30813 / 47805 | 0.053 / 0.053 / 0.112 | 8.8 / 9.1 / 13.8 | 3/3 |
| m01 | old | 21265 / 22145 / 22529 | 0.023 / 0.035 / 0.040 | 7.6 / 9.5 / 10.3 | 3/3 |
| e02 | context | 13643 / 13675 / 32421 | 0.007 / 0.026 / 0.027 | 3.9 / 4.7 / 12.9 | 3/3 |
| e02 | old | 12173 / 12306 / 33235 | 0.010 / 0.011 / 0.058 | 6.0 / 6.5 / 12.4 | 2/3 |
| k04 | context | 37734 / 37894 / 38098 | 0.036 / 0.038 / 0.072 | 10.3 / 12.4 / 19.2 | 3/3 |
| k04 | old | 14865 / 14910 / 14943 | 0.032 / 0.033 / 0.034 | 5.0 / 5.7 / 6.8 | 3/3 |

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
