# ResearchStudio Phase 4.1.5 — implementability audit

## Verdict

`ORACLE_METHOD_IMPLEMENTABLE`  
`BANK_FREE_M1 = OPEN`

The three oracle-stage steps are concrete enough to implement without inventing load-bearing decisions. The unknown-site replacement for the oracle M1 remains intentionally open and is not filled by speculation.

## Step S1 — M1 CREL

### Concrete oracle object

Input tensor after the frozen route-bank reader:

```text
E[case, source, member, stop] : bool
```

For one source update, select the visible prefix and compute:

```text
K[source, member] = sum_stop E[source, member, stop]
hist[source, k]   = number of members with K == k
```

Output schema:

```text
counts: uint8 [S,M]
hist:   integer [S,N+1]
```

No measured gas is used in S1.

【author decision: the final unknown-site paper claim requires a bank-free procedure that produces or bounds this source-conditioned encounter law from map + executed route + deployable wind/context. The oracle route bank is only a falsification teacher and cannot be the deployment implementation.】

## Step S2 — M2 CDIG

Input: `hist[source,k]` from S1 only.

Compute:

1. F00 mean-projection numerator `T_s = sum_m K_sm`;
2. cumulative histogram `C_s(k)` for `k=0..N-1`;
3. pairwise integer CDF separation `G_ij = sum_k (C_i-C_j)^2`;
4. pairwise empirical replacement radius `R_T = 0.5 * L1(hist_i-hist_j)`;
5. exact hard-pair flag `T_i == T_j and G_ij > 0`.

Output schema:

```text
T:             integer [S]
G:             integer [S,S]
R_T:           integer [S,S]
hard_pair:     bool    [S,S]
```

S2 does not read measured gas or truth. No threshold is used to declare a pair “close”; the complete matrices are retained.

## Step S3 — M3 APRS

Inputs:

```text
K[source,member]
R_T[source,source]
H = observed number of hit stops
N = number of visible stops
```

For every candidate and every retained ensemble size `r=M-q`, compute exact minimum and maximum Ranked Probability Score numerator over all valid sub-multisets of the source histogram using dynamic programming over count bins. The DP state is `(current K-bin, number retained so far)` and the additive cost at threshold `k` is the squared empirical-CDF residual against the step CDF induced by observed count `H`.

For each ordered source pair, build `R_O[a,b]`, the number of consecutive deletion levels from `q=0` for which the worst score of `a` is strictly lower than the best score of `b`.

Output the full surface:

```text
survivor[r_T_level, r_O_level, source] : bool
```

for all intrinsic integer levels `1..M` on both axes. Do not select one level inside the method.

Secondary descriptive output:

```text
persistence[source] = mean over the M x M survivor surface
```

This score is not a calibrated probability.

## Open design point

The only load-bearing open implementation decision is the bank-free M1 mapping. It must satisfy the deployment contract and later be tested by LOHO; no network or new GADEN run is authorized merely because the oracle framework passes.

## Additional mechanism-faithfulness check

The exact F00 mean-projection theorem can be mathematically true while all equal-mean/full-law-distinct pairs lie far from the true source. Therefore Stage2 now audits direct task relevance without introducing an effect-size threshold: whenever the truth carrier has exact-F00-mean/full-law-distinct competitors, it records the unweighted CTPI robustness-surface persistence margin of truth versus the mean of those alias competitors. Houses without such contexts are `NOT_IDENTIFIED` for this mechanism diagnostic; observed Houses must not have a negative mean margin and the pooled context-weighted margin must be positive for Oracle GO.
