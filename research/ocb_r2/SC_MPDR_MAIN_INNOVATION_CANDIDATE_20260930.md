# Main Innovation Candidate — SC-MPDR

Date: 2026-09-30

Status: **ALGORITHM DESIGN CANDIDATE / NOT YET VALIDATED**

## Name

**SC-MPDR: Source-Conditioned Marginal-Preserving Dependence Restoration**

Chinese:

**源条件边缘保持依赖恢复模块**

Working paper-level title:

**Marginal-Preserving Dependence Restoration for Turbulent Source Inference**

## 1. Why this is the algorithmic innovation, not "evidence"

R0/R1/R2 establish a mechanism: after preserving every time-specific spatial
snapshot distribution, intact cross-time dependence still contains source
identity.

That mechanism is not itself the algorithm.

SC-MPDR turns the mechanism into an inference operator:

1. construct a candidate-specific dependence-forgetting process that preserves
   every time-block marginal;
2. learn to reverse / discriminate the dependence destruction;
3. recover a candidate-specific path dependence density correction;
4. inject that correction into the source probability map.

The module is therefore a source-likelihood correction operator, not a
two-stage reranker.

## 2. Important terminology correction

Do not claim that the current R0/R1/R2 quantity is a formal PID/PIRD
"synergy" term.

The current intervention establishes **joint temporal dependence information
beyond time-block marginals**.

Formal PID/PIRD synergy has a stricter information-decomposition definition and
has not yet been estimated here.

PIRD remains motivation for high-order dynamic information; the more exact
algorithmic mother theory is **marginal/dependence decomposition plus
dependence forgetting-and-restoration**.

## 3. Mother theory

### Statistical foundation

For candidate source s:

`P_s(Y_1:T) = Q_s(Y_1:T) R_s(Y_1:T)`

with

`Q_s(Y_1:T) = product_t P_s(Y_t)`

and

`R_s(Y_1:T) = P_s(Y_1:T) / Q_s(Y_1:T)`.

Each Y_t is the complete spatial snapshot block, not an independent-probe
scalar.

The dependence factor R_s contains only what is lost by destroying cross-time
coupling while preserving every time-block marginal.

### Modern algorithmic inspiration

ICLR 2026 Diffusion and Flow-based Copulas develops a
"forget dependencies while preserving marginals, then learn to remember them"
framework.

SC-MPDR transfers this principle to source-conditioned **time-block
marginals** and inverse-source inference.

## 4. GSL-specific second innovation: block-marginal forgetting

Standard scalar copula processes preserve dimension-wise marginals.

Our scientific contract requires something stronger:

> preserve the complete 30-D spatial snapshot law at each time and destroy only
> cross-time realization coupling.

Therefore define a block-marginal forgetting operator F_tau.

For an intact candidate trajectory
`Y=(Y_1,...,Y_T)`, where each `Y_t in R^30` or `{0,1}^30`:

- tau=0: all time blocks come from the same intact realization;
- increasing tau: selected time blocks are replaced by blocks sampled from
  other realizations of the same candidate source at the same time;
- tau=1: time-block identities are independent across t, producing the
  empirical Q-time reference.

At every tau, each `P_s(Y_t)` is exactly preserved.

This forward corruption works for binary and continuous plume observations and
does not require a Gaussian/univariate copula transform.

## 5. Restoration / ratio learner

Train a shared source-conditioned classifier or flow
`g_theta(Y, tau, support_s)` to identify the dependence-corruption level.

The support set for candidate s is its reference realization bank; the model is
not allowed to memorize a global source label.

At minimum, the endpoint classifier distinguishes:

- intact candidate paths P_s;
- block-marginal-forgotten paths Q_s.

Classifier odds estimate the candidate-specific density ratio:

`ell_dep(s,Y) ~= log P_s(Y) - log Q_s(Y) = log R_s(Y)`.

A multi-level corruption classifier is the preferred eventual implementation,
because it follows the 2026 forgetting/remembering principle and supplies a
graded dependence path rather than one binary contrast.

## 6. Source-map integration

Do not use an arbitrary tuned fusion weight.

If the base map represents the time-factorized / marginal evidence layer, the
candidate update is:

`log score_new(s) = log score_base(s) + ell_dep(s,Y)`

followed by normalization over legal source cells.

Operationally, PMFS remains the source-probability-map output interface.
Before claiming exact probabilistic factorization with native PMFS, verify
which marginal evidence PMFS actually computes.

If exact equality to Q_s cannot be proven, report the module as a
dependence-residual correction and calibrate only on discovery data under a
separately frozen protocol.

## 7. Architecture constraints

The first prototype must be deliberately low-capacity because the current
discovery panel has only four realizations/source/context.

Required anti-pseudoreplication rules:

- cross-fit by whole realization, never by shuffled window;
- all windows derived from one trajectory stay in the same fold;
- Q-time surrogates are negative constructions, not independent biological/
  physical realizations;
- no train/test leakage through candidate support sets;
- report effective number of physical trajectories separately from augmented
  sample count.

Do not start with a large Transformer or diffusion network.

Preferred prototype order:

1. dependence-sensitive nonparametric score (R2B);
2. low-capacity binary density-ratio classifier;
3. only if 1/2 show amplification, multi-level SC-MPDR restoration model.

## 8. What would make SC-MPDR a main innovation

The module is promotion-eligible only if it eventually demonstrates all of:

1. dependence-forgetting intervention is source-discriminative;
2. learned restoration/ratio score materially exceeds the frozen R2 Energy
   Score factor on held-out physical realizations;
3. both H01 and H02 improve, not one House only;
4. gain is strongest or remains positive on marginally hard cases;
5. source ranking / probability-map inference improves once a benchmark with
   ranking headroom is used;
6. formulas/model are frozen before confirmation;
7. later confirmation and unseen-House tests pass.

## 9. What is not the innovation

Not sufficient by itself:

- "use temporal information";
- "use PID";
- "use a copula";
- "use a Transformer";
- "use diffusion";
- "add another score to PMFS";
- "two-stage reranking".

The innovation candidate is the full operator:

> **source-conditioned block-marginal dependence forgetting -> dependence
> restoration / density-ratio recovery -> source-map likelihood correction.**

## 10. Current next action

Execute R2B first.

R2B tests whether replacing the generic Energy Score with a
dependence-sensitive proper score amplifies the existing mechanism.

Do not implement the learned SC-MPDR model until R2B is reviewed.
