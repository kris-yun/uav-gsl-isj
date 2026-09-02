# CTPI V0.4 offline development audit

Date: 2026-09-02

## Verdict

`CTPI_V04_DEVELOPMENT_GO_TO_VM_EXACT_OFFLINE_AND_RUNTIME_PARITY`

This is narrower than paper-level GO or unrestricted closed-loop GO.

## Local data used

### H01 K4 development bank
- 4 House01 configurations.
- 9 source updates each = 36 contexts.
- 4 stochastic transport response maps per candidate/context.
- Current PMFS measured-hit-probability and confidence fields.
- Truth was evaluator-only after scores were formed.

### FULL60 historical package
- H01/H02/H03 x seeds 0..9 x updates 1..5 = 150 contexts.
- Used only for PSRG cross-House geometry because it does not contain the same four-member K4 ensemble required for the full CREL/APRS test.

## M1 CREL

The frozen CPIR exact-route audit remains the strongest causal-M1 evidence. On the H01 K4 development bank, four-member marginalization gave:

- ensemble top-error mean `3.532279 m`;
- equal-member mean single-member top-error `3.590425 m`;
- reduction `1.619%`;
- mean truth proper-score gain `+0.063704`.

This is a modest ensemble-marginalization increment, not the main M1 claim.

## M2 PSRG — H01 mechanism test

With exact quadtree shared-edge neighbours and no radius/kNN tuning:

- support count vs median local resolution scale: Spearman `rho=-0.873704`, `p=3.53e-12`;
- support count vs truth-nearest local scale: `rho=-0.691827`, `p=2.97e-6`;
- truth-nearest local scale vs native true-source rank: `rho=+0.648603`, `p=1.88e-5`;
- truth-nearest local scale vs native map error: `rho=+0.510526`, `p=0.001466`;
- real source-coordinate local response fit beats source-label shuffle in `36/36` contexts;
- median real/shuffle fit-residual ratio `0.584346`;
- leave-one-transport-member-out resolution-ranking Spearman: minimum `0.972581`, median `0.984917`.

### FULL60 cross-House diagnostic

Support vs median local resolution scale:

- H01 `rho=-0.088987` (not stable here);
- H02 `rho=-0.608671`, `p=2.74e-6`;
- H03 `rho=-0.977148`, `p=6.14e-34`;
- pooled `rho=-0.597945`, `p=6.53e-16`.

Truth-error relations are mixed/confounded. Therefore PSRG passes only as a **local response-metrology object**, not a calibrated global uncertainty measure.

A direct misuse test rejects the confidence-radius interpretation: using the top candidate's `1/sqrt(lambda_min)` as a localization error radius covered truth in `0/36` H01 contexts; median error/scale ratio was `20.55`.

## M3 APRS — correct current-object H01 development test

Primary V0.4 APRS uses the transport-marginal probability and the **current** measured-hit-probability/confidence field; it does not use a future window.

Mean top-location error over 36 contexts:

- C0 `4.436277 m`;
- APRS `3.532279 m`;
- reduction `20.377%`.

Time-normalized AUE:

| H01 config | C0 | APRS | improvement |
|---|---:|---:|---:|
| `1,3-2,4_fast` | 6.284571 | 5.622457 | 10.536% |
| `1,3-2,4_slow` | 5.242443 | 5.190324 | 0.994% |
| `2,4-1_fast` | 4.106721 | 1.272085 | 69.024% |
| `2,4-1_slow` | 2.085563 | 2.042253 | 2.077% |

AUE improves in `4/4` H01 development configurations. Equal-configuration mean normalized AUE is `4.429825 -> 3.531780`, a `20.273%` reduction.

Truth-nearest source rank is mixed in some configurations; V0.4 does **not** claim universal rank improvement.

### Destructive and finite-member controls

- real top-location error beats the per-context canonical source-law-reassignment median in `36/36` contexts;
- median fraction of reassignment controls with worse error `0.701371`;
- leave-one-member-out score-ranking Spearman: minimum `0.964466`, median `0.993528`;
- median top-error shift after dropping one member `0 m`; maximum `2.391628 m`.

## Negative result retained

Using update-u response maps to predict the later `u -> u+1` measurement window was worse than C0: `12` rank wins / `20` losses over 32 windows and mean error worsened. This is the **stale-context negative control**. V0.4 must recompute/condition CREL on current runtime transport context rather than reusing an old response field as a future plume forecast.

## Authorization boundary

Local evidence supports:
- CREL causal physical response: supported/inherited;
- PSRG local metrology premise: development PASS with calibration limitation;
- APRS current-field scorer: H01 development PASS with destructive/LOO controls.

Local evidence does not establish:
- three-House four-member APRS improvement under one exact route-bank contract;
- bank-free unknown-site CREL;
- C++/Python runtime parity;
- no-double-consumption PMFS integration;
- active PSRG planner benefit;
- unseen-seed closed-loop paper-level confirmation.

Those are VM/Codex stages.
