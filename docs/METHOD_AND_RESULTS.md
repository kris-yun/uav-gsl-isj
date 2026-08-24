# Sequential Replication-Gated ME-ACI V10

## Frozen verdict

The main innovation is established on the requested development boundary: one frozen online binary, three real House closed-loop datasets, two seeds per House, and six paired native-PMFS/module posterior comparisons. All six reduce the original PMFS final localization error by more than 10%.

This freeze validates the main module only. It does not claim that TADM or a future third module is already validated, and it does not replace a later truth-blind confirmatory study with additional held-out seeds.

## What was actually fixed

The failed version updated from a temporally non-identifying window. A single spatial hit location could be an intermittent plume encounter rather than source evidence, and an all-hit or all-miss fold could not eliminate unknown release/sensor amplitude. The V10 operator therefore separates evidence acquisition from posterior release:

1. Store raw completed measurement events in a sequential reservoir.
2. Require both disjoint temporal folds to contain hits and misses.
3. Require hits to replicate at at least two distinct occupied grid locations.
4. If either condition fails, retain the events and leave the PMFS posterior unchanged.
5. When both conditions hold, evaluate one conditional inverse-transport likelihood and clear the reservoir.

This is an identifiability rule, not a truth-, distance-, likelihood-, temperature-, or posterior-based gate.

## Mathematical contract

For event `i`, source candidate `s`, and fixed transport nuisance member `theta`, define a log propensity

```
psi_i(s, theta) =
  - 0.5 [r_perp / (Delta + a r_parallel,+)]^2
  - log(1 + r_parallel,+ / ell)
  - b r_parallel,- / Delta
```

where `r_parallel` and `r_perp` are source-relative wind coordinates, `Delta=0.3 m`, and `(a, ell, b, slope)` ranges over the frozen 54-member physics family.

Conditioning on the observed hit count `K=sum_i y_i` removes the unknown release/sensor intercept:

```
log L_theta(s)
  = sum_i y_i psi_i(s, theta)
    - log e_K(exp(psi_1), ..., exp(psi_n)),
```

where `e_K` is the K-th elementary symmetric polynomial, computed by stable dynamic programming. Model discrepancy is marginalized rather than selected:

```
log L(s) = logmeanexp_theta log L_theta(s).
```

Disjoint even/odd temporal realizations are converted to candidate-wise normal ranks `z_even(s)` and `z_odd(s)` and combined as

```
z_SD(s) = [z_even(s) + z_odd(s)] / sqrt(2).
```

Let `R_t` be the reservoir after appending the newest window. Evidence is released only when

```
G(R_t) = 1{
  0 < K_even < n_even,
  0 < K_odd  < n_odd,
  number_of_distinct_hit_cells >= 2
}.
```

If `G=0`, `R_t` is retained and the native posterior is unchanged. If `G=1`,

```
p_MEACI(s | R_t) proportional to p_causal(s) exp(z_SD(s)),
```

followed by normalization and reservoir clearing. At the first accepted update `p_causal` is the geometry-only design prior; later accepted updates use the previous causal ME-ACI posterior. The current qualification stops after the first accepted update, so the native shadow is an exact paired counterfactual on the identical trajectory up to release.

## Original PMFS metric alignment

The authoritative PMFS implementation logs its final `Error` from
`ExpectedValue(sourceProbability, 0.05)`, i.e. the probability-weighted location of the top 5% free cells. Full-posterior expected error (`errorAll`) is a separate auxiliary value, and posterior variance is the stopping statistic. V10 qualification therefore freezes top-5% expected-location error as primary, while MAP, full mean, variance, and truth-candidate rank remain diagnostics.

## Closed-loop result matrix

| House | Seed | Accepted update | Events | Sim time (s) | Native PMFS (m) | V10 (m) | Gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01 | 0 | 2 | 56 | 135.673 | 5.152589 | 2.501097 | 51.459% |
| H01 | 1 | 3 | 80 | 217.811 | 6.928495 | 5.006343 | 27.743% |
| H02 | 0 | 3 | 80 | 196.675 | 2.926781 | 2.271832 | 22.378% |
| H02 | 1 | 1 | 32 | 72.851 | 1.813416 | 1.307146 | 27.918% |
| H03 | 0 | 1 | 32 | 78.002 | 6.652648 | 2.863832 | 56.952% |
| H03 | 1 | 1 | 32 | 80.616 | 5.219942 | 2.982003 | 42.873% |

Aggregate results:

- Pass rate: `6/6`.
- Pooled native mean: `4.782312 m`.
- Pooled V10 mean: `2.822042 m`.
- Pooled reduction: `40.990%`.
- Minimum/median/maximum individual gain: `22.378% / 35.395% / 56.952%`.
- Accepted inference runtime: `0.022-0.162 s`; evidence acquisition, not inference, dominates latency.
- First accepted update occurs at `72.851-217.811` simulation seconds, within the 300 s budget.

## Interpretation of SD-TFEI

The validated main innovation is no longer merely an eigenfeature. SD-TFEI survives as the physical principle—source evidence must replicate across temporal realizations while temporal fluctuation is treated as nuisance—but its publishable inference form is the sequential replication-gated conditional channel above. Calling the old generalized-eigenvector feature alone “closed-loop validated” would be inaccurate.

## Scientific limits and next gate

This is a strong mechanism/development result, not yet a final population-level paper claim. The formula and gate were developed while House01/02/03 results were visible. The next confirmatory step must freeze this exact source and binary, then run additional truth-blind seeds (or genuinely held-out realizations) without modifying the likelihood, reservoir, gate, cadence, metric, or stopping rule. TADM should be evaluated only after this main freeze is preserved as the isolated reference arm.

## Frozen identifiers

- Binary SHA-256: `14133117b9d24502acc8e45ad7c72fbd668fbe867fd73aeee17b70e52cfbe938`
- Run contract: `MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4`
- Formula marker: `inverse_transport_sequential_replication_v3`
- Cadence: `stepsSourceUpdate=3`
- Run budget: `300 s`
- Evaluation contract: `MEACI_EXTERNAL_TRUTH_EVALUATOR_V2`

