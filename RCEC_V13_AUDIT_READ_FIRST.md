# READ FIRST — RCEC V13 v2 audited candidate

This file is the highest-priority instruction for the current RCEC branch.

## Current status

RCEC V13 is **not yet closed-loop qualified**. Do not start parity or new-seed runs from an unmaterialized checkout.

A full static audit found a scientific defect in the first RCEC M2 draft: the native channel used a log increment against the pre-native source state. That pre-native state can already contain the previous V11/RCEC injection, so M2 was feeding the method's previous output back into its supposedly native view. The old 15-pair replay also used the previous V11 state, whereas a real RCEC run would have the previous RCEC state. Therefore the old native-increment audit is superseded.

## Active formula — v2

Materialize `tools/fix_rcec_v13_native_absolute.py` before any experiment.

M1 ACIT remains frozen V11.

M2 CREI is now:

```text
z_native,t(s) = NormalRank(current post-native/pre-RCEC PMFS candidate mass)
c_t(s) = min(z_native,t(s), z_even,t(s), z_odd,t(s))
```

There is no previous-source-state subtraction.

M3 TMEM remains:

```text
m_t(s) = candidate-wise median of identifiable c_u(s)
q_t(s) proportional q0(s) exp(m_t(s))
```

There is no extra three-update gate. The median is used for every available identifiable history length.

Formula marker:

`rcec_v13_acit_crei_native_absolute_tmem_v2`

## Why this avoids the old coupling

The native view uses only the current PMFS state after the native source update and before RCEC injection. CREI is a lower-envelope rank veto, not a likelihood product. PMFS and ACIT may use overlapping gas measurements, so no independence claim is made.

The previous RCEC/V11 posterior is not an input to CREI.

## State boundary

The materializer also adds explicit clearing of:

- `rcecV13CandidateIds`
- `rcecV13ConsensusHistory`

at map initialization. Candidate identity drift later in a run remains fail-closed.

## Corrected development shadow audit

Authoritative evidence files:

- `evidence/rcec_v13/rcec_v13_native_absolute_pairs_v3.csv`
- `evidence/rcec_v13/rcec_v13_native_absolute_summary_v3.json`
- `analysis/rcec_v13_native_absolute_offline_replay.py`

On 15 already revealed V11 pairs, fixed archived trajectories only:

- A1 V11: +9.077%, 11/15, 1 catastrophe;
- A2 native-absolute CREI: +13.178%, 13/15, 0 catastrophes;
- A3 + TMEM: +16.354%, 15/15, 0 catastrophes.

A3 House pooled: H01 +23.041%, H02 +9.775%, H03 +14.300%.

A3 worst revealed pair: +1.821%.

This is **fixed-trajectory shadow evidence**, not a dynamic RCEC closed-loop replay. It cannot establish planner/trajectory feedback or new-seed generalization.

The older files `rcec_v13_offline_15pairs.csv` / `rcec_v13_offline_15pairs_summary.json` document the rejected native-increment draft and must not be used as the active RCEC method evidence.

## Required execution order

```bash
python3 tools/fix_rcec_v13_native_absolute.py
python3 tools/close_rcec_v13_build_dependency.py
python3 reference/verify_rcec_v13_build_closure.py
python3 reference/verify_rcec_v13_source.py
```

Then isolated ROS build -> OFF parity -> A1 V11 parity -> revealed seed653959 mechanism regression -> source/binary freeze -> genuinely unseen H01/H02/H03 full-300 s qualification.

Any failure stops the protocol. Do not repair it by tuning scientific parameters, copying untracked workstation dependencies, or resuming the rejected CTT/HMM path.
