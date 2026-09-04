# CTPI-G2 M3 code and contract audit

Date: 2026-09-04
Base: `c5949c8a89b4d360fe239a3c8948890a5dd84a36`

## VERIFIED — old exploit definition

The actual uncommitted benchmark script was recovered from the preserved VM at
`/tmp/_tmp_m3_falsification.py` (SHA-256
`3bdaa79ee4fe5d883dbc3827ba40c2305b76f356f5129b73f89c95ace096c090`).
Its exploit branch computes:

`score_exploit(a) = sum_s pi_t(s) C_hat_M2(s,a)`

and chooses the largest score among unvisited actions. It is therefore a
**predicted-concentration exploit**, not posterior-MAP navigation and not a
measured-concentration chase. The previous report changes labels midway and its
root-cause interpretation is not reliable until corrected to this definition.

## VERIFIED — current G2 M2 observation interface

The current G2 runtime in `CTPI.cpp` computes a deterministic Gaussian-plume-like
response. M3 then maps that response to `C/(C+0.3)`. No calibration evidence is
attached to that map. The file still contains the older calibrated
`tsdcProbability(count,sensorState)`, but the current G2 action scorer never
calls it; moreover, its input is the removed eight-member site-specific bank.

The G2 L0 reports describe an advection-diffusion numerical concentration/peak
field. The scripts that produced those reports existed only under VM `/tmp` and
were not committed. They also produce deterministic concentration means, not a
validated probability distribution.

Therefore the statement “current bank-free M2 already supplies a calibrated
Bernoulli observation law to M3” is false. Proper EID code can be implemented
now, but a scientific M3 PASS must wait for a separately frozen and qualified
`p(Y|S,a,h_t)` adapter. Deterministic concentration must not be relabelled as a
likelihood.

## VERIFIED — carrier-center bug

`evaluateCTPIActionInformation()` parses each region carrier and substitutes a
single geometric center. This violates the region-valued source contract. The
new offline reference instead accepts physical-placement predictions and
marginalizes uniformly over all free placements inside each carrier, excluding
obstacles before normalization. The same marginalized law feeds myopic and H2.

## NEW RESULT — proper H2 reference implementation

`experiments/cg_pc_ctt/ctpi_g2_m3_nonmyopic.py` implements exact binary posterior
branches and

`Q2(pi,a0) = I(pi,a0) + sum_y p(y|pi,a0) max_a1 I(pi^y,a1)`.

It supports first-action and transition-dependent second-action feasibility,
never constructs a posterior from an expected observation, and contains no
posterior multiplier, distance penalty, discount, or tunable explore/exploit
weight.

The deterministic self-test proves posterior normalization, finite handling of
zero-probability branches, different posteriors for different observations, a
constructed case with different second actions by branch, H2 degeneration to
myopic, and obstacle-aware carrier marginalization.

## GATE STATUS

`CODE_CORRECTNESS_PASS`, but `M3_SCIENTIFIC_GATE_NOT_RUN` because the current
bank-free M2 has no qualified observation distribution. Running the held-out
policy comparison with `C/(C+0.3)` would create a fast but invalid positive or
negative result. The pre-registration freezes the gate before that adapter and
the held-out outcomes are evaluated.
