# CSTAR composition theory — why M1, M2 and M3 are one method rather than three add-ons

Date: 2026-09-06
Status: mathematical design note; empirical House gain is not asserted.

## 1. Common downstream object

For a candidate future route `tau`, source posterior `pi`, and source-conditioned future observation law `P_s^tau`, define

`B(tau; pi, P) = sum_{i<j} sqrt(pi_i*pi_j) * BC(P_i^tau, P_j^tau)`

where `BC(P,Q)=sum_y sqrt(P(y)Q(y))` is the Bhattacharyya coefficient.

Small `B` means the posterior-relevant source alternatives predict distinguishable future observations on that route. PHS selects the feasible route minimizing this quantity (equivalently maximizing normalized resolution).

This one object exposes a clean role for every module:

- M1 controls the source-pair weights `sqrt(pi_i*pi_j)`;
- M2 controls the source-conditioned future laws and therefore each `BC`;
- M3 controls which route `tau` is executed.

## 2. M3 model-space dominance over the native route

Let `T` be the finite feasible route set and require the native PMFS route `tau_native` to be included in `T` whenever it is feasible. Let

`tau_hat = argmin_{tau in T} B(tau; pi_hat, P_hat)`.

Then by construction

`B(tau_hat; pi_hat, P_hat) <= B(tau_native; pi_hat, P_hat)`.

Thus PHS has no need for a separate action gate or `20x` exploitation multiplier: under its currently supplied posterior/predictive model it cannot select a route with worse pairwise confusion than the included native route. This is **model-space** dominance only; prediction error can still make the physical outcome worse, which is why M1/M2 calibration gates remain mandatory.

## 3. M2 prediction error gives a direct PHS score-error bound

Use the Hellinger convention

`H^2(P,Q) = 1 - BC(P,Q)`.

Suppose for one route and each source `s`, M2 law error satisfies

`H(P_s, P_hat_s) <= epsilon_s`.

By the triangle inequality,

`|H(P_i,P_j) - H(P_hat_i,P_hat_j)| <= epsilon_i + epsilon_j`.

Since Hellinger distance lies in `[0,1]`,

`|H^2(P_i,P_j) - H^2(P_hat_i,P_hat_j)| <= 2*(epsilon_i+epsilon_j)`.

Therefore

`|BC(P_i,P_j) - BC(P_hat_i,P_hat_j)| <= 2*(epsilon_i+epsilon_j)`.

Holding the posterior fixed, the route-confusion error due only to M2 is bounded by

`Delta_M2(tau) <= 2 * sum_{i<j} sqrt(pi_i*pi_j)*(epsilon_i+epsilon_j)`.

Consequently the M2 gate is directly meaningful to M3: reducing held-out Hellinger/first-passage distribution error reduces an explicit upper bound on route-score error. Average concentration RMSE alone would not provide this link.

## 4. M1 posterior error is the other explicit route-score term

Holding future laws fixed, let true/calibrated posterior be `pi` and M1 output be `pi_hat`. Since every Bhattacharyya coefficient is in `[0,1]`,

`Delta_M1(tau) <= sum_{i<j} |sqrt(pi_i*pi_j) - sqrt(pi_hat_i*pi_hat_j)|`.

Thus M1 does not merely provide a heat map for exploitation. Its posterior calibration directly determines how much PHS emphasizes each competing source pair.

This is why the M1 offline gate must include a proper source score/calibration measure, not only MAP distance.

## 5. Combined planner robustness statement

Let

`delta(tau) = Delta_M1(tau) + Delta_M2(tau)`

be an upper bound on the difference between true route confusion and the route confusion computed from PICR+CPO. If `delta(tau) <= delta_max` over all feasible routes, then

`B_true(tau_hat) <= B_true(tau_native) + 2*delta_max`.

Reason: PHS is no worse than native under the estimated score, and each estimated/true score differs by at most `delta_max`.

This does not guarantee a physical localization improvement; it gives a falsifiable route by which M1 and M2 predictive quality controls M3 decision risk. Improving M1 without M2, or M2 without M1, shrinks different terms of the same bound.

## 6. Relation to the incremental arms

- `F00-A0` tests whether M1's improved causal source posterior has downstream value under the native information planner.
- `F10-F00` tests whether choosing a route by pairwise prospective resolution has downstream value when the predictive provider is held fixed.
- `F11-F10` tests whether reducing M2 future-law error improves the identical PHS planner.
- `F11-A0` tests the complete causal experiment loop.

The full paper may only call all three modules load-bearing if the corresponding empirical increments agree with this directional interpretation.

## 7. Required diagnostic metrics

To make this theory testable, log/report:

M1:
- candidate proper log score / Brier score;
- posterior Hellinger/TV calibration against evaluator truth offline;
- pair-weight error term above;
- spatial error and source rank.

M2:
- per-source/per-route Hellinger error of the first-passage law;
- NLL/Brier and committor calibration;
- empirical `Delta_M2` bound.

M3:
- native-route and selected-route estimated `B`;
- held-out realized/empirical source confusion where available;
- route changes and tie-breaks;
- whether native route was included in every valid decision set.

Full:
- correlation between predicted confusion reduction and actual subsequent source-posterior/source-error improvement. If that relation is absent, the composition mechanism is not supported even if final AUC happens to improve.
