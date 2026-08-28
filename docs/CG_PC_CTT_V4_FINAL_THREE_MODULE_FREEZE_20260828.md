# CG-PC-CTT V4 final three-module freeze — science-contract revision

Date: 2026-08-28
Status: **REFERENCE SCIENCE CONTRACT FROZEN / C++ HOLD UNTIL THREE-HOUSE TRUTH-BLIND COVERAGE AUDIT**

## Paper-level innovation

**Causal Spatiotemporal Representation and Assimilation for Robotic Gas-Source Localization**

The method remains exactly three paper-level modules:

1. **M1 — Spatiotemporal Transport Representation**
2. **M2 — Cross-Context Invariant Causal Source Residual**
3. **M3 — Observation-Resolved Minimum Causal Assimilation**

LOSO, component construction, coherent transport marginalization, the absolute null, and KL projection are internal mechanisms, not separate headline innovations.

## M1 — physical-stop representation and observation-resolved source components

For source carrier `s`, keyed transport realization `m`, and physical stop `j`,

`p[s,m,j] = P(hit at stop j | source s, transport member m, observed context R_j)`.

One transport member is one coherent realization across every stop. Member identity cannot be re-selected per stop.

The inferential unit is one **physical stop**, not one completed measurement block. For `B_j` repeated blocks,

`r_j = (1/B_j) sum_b y_jb`.

All repeated blocks at one stop have total source-likelihood weight one. An explicit monotone `physical_stop_id` defines stop identity; floating-point position equality does not.

Probability continuity floor:

`eps_T = 0.5/(T+1)`, where `T=settings.iterationsToRecord`.

### Calibration-member component construction

Calibration members `m=0..3` define only the observation-resolved spatial quotient. Scoring outcomes are not consulted.

Using the actual stops in the current window, construct transport covariance `C_tr` from pairwise calibration-member response differences and add the frozen conservative one-stop observation covariance

`C_y = (1/4 + eps_T^2) I`.

Then

`C_eff = C_tr + C_y`

is strictly positive definite. Its inverse gives finite precision in low-transport-variance/stable-complement directions rather than deleting them with a Moore-Penrose cutoff.

For every adjacent persistent carrier pair `(i,j)`, calibration-member stop-response differences `d_m` define

`eta_ij = ( ||sum_m d_m||^2_{C_eff^-1} - sum_m ||d_m||^2_{C_eff^-1} ) / (M(M-1))`.

The boundary is resolved only if `eta_ij > numerical_zero` and every leave-one-calibration-member-out value is also `> numerical_zero`. Otherwise the carriers are united. Exact geometric aliases are always united. Connected components are the only macro-regions M2/M3 may act on.

The canonical executable definition is `build_components(...)` in `experiments/cg_pc_ctt/v4_final_reference.py`.

## M2 — coherent cross-context source residual with absolute adequacy

For scoring members `m=4..7`, use the unit-weight fractional-Bernoulli proper score

`ell_j(s,m) = r_j log p[s,m,j] + (1-r_j) log(1-p[s,m,j])`.

For a LOSO fold holding out stop `h`, preserve one source/member identity across training stops:

`L_-h(s,m) = sum_{j != h} ell_j(s,m)`.

Training source evidence is

`L_-h(s) = logmeanexp_m L_-h(s,m)`.

With frozen geometry-prior conditional weights `q0(s|C)`, training component evidence is

`A_-h(C) = logsumexp_{s in C, q0(.|C)} L_-h(s)`.

All LOSO folds must have exactly one common numerically best component `B`.

### Held-out conditional prediction

The held-out score must not restart a uniform member mixture. It is the exact conditional posterior-predictive score under the joint latent `(source, transport member)` within component `C`:

`A_h(C) = log [ sum_{s in C} q0(s|C) mean_m exp(L_-h(s,m)+ell_h(s,m)) ]`
`         - log [ sum_{s in C} q0(s|C) mean_m exp(L_-h(s,m)) ]`.

This is the binding correction for the prior member-identity-switch counterexample.

### Frozen source-independent absolute null

