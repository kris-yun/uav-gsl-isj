# MDBIL-D0 pre-analysis freeze

Date: 2026-10-01  
Branch: `research/mdbil-d0-source-weather-invariance-20261001`

## Question

Test whether the frozen observations contain a learned latent block that is source-discriminative but stable across non-source contexts:

```
E(O) -> (z_s, z_m)
```

`z_s` is the source block; `z_m` is the context/meteorology-sensitive block. This is a block-invariance feasibility test, not a claim that a causal source variable has been recovered.

The prior result `CDSI_T01B_SOURCE_INFORMATION_STATIC_ONLY_HOLD` stays unchanged. T0.1B tested a fixed Energy statistic; MDBIL-D0 asks a different question: whether supervised sufficiency + invariance can learn a source block that transfers to an unseen context.

## Frozen inputs and split

Use only the SHA-bound 64 CDSI tensors:

- `evidence/cdsi_t01b/pass1/EXACT_64_RUN_MANIFEST.tsv`
- `evidence/ocb_r2/mechanism_census_r0/inputs/<run_id>.pooled.npy`

Tensor shape is 10x30 and the frozen binary definition is C>0. No new GADEN runs or result-driven source/seed/probe/time/threshold/wind/gas selection.

Within each House, hold out one of four complete contexts and train on the other three: 8 folds total. Each held-out context also has one same-gas training sibling with a different wind condition, producing a direct same-gas cross-wind stability audit.

## Arms and frozen objectives

RAW: flattened 300D cosine prototype baseline.  
STATIC: 30D time-mean cosine prototype baseline, included because CDSI-T0.1B previously found static source information.  
VANILLA: same small TCN trained for source discrimination + prototype ranking.  
MDBIL: same TCN with two 8D latent blocks.

MDBIL uses source CE, same-source/different-context supervised contrastive loss, source-conditional mean/covariance alignment, context CE from z_m, gradient-reversal context suppression from z_s, cross-block covariance penalty, reconstruction from [z_s,z_m], and source prototype ranking.

Training seeds are exactly 2026100101, 2026100102, 2026100103. Scientific fold metrics use the median over these three seeds.

## Frozen gates

G1 passes only if median MDBIL held-out accuracy >=0.75, at least 6/8 folds >=0.75, median source margin >0, and at least 7/8 folds have positive margin.

G2 passes only if median general invariance ratio <0.75, at least 6/8 folds have ratio <1, median same-gas cross-wind ratio <1, and at least 6/8 folds have same-gas cross-wind ratio <1.

G3 passes only if MDBIL median accuracy is within 0.125 of the best RAW/STATIC/VANILLA median accuracy; median general ratio gain is positive versus all three baselines; at least 6/8 folds improve general ratio versus RAW, STATIC, and VANILLA; and median same-gas cross-wind ratio gain is positive versus all three.

G4 passes only if median z_m leave-one-out context accuracy >=2/3, median z_s context-leakage reduction versus VANILLA is nonnegative, and at least 5/8 folds have non-worse z_s context leakage.

Decisions:

- G1 fail -> `MDBIL_D0_NO_STABLE_SOURCE_BLOCK_STOP`
- G1-G4 all pass -> `MDBIL_D0_SOURCE_WEATHER_BLOCK_SIGNAL_PASS`
- otherwise -> `MDBIL_D0_SOURCE_BLOCK_SIGNAL_HOLD`

Even PASS means only source-configuration (x,y,z) block stability across the frozen contexts. The A/B sources differ in z, so this is not pure XY identifiability. It is not a PMFS ranking result.

After D0: STOP. No result-driven tuning, GADEN, PMFS, H03 confirmation, or closed loop.
