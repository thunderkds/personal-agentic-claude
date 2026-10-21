# easy-context search vs grep + Read: benchmark (T171, 2026-10-21)

## Recommendation

On 34 scored questions in script mode, the context way hit@5 16/34 against 28/39 (grep + whole-file Read) and 28/39 (bounded grep + ranged Read). Estimated tokens: 62103 vs 365769 vs 37332; median time 0.119s vs 0.010s vs 0.010s. Upkeep: a full re-index takes 6.7s and an incremental one 0.2s for 10 touched files; after an edit, search returned the old text until the file was re-indexed.

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

## Index upkeep and staleness

| operation | seconds |
|---|---|
| full re-index (force, 623 files / 7213 slices) | 6.69 |
| re-index, nothing changed | 0.24 |
| re-index after touching 1 file (mtime only) | 0.24 |
| re-index after touching 10 files (mtime only) | 0.24 |
| re-index after adding 1 new file | 0.26 |

**Staleness probe** (a new untracked file is indexed, edited, searched before re-index, then removed):

- new file found by search after indexing: **yes**
- after edit, before re-index: search still returns the OLD text: **yes**
- after edit, before re-index: search finds the NEW text: **no**
- after re-index: search finds the new text: **yes**
- after delete, before re-index: deleted file still returned: **yes**
- after delete and re-index: deleted file still returned: **no**

Main checkout `git status` unchanged afterwards: **yes**.