The candidate family cannot validate itself. Each fold therefore also uses a source-independent Jeffreys-Beta prequential null, fixed before localization outcomes:

`theta ~ Beta(1/2, 1/2)`.

Using training physical stops only,

`a_h = 1/2 + sum_{j != h} r_j`,
`b_h = 1/2 + sum_{j != h} (1-r_j)`,
`rho_h = a_h/(a_h+b_h)`.

Held-out null score:

`N_h = r_h log rho_h + (1-r_h) log(1-rho_h)`.

This null contains no source identity, candidate prediction, House id, seed, truth, route, or localization error. It is allowed to condition on training outcomes but never on the held-out outcome when forming `rho_h`.

### ACCEPT contract

Require at least three physical stops and at least two observation-resolved components. ACCEPT only if:

1. every LOSO training fold shares one common component `B`;
2. on every held-out stop, `A_h(B)` does not lose to any rival component;
3. on every held-out stop, `A_h(B) - N_h > numerical_zero`;
4. at least two held-out stops have a strictly positive rival margin;
5. deleting any one scoring transport member cannot reverse the accepted component.

Any failure => **ABSTAIN**.

The old geometry-prior mixture of the candidate family is no longer an adequacy null.

## M3 — minimum causal assimilation

Maintain an independent causal carrier distribution `q_C`, initialized once from geometry prior `q0`. Each accepted raw window updates only the validated binary contrast `B` versus its complement. Raw windows are consumed exactly once. A later ABSTAIN does not replay them.

Let the accepted causal state assign

`alpha = Q_C(B)`

and current native PMFS posterior assign

`beta = Q_N(B)`.

Final posterior is the KL-nearest distribution to native PMFS subject only to the validated floor:

`q* = argmin_q D_KL(q || q_N)` subject to `Q(B) >= alpha`.

Closed form:

- if `beta >= alpha`: return native PMFS **exactly**;
- if `beta < alpha`: raise only `B` to mass `alpha`, preserving native conditional proportions inside `B` and outside `B`.

ABSTAIN returns native PMFS exactly. No posterior reset, temperature, arbitrary blend, or House/seed-specific confidence threshold exists.

## Scientific regression tests now binding

`selftest_v4_final_reference.py` must pass before any C++ translation. It includes:

- physical-stop collapse and prediction-drift contract;
- `eps_T` semantics;
- finite stable-complement precision;
- exact-coordinate alias behavior;
- calibration/scoring-member and candidate permutation invariance;
- the shared-common-bias counterexample (`0.01` versus `0.005` under observed hits) => ABSTAIN;
- the fixed member-identity-switch counterexample => no incoherent ACCEPT;
- 10,000 randomized KL/I-projection checks;
- consumed-window replay rejection;
- exact native output when the mass-floor constraint is inactive.

The NumPy axis semantics in `coherent_source_score()` are part of the contract: stops are summed **inside each member** before `logmeanexp_m`.

## Pre-C++ actionability gate

Before C++ work, materialize the archived H01/H02/H03 development OFF source-update contexts into the truth-free NPZ schema consumed by

`experiments/cg_pc_ctt/v4_truthblind_coverage.py`.

Run the frozen M1/M2 rule without truth or localization error and publish House-wise ACCEPT/ABSTAIN counts and reasons.

Mechanical stop conditions:

- zero ACCEPT across all three Houses => `STOP_ZERO_ACTIONABILITY`;
- ACCEPT occurs in only one of H01/H02/H03 => `STOP_SINGLE_HOUSE_ACTIONABILITY`.

These are feasibility checks only; they cannot be used to tune M1/M2 thresholds.

If coverage is actionable, C++ translation/parity/smoke may proceed. Only after those pass may the fixed development matrix run:

`H01/H02/H03 × seeds 0..9 × OFF/ON = 60 arms`.

Seeds 0..9 remain development-only. Fresh seeds 10..19 are confirmatory only after a frozen development GO.

`CODEX_CPP_AUTHORIZATION = CONDITIONAL_ON_TRUTHBLIND_COVERAGE`
