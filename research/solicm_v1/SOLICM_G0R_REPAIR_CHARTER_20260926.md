# SOLICM-G0R — Repaired Latent Causal Alignment Transfer Gate

Date: 2026-09-26

Status: **NEW VERSION AFTER IMPLEMENTATION-ONLY FAILURE / ZERO-PLUME / SCIENTIFIC G0 REPEAT FROM SCRATCH**

Upstream scientific status:
- `SOLICM_G0_INCOMPLETE_NUMERICAL_FAILURE` retained for the original frozen implementation;
- original `scientific_decision = null` remains final;
- JTD/NPG/RPO STOP remain unchanged;
- RIA-A0 and RIA-A1 diagnostic conclusions remain unchanged.

## 1. Why a repaired version is justified

The original SOLICM-G0 did not reach a scientific comparison.
Independent review found three implementation-semantics failures that prevent the frozen arms from meaningfully testing the intended latent-causal-alignment hypothesis:

1. the classifier returns probabilities but those probabilities are passed to CrossEntropyLoss and softmaxed again for pseudo-label confidence;
2. `get_features` returns `z_std` in the slot used downstream as the sampled latent `z`;
3. `config.z_dim` is overwritten by input channel count, so the configured 9-D latent is not executed;
4. source-channel z-score can create target magnitudes above 8e4 because a source channel may have nearly zero variance;
5. target classifier forward updates BatchNorm running state even when the pseudo-label loss is inactive.

These are implementation questions, not scientific failures of latent invariant causal mechanisms.

## 2. Scientific mother theory remains unchanged

Primary anchor:
Cai et al., `Time Series Domain Adaptation via Latent Invariant Causal Mechanism`, IEEE TPAMI 48(3), 2026, DOI 10.1109/TPAMI.2025.3642245.

The paper's central assumption is that latent causal structure can remain stable across domains even when conditional dynamics change.

Project mapping remains:
> across House02 W0/W2 with identical source candidates and observation protocol, aligning latent temporal causal structure should improve transfer of source-discriminative evidence relative to the same latent model without cross-domain structure alignment.

Project-specific SOLICM innovation is still NOT executed at G0R.

## 3. Version boundary

G0R is NOT allowed to reuse any of the 49 original completed scientific runs.

All 96 planned configurations are rerun from scratch because the probability interface, latent path and numerical preconditioning change.

The original package remains immutable historical evidence.

## 4. Data contract

Exactly inherit original G0:
- House02 W0 `3,5-1_slow` and W2 `4,5-3_slow` only;
- same six source locations;
- same E2 30-probe contract;
- same 10 time points;
- 16 open realizations/source/domain;
- four target folds;
- three neural seeds 0/1/2;
- 0 new plume;
- no H01 DEV;
- no House03;
- no G1A 168-source training.

## 5. Repaired input preconditioner

Replace the failed per-channel source z-score with one fixed physical/numerical transform for ALL arms:

`x0 = log1p(max(ppm, 0))` elementwise.

Then compute ONE global scalar mean and ONE global scalar standard deviation on the labeled SOURCE training tensor only:

`x = (x0 - mu_source_global) / sigma_source_global`.

Requirements:
- `sigma_source_global > 0`;
- same source-fitted two scalars are applied to target-unlabeled and target-heldout;
- no target labels/statistics enter scaling;
- no channel-specific division;
- no clipping chosen from target data.

Report source and target transformed max/p99 only as numerical diagnostics.

## 6. Repaired probability interface

Classifier final layer must return RAW LOGITS.

Required semantics:
- source classification loss = `CrossEntropyLoss(logits, y)`;
- pseudo-label probabilities = exactly one `softmax(target_logits)`;
- pseudo-label confidence threshold remains frozen at 0.99;
- target pseudo-label is detached argmax of the one-softmax probability;
- exported probabilities = exactly one softmax of saved raw logits;
- target NLL/Brier are computed from those exported probabilities.

No model component may apply a terminal softmax before CrossEntropyLoss.

## 7. Repaired latent path

Honor the previously configured latent dimension:
`z_dim = 9`.

Do NOT overwrite it with the 30 input channels.

`get_features` / equivalent API must return:
- latent mean;
- bounded log-variance;
- sampled latent `z`;
as three distinct tensors.

The transition prior, KL term, sparsity term and causal-structure audit must consume the sampled latent `z`, not log-variance.

## 8. Stable variance parameterization

Let the network output raw log-variance `l_raw`.

Use:
`l = clamp(l_raw, -20, 20)`
for BOTH reparameterization and q-distribution construction.

`sigma = exp(0.5*l)` must remain finite.

This fixed bound is a numerical conformance rule and is identical for all arms and both directions.

## 9. BatchNorm semantics

