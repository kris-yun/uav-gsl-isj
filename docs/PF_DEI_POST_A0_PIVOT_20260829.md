# PF-DEI post-A0 pivot: from trajectory energy score to marginal ensemble evidence

Date: 2026-08-29
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
Status: FROZEN SCIENTIFIC INTERPRETATION AFTER H01 ACTUAL SOURCE-UPDATE GATE

## 1. Evidence now frozen

The H01 seed0..9 actual PMFS source-update replay produced the terminal verdicts:

- `PFDEI_DIRECT_ONLINE_ORDERING_NOT_READY`
- `PFDEI_A0_CALIBRATION_BLOCKER`

Across 50 FULL source-update cases:

- raw Top1/Top5/Top10 = 1/50, 7/50, 10/50;
- raw median rank = 25.5/210;
- severe raw normalized-rank > 0.5 = 11/50;
- update 1 raw Top5 = 0/10, median rank = 151.5/210, severe = 8/10;
- A0 worsened true-source rank in 50/50 cases;
- A0 changed raw Top5 7/50 to posterior Top5 0/50 and median rank 25.5 to 91.5.

Module evidence at identical source-update pairs:

- clean M1: mixed, 14 FULL wins / 21 ties / 15 ablation wins;
- M2 nuisance-distribution marginalization: directional but not uniform, 27 FULL wins / 4 ties / 19 ablation wins; median rank 25.5 vs 40.0;
- M3 coherent nuisance-member trajectories: counter-supported, its removal wins 36/50; median rank 21.0 without M3 vs 25.5 FULL;
- M4 adjacent temporal increment channel: nearly inert, 39/50 ties.

No shadow or closed-loop is authorized from these results.

## 2. Scientific consequence

Do not repair A0 alone. A monotone score-to-posterior calibration cannot repair a raw source ordering that is already poor at the first online decisions.

Do not launch TrajCast-like temporal autoregression or any new TCN from the current evidence. The data do not support M3/M4 as the useful information-bearing mechanism.

The supported signal is instead the finite predictive distribution over unresolved source-placement / transport nuisance. Therefore the next method class is:

**Physics-Factorized Marginal Ensemble Inference (PF-MEI)**

Interpret each candidate source `s` at each causally visited sensing block `b` as an ensemble probabilistic forecast of what the sensor should measure after marginalizing unresolved physics:

`F_{s,b} = { Mtilde_{s,m,b} : m = 1..M }`.

Here `Mtilde = T(C)` uses the frozen forward sensor operator. The primary comparison therefore remains in measured-sensor space rather than deconvolving the real observation. This preserves the physical sensor closure while avoiding unnecessary inverse amplification in future noisy real sensors.

## 3. Primary ordering score: finite-ensemble block CRPS

For sensing block `b`, let

- `Y_b = g(mean measured_ppm over block b)`;
- `X_{s,m,b} = g(mean forward-sensor-predicted ppm for candidate s, member m, block b)`;
- `g(x) = log(1 + max(x,0)/0.1 ppm)` using the already frozen physical threshold as reference, not a tuned scale.

Define the finite-ensemble Continuous Ranked Probability Score:

`CRPS_b(s) = (1/M) sum_m |Y_b-X_{s,m,b}| - (1/(2M^2)) sum_{m,n} |X_{s,m,b}-X_{s,n,b}|`.

Lower is better.

At source-update `u`, rank candidates by the cumulative prequential score

`L_u(s) = sum_{b <= u} CRPS_b(s)`.

This deliberately:

- preserves M2: the complete nuisance ensemble matters;
- removes M3: no nuisance member is assumed to remain a coherent realization through the complete path;
- removes M4: no hand-built adjacent-difference channel;
- uses the actual PMFS sensing-block observation scale rather than treating every 0.2 s sample as an independent evidence unit;
- requires no learned weights, neural network, temperature, threshold search, GADEN rerun, or source-outcome tuning.

A sample-level marginal CRPS may be reported as a secondary diagnostic only. The frozen primary is block-level CRPS.

## 4. Why this is not an arbitrary simplification

The previous multivariate energy score asks whether one complete nuisance trajectory resembles the complete observed trajectory. Actual source-update evidence says coherent nuisance identity is not beneficial and can be harmful. PF-MEI instead asks the probabilistic-forecast question supported by M2: at each observed context, does the candidate's predictive distribution assign good proper-score support to what was measured?

This matches modern ensemble forecast methodology. In atmospheric forecasting, finite stochastic ensembles are explicitly evaluated and trained using proper scores such as CRPS; recent examples include AIFS-CRPS (npj Artificial Intelligence, 2026) and probabilistic weather ensemble work such as GenCast (Nature, 2024). The methodological transfer here is from ensemble forecast verification to source inference under stochastic plume transport, not a claim that CRPS itself is new.

## 5. A0 replacement is conditional on ordering success

Do not construct a posterior until the raw PF-MEI ordering gate passes.

If ordering passes, replace rank-Gaussian A0 with a proper-score generalized posterior:

`q_u(s) proportional to q0(s) * exp(-beta * L_u(s))`.

The scalar `beta` must never be fitted to H01 historical localization error or selected after looking at held-out source ranks. It must be frozen using simulator-only pseudo-observations with strict member exclusion, e.g. leave-one-member-out predictive calibration on designated development members, minimizing logarithmic score of the known simulated source under a predeclared calibration split. One global beta is then reused across environments if cross-House validation supports it.

This preserves the correct area prior `q0(s)` while giving the proper score a calibrated evidence scale. No rank-to-Gaussian transform remains.

## 6. Deployment consequences

If PF-MEI succeeds, the final online mechanism is lightweight and training-free at deployment:

- new environment: map + source-carrier support + physics ensemble + source-independent sensor/wind calibration;
- no House-specific neural training;
- no source labels required in the new environment;
- online scoring is O(S*M^2*B) in the direct form and can be reduced by precomputing the ensemble pairwise term per block/candidate;
- source-update scoring should be far below the PMFS sensing/update interval.

The global generalized-Bayes calibration scalar, if later authorized, is a one-time cross-environment method parameter rather than per-room retraining.

## 7. Decision tree after the cheap ordering gate

- If block-CRPS substantially improves actual-update ordering and removes most severe early failures: proceed to simulation-only beta calibration, still no neural network.
- If block-CRPS improves late ranking but update 1 remains non-informative: design a source-independent evidence-readiness / safe-fusion rule while baseline PMFS continues; do not force an early PF-MEI update.
- If block-CRPS does not materially improve ordering: stop this direct proper-score backend. Only then consider a compact shared nonlinear likelihood-ratio / SBI model, with H01 explicitly treated as development data and H02/H03 reserved for clean cross-environment testing.

No closed-loop experiment is authorized until raw ordering and score-to-posterior calibration pass separately.
