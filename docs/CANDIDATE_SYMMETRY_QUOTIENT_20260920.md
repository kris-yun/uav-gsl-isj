# Candidate main theme: physics-symmetry quotient inference
Date: 2026-09-20

## Why this branch survives the current screen

The previous dynamic-operator branch did not survive a source-identity falsification test. A Koopman/ARX-style operator descriptor was evaluated on the open Orebro3DSEN gas-dispersion data (10 experiments; 27 MOX sensors; 2 Hz). Five experiments share the same physical source location while changing release strength and/or airflow. Dynamic operator descriptors did not cluster same-source experiments reliably:

- 5 min windows: operator-spectrum proxy same-vs-different AUC 0.409, leave-condition-out accuracy 0.02.
- 10 min windows: AUC 0.463, accuracy 0.04.
- Wind-residualization only raised AUC to about 0.55 and accuracy to 0.38–0.44.
- Time-shuffled controls were of comparable order, so the observed dynamic signature is not strong enough to justify a Koopman/TimeBridge-style main claim.

Therefore KoopSTD / operator invariance is **rejected as the main innovation**. It may remain a diagnostic only.

## New organizing principle

Treat gas-source localization as inference on a **quotient observation space**: remove physically non-identifying nuisance transformations before computing source evidence, rather than asking a model to learn through them.

This is not generic “invariance.” The proposed main scientific principle is:

> **A source hypothesis should be compared only through observables that are invariant/equivariant under known plume nuisance symmetries; nuisance-group coordinates should be analytically canonicalized or marginalized before posterior updating.**

The remote-domain inspiration is the 2025 canonicalization/equivariance line:
- Shumaylov et al., *Lie Algebra Canonicalization: Equivariant Neural Operators under arbitrary Lie Groups*, ICLR 2025.
- Tahmasebi & Jegelka, *Generalization Bounds for Canonicalization: A Comparative Study with Group Averaging*, ICLR 2025.
- Lawrence et al., *Improving Equivariant Networks with Probabilistic Symmetry Breaking*, ICLR 2025.
- Li et al., *Affine Steerable Equivariant Layer for Canonicalization of Neural Networks*, ICLR 2025.

These works establish canonicalization as a modern route for exploiting continuous/non-compact symmetries and show that deterministic canonicalization and group averaging occupy different regimes.

## Exact physics connection to the existing successful V10 mechanism

### 1. Unknown release/sensor strength is a nuisance-group coordinate

For binary hit events, write

```
logit p_i(s, theta, beta) = beta + psi_i(s, theta)
```

where `beta` absorbs unknown release strength / sensor threshold / common log-odds offset.

The nuisance group is the additive Lie group `R` acting as

```
psi_i -> psi_i + beta   for all i.
```

Conditioning on total hit count `K=sum_i y_i` gives

```
P(y | K, s, theta)
  = exp(sum_i y_i psi_i)
    / e_K(exp(psi_1), ..., exp(psi_n)),
```

so `beta` cancels exactly. The existing ME-ACI conditional likelihood is therefore naturally interpretable as **quotient inference under a one-dimensional nuisance symmetry**, not merely an ad-hoc normalization trick.

### 2. Wind-relative coordinates are an SO(2)-invariant representation

The current transport score uses source-relative wind coordinates `r_parallel` and `r_perp`. Under a simultaneous planar rotation of the displacement vector and wind vector, these quantities remain unchanged. Thus the observation model is already operating in a canonical wind-relative frame.

This gives a coherent main-theme interpretation of two previously separate design choices:
- spatial frame canonicalization (rotation symmetry);
- release/sensor nuisance quotienting (logit-shift symmetry).

### 3. Sequential replication gate becomes an identifiability condition

The existing temporal-fold + distinct-hit-cell gate should no longer be presented as a disconnected heuristic. Its role is to prevent quotient evidence from being released when the canonical representative is not identifiable from the accumulated observations.

This gives a single paper-level line:

**symmetry quotient -> identifiable canonical evidence -> posterior release.**

## Public-data falsification result

Dataset: Burgués et al. Orebro3DSEN open indoor gas-dispersion data.

Important experimental structure from the dataset table:
- Exp01 and Exp02: same source coordinate, different release strength.
- Exp06: same source coordinate, DC-fan airflow.
- Exp08 and Exp09: same source coordinate, tower-fan airflow and different release strengths.
- Remaining experiments use different source coordinates.

Using only 40–90 min windows and no source truth inside the feature computation:

| representation | 2 min same/diff AUC | 5 min AUC | 10 min AUC | 5 min leave-condition-out source accuracy |
|---|---:|---:|---:|---:|
| raw mean concentrations | 0.483 | 0.483 | 0.483 | 0.20 |
| L1 scale quotient | 0.783 | 0.783 | 0.769 | 0.80 |
| z-normalized spatial canonical form | 0.886 | 0.883 | 0.880 | 0.82 |
| rank invariant | 0.846 | 0.843 | 0.843 | 0.80 |

After linear removal of wind-summary leakage, the scale-quotient / rank / z canonical forms remain strongly source-discriminative; for 5–10 min windows leave-condition-out accuracy reaches 0.96–1.00 on the five repeated-source experiments. Raw concentration remains poor.

Interpretation: **source identity is much more stable in the nuisance-quotiented spatial representation than in raw amplitude or in the rejected dynamic-operator representation.** This is the first branch in the current search cycle whose physics principle and data screen point in the same direction.

This is still a development/proxy result, not a final localization claim.

## Novelty boundary / collision scan

A 2026 GSL line already exists on calibration-free rank features:
- Jin, Duranceau, Erünsal & Martinoli, ICRA 2026, *Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking*.
- Jin, Arias Mitjà & Martinoli, DARS 2026, *Probabilistic Multi-Robot Gas Source Localization with Uncalibrated Sensors: A Distributed Estimation Approach*.

Therefore the paper must **not** claim “invariance to sensor scaling” or “rank-based calibration-free localization” as its novelty.

The defensible novelty target is narrower and deeper:
1. formulate source inference as a quotient/canonicalization problem under explicit physical nuisance groups;
2. derive the conditional source likelihood as exact nuisance-group elimination;
3. couple deterministic canonicalization with an identifiability/symmetry-breaking rule for weakly aligned regimes;
4. use the resulting quotient posterior inside the existing PMFS closed loop.

## Candidate module structure

### Main innovation — QCI: Quotient-Canonicalized Inference
Analytically remove known nuisance-group coordinates before source evidence accumulation. The current conditional inverse-transport likelihood is the first concrete instance.

### Auxiliary 1 — alignment-aware canonicalization vs group averaging
Recent canonicalization theory shows a phase distinction between canonicalization and group averaging. For GSL:
- strong directional alignment (reliable wind): canonicalize to the wind frame;
- weak/ambiguous alignment: do not impose an arbitrary frame; marginalize/group-average directional evidence.

This directly targets the physical pathology of near-zero wind, where direction is poorly defined.

### Auxiliary 2 — replication-based symmetry breaking
When observations remain self-symmetric or insufficiently identifying, delay committing to a broken-symmetry source mode. Release posterior evidence only after independent temporal folds and multiple spatial hit locations support a stable representative. This is the existing reservoir gate reinterpreted under the symmetry framework.

## Immediate next falsification gates

1. Verify on House01/02/03 event traces that low-wind windows produce larger directional-canonicalization instability than higher-wind windows.
2. Compare deterministic wind-frame scoring against an orientation-marginalized/group-averaged variant in low-wind subsets, with all thresholds frozen before truth evaluation.
3. Confirm that the quotient likelihood is invariant to synthetic common logit shifts / release-amplitude perturbations while native PMFS likelihood is not.
4. Search the 2024–2026 GSL literature specifically for Lie-group, quotient-space, or canonicalization formulations; reject this branch if an essentially identical formulation already exists.
5. Only after these gates pass, elevate symmetry quotienting from “candidate” to the paper's main organizing principle.


## 2026-09-20 late-cycle status

The offline branch has now advanced to a frozen closed-loop candidate.

Additional conservative measured-data probes confirm that a local spatial-adjacency order channel carries repeated-source signal across 2/5/10 min windows and is exactly preserved under condition-specific strictly monotone sensor transforms. It is retained only as an auxiliary robustness channel because ICRA 2026 already establishes global concentration-ranking GSL.

The VGR project-data screen has now corrected the online combination rule twice:
- centered confidence-weighted logit-field cosine is the privileged exact affine quotient;
- local spatial adjacency order is a broader monotone-invariant corroboration channel;
- unconditional 1:1 fusion was falsified on H02/fast/SA because it overrode a correct affine decision;
- the first per-candidate sign guard was later rejected by a ranking counterexample: candidate signs can be preserved while the order between two hypotheses is still reversed;
- the current **candidate-bank quotient-channel concordance gate** computes one shared non-negative strength (g_u=max(0,C_u)) from pairwise agreement between the affine and local-order candidate rankings, then uses (e_i=g_u q_{aff,i});
- because the same (g_u>=0) multiplies every candidate, the auxiliary channel may attenuate/abstain but cannot reverse affine candidate ordering;
- quotient evidence remains bounded in [-1,1], avoiding sqrt(cell-count) pseudo-replication.

On the actual VGR 0.3-m PMFS spatial grid, the affine quotient is 12/12 at 240 s. The corrected bank gate releases 11/12 cases and is 11/11 correct; across all 100 source-blind positive-scale and 200 source-blind monotone-compression stress seeds it retains 11/12 coverage with 100% conditional accuracy. This is a fixed-route mechanism result, not the final localization endpoint.

Frozen record: `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json`.

Status: **VGR MECHANISM POSITIVE; 300-S VGR LOCALIZATION GATE PENDING; CLOSED LOOP HOLD.**
