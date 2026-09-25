# SOLICM-G0 — Latent Invariant Causal Mechanism Transfer Gate

Date: 2026-09-26

Status: **NEW MAINLINE CANDIDATE / ZERO-PLUME / MOTHER-THEORY TRANSFER TEST**

Frozen upstream status:
- JTD mainline STOP remains final.
- NPG mapping STOP remains final.
- RPO-G0 STOP remains final.
- RIA-A0 positive admission result remains valid.
- RIA-A1 = `RIA_A1_MIXED_SIGNAL_AND_VARIABILITY`; no single sensory/noise mother theory selected.

This is NOT a rescue of any stopped route.

## 1. Mother-theory anchors

### Anchor A — Latent invariant causal mechanism

Cai et al., IEEE TPAMI 2026:
`Time Series Domain Adaptation via Latent Invariant Causal Mechanism`
DOI: `10.1109/TPAMI.2025.3642245`.

Key theory:
- high-dimensional time series can be generated from lower-dimensional latent variables;
- latent temporal causal structures can remain stable even when observed-domain distributions shift;
- LCA aligns latent causal structure across labeled source and unlabeled target domains;
- the paper provides identifiability results and an official implementation.

Frozen upstream implementation:
`DMIRLAB-Group/LCA@45c091fca909ac13675c6ddac7e0464f0a186355`.

### Anchor B — Task-oriented causal representation

Yan, Acartürk & Tajer, NeurIPS 2025:
`Reward-oriented Causal Representation Learning`
DOI: `10.52202/085713-1381`.

Key theory:
- perfect latent causal recovery can be unnecessary for a downstream task;
- learn the coarsest causal representation sufficient for optimizing task utility;
- finite-sample task-oriented causal recovery is treated explicitly.

Frozen upstream implementation reference:
`ZiruiYan/RO-CRL@86d5e1b09f3df092c7ae37e7bb846ea48dc970a2`.

RO-CRL code is NOT executed in G0. It motivates the later source-oriented secondary innovation only if G0 passes.

## 2. New-mainline scientific hypothesis

First-stage hypothesis:

> Across wind environments with identical candidate sources and observation protocol, a latent causal mechanism alignment model should preserve source-discriminative structure better than ordinary source-only learning, pseudo-label adaptation, or the same latent model without cross-domain causal-structure alignment.

G0 tests the published mother theory only.

The proposed project-specific innovation is reserved for a later stage:

> align only latent causal mechanisms that are sufficient for source discrimination, rather than all latent causal mechanisms.

This later object is called:
`Source-Oriented Latent Invariant Causal Mechanism (SOLICM)`.

No source-oriented modification is allowed in G0.

## 3. Data scope

Use only already-open House02 data from JTD-E2:

Domain W0:
`3,5-1_slow`

Domain W2:
`4,5-3_slow`

Both domains use:
- the same six frozen source locations;
- the same House02 E1/E2 30-probe observation contract;
- the same 10 time indices;
- 16 already-open realizations/source (12 former references + 4 former E2 fresh targets, now historical/open).

Total per domain:
`6 sources × 16 = 96 sequences`.

0 new plume.
Do NOT read H01 DEV.
Do NOT read House03.
Do NOT use G1A central-strip 168-source bank for training or gate selection.

## 4. Input contract

Input per realization:
`X in R^(10 × 30)` raw frozen ppm tensor from the E2 observation contract.

For the official LCA implementation, transpose only as required by the repository data loader so that:
- sequence length = 10;
- input channels = 30;
- number of classes = 6.

No PCA.
No handcrafted RIA descriptors.
No wind/occupancy features.
No PMFS/JTD features.

Input scaling must follow one frozen rule for all models:
- channel-wise z-score using labeled SOURCE-domain training samples only;
- apply the same source-fit scaler to target-unlabeled and target-heldout.

Do not use target labels or target-heldout statistics for scaling.

## 5. Adaptation directions

Run both:

A. `W0 -> W2`
B. `W2 -> W0`

Each direction is required to pass; a one-way gain is not sufficient.

## 6. Four target folds

For each target domain, partition the 16 realization indices/source into four frozen heldout groups:
- Fold0: indices 0-3;
- Fold1: 4-7;
- Fold2: 8-11;
- Fold3: 12-15.

For each direction/fold:
- source labeled training: all 16 realizations/source;
- target unlabeled adaptation: the 12 target realizations/source outside the heldout group;
- target heldout evaluation: exactly the 4 target realizations/source in the heldout group.

Target class labels are hidden from every training/model-selection procedure.

Across four folds every target realization is evaluated exactly once.

Folds are not treated as independent experimental units because their target-unlabeled sets overlap.

## 7. Frozen training seeds

Run exactly three neural-training seeds:
`0, 1, 2`.

No extra seeds after results are seen.

For every model/direction/fold/seed:
- 40 epochs;
- batch size 32;
- Adam;
- use the official LCA default hyperparameters unless explicitly overridden below by the input-shape adaptation.

Primary checkpoint:
- lowest SOURCE classification loss checkpoint under the official source-risk rule;
- target labels may never be used for early stopping or checkpoint selection.

