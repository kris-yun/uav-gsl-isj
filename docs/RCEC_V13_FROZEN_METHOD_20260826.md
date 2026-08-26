# RCEC V13 v2 — Replicated Causal Evidence Consensus

Status: **FROZEN CANDIDATE FOR IMPLEMENTATION/PARITY, NOT YET CLOSED-LOOP QUALIFIED**

Formula marker after materialization:

`rcec_v13_acit_crei_native_absolute_tmem_v2`

This document supersedes the earlier RCEC draft that used a native log-increment against the pre-native source state. That increment definition is rejected because the pre-native state can contain the previous V11/RCEC injection, creating feedback coupling and making archived V11 shadow replay different from a true RCEC recursion.

## Scientific premise retained from V11

The V11 multiseed failure did not show that causal/spatiotemporal information disappeared. V11 improved 11/15 revealed pairs and pooled about 9.08%, but missed the preregistered >=10% threshold and had one catastrophic regression. The failure mode is therefore treated as a robustness/tail problem: one misspecified causal ranking can sometimes dominate the source state.

RCEC does not replace the V11 scientific premise. It adds two orthogonal robustness layers around it.

## M1 — ACIT + existing spatiotemporal identifiability

M1 is the frozen V11 source-abduction channel.

For candidate source `s`, completed hit/miss events are scored under the frozen 54-member inverse-transport nuisance family. Even and odd event-index folds produce candidate-relative normal ranks

`z_even,t(s)` and `z_odd,t(s)`.

The existing truth-blind release condition is unchanged:

- both temporal folds must contain at least one hit and at least one miss;
- hits must occupy at least two distinct spatial cells.

No truth coordinate, final localization error, posterior distance threshold, House-specific rule, temperature or learned calibration enters M1.

## M2 — CREI: Cross-view Replicated Evidence Intersection

### Rejected first draft

Do **not** use

`log M_native,after - log M_native,before`

where `M_native,before` is the pre-native source state. In the online stack that state may be the source distribution injected by the previous V11/RCEC update. Subtracting it feeds the method's previous output back into its supposedly native view and makes the old fixed-trajectory replay recursion-inconsistent.

### Frozen v2 definition

Let `M_native,t(s)` be the candidate-region mass of the **current native PMFS source update after the native PMFS update and before ME-ACI/RCEC injection**. Normalize/rank this current state only:

`z_native,t(s) = NormalRank_s[M_native,t(s)]`.

Then define the cross-view lower envelope

`c_t(s) = min(z_native,t(s), z_even,t(s), z_odd,t(s))`.

Interpretation: a source candidate receives high consensus support only when the current native PMFS ordering and both replicated causal temporal views do not strongly veto it.

This is **not** a product of independent likelihoods and is not called a Bayes factor. PMFS and ACIT may consume overlapping gas observations. CREI is an order/rank consensus operator, so the scientific claim is robust cross-model agreement, not probabilistic independence.

There is no fusion weight, alpha or temperature.

## M3 — TMEM: Temporal Median Evidence Memory

For each identifiable source update, append its CREI vector to candidate-aligned history. The active robust score is the candidate-wise median

`m_t(s) = median_{u <= t, identifiable} c_u(s)`.

The final generalized source state is rebuilt from the frozen geometry-only design prior:

`q_t(s) proportional to q0(s) exp(m_t(s))`.

The median is defined for every history length; there is **no additional minimum-three-update gate**. At one snapshot it equals that snapshot; at two snapshots it is the two-value median; from three snapshots onward it obtains the usual single-outlier resistance property.

TMEM is an order-statistic robust memory, not a multiplication of independent temporal likelihoods. ACIT snapshots are cumulative and therefore statistically dependent. Do not claim independent replicates, exact Bayesian posterior coverage, or an anytime-valid theorem.

## Candidate identity / state boundary

RCEC history is keyed by stable candidate IDs. If the candidate ID vector changes, runtime must fail/abstain rather than silently align mismatched candidates.

`initializeMap()` must clear:

- `rcecV13CandidateIds`
- `rcecV13ConsensusHistory`

so no temporal memory can leak across map/run initialization.

## Same-binary ablations

Keep `pfdi_mode=me_aci` and select one arm at process launch:

- `RCEC_V13_ARM=v11_stouffer`: frozen V11 A1 parity arm;
- `RCEC_V13_ARM=crei_latest`: M1 + M2, latest CREI only;
- `RCEC_V13_ARM=rcec_full`: M1 + M2 + M3.

No `RCEC_V13_ARM` is equivalent to `v11_stouffer`.

The purpose is to run ablations without recompiling different formulas.

## Corrected revealed-data fixed-trajectory shadow audit

Authoritative development contract:

`RCEC_V13_NATIVE_ABSOLUTE_FIXED_TRAJECTORY_AUDIT_V3`

Fifteen already revealed V11 pairs were replayed from archived candidate score/native-shadow files. The score reconstruction never read source truth; truth was used only by the external final-error evaluator.

V11 posterior replay integrity:

`max_abs = 8.257283745649602e-16`.

Results on the **archived V11 trajectories**:

| Arm | Pooled improvement vs frozen OFF | Improved pairs | Catastrophic regressions |
|---|---:|---:|---:|
| A1 V11 Stouffer | 9.077% | 11/15 | 1 |
| A2 ACIT + native-absolute CREI | 13.178% | 13/15 | 0 |
| A3 A2 + TMEM | 16.354% | 15/15 | 0 |

A3 per-House pooled improvements:

- House01: 23.041%
- House02: 9.775%
- House03: 14.300%

A3 worst revealed pair improvement: +1.821%.

Revealed catastrophic stress case H01/seed653959:

- frozen OFF: 4.607520 m
- V11 A1: 6.362662 m
- corrected A2: 5.216955 m
- corrected A3: 4.318013 m

These values are **development evidence only**. They are not a dynamic RCEC closed-loop replay because robot trajectories were produced by archived V11 runs. They justify proceeding to implementation/parity/new-seed testing; they do not confirm closed-loop generalization.

Also do not claim every module improves every individual pair. A3 improves the aggregate/tail profile and all final pair signs in this revealed set, but some individual A3 errors are worse than A2.

## Prohibited changes before qualification

Do not add or tune:

- adaptive weights;
- temperatures;
- House/seed-specific rules;
- truth/error gates;
- planner parameters;
- ACIT 54-member ranges;
- temporal/spatial identifiability thresholds;
- a rolling-memory window selected from revealed outcomes.

Do not resume the rejected CTT HMM/count-survival path in this RCEC branch.

## Required qualification sequence

1. Materialize native-absolute v2 correction.
2. Close the incomplete dormant V12-M build dependency.
3. Pass build-closure verifier, source verifier and RCEC core test.
4. Pass isolated ROS build.
5. PMFS OFF parity.
6. A1 `v11_stouffer` parity against frozen V11.
7. Revealed H01/seed653959 A1/A2/A3 mechanism regression only.
8. Freeze materialized source commit and binary SHA before viewing any new-seed truth.
9. Run genuinely unseen H01/H02/H03 full-300 s OFF vs `rcec_full` pairs.

Any new compiler/runtime contract failure must stop the sequence. Do not repair it by copying untracked workstation code or by tuning scientific parameters.
