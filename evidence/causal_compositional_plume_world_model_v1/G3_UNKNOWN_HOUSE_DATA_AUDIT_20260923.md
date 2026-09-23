# M4-v2 G3 unknown-House data audit

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`  
Decision: **HOLD — UNKNOWN-HOUSE DATA NOT AVAILABLE**

This is a read-only asset audit. It does not launch GADEN, consume a new
plume seed, train a model, replay PMFS, or touch the ROS/live loop. The
machine-readable result is
`c0_5_real_gaden_bank/g3_unknown_house_asset_audit.json`, produced by
`research/causal_compositional_plume_world_model_v1/audit_g3_unknown_house_assets.py`.

## Frozen G3 requirement

The committed
[`G3_UNKNOWN_HOUSE_TRANSFER_HARD_GATE_20260923.md`](G3_UNKNOWN_HOUSE_TRANSFER_HARD_GATE_20260923.md)
requires at least two held-out Houses with source-blind training on other
Houses, a physical wind family held out in the target House, two independent
target-House plume seeds, spatial fields, and a predeclared sensor-shift
evaluation. Truth-containing source-candidate rank remains the hard endpoint.

## Asset audit

| Requirement | Read-only finding | Status |
|---|---|---|
| Canonical geometry/wind assets for Houses 01/02/03 | Occupancy files and canonical 11-iteration wind directories exist for all three Houses | **READY as infrastructure** |
| Held-out House spatial plume bank | No `concentration.npy` spatial field bank exists for House01 or House03 | **UNAVAILABLE** |
| Two independent seeds in a held-out House | Existing HCMC native runs contain sensor/wind trajectories, but no spatial concentration field bank or C0.5 source×wind manifests | **UNAVAILABLE** |
| Entire unseen physical wind family with target fields | Canonical wind files exist, but no held-out-House plume fields generated under that family | **UNAVAILABLE** |
| Sensor-shift field bank | No predeclared sensor-shift field artifacts were found | **UNAVAILABLE** |
| Truth-source rank endpoint | No G3 target-House candidate-field replay/evaluation exists | **UNAVAILABLE** |

The current compact spatial bank has eight files, all explicitly tagged
`House02` (`S1/S2 × W1/W2 × seedA/seedB`). It is retained as a local
same-House physical precondition and data-integrity record. It cannot serve as
an unknown-House target. Existing HCMC native runs at
`/home/zyc/hcmc_v1_native_runs_20260922/H01..H03` contain trajectory-level
`sensor_trace.csv` and `wind_trace.csv`, not the required spatial plume field
bank. The older H03 filament directory is a single raw realization without a
paired source×wind×seed manifest and is not substituted into G3.

## Gate result

Because the target-House spatial fields, two independent target seeds, and
sensor-shift bank are absent, no leave-one-House-out model comparison, source
rank endpoint, or null interpretation is scientifically authorized. The
correct result is **HOLD**, with no architecture or threshold tuning.
