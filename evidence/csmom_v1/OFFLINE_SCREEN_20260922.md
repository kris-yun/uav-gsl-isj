# CS-MoM V1 — authoritative R2 offline screen

Date: 2026-09-22  
Decision: **STAGE-2 POSITIVE / CONTINUE FALSIFICATION**

## Frozen evidence source

Release asset:
\`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz\`

SHA256:
\`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708\`

The uploaded copy was byte-hash verified against the GitHub Release asset before extraction.

## Predeclared robust scale

The runtime already fixes:
- cell size 0.3 m;
- kernelSigma 0.5 m;
- confidenceSigmaSpatial 0.5 m.

Thus \`ceil(2*0.5/0.3)=4\` cells is used as the robust spatial block width.

No source truth or endpoint result participates in that choice.

## Translation-invariant CS-MoM

For each candidate:

1. retain the exact native PMFS cell loss;
2. for each of all 16 origins of a 4×4 block lattice, average loss within each spatial block and take the median block mean;
3. take the median across the 16 origin-level risks;
4. multiply by candidate support count;
5. use the unchanged exported final quadtree partition and softmax;
6. evaluate the unchanged 300 s top-5% ExpectedValue endpoint.

## Results

| Case | Native error (m) | CS-MoM error (m) | Direction |
|---|---:|---:|---|
| House01 seed0 | 5.527 | 7.213 | worse |
| House01 seed1 | 4.002 | 3.490 | better |
| House02 seed0 | 4.107 | 1.797 | better |
| House02 seed1 | 3.701 | 1.934 | better |
| House03 seed0 | 7.782 | 1.623 | better |
| House03 seed1 | 8.212 | 7.578 | better |

Pooled:
- native = **5.5551 m**
- CS-MoM = **3.9393 m**
- improvement = **29.09%**
- non-worse = **5/6**
- false-confident collapse = **0/6** versus native **6/6**

## Destructive controls

Random cell grouping with the same target 16 cells/block, 30 seeds:

- mean endpoint = **5.3150 m**
- mean improvement = **4.32%**
- best random seed = 4.8917 m
- 17/30 seeds still have 5 false-confident-collapse cases;
- 10/30 have 4 collapses.

Therefore the strong gain depends on coherent spatial blocking at the correlation scale, not merely on replacing a sum with a median.

Temperature and fixed-half-cell controls are much weaker and cannot explain the result.

## Current failure

House01 seed0 is the blocking counterexample:
- native: 5.527 m
- CS-MoM: 7.213 m.

No case-specific repair is allowed.

The next screen must seek a source-blind diagnostic of when block-MoM is trustworthy. If no such diagnostic exists, the main-candidate status must be reconsidered.

## Claim boundary

This evidence supports:

> **spatially correlated robust evidence aggregation is a plausible load-bearing mechanism for the R2 false-confidence pathology.**

It does not yet support:
- a closed-loop performance claim;
- universal robustness;
- a theorem that PMFS cell errors follow an adversarial contamination model;
- a claim that MoM itself is new.

Closed loop remains prohibited until the failure analysis and temporal/source-blind gates pass.
