# CTPI-G2 three-module status after proper H2 falsification

Date: 2026-09-04

| Module | Evidence now verified | Honest status |
|---|---|---|
| M1 | H01 three-seed closed-loop development screen, error AUC -3.6%, 2/3 wins; likelihood and source-seeking navigation changed together | `H01_DEVELOPMENT_LOAD_BEARING_PASS`; not yet a cross-House final qualification |
| M2 | leakage-free all-carrier H02/H03 field gate against current Gaussian plume; all four criteria pass in both Houses | `CROSS_ENVIRONMENT_PREDICTION_PASS`; downstream closed-loop utility still inconclusive |
| M3 | proper exact binary H2 with qualified held-out observation adapter, 128 paired worlds | `PROPER_H2_NO_GO` (22/106 versus myopic) |

The earlier handoff was directionally correct about M3's code bugs, but too
strong about the overall three-module state. It misidentified the old exploit
and conflated the legacy bank-based TSDC Bernoulli law with the current G2
bank-free deterministic predictor. After repairing those issues, M2 now has a
defensible predictive PASS, while the proposed proper H2 M3 is decisively not
effective.

Therefore “all three modules are proved effective” is currently false. The
fastest scientifically valid outcome was to establish M2 and falsify M3 before
another expensive closed loop. Preserving this NO-GO prevents a paper claim
from resting on a mathematically correct but empirically harmful planner.
