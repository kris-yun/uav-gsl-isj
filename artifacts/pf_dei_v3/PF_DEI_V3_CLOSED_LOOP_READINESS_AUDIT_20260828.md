# PF-DEI V3 closed-loop readiness audit — 2026-08-28

## Verdict

`NOT_READY_FOR_PERFORMANCE_CLOSED_LOOP`

The V3 simulator plumbing is credible, but the main innovation mechanism has not yet been shown to improve relative source evidence. Running the 60-arm matrix now would test an unimplemented/unqualified inference engine and would repeat the prior failure pattern in which engineering activation was mistaken for scientific validity.

## What is genuinely closed

1. Persistent PMFS source hypotheses are represented as regions rather than invalid carrier centroids.
2. Every H01/H02/H03 carrier has legal 3-D placement support inside its own region.
3. The isolated GADEN RNG hook preserves default native output exactly and produces seed-dependent plume realizations in all Houses.
4. Native physical query and run-persistent sensor-forward smoke/parity pass.
5. Small contract-valid physical banks can be generated reproducibly.

These results remove source-support, stochastic-member and sensor-forward implementation blockers. They do not establish correct source ranking.

## Previous failure mechanism versus current evidence

The observed multi-seed regression was caused at the decision level by unreliable candidate-relative evidence: on some trajectories a wrong basin was more compatible with the simplified transport/observation model than the true carrier. Posterior gates and confidence repairs could not recover source support after it had been ranked incorrectly.

V3 is scientifically aimed at this failure by replacing blockwise handcrafted evidence with a causal, candidate-conditioned simulation-based ratio estimator over the complete measured prefix while marginalizing legal intra-region placement, stochastic transport and persistent sensor dynamics. This is the correct location for the main innovation: before Bayesian accumulation, where it can change relative carrier ordering.

However, no V3 causal-TCN/NRE implementation, trained weights, reserved synthetic qualification, or 30-run truth-blind future-predictive result currently exists. Therefore there is no evidence yet that the failure mechanism is solved.

## Shortest defensible route to closed loop

Only three pre-runtime gates remain scientifically indispensable:

1. **Generator freeze:** build one streaming native generator over the frozen carrier regions, 8 joint training members, 4 reserved members and source-independent trajectory skeletons; store compact scheduled traces rather than full fields.
2. **Inference qualification:** implement the frozen causal-TCN exactly once and require reserved synthetic carrier-identification PASS.
3. **Truth-blind historical prediction:** freeze weights, then require the prescribed 30-run future-predictive PASS. This directly tests whether candidate ordering generalizes on H01/H02/H03 without reading source truth or localization error.

After these pass, run offline safety, Python/runtime parity and six 300-second infrastructure smokes. Only then is the 60-arm OFF/ON matrix scientifically interpretable.

## Fast engineering decisions

- Stream only scheduled concentration/sensor samples and save compressed arrays; do not materialize full 3-D fields for every carrier/member/trajectory.
- Reuse the ten existing OFF pose/time skeletons per House after stripping gas/source labels.
- Generate the fixed random training/qualification skeletons once and hash-freeze them.
- Keep the two existing long-running forward-closure player processes untouched.
- Write large bank shards to host-backed storage because the VM root has only about 5.1 GiB free.
- Do not add thresholds, gates, active probes, network sweeps or seed-specific changes.

## Honest time estimate

The remaining work is implementation plus computation, not merely launching an existing binary. With no new engineering failure, the fastest credible path to the first meaningful scientific verdict (truth-blind future-predictive PASS/NO-GO) is roughly 8–16 wall-clock hours. The six smoke runs and 60-arm matrix add roughly 4–10 hours depending on safe parallelism and simulator startup time. A result within minutes is not credible.
