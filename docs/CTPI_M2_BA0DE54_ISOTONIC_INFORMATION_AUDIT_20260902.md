# CTPI M2 `ba0de54` isotonic-information audit

Audited candidate: `GLOBAL_POSTERIOR_WEIGHTED_ISOTONIC_EVENT_RELIABILITY` from commit `ba0de54311b762a22ba43a712b4f60a37b08ff5e`.

Status: `PREGEN_NO_GO_FOR_CURRENT_ISOTONIC_CALIBRATOR`.

This audit uses only the already-opened development/failure-analysis evidence in `CTPI_THREE_MODULE_OFFLINE_NO_GO_20260902_7a58f02_R3.tar.gz`. It does not use or generate M2 CAL/CONFIRM data and therefore does not contaminate future confirmatory data.

## 1. Structural statistical problem

The implemented fit constructs, for member-hit count `k`,

`W_k = sum_{j,s} pi_j(s) 1[K_j(s)=k]`

`A_k = sum_{j,s} pi_j(s) 1[K_j(s)=k] Y_j`

and then fits a monotone reliability table `g(k)`.

For each transition, the same realized event `Y_j` is fractionally copied to every candidate source according to the pre-event posterior. This is not the proper-score objective later evaluated by the confirmatory Gate.

The Gate evaluates the posterior-mixture forecast

`q_j = sum_s pi_j(s) g(K_j(s))`.

For Brier score, the source-weighted pseudo-objective obeys the exact identity

`sum_s pi_s (p_s-y)^2 = (sum_s pi_s p_s-y)^2 + sum_s pi_s (p_s-q)^2`.

The second term is a posterior-weighted variance penalty. Therefore the pseudo-fit explicitly rewards making source-conditioned probabilities similar, even though M3 requires those source contrasts to remain informative.

For log score, Jensen's inequality gives the same qualitative failure:

`-log(sum_s pi_s P(Y|s)) <= sum_s pi_s[-log P(Y|s)]`.

The implemented fractional-source fit minimizes the right-hand upper bound, not the mixture NLL scored by the Gate. The Jensen gap again penalizes heterogeneous source-conditioned probabilities and can drive the table toward a common event base rate.

Therefore a good mixture NLL/Brier result from this fit is not evidence that the source-conditioned law used by M3 is good. The fit is structurally biased toward information collapse.

## 2. Development-only cross-validation on the old 30 tapes

The frozen historical evidence contains H01/H02/H03 seed0--9 and 15 route events per case. M1's passing cadence was preserved for this audit: prior for stops 1--3, update-1 posterior for stops 4--6, update-2 for stops 7--9, update-3 for stops 10--12, and update-4 for stops 13--15.

A 10-fold leave-one-seed-out debug test was run on these old tapes only. The current isotonic formula was fitted on nine seed identities across all three Houses and evaluated on the held-out seed identity.

Results:

- held-out mixture NLL improved in 10/10 folds;
- held-out mixture Brier improved in 9/10 folds;
- fitted table had only 1 or 2 distinct values in every fold;
- the preregistered `minimum_distinct_table_values >= 3` condition would fail in all 10 folds;
- mean retained posterior-weighted source information was only `0.000373` of the raw CREL event law;
- median retained information ratio was `5.96e-05`;
- maximum fold information ratio was only `0.00172`.

Thus the old development data reproduce the exact dangerous pattern predicted by the theory:

> mixture forecast looks better while source-conditioned information required by M3 is essentially erased.

Two 5-vs-5 seed split examples are also diagnostic. One fit produced approximately

`[0.552,0.552,0.552,0.552,0.552,0.552,0.552,0.571,0.731]`,

which improved pooled held-out NLL from about `1.281` to `0.690`, but retained only about `7.6%` of the original information. The reverse split collapsed to one constant value near `0.656`, improved pooled NLL from about `0.884` to `0.654`, and reduced source information to numerical zero.

These are development diagnostics only and must not be reported as confirmatory evidence.

## 3. Why the collapse is especially likely across Houses

The old development tapes have very different empirical event prevalences:

- H01: about `0.367` hit rate;
- H02: about `0.653`;
- H03: about `0.933`.

A single global `k -> probability` reliability table fitted from posterior-weighted pseudo-labels therefore has a strong incentive to learn pooled House/event prevalence instead of preserving source/action structure. This is consistent with the observed constant or nearly constant tables.

House-specific tables are not the preferred repair because they would turn House identity into a fitted nuisance parameter and weaken cross-site generalization. The correct repair is to change the calibration experiment so that the source-conditioned law is identifiable.

