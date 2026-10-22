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
