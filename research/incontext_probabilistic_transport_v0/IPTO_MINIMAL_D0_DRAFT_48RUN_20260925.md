# IPTO Minimal Cross-Operator D0 — 48-New-Run Draft

Date: 2026-09-25

Status: **DRAFT ONLY — NOT AUTHORIZED FOR EXECUTION**

This design may be frozen only after the current Pro theory/prior-art audit returns.

## 1. Goal

Test one narrow claim:

> after training across several physical wind operators in one fixed House, can a model identify a previously unseen wind-specific transport operator from a very small plume context set, without weight updates, and improve prediction/inference on source locations not present in that context?

The D0 must also test whether the inferred operator preserves the local stochastic source-distinguishability geometry identified by LSC.

## 2. Why House02 is sufficient for the first knife

House02 has four complete canonical same-geometry GADEN wind configurations:

- W_A = 3,5-1_fast;
- W_B = 3,5-1_slow;
- W_C = 4,5-3_fast;
- W_D = 4,5-3_slow.

No synthetic rotation or speed scaling is needed.

W_B is the same physical wind regime used by the completed D1R bank.

## 3. Source panel

Use exactly 8 source locations selected **geometry-only** from the existing valid 168-cell D1R panel.

Selection objective before any new plume generation:
- cover the House02 D1R source region spatially;
- include four local adjacent source pairs so distinguishability preservation can be evaluated;
- not use D1R NLL, confusability, rank, LSC score or plume outcome for source selection.

Exact source IDs must be frozen before execution.

## 4. Data budget

For every source/wind cell use exactly two independent plume seeds.

W_B:
- reuse two predeclared D1R realizations/source for the eight frozen sources;
- no new W_B generation.

New generation:
- W_A: 8 sources x2 seeds = 16;
- W_C: 8 x2 = 16;
- W_D: 8 x2 = 16.

Total new GADEN runs:

**48**.

## 5. Held-out operator firewall

Predeclare W_D as the untouched target operator before generation.

Training/meta-development may use:
- W_A;
- W_B;
- W_C.

W_D plume files are generated and hashed, then separated into:

### Context set
- exactly 2 geometry-predeclared source locations;
- 2 seeds/source;
- total 4 context realizations.

These four observations may be shown to the IPTO/fine-tuning baselines only after all generic model architecture and training choices are frozen from W_A/W_B/W_C.

### Query target set
- remaining 6 source locations;
- 2 seeds/source;
- total 12 target realizations.

These files remain unopened until:
- IPTO context-handling rule is frozen;
- fine-tuning baseline is frozen;
- all posterior/scoring code is hashed;
- LSC-distinguishability evaluation code is frozen.

No W_D query source may enter context.

## 6. Required models

All use equal training/operator data budgets where applicable.

### B0 — No-context global model
Train on W_A/W_B/W_C, apply to W_D without target plume context.

### B1 — Explicit-wind fixed operator
M4/neural-operator-style model that receives the physical W_D wind/geometry input but no W_D plume context.

This is critical: IPTO is not useful if explicit physical wind conditioning already solves the target operator.

### B2 — Equal-context fine-tuning/meta-learning
Start from the same global training information and update parameters using the four W_D context realizations.

### C — IPTO
Use the same four context realizations to infer/adapt the operator **without weight updates**.

## 7. Primary endpoints on the six unseen W_D query sources

### P1 — Source posterior proper score
All methods must ultimately produce or support a normalized posterior on the same candidate-source support.

Primary endpoint:
- mean true-source log score.

### P2 — Source ranking
- truth rank;
- top-k;
- MAP spatial error.

Secondary to proper score.

### P3 — Local distinguishability preservation
For the geometry-frozen local source pairs among the eight-source panel, compare predicted versus real W_D source-conditioned stochastic distinguishability.

Report:
- pairwise distinguishability ordering/rank correlation;
- predicted local confusion mass error;
- whether the model preserves which neighboring source pairs are difficult/easy.

Field MSE alone cannot PASS the D0.

## 8. Advance rule

IPTO can advance only if, on the sealed W_D query set:

1. four-context IPTO improves proper score over B0;
2. it improves over or remains meaningfully distinct from B1 explicit-wind fixed operator;
3. it beats equal-context B2 fine-tuning/meta-learning under the frozen budget, or demonstrates a clear no-weight-update advantage with comparable predictive quality;
4. it preserves local source-distinguishability geometry better than the fixed-operator baselines;
5. gains are present across both W_D query plume seeds;
6. no query source entered context/tuning.

## 9. STOP rules

STOP if:
- context gives no unseen-source benefit;
- fine-tuning/meta-learning matches the result at the same context budget;
- explicit physical wind conditioning makes in-context plume prompts unnecessary;
- only field MSE improves while source proper score/distinguishability does not;
- two context source locations are insufficient and dense target-wind source coverage is required.

## 10. What this D0 cannot establish

Even if positive, this House02 same-geometry D0 does not establish:
- unseen-House transfer;
- real-flight calibration sufficiency;
- universal stochastic operator learning;
- closed-loop PMFS benefit.

A positive D0 would only authorize a later cross-House gate.

## 11. Execution status

**DO NOT RUN YET.**

Wait for the Pro IPTO theory/prior-art response and primary-thread approval.