# PRO6 NEXT TASK — Blackwell / Le Cam Source-Decision Sufficiency Audit

Date: 2026-09-25

Primary-thread status:
- CESS/FSEI: STOP;
- successor/occupation mainline: STOP;
- RR-MVSI: HOLD;
- DASN: HOLD;
- LSC: mechanism ADVANCE, but direct posterior/representation algorithms did not beat strong ordinary baselines;
- IPTO: STOP as main innovation after Pro review and ordinary-calibration/task-aware-operator absorption test;
- Codex is executing the currently assigned implementation/experiment. Do NOT duplicate Codex work.

Current candidate mother-theory question:

**Can Blackwell / Le Cam statistical-experiment sufficiency provide a genuinely distinct main innovation for UAV gas-source localization?**

Scientific reframing:
- raw plume observation Y is one statistical experiment about source S;
- a learned representation T(Y) is useful only if it preserves the source-decision information needed to distinguish candidate source hypotheses;
- nuisance from turbulent realization/environment should be discarded only if source likelihood-ratio / posterior-odds structure is preserved;
- D1R LSC already shows that local neighboring-source stochastic distinguishability predicts fresh source confusion and proper NLL.

Your task is THEORY / PRIOR-ART / RED-TEAM ONLY.
Do not run simulations.
Do not generate targets.
Do not change Codex gates.

## 1. Exact theory audit

Derive the precise relation among:
- Blackwell sufficiency / comparison of statistical experiments;
- Le Cam deficiency / approximate experiment equivalence;
- likelihood-ratio sufficiency for a finite source-hypothesis family;
- decision risk under proper scoring / source classification;
- approximate sufficient representations.

Answer specifically:
- for finite source set S, what condition on T(Y) guarantees no loss for all source decisions?
- when is preserving all pairwise likelihood ratios equivalent to sufficiency?
- what measurable/estimable surrogate can be used with only finite repeated plume realizations?
- which claims require exact densities and which can be stated with finite-sample approximations?

## 2. Strongest novelty attack

Determine whether this route reduces to any established method:
- LDA / QDA;
- sufficient dimension reduction;
- supervised contrastive learning;
- information bottleneck / variational information bottleneck;
- metric learning;
- posterior distillation / knowledge distillation;
- discriminative classification with calibrated softmax;
- likelihood-ratio estimation / classifier-based ratio estimation;
- domain-invariant / nuisance-invariant representation learning;
- goal-oriented dimension reduction.

State the minimal property that would make a Blackwell/Le Cam GSL method scientifically distinct from all of the above.

## 3. 2025/2026 literature and code

Find 2025/2026 top-journal/top-conference anchors, with public code where possible, for:
- Blackwell sufficiency in representation learning;
- Le Cam deficiency / approximate statistical experiment comparison;
- sufficient representations under distribution shift;
- likelihood-ratio-preserving representation learning;
- decision-theoretic representation learning.

Also search direct GSL/olfaction prior art for:
- sufficient statistics / sufficient representation;
- Blackwell / Le Cam;
- likelihood-ratio-preserving embeddings;
- source-hypothesis experiment comparison;
- pairwise source distinguishability graphs.

Do not claim novelty from absence in one keyword search. Give strongest overlap risks.

## 4. Connect to existing D1R evidence

Use only already established facts:
- neighboring source distribution distinguishability is reproducible;
- Bhattacharyya/energy-distance proxies predict fresh binary confusion;
- local confusion mass predicts fresh 168-cell posterior NLL;
- global LDA is a very strong ordinary baseline;
- LSC-specific linear objective did not stably beat global LDA.

Explain what Blackwell/Le Cam theory predicts that ordinary global LDA does NOT automatically guarantee.

## 5. Define one zero-new-simulation falsification gate

Propose exactly one D1R-only gate that can distinguish:

A. ordinary discriminant compression that merely improves average classification;
from
B. a representation that approximately preserves the source statistical experiment.

Mandatory requirements:
- original 168-cell support;
- fresh-realization split;
- local source pairs plus multiclass proper score;
- compare against global LDA, calibrated classifier, supervised contrastive, PCA;
- no new GADEN runs;
- no target leakage.

Prefer a criterion based on decision-risk/deficiency or recoverability of likelihood-ratio structure, not just accuracy.

## 6. Mainline decision rule

Return exactly one of:

- GO_THEORY_ONLY_BLACKWELL_CANDIDATE
- HOLD_NOT_DISTINCT_FROM_STANDARD_REPRESENTATION
- STOP_BLACKWELL_MAINLINE

GO requires:
- a distinct mathematical object beyond ordinary discriminant learning;
- a testable finite-data surrogate;
- no direct GSL prior-art collision;
- a clear path back to a PMFS microcell probability map.

## 7. Deliver only

1. BLACKWELL_LECAM_THEORY_AUDIT.md
2. STANDARD_REPRESENTATION_ABSORPTION_TEST.md
3. GSL_PRIOR_ART_AND_2025_2026_ANCHORS.md
4. D1R_ZERO_SIMULATION_FALSIFICATION.md
5. one-page GO/HOLD/STOP recommendation.

Do not design a new neural architecture yet.
Do not propose new simulation acquisition.
Do not revive IPTO unless Blackwell/Le Cam analysis independently requires it.