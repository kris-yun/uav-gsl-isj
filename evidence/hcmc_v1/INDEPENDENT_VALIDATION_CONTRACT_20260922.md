# HCMC V1 independent-validation contract

Status at freeze: `SOURCE_BLIND_CONTRACT_FROZEN`; no independent-realization endpoint has been generated or inspected.

## Method freeze

- HCMC V1 only: powers `{1,2,3,4}`, scales `{1,2,4,8}`, `+x/+y`, confidence floor `1e-6`, square-root confidence weights, slope mismatch, and average percentile ranks.
- Native and HCMC remain separate. There is no Native/HCMC fusion and no parameter tuning.
- This validation is fixed-trajectory offline evaluation only. HCMC closed-loop is forbidden.
- Endpoint is the linked C++ `GSL::Utils::ExpectedValue(grid, 0.05)` implementation with its native `ceil(0.05*N)` and `std::sort` semantics. Equal-probability cutoff ties are reported as a sensitivity diagnostic; Python stable-sort values are not substituted for linked-native values.

## Independence freeze

- Existing navigation seeds 2 and 3 reuse overlapping windows of one deterministic plume and are trajectory-only checks, not independent plume evidence.
- Exactly two new GADEN plume realizations are generated for each of H01, H02, and H03.
- The authoritative GADEN source is copied into an isolated VM build. The only permitted source difference is the optional `GADEN_RNG_SEED` hook in `MathUtils.hpp`; source, wind, occupancy, gas physics, and saved-frame cadence stay fixed.
- Predeclared plume seeds are in `INDEPENDENT_DATA_FREEZE_20260922.json`. They were fixed before any new endpoint was available.

## Truth isolation and controls

- Posterior construction accepts no truth coordinates. It freezes Native/HCMC posteriors, 300 leaf-permutation assignments, and 30 spatial-shuffle assignments plus SHA-256 manifests before truth-sidecar evaluation.
- The truth evaluator verifies those hashes, calls the linked-native endpoint, and reports MAP error, full expected truth distance, mass within 1 m and 2 m, entropy, effective support, posterior variance, and nearest-truth candidate rank.
- False-confident collapse is predeclared as: HCMC has strictly worse full expected truth distance than Native while HCMC effective support is strictly smaller than Native. No threshold is tuned after truth reveal.

## Gate

PASS requires all of: six independent realizations complete; HCMC non-worse than Native on at least four of six linked-native endpoint errors; mean HCMC improvement at least 10%; both destructive-control-family pooled means are worse than real HCMC; zero new false-confident-collapse cases; and all provenance, integrity, and endpoint-parity checks pass. A failed scientific condition is `NO_GO`; incomplete provenance, execution, or independence is `HOLD`. Neither result authorizes closed-loop HCMC.