Disable target-F1 logging during training to remove accidental target-label visibility.

## 8. Four frozen model variants

All variants use the same z_net, feature extractor and classifier architecture from the pinned official LCA repository.

### M0 — SOURCE_ONLY
- train on labeled source sequences only;
- source cross-entropy only;
- no target pseudo-labels;
- no reconstruction/KL/sparsity/structure losses.

### M1 — PL_ONLY
- same source classifier and target-unlabeled batches;
- source cross-entropy;
- official target pseudo-label schedule/threshold after epoch 30;
- no reconstruction/KL/sparsity/structure losses.

This is the strong ordinary adaptation baseline.

### M2 — LCA_NO_ALIGN
- full official latent generative/causal model;
- reconstruction, KL and intra-domain sparsity enabled;
- target pseudo-label schedule identical to FULL;
- set only `structure_weight = 0`.

This isolates the cross-domain latent causal-structure alignment term.

### M3 — LCA_FULL
- official LCA loss and defaults;
- `z_kl_weight=0.001`;
- `rec_weight=0.1`;
- `sparsity_weight=0.001`;
- `structure_weight=0.1`;
- `class_weight=1`;
- pseudo-label start epoch 30;
- pseudo-label threshold 0.99.

No hyperparameter search in G0.

## 9. Primary target-domain outputs

For every heldout target realization export full six-class logits/probabilities.

Metrics:
- multiclass NLL;
- multiclass Brier score;
- accuracy;
- macro-F1;
- top-3 accuracy;
- truth rank;
- entropy of predicted posterior.

For the three frozen adjacent E2 source pairs, also report:
- true-vs-partner log-odds;
- pair-restricted Brier;
- pair-restricted accuracy.

Primary scientific endpoint:
`Delta_align = NLL(LCA_NO_ALIGN) - NLL(LCA_FULL)`.

Positive means latent causal-structure alignment helps.

Secondary ordinary-adaptation endpoint:
`Delta_PL = NLL(PL_ONLY) - NLL(LCA_FULL)`.

## 10. Aggregation units

First average repeated neural seeds at each heldout target realization.

Then aggregate by:
- direction;
- source within direction;
- pooled 12 direction×source units.

Use direction×source as the cluster-bootstrap unit for pooled sensitivity analysis.

Do not bootstrap neural seeds as independent data.

## 11. Frozen G0 gates

### G0-1 — bidirectional proper-score gain from causal alignment
For BOTH W0->W2 and W2->W0:
- mean `Delta_align > 0`.

### G0-2 — pooled alignment effect is robust
On the 12 direction×source unit means:
- 10,000 cluster-bootstrap 95% CI lower bound of pooled mean `Delta_align > 0`.

### G0-3 — breadth
- at least 8/12 direction×source units have positive `Delta_align`;
- each adaptation direction has at least 4/6 positive source units.

### G0-4 — not just pseudo-label adaptation
For BOTH directions:
- mean `Delta_PL > 0`;
- pooled 12-unit bootstrap 95% CI lower bound of `Delta_PL > 0`.

### G0-5 — bounded probability quality
For BOTH directions, LCA_FULL must:
- have lower mean Brier than LCA_NO_ALIGN;
- have lower mean Brier than PL_ONLY;
- not reduce accuracy by more than 2 percentage points relative to the better of LCA_NO_ALIGN and PL_ONLY.

### G0-6 — seed robustness
For each direction:
- median across the three training seeds of mean `Delta_align` > 0;
- no seed may have LCA_FULL mean NLL more than 10% worse than LCA_NO_ALIGN.

## 12. Mechanism audit

Export, for M2 and M3:
- per-domain latent Jacobian magnitude matrices;
- thresholded adjacency masks using the model's frozen learned threshold;
- source-target weighted-structure discrepancy;
- binary mask Jaccard agreement.

This is descriptive and does not create a new gate.

Do NOT claim causal recovery merely because structure discrepancy decreases.

The causal claim is admissible only at the level supported by the published LCA assumptions and the frozen performance ablation.

## 13. Decision

PASS:
`SOLICM_G0_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL`
only if G0-1..G0-6 all pass.

HOLD:
`SOLICM_G0_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL`
only if G0-1..G0-5 pass and G0-6 alone fails.

STOP:
`SOLICM_G0_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL`
for failure of any of G0-1..G0-5.

DATA STOP:
`SOLICM_G0_DATA_CONTRACT_STOP`
if the exact H02 W0/W2 source/probe/input correspondence cannot be reproduced.

## 14. Consequence

PASS does NOT make published LCA the project innovation.

PASS authorizes one project-specific G1:
`source-oriented causal sufficiency`.

G1 must derive a task-relevance mask/regularizer so that only latent causal relations that affect source posterior odds are forced to be invariant across environments.

Conceptual target:
`min representation complexity subject to preserving source-discriminative posterior information and cross-domain causal stability`.

This is where the NeurIPS 2025 reward-oriented CRL principle enters.

Any G1 method must still output a normalized PMFS-style probability map over candidate source locations and must not require a dense stochastic source bank at deployment.

STOP retires this causal-representation mapping before any custom network is built.