# Rough-Path Signature Inference as the Main-Algorithm Candidate

Date: 2026-09-30

Status: **CANDIDATE, contingent on R2C**

## Candidate name

**SC-RPSI — Source-Conditioned Rough-Path Signature Inference**

Chinese:

**源条件粗糙路径签名推断**

Alternative concise paper name:

**Marginal-Preserving Signature Path Inference**

## Why this candidate appears after R2B

R2B's pairwise Variogram score collapsed from the frozen R2 Energy factor's
53/64 target correctness to 35/64.

That failure is evidence against a simple second-order / pairwise-dependence
explanation.

The remaining R2 signal is therefore better treated as an ordered
whole-path / higher-order distributional phenomenon until falsified.

Path signatures are a principled mathematical representation of ordered paths:
their iterated-integral hierarchy captures increasingly high-order temporal
interactions. Signature kernels compare paths in the resulting feature space
without explicitly enumerating all orders.

## Algorithm module

For each source candidate s:

1. construct the intact candidate path law P_s from reference plume
   trajectories;
2. construct Q_s by preserving every time-specific full spatial snapshot
   marginal while destroying cross-time realization identity;
3. score the target path under P_s and Q_s with a strictly proper
   signature-kernel score;
4. form the source-specific dependence residual
   D_sig(s,y)=SIG_Q-SIG_RAW;
5. use D_sig as the missing dynamic path term in source inference.

This is not "use temporal information" and not "put an RNN after PMFS".

The GSL-specific second innovation is the combination of:

- source conditioning;
- full spatial-block marginal preservation;
- rough-path ordered-interaction representation;
- dependence-only candidate residual;
- later source-probability-map correction.

## Recent theory bridge

Relevant recent distant-field developments include:

- NeurIPS 2025: scalable signature-kernel computation for long,
  high-dimensional sequential data;
- ICLR 2026: Random Controlled Differential Equations / Random Rough DEs,
  using log-signatures to capture higher-order temporal interactions with only
  a light trainable readout;
- 2025/2026 work on signature-kernel scoring for high-dimensional
  spatio-temporal weather ensembles, where the score is designed specifically
  to assess path-dependent spatial-temporal structure.

Do not promote Random CDE/R-RDE before the non-learned R2C score proves that
the rough-path representation actually amplifies the GSL signal.

## Promotion rule

SC-RPSI becomes the leading main-innovation candidate only if R2C materially
beats the frozen R2 53/64 signal under the preregistered cross-House stability
gate.

If R2C fails, do not rescue the family with architecture scale.