Target-unlabeled data must not silently adapt classifier BatchNorm running statistics.

Required implementation split:

### source path
- source latent encoding / feature extractor / classifier execute in normal training mode;
- source batches update BN running statistics.

### target latent-generative path
- target z-net / reconstruction / latent-prior computations run as required by LCA;
- these computations do not require classifier feature-extractor BN.

### target pseudo-label classifier path
- only when pseudo-label computation is required, run the classifier feature extractor with BN running-stat updates disabled;
- BN affine parameters may receive gradient, but running_mean/running_var/num_batches_tracked must not change from target batches.

Thus any target effect in PL_ONLY must come from pseudo-label gradient, not hidden BN-state adaptation.

## 10. Four scientific arms

Keep the original scientific arm definitions:

M0 SOURCE_ONLY:
- source CE only;
- target data not passed through adaptation losses.

M1 PL_ONLY:
- source CE;
- target pseudo-label CE after epoch 30 when confidence >0.99;
- no KL/reconstruction/sparsity/structure terms;
- target BN running stats frozen.

M2 LCA_NO_ALIGN:
- repaired latent generative model;
- reconstruction/KL/intra-domain sparsity;
- pseudo-label schedule identical to M3;
- `structure_weight = 0` for cross-domain alignment.

M3 LCA_FULL:
- identical to M2 plus cross-domain latent-structure alignment weight 0.1.

No extra arm is added at G0R.

## 11. Software-conformance preflight — mandatory before scientific training

These checks use synthetic tensors and/or training inputs but NO target labels or target performance.

All must pass:

C1 — logits/CE contract:
- classifier output is unconstrained raw logits;
- synthetic correct logit [10,0,0,0,0,0] produces CE < 1e-3;
- probability export sums to 1.

C2 — pseudo-label reachability:
- the same synthetic logits produce max confidence >0.99 after one softmax;
- exactly one pseudo-label is selected at threshold 0.99.

C3 — latent API:
- configured latent dimension is exactly 9;
- mean/logvar/z all have final dimension 9;
- returned z is numerically distinct from logvar on a stochastic training forward;
- transition prior receives z.

C4 — variance finiteness:
- synthetic extreme raw logvar values remain finite after clamp/reparameterization;
- all sigma/q-logprob outputs finite.

C5 — target BN isolation:
- run one target pseudo-label forward/backward with classifier BN running-state snapshot;
- running_mean/running_var/num_batches_tracked are bitwise unchanged after target-only path.

C6 — input preconditioner:
- both adaptation directions produce finite source/target transformed tensors;
- no negative raw ppm before log1p after tolerance check;
- global source sigma is finite and >0.

C7 — optimizer smoke:
- for each direction and M0-M3, execute 3 optimizer steps on actual training batches;
- every parameter, gradient used for update and persistent buffer remains finite;
- no target labels are loaded.

If any C1-C7 fails, return:
`SOLICM_G0R_SOFTWARE_CONFORMANCE_STOP`
and do not start the 96-run scientific matrix.

## 12. Scientific training

If C1-C7 pass:
- rerun all 96 configurations from scratch;
- both W0->W2 and W2->W0;
- 4 folds;
- 3 seeds;
- 4 arms;
- 40 epochs;
- batch size 32;
- Adam;
- source-risk checkpoint selection only;
- no target-label metric during training.

Pseudo-label coverage must be reported per run and epoch, but coverage itself is not a scientific gate.

## 13. Scientific outputs and gates

Inherit original G0 target outputs and G0-1..G0-6 EXACTLY:
- proper-score alignment gain FULL vs NO_ALIGN;
- pooled bootstrap robustness;
- source breadth;
- FULL vs PL_ONLY;
- Brier/accuracy quality;
- seed robustness.

Do not relax any threshold because this is a repaired implementation.

## 14. Decision

Software stop:
`SOLICM_G0R_SOFTWARE_CONFORMANCE_STOP`
if preflight C1-C7 fails.

Scientific PASS:
`SOLICM_G0R_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL`
only if inherited G0-1..G0-6 all pass.

Scientific HOLD:
`SOLICM_G0R_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL`
only if inherited G0-1..G0-5 pass and G0-6 alone fails.

Scientific STOP:
`SOLICM_G0R_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL`
for failure of inherited G0-1..G0-5.

## 15. Consequence

PASS authorizes exactly one G1 design:
`source-oriented causal sufficiency`,
where only latent causal relations that materially affect source posterior odds are encouraged to remain cross-domain stable.

PASS does NOT make the published LCA implementation the project innovation.

HOLD does not authorize architecture expansion.

STOP retires the latent-invariant-causal-mechanism mapping for this project.

Software conformance stop remains non-scientific and must be fixed only by a separately versioned implementation decision.