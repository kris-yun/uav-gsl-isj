# CTT H01 cross-wind native first-passage source-information diagnosis

Status: `PREREGISTERED_AFTER_TEST_OPENING_MECHANISM_DIAGNOSTIC`

This diagnosis does not alter the frozen terminal verdict
`CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO`.  It trains no model,
generates no GADEN world, uses no PMFS prior/posterior, and cannot authorize
closed loop.  TEST contexts 1 and 2 have already been opened, so every result
is diagnostic rather than confirmatory.

## Frozen population

- bank: the G0-passing `R2_FORMAL` native bank;
- wind contexts: `1,2`;
- observation route: `4005` (stream index 4), ten complete physical stops;
- held-out observation transport keys: `6,7`;
- candidate predictive transport keys: `0,1,2,3,4,5` in the same context;
- truth/candidate support: all 210 frozen persistent carriers;
- cases: `2 contexts x 2 observation keys x 210 truths = 840`.

The native physical ppm stream is transformed once by the frozen bitwise-exact
run-persistent sensor.  A stop is the first 80 stationary samples associated
with its frozen PMFS stop ID.  A measured hit is strictly `ppm > 0.1`; first
passage is the first hit index in `0..79`, or `80` for never.

## Frozen scorers

For candidate source `s`, stop `b`, predictive member `k in 0..5`, and
`t in 0..79`,

`G[s,b,t] = mean_k 1(F[s,b,k] <= t)`.

`FULL_FIRST_PASSAGE` minimizes

`sum_b sum_t (G[s,b,t] - 1(F_observed[b] <= t))^2`.

`SURVIVAL_ONLY` uses `E=1(F<80)`, predictive probability
`p[s,b]=mean_k E[s,b,k]`, and minimizes

`sum_b (p[s,b] - E_observed[b])^2`.

No averaging constant affects ordering, so the sums above are used exactly.
There is no fitted bandwidth, weight, temperature or calibration.

`TIME_PERMUTE` applies a fixed permutation to each held observation's raw
80-sample measured binary tape before extracting first passage.  Index `i` is
ordered lexicographically by

`SHA256("CTT-H01-CROSS-WIND-TIME-PERMUTE-V1|context|key|truth|stop|i")`.

This is independent of all candidate scores and preserves hit count exactly.
The candidate predictive CDF remains unchanged.

## Ranking and tests

Lower distance is better.  The true candidate receives exact-equality midrank:

`1 + count(D < D_true) + 0.5 * (count(D == D_true) - 1)`.

Normalized rank is `(rank-1)/209`.  Top-5 and Top-10 include exact midranks
`<=5` and `<=10`.  FULL wins a paired case when its true-source rank is lower;
ties are removed from the exact one-sided binomial sign test with null win
probability `0.5`.

Report overall, per-context, and per-observation-key summaries plus all 840
case rows.

## Frozen verdict

Each comparison (FULL vs SURVIVAL, FULL vs TIME_PERMUTE) passes only if:

1. FULL overall mean normalized rank is strictly lower;
2. the one-sided exact sign-test p-value is at most `0.01`;
3. in context 1 and context 2 separately, FULL mean normalized rank is no
   greater than the comparator.

- both comparisons pass: `CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS`;
- exactly one comparison passes: `CROSS_WIND_FIRST_PASSAGE_PARTIAL`;
- neither comparison passes: `CROSS_WIND_FIRST_PASSAGE_NO_GO`.

PASS supports a neural-representation failure interpretation but requires new
unseen wind contexts for any future confirmatory neural result.  PARTIAL is
mechanistically ambiguous.  NO-GO stops the current wind-conditioned
first-passage main line; changing the neural architecture cannot rescue this
diagnostic.

