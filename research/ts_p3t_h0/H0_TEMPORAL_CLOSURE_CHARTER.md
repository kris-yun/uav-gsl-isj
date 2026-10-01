# TS-P3T-H0 — Temporal Closure / State-Sufficiency Audit

Date: 2026-10-01
State: FINAL PRE-REGISTRATION / OFFLINE ONLY

## 1. Hypothesis

PMFS treats source location s as if it were sufficient to define a candidate observation distribution:

p(y | s).

But for a partially observed, advected plume the physically relevant process is:

z_(t+1) = F(z_t, W_t, s)
y_t = G(z_t, xi_t)

where z_t is the hidden transport/plume state, W_t is flow, and xi_t is UAV pose.

If observations accumulated over hundreds of seconds are scored against a source-only forward that repeatedly resets z to an empty state and rolls out only ~40 s, the likelihood may be non-closed in time.

H0 asks:

> Does matching the observation-memory horizon to the frozen ~40 s candidate horizon restore true-source compatibility?

A positive answer does not prove the final world model. It establishes that the stateless source-only likelihood is temporally insufficient and licenses a separate persistent-state oracle.

## 2. Cases

Exactly the four R1/D0 historical cases:

- House01_seed0_off_off
- House01_seed1_off_off
- House02_seed0_off_off
- House02_seed1_off_off

Terminal update times are frozen from R1:
- H01/s0 275.8 s
- H01/s1 279.6 s
- H02/s0 274.2 s
- H02/s1 275.6 s

Use the exact authoritative historical TNQC archive used by the R1 transfer audit. Do not substitute HCMC or newer native runs.

## 3. P0 raw-history provenance gate

Before any scientific scoring, locate and hash the exact R1-parent artifacts required to reconstruct the observation side:

Preferred:
- PMFS measurement-event log if retained;
- pose/wind/sensor traces;
- source-update timings;
- frozen launch/runtime parameters;
- occupancy and map metadata.

The raw/event artifacts must be linked to the same authoritative TNQC package and terminal snapshots used by R1 through existing hashes/manifests.

Then reproduce the archived terminal \`measured_hit_probability.csv\` with the frozen PMFS measurement update semantics.

Required numerical parity:
- logOdds max absolute error <= 1e-10;
- omega/confidence max absolute error <= 1e-10;
- same free/obstacle support;
- same terminal source-update time.

If exact reconstruction is impossible because the authoritative event stream is absent or ambiguous:
\`TS_P3T_H0_INVALID_STOP\`.

Do not borrow event traces from a different run.

## 4. Frozen observation-memory arms

All arms use the same PMFS measurement-update code, parameters, geometry, event ordering and wind semantics.

At terminal time t* construct:

### O_full
Exact archived full-history observation map.

### O_40
Reset the hit-probability map to the same prior at t*-40 s and replay only the exact measurement events in the final 40 s.

40 s is fixed because the candidate forward records 200 x 0.2 s.

### O_update
Reset to the same prior at the previous source-update time and replay only events since that update.

This is a second, algorithm-native recency control. Its duration is determined by frozen source-update timing, not tuned.

No other window length is part of the scientific gate.

## 5. Frozen candidate predictions

Do not generate any new candidate forward.

Read the already frozen D0 maps/scores for:
- P2
- P3
- G2
- G3

For each observation-memory arm, recompute the unchanged PMFS likelihood for all candidates from the saved hit maps.

Primary mechanistic arm is G3 because it is the strongest physically grounded 3-D representation tested in D0.

P3 is a mandatory robustness check.
P2/G2 are descriptive controls.

## 6. Source-blind temporal-memory diagnostics

Before opening source truth, write and hash:

For every case:
- number of measurement events in full / O_40 / O_update;
- O_40 and O_update durations;
- fraction of terminal omega/confidence accumulation contributed before t*-40 s;
- L1 and cosine differences between O_full and O_40 probability/logOdds fields on free cells;
- candidate rank correlation between O_full and O_40 for P3/G3, without using truth;
- all candidate scores under every observation-memory arm.

No truth may enter map construction, candidate selection, window choice or scoring.

## 7. Truth evaluation

After source-blind score freeze, report for P3 and G3:

- truth log score;
- truth midrank and pessimistic rank;
- truth-vs-best-wrong margin;
- truth ties;
- number of cells where predicted truth hit probability >0 and observation confidence >0;
- number of those cells with observation probability above prior.

Compare:
- O_40 vs O_full (primary);
- O_update vs O_full (robustness).

## 8. Frozen decision gate

### A. Primary O_40 temporal-closure signal

A case is a primary temporal-closure improvement for G3 if:
- truth log score increases;
- truth midrank improves;
- source margin improves.

\`PRIMARY_TEMPORAL_CLOSURE\` requires:
- >=3/4 improved cases;
- median truth-rank improvement >=10 positions;
- no more than one case with worse truth rank.

### B. Algorithm-native robustness

O_update must show the same direction in >=3/4 cases for:
- truth log score;
- truth rank;
- source margin.

### Decisions

- provenance/reconstruction failure:
  \`TS_P3T_H0_INVALID_STOP\`

- A passes and B passes:
  \`TS_P3T_H0_TEMPORAL_STATE_INSUFFICIENCY_SIGNAL\`

- A passes but B fails, or >=2/4 cases show consistent improvement:
  \`TS_P3T_H0_HOLD_PARTIAL_TEMPORAL_SIGNAL\`

- otherwise:
  \`TS_P3T_H0_NO_TEMPORAL_CLOSURE_SIGNAL_STOP\`

P3 must also be reported. If only G3 passes while P3 moves oppositely, classify as HOLD pending representation interaction; do not promote the state-sufficiency claim.

## 9. Interpretation boundary

A positive H0 establishes only:

> the stateless short-horizon candidate likelihood is incompatible with the long-memory observation state, and source-only state is not an adequate temporal closure for this frozen scoring setup.

It does **not** prove:
- a learned world model;
- 3-D latent superiority;
- task-sufficient compression;
- flow equivariance;
- closed-loop improvement.

A positive H0 authorizes H1 only:

> a full-history persistent physical oracle that keeps hidden transport state alive and queries it along the UAV trajectory, compared against the recency-forgetting baseline.

Only H1 may decide whether persistent state is better than simply forgetting old measurements.

## 10. Strict STOP

After H0 decision: STOP.

No new GADEN.
No new candidate forward.
No neural training.
No H03/confirmation.
No ROS closed loop.
No threshold/window tuning.