## 4. The 8-member bank itself is not the blocker

The raw CREL event probabilities were audited before any new data generation. For each historical visited stop, `q_raw=(member_hit_count+0.5)/9` was evaluated across candidate sources using the frozen M1 pre-event posterior.

Posterior-weighted binary mutual-information diagnostics show substantial source discrimination:

| House | mean MI (nats) | median MI | fraction MI > 0.01 | fraction MI > 0.05 |
|---|---:|---:|---:|---:|
| H01 | 0.123 | 0.097 | 0.860 | 0.707 |
| H02 | 0.088 | 0.053 | 0.800 | 0.507 |
| H03 | 0.039 | 0.018 | 0.593 | 0.293 |

The candidate-source probability range is large in all three Houses. H03 is clearly weaker under the posterior, but not degenerate.

Across each historical 15-stop route, candidate-action variation is also substantial. The mean per-source probability range is about `0.788` in H01, `0.747` in H02, and `0.405` in H03.

Therefore the present stop condition is not "eight members contain no action/source information". The information exists; the current isotonic fit destroys most of it.

## 5. M3 opportunity diagnostic from existing route locations

A truth-blind proxy action audit was also run. At each of the five M1 decision epochs, the current M1 posterior was frozen and the predictive mutual information of the remaining historical route stops was compared with the first actually visited stop. This is not a closed-loop performance claim because the counterfactual observations are unavailable; it is only an action-discrimination diagnostic.

| House | actual-next MI mean | best remaining-route MI mean | mean opportunity gap | first action already best |
|---|---:|---:|---:|---:|
| H01 | 0.091 | 0.231 | 0.140 | 10% |
| H02 | 0.073 | 0.207 | 0.134 | 16% |
| H03 | 0.027 | 0.123 | 0.096 | 16% |

This is positive evidence that an information-seeking M3 has room to alter actions. H03 has weaker immediate information but still a sizable gap between the historical next stop and the best stop among the remaining visited-route locations.

## 6. Correct M2 identification experiment

Retain the M2 scientific role:

`P(Y_next | do(S=s), action=a, physical context)`.

Retire only the posterior-weighted latent-source calibration rule.

The source-conditioned forward law cannot be validated from observation tapes generated only at one hidden true source while keeping source identity sealed. The realized event provides only one mixture outcome; it does not directly label the counterfactual probabilities for false candidate sources.

For M2 calibration, source identity should instead be treated as a controlled simulator intervention, not as forbidden localization truth. A calibration record should be generated as

`(House, controlled_source_id, action_id, independent_world_seed, member_hit_count, observed_event)`.

The controlled source is the independent variable of a forward-model experiment. It must never enter M1 inference, localization error, planner reward, or runtime source estimation.

A direct source-conditioned reliability fit can then use

`W_k = number of controlled-source records with K=k`

`A_k = number of hits among those same records`,

followed by the preregistered Jeffreys/PAV rule if isotonic calibration is still desired. The confirmatory Gate must score `g(K)` directly against the event generated from that same controlled source, not only a posterior mixture.

This removes the posterior-smearing/Jensen problem, removes the ragged cross-House source-array problem, and validates exactly the probability object consumed by M3.

## 7. Data-budget implication

No full predictive-bank rebuild is required.

The already planned 60 independent observation worlds can be repurposed before generation into source-intervention CAL/CONFIRM worlds instead of 60 worlds at the single frozen true source. A deterministic, preregistered spatial/response-stratified source selection can allocate 10 CAL and 10 CONFIRM controlled-source worlds per House while retaining the same order of simulation cost.

The predictive bank remains read-only. CAL and CONFIRM world RNG domains remain disjoint. The old 30 tapes remain development-only.

## 8. Decision

Current implementation decision:

`GLOBAL_POSTERIOR_WEIGHTED_ISOTONIC_EVENT_RELIABILITY = PREGEN_NO_GO`.

Module-level decision:

`M2_CAUSAL_TRANSPORT_PREDICTIVE_LAW = RETAIN_AND_REIDENTIFY`.

M3 decision:

`M3_PREDICTIVE_INFORMATION_PLANNING = KEEP_CANDIDATE; ACTION_DISCRIMINATION_SIGNAL_PRESENT; CLOSED_LOOP_GAIN_NOT_YET_TESTED`.

Do not generate the currently preregistered single-true-source M2 CAL tapes. Amend the freeze before any new world is generated so that M2 is calibrated/confirmed under controlled source interventions and its source-conditioned law is directly validated.
