# Boundary and current prior-art collision

## Already killed / not to repeat

### H01 distributional_forward_v1
The previous frozen H01 test compared mean block-count, joint block-CRPS and
multivariate Energy Score on a 200-sample window containing 0/200 gas hits.
All three ranked the truth 56/121; 500 joint-destruction nulls produced the same
rank. That is a NO-GO for load-bearing high-order phase/joint structure in that
test. Do not resurrect it.

### R0 post-PASS source identity
R0 already showed that the source-specific mean Bernoulli encounter field
carries strong 18-source identity:
- first8 -> last8: encounter likelihood top1 90.3%, raw mean-path SSE 88.2%;
- last8 -> first8: encounter likelihood top1 89.6%, raw mean-path SSE 81.9%.

But a Bernoulli encounter field is still parameterized by the mean encounter
probability p_s(t,q). It does not prove that distributional shape around that
mean carries extra identity.

## 2026 mother-theory candidates — provisional only

Two ICLR 2026 papers motivate the *general* failure of deterministic/unimodal
world models in stochastic or multimodal dynamics:

- Wan, Gan, Zhan, "Learning to Be Uncertain: Pre-training World Models with
  Horizon-Calibrated Uncertainty", ICLR 2026. It argues that a single
  deterministic future is ill-posed in stochastic environments and learns a
  structured probabilistic future representation.
- Aghabozorgi et al., "WIMLE: Uncertainty-Aware World Models with IMLE for
  Sample-Efficient Continuous Control", ICLR 2026. It explicitly targets
  unimodal models that average over multi-modal dynamics. Public code:
  https://github.com/mehranagh20/wimle

These papers are NOT evidence that this UAV-GSL mechanism is true. D0 below
must establish that first.

## Direct GSL collision

Kim et al., "Deep Probabilistic Indoor Gas Source Localization via Physical
Dependency-Guided Sequential Inference", arXiv:2608.16221 (2026), already
performs deep probabilistic indoor GSL with uncertainty propagated through
wind/concentration fields toward a source posterior.

Therefore this project must NOT claim novelty for:
- probabilistic GSL;
- field uncertainty;
- Monte-Carlo marginalization;
- multi-wind averaging;
- an ensemble by itself.

The only potentially distinct object tested here is **source-specific
realization branching/residual geometry after the source mean trajectory is
held fixed**.
