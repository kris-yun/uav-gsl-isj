# Nonequilibrium irreversibility / entropy-production transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Nonequilibrium stochastic thermodynamics interprets broken time-reversal symmetry through directed probability currents and entropy production.

Relevant 2025–2026 scite anchors:
- *Coarse-graining nonequilibrium diffusions with Markov chains*, J. Stat. Mech. 2026, DOI 10.1088/1742-5468/ae4f7d.
- *Force Geometry and Irreversibility in Nonequilibrium Overdamped Dynamics* (2026), arXiv:2603.29416.
- *Evaluation of the probability current in the stochastic path integral formalism*, J. Phys. A 2025, DOI 10.1088/1751-8121/adf534.

## Transfer tested

For each source hypothesis:
- rank-state its simulated hit field along the actual robot trajectory;
- form a joint discrete state with measured gas-presence;
- estimate directed empirical probability flux;
- compute coarse-grained entropy-production / time-reversal-asymmetry proxy;
- subtract candidate-only irreversibility and robot-to-candidate geometry irreversibility;
- infer the source from the excess sensor/plume irreversibility.

A family of state counts K=3,4,5 and lags 1,2,5,10 was screened.

To avoid selecting the numerically best member, the final development screen used median candidate ranks across all 12 configurations.

## Joint old+new result

Consensus:
- mean error = **3.8628 m**
- pooled reduction = **33.22%**
- non-worse = **10/12**
- old six = **43.59%**, 6/6
- new six = **23.64%**, 4/6

## Mechanism controls

Final-leaf permutation, 500 repetitions:
- null mean = **4.4426 m**
- null as good as/better than real = **8.6%**

Candidate-identity mismatch, 50 repetitions:
- null mean = **4.3578 m**
- null as good as/better than real = **14%**

Both violate the failure-informed <=5% mechanism gate.

The screen was stopped at this point rather than selecting the best K/lag configuration or tuning the coarse-graining.

## Decision

The nonequilibrium mother theory is strong and the old/new transfer is better than HCMC, but source identity is not sufficiently load-bearing.

Final verdict:
`IRREVERSIBILITY_ENTROPY_PRODUCTION_GSL_TRANSFER_NO_GO_20260922`

Do not tune state count, lag, pseudocount, or event threshold on these same 12 cases.
