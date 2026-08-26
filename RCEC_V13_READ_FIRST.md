# READ FIRST — RCEC V13

**Repository:** `kris-yun/uav-gsl-isj`  
**Branch:** `codex/rcec-v13-materialized-20260826`

The authoritative current entrypoint is:

`RCEC_V13_AUDIT_READ_FIRST.md`

Read that file before this historical overview.

## Active method after audit

RCEC V13 v2 has three layers:

1. **ACIT** — frozen V11 amplitude-conditioned inverse-transport even/odd causal views plus existing spatiotemporal identifiability;
2. **CREI** — lower-envelope consensus of the **current post-native/pre-RCEC PMFS absolute candidate rank**, even causal rank and odd causal rank;
3. **TMEM** — candidate-wise temporal median of CREI scores across identifiable source updates.

Final generalized source state is rebuilt from the frozen geometry-only prior. There are no adaptive weights, temperatures, truth/error gates, House-specific settings, or new inverse-transport parameters.

The earlier native log-increment definition is rejected because it could subtract a previous source state already containing V11/RCEC injection. Do not use the old native-increment evidence files as the active method.

## Required materialization order

```bash
python3 tools/fix_rcec_v13_native_absolute.py
python3 tools/close_rcec_v13_build_dependency.py
python3 reference/verify_rcec_v13_build_closure.py
python3 reference/verify_rcec_v13_source.py
```

Only after all contracts and the isolated ROS build pass may Codex continue to parity/regression/new-seed qualification.

## Same-binary ablation

Keep `pfdi_mode=me_aci` and select exactly one:

```bash
RCEC_V13_ARM=v11_stouffer
RCEC_V13_ARM=crei_latest
RCEC_V13_ARM=rcec_full
```

No variable is A1 V11 parity.

## Corrected development shadow evidence

Authoritative files:

- `evidence/rcec_v13/rcec_v13_native_absolute_pairs_v3.csv`
- `evidence/rcec_v13/rcec_v13_native_absolute_summary_v3.json`
- `analysis/rcec_v13_native_absolute_offline_replay.py`

On 15 already revealed archived V11 trajectories:

- A1: +9.077%, 11/15, 1 catastrophe;
- A2: +13.178%, 13/15, 0 catastrophes;
- A3: +16.354%, 15/15, 0 catastrophes.

These are fixed-trajectory development shadow results, **not** new closed-loop confirmation.

CTT/HMM/count-survival files may remain in repository history but are not part of RCEC and must not be activated in this branch.
