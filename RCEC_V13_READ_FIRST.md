# READ FIRST — RCEC V13 frozen candidate

**Repository:** `kris-yun/uav-gsl-isj`  
**Branch:** `rcec-v13-frozen-candidate-20260826`  
**Base checkpoint:** `3f95e646dcfa2182fde60dcad11c8b0d8a7945d2`

This branch is the single handoff point for the next Codex experiment.

## Method

RCEC V13 = three orthogonal layers:

1. **ACIT** — frozen V11 amplitude-conditioned inverse-transport even/odd causal views and existing spatiotemporal identifiability;
2. **CREI** — lower-envelope consensus of native PMFS current increment rank, even causal rank and odd causal rank;
3. **TMEM** — candidate-wise temporal median of CREI scores across identifiable source updates.

Final generalized source state is rebuilt from the frozen geometry-only prior. There are no adaptive weights, temperatures, truth/error gates, House-specific settings, or new inverse-transport parameters.

## Important implementation note

The branch was forked from the earlier CTT checkpoint so CTT diagnostic files remain in the tree. **CTT HMM/count-survival is not part of RCEC V13 and must not be activated.**

GitHub cannot execute the source materializer itself. After checkout, Codex must run:

```bash
python3 tools/apply_rcec_v13_patch.py
python3 reference/verify_rcec_v13_source.py
```

Then commit the resulting materialized `Simulations.cpp/.hpp` on a child branch and freeze that commit before new-seed truth is viewed.

## Same-binary ablation

Keep `pfdi_mode=me_aci` and use exactly one:

```bash
RCEC_V13_ARM=v11_stouffer
RCEC_V13_ARM=crei_latest
RCEC_V13_ARM=rcec_full
```

No environment variable is equivalent to `v11_stouffer` and is used for parity.

## Offline development result

On all 15 revealed V11 pairs:

- A1 V11: +9.08%, 11/15, 1 catastrophe;
- A2 ACIT+CREI: +13.35%, 13/15, 0 catastrophe;
- A3 ACIT+CREI+TMEM: +16.39%, 15/15, 0 catastrophe.

V11 posterior replay parity max absolute error: `8.257283745649602e-16`.

These are development-visible shadow results, not confirmatory evidence and not a substitute for a new closed-loop run.

## Required reading order

1. `RCEC_V13_READ_FIRST.md`
2. `docs/RCEC_V13_FROZEN_METHOD_20260826.md`
3. `CODEX_RCEC_V13_EXPERIMENT.md`
4. `evidence/rcec_v13/rcec_v13_offline_15pairs_summary.json`
5. `tools/apply_rcec_v13_patch.py`
6. `reference/verify_rcec_v13_source.py`
