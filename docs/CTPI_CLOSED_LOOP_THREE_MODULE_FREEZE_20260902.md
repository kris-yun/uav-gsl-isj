# CTPI three-load-bearing-module freeze

## Terminal objective

The method is a closed causal loop, not three parallel diagnostics:

`M1 predictive law -> M2 source posterior -> M3 next action -> new observation -> M1/M2`.

Every main module must improve at least one robot-task metric and must not
significantly worsen final localization error.  Formula correctness, response
geometry, posterior change, action change, or a successful ROS launch is not a
sufficient module Gate.

## M1 — CREL physical prediction

M1 retains the coherent member-level route encounter law produced under each
candidate source intervention.  The M1-only arm deliberately exposes the
frozen F00 mean projection and count likelihood so its downstream contribution
can be compared with authoritative PMFS as `F00 vs A0`.

## M2 — complete-law proper-score assimilation

For a visible prefix of `N` stops, each candidate source has eight coherent
member counts `K_sm`.  Let `n_s(h)` be the number of members whose cumulative
count equals the observed `H`.  The source-independent Jeffreys categorical
predictive probability is

`P(H|s) = [n_s(H)+1/2] / [M + (N+1)/2]`.

F01 is formed directly from `q0(s) P(H|s)`.  Every source-update snapshot is a
fresh current-prefix posterior; dependent prefixes are not multiplied.  Native
PMFS source evidence is not multiplied into F01, so the same gas observation
is owned exactly once.

Unlike V0.4's member-mean Bernoulli score, this operator consumes the complete
empirical count law and can distinguish equal-F00-mean laws.  Unlike a Gibbs
posterior from RPS, it introduces no likelihood temperature.  RPS/CDF geometry
remains a mechanism and robustness diagnostic.

## M3 — predictive-information action selection

M3 is the active form of distributional identifiability.  It is not the PSRG
local scale and never treats that scale as a localization confidence radius.

For each unchanged feasible next action `a`, compute each source's finite-member
binary predictive probability `p_sa`, then

`I(S;Y|a) = H(sum_s q_s p_sa) - sum_s q_s H(p_sa)`.

Select maximum information.  Exact ties use minimum native travel cost, then
stable action index.  No tunable information/distance mixture is introduced.
M3 must be isolated by `F11 vs F01` in a true closed loop and must improve final
error, error AUC, or time-to-2m without significant final-error worsening.

## Frozen arm ladder

| Arm | Prediction | Inference | Action |
|---|---|---|---|
| A0 | native | native | native |
| F00 | CREL mean projection | count likelihood | native |
| F01 | CREL complete count law | categorical proper score | native |
| F11 | CREL complete count law | categorical proper score | predictive-information action |

`F10` may be added only as an interaction diagnostic; it is never the unique
M3 Gate.

## Execution boundary

First run the frozen H01/H02/H03 route-tape factorial for A0/F00/F01.  It uses
the already-generated route bank and invokes neither GADEN nor ROS.  Only a
cross-House M1+M2 PASS authorizes runtime implementation, parity, full-grid
action-support coverage audit, and one four-arm closed-loop smoke.  The smoke,
not offline geometry, is the first possible M3 effectiveness Gate.

Prepared-site closed-loop validity and unknown-site bank-free deployment are
separate claims.  The latter still requires a bank-free CREL provider.
