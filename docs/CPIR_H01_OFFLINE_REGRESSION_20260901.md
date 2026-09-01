# CPIR H01 offline regression — 2026-09-01

Status: `DEVELOPMENT_ONLY_OFFLINE_REGRESSION`

## Scope

This regression uses the recovered H01 `predictive8` physical bank and the exact reserved route schedules. It does **not** replace VM Release compilation, C++/Python posterior parity, the H01/H02/H03 full-grid-bank replay, or paired closed loop.

The executable-code state is the code-changing commit `4cdc7c5825ea1ea45d91016b44a7268a9a7286cf`. The later branch commits through `e634f5a68da4fcc44856cbeb58a2471903150822` add documentation only, so they do not alter the tested executable logic.

## Bank integrity and sensor parity

Recovered H01 predictive bank:

- 210 source carriers × 8 predictive members × 5 reserved routes;
- 1680 binary shards;
- 14,128,800 physical samples;
- each route contains 1682 native samples;
- ordered-shard SHA-256 `63783e2e5062e161bef894f99eef55afeabb6cf385567197dacfaad7cc89f511`, exactly matching the frozen bank summary.

The current CPIR delayed first-order persistent state was compared against the frozen H01 sensor forward operator over all five routes:

- numeric maximum absolute difference: `0.0`;
- stop-event comparisons: `82,320`;
- event mismatches: `0`.

Verdict: `H01_BANK_AND_CPIR_SENSOR_PARITY = PASS`.

## Formula/property regression

The following frozen properties were checked:

- `alpha = exp(-0.2/1.2)`;
- carrier-to-cell I-projection preserves carrier mass;
- count-only and stop-resolved likelihoods agree when every stop has identical predictive probability;
- the two scores differ when stop identity is informative;
- posterior normalization remains exact for prefix and full-history recomputation.

Verdict: `CPIR_FORMULA_PROPERTY_SELFTEST = PASS`.

## Real-data nested A1/A2/A3 LOO replay

The original reserved4 observation worlds are not contained in the recovered package. Therefore one predictive member is held out as a pseudo-observation and the remaining seven members form the predictive nuisance ensemble. This produces 40 route × held-member development units over routes 4001–4005. Stop counts are `10,10,10,9,10`.

The arms follow the frozen CPIR semantics:

- A1: memoryless raw candidate event + count-only likelihood;
- A2: persistent sensor-state candidate event + count-only likelihood;
- A3: persistent sensor-state candidate event + stop-resolved composite likelihood.

Observed events are always generated through the persistent sensor chain. With seven predictive members, the Jeffreys estimate is `(hits+0.5)/8` rather than the formal eight-member `(hits+0.5)/9`.

| Arm | Mean normalized true-source rank ↓ | Mean carrier-posterior error / m ↓ |
|---|---:|---:|
| A1 raw + count | 0.264406 | 3.328694 |
| A2 state + count | 0.252126 | 3.285777 |
| A3 state + stop-resolved | 0.139027 | 2.567811 |

Incremental comparisons over the 40 development units:

- A2 vs A1: normalized rank improves `4.64%`, wins/losses `36/4`; carrier-posterior error improves `1.29%`, wins/losses `29/11`.
- A3 vs A2: normalized rank improves `44.86%`, wins/losses `40/0`; carrier-posterior error improves `21.85%`, wins/losses `40/0`.
- A3 vs A1: normalized rank improves `47.42%`, wins/losses `40/0`; carrier-posterior error improves `22.86%`, wins/losses `40/0`.

One-sided exact sign-test probabilities are approximately `9.29e-8` for the A2-vs-A1 rank direction, `0.00321` for the A2-vs-A1 error direction, and `9.09e-13` for either 40/0 A3 comparison.

Every route 4001–4005 improves from A2 to A3 in both rank and error. A2 is weaker: route 4001 has a small error regression even though the pooled A2 direction is positive.

## Interpretation boundary

This is strong mechanism-level evidence for M3/SRDCL preserving stop identity on top of M1+M2. M2/PSST is directionally positive but materially smaller under the frozen nested count-only A2 definition.

This result must **not** be advertised as the paper's required >10% improvement over authoritative PMFS because:

1. this is H01 only;
2. the pseudo-observation is a held member of the same predictive8 family rather than an external observation world;
3. the endpoint reported here is carrier-posterior mean Euclidean error, not the formal PMFS top-5%-mass endpoint;
4. the H01/H02/H03 CPIR full-grid banks are not available in the current local test runtime, so the exact `cpir_three_module_shadow.py` Stage-1/Stage-2 replay was not executed here;
5. VM Release build and C++/Python posterior parity remain pending.

## Readiness

- source/formula level: `OFFLINE_REGRESSION_PASS`;
- M2 persistent sensor numerical/event parity on recovered real H01 bank: `PASS`;
- M3 incremental H01 development signal: `STRONG_POSITIVE`;
- exact full-grid H01/H02/H03 shadow: `PENDING`;
- VM C++ build/parity: `PENDING`;
- formal paired closed loop: `NOT_YET_AUTHORIZED`.
