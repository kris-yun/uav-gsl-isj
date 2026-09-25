# IPTO v0 — In-Context Probabilistic Transport Operator

Date: 2026-09-25

Status: **THEORY CANDIDATE — NO NEW SIMULATION AUTHORIZED**

## Scientific question

Can a single transport world model infer a new environment-specific plume operator from a few source-to-observation context examples, then predict unseen candidate sources without weight updates?

Each environment/wind regime E defines an operator G_E.

G_E maps source/context/query conditions to an expected or probabilistic observation:

  G_E : (source, query/trajectory, local wind/geometry) -> distribution of plume observations.

The main scientific novelty under test is not neural-operator approximation itself, but **in-context identification of G_E for a new House/wind regime**.

## Why this follows from D1R

D1R showed:
- expected encounter/profile structure is highly reproducible across plume realizations;
- source-conditioned mean profiles are low-dimensional and spatially smooth;
- completely unseen source profiles can be interpolated close to the stochastic noise floor;
- direct source-specific means still outperform source-context KRR by roughly 0.6 bit/target in proper score;
- source-specific nuisance variance is also spatially predictable (heldout-source Spearman about 0.65-0.68).

Therefore a source->observation mapping exists and is smooth within one operator, but current context mapping is incomplete.

## Difference from M4

M4 learned a fixed deterministic source/wind field operator and asked whether source/wind factorization improves prediction/ranking.

IPTO instead treats different House/wind regimes as different operators and asks whether a general model can infer a previously unseen operator from a small prompt/context set without parameter updates.

Probabilistic IPTO additionally represents uncertainty in the inferred operator and/or source-conditioned observation distribution.

## Mother theory

- In-Context Operator Networks (ICON): infer an operator from data prompts at inference time without weight updates.
- GenICON / probabilistic operator learning (2025): posterior predictive distribution over operators and generative uncertainty.
- Multiple operator learning (2026): statistical generalization to unseen operator descriptors/tasks.

## Prior-art boundary

Not novel:
- neural operator for GSL;
- physics-guided NN/PINN/FNO/PINO;
- probabilistic source posterior;
- ordinary domain adaptation or fine-tuning.

Candidate novelty only survives if GSL has not already used **few-shot in-context operator identification for a new transport regime**.

## Minimal D0 principle

No large bank.

If prior-art/theory audit passes, acquire at most ~150 new GADEN runs across several target operators.

For each target operator:
- a small context set of source->observation examples is revealed;
- query source locations are completely excluded from context;
- compare no-context global model, per-operator fit, fine-tuning/meta-learning, and in-context operator prediction;
- use same candidate source support and proper score.

STOP if:
- context examples do not improve unseen-source prediction;
- fine-tuning/meta-learning matches IPTO at equal context budget;
- dense source coverage is needed;
- direct GSL prior art already implements the same mechanism.

## Sim-to-real requirement

A real site may use a small number of controlled calibration releases or naturally known-source events as context.

The method is disqualified if each new site requires exhaustive source-wise repeated releases.