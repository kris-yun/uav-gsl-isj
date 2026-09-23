# M6 Novelty Audit v3 — ST-GasNet Pretrained Plume-Prediction Boundary

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## New strong near-neighbor

Wang et al., *Spatiotemporal predictions of toxic urban plumes using deep learning*, PNAS Nexus 4(6), 2025, pgaf198.

The paper proposes ST-GasNet.

It:
- learns from high-resolution LES toxic urban plume sequences;
- receives early-time plume behavior;
- incorporates large-scale wind boundary-condition information;
- predicts late-time plume evolution on independent plume sequences;
- explicitly targets complex urban/building plume transport.

Therefore M6 must NOT claim:
- first pretrained/deep model for unseen plume prediction;
- first learned urban plume temporal predictor;
- first plume network using wind boundary information;
- first ML model that predicts unseen toxic-plume evolution.

## Important distinction

ST-GasNet is **gas/plume-specific supervised pretraining/training**.

Its representation is learned from toxic plume sequences themselves.

M6 instead tests:

> whether a physics foundation representation pretrained **before seeing gas-plume labels**, across broad geometry–dynamics simulation data, transfers into PMFS with very little gas-specific supervision.

This is a transfer-learning / scientific-foundation-model hypothesis, not merely another plume predictor.

## Task distinction

ST-GasNet:
- forward temporal plume forecasting;
- early plume observations -> future plume.

M6:
- candidate-source forward modeling for inverse localization;
- geometry + wind + hypothetical source injection -> candidate plume/hit prediction;
- embedded inside the PMFS source probability map and candidate ranking.

Do not overstate this distinction: both are still learned plume-forward models at a broad level.

## Strengthened hard gate

M6 now needs to beat three conceptual controls:

1. same Transolver architecture from scratch;
2. gas-specific physics-enhanced surrogate (PHOENIX-like);
3. where feasible, gas-specific pretrained/temporal plume model family.

The scientific signature must be **cross-domain pretraining efficiency**, especially under very small gas-data budgets.

## Current verdict

No direct collision found yet for:

`cross-physics dynamics-lifted foundation pretraining -> PMFS candidate-source forward model`.

But the surrounding plume-surrogate literature is crowded.

Therefore novelty language must remain narrow and evidence-based.

Status:

`KEEP — FOUNDATION-TRANSFER CLAIM ONLY`.
