# CESS D0 Intervention-Weighting Correction

Date: 2026-09-25

Status: **CORRECTED D0 STILL POSITIVE — OLD D0 NUMBERS SUPERSEDED**

## Why a correction was required

The earlier strict D0 correctly constructed each macro likelihood as a uniform
mixture of already-trained micro likelihoods. However, its held-out CE/EI
average was taken uniformly over micro-source samples.

For unequal macro cluster sizes this does **not** match the declared causal
intervention distribution:

[
p(M=m)=1/M,qquad p(S=smid M=m)=1/|S_m|.
]

The corrected evaluation first averages held-out log posterior within each
macrostate, then averages equally across macrostates.

No new data and no new hierarchy were used.

## Corrected result

Using the same 18-source ×16-realization R0 panel and the same two 8/8 splits:

| M | Split A raw EI | Split B raw EI | average raw EI |
|---:|---:|---:|---:|
| 18 micro | 0.942668 | 1.670282 | **1.306475** |
| 12 | **2.232506** | **1.779616** | **2.006061** |
| 9 | 2.122174 | 1.479088 | 1.800631 |
| 6 | 1.689025 | 0.889777 | 1.289401 |
| 4 | 1.325793 | 1.332761 | 1.329277 |
| 3 | 1.098612 | 1.098612 | 1.098612 |
| 2 | 0.693147 | 0.693147 | 0.693147 |

The primary fact survives correction:

> M=12 exceeds the 18-microstate raw EI lower bound in both independent split
> directions.

Average gain at M=12:

[
2.006061-1.306475 = 0.699586 {m nats}.
]

## Corrected size-matched random control

For M=12, using 250 random non-spatial partitions with the identical
cluster-size vector:

- spatial average EI: **2.006061 nats**
- random mean: **0.957498**
- random 95th percentile: **1.395902**
- spatial percentile: **0.996**

Therefore the corrected positive signal is not explained by merely reducing
the class count or by the M=12 size vector.

## Interpretation boundary

This still does **not** prove causal emergence because:

- only 18 sparse source locations are represented;
- the result was discovered post-R0;
- the macro hierarchy is sparse-panel geometry;
- the Bernoulli decoder is a lower-bound measurement instrument.

The corrected D0 authorizes only a dense, pre-registered >=143-source
falsification gate.

## Mainline design consequence

The previously frozen 630×8 D1 should **not** be executed as written.

Two changes are required before any new GADEN work:

1. use correct intervention-weighted EI everywhere, including random controls
   and uncertainty intervals;
2. use a cheaper dense >=143-source first knife with R0-supported 8/8
   train/validation rather than spending 5040 simulations immediately.

The next frozen gate is CESS D1A.
