# CTAER literature trace

Checked: 2026-09-13.  Only primary publisher/paper pages are used for the
mechanism statement.

## Direct 2026 theory anchor

Miguel Aguilera, Sosuke Ito and Artemy Kolchinsky, **Inferring Entropy
Production in Many-Body Systems Using Nonequilibrium Maximum Entropy**,
Physical Review Letters 136, 077101 (2026), DOI `10.1103/xgkj-dxzh`.

- Open author PDF:
  https://artemyk.github.io/assets/pdf/papers/AguileraItoKolchinsky_InferringEntropyProduction_PRL_2026.pdf
- Verified content: the paper defines trajectory-level irreversibility by
  `log p_forward(x) / p_reverse(x)` and studies what part remains identifiable
  from trajectory observables without reconstructing the full distribution.
- Transfer: compare each candidate's forward response with its paired reverse
  response, rather than treating reverse time only as an external ablation.
- Boundary: CTAER is not a thermodynamic entropy-production estimator.

## 2026 coarse-observation boundary

Udo Seifert, **Universal bounds on entropy production from fluctuating
coarse-grained trajectories**, Nature Reviews Physics 8, 493-507 (2026), DOI
`10.1038/s42254-026-00954-5`.

- Publisher page:
  https://www.nature.com/articles/s42254-026-00954-5
- Verified content: experimentally accessible time series reveal only bounded
  information about irreversibility when hidden degrees of freedom are
  coarse-grained.
- Transfer: use the forward/reverse ordinal contrast as partial evidence and
  retain an explicit no-identifiability/no-cross-dataset claim boundary.
- Boundary: a positive CTAER score cannot prove the full plume mechanism.

## Gas-specific comparator and hardware boundary

Jin et al., **Calibration-Free Gas Source Localization with Mobile Robots:
Source Term Estimation Based on Concentration Measurement Ranking**, ICRA 2026.

- Primary record: https://arxiv.org/abs/2605.13208
- Transfer retained from TAORL: ordinal measurements reduce dependence on an
  unknown positive monotone concentration calibration.
- Boundary: global empirical ranks are Jin et al.'s comparator; CTAER's added
  object is the candidate-wise forward/reverse contrast.

Zhang et al., **Advanced electronic noses for future robotic olfaction**, npj
Robotics 4, 11 (2026).

- Publisher page: https://www.nature.com/articles/s44182-025-00071-y
- Transfer retained from TAORL: sensor hysteresis, recovery, sampling bandwidth
  and motion timing must be represented explicitly.

## Search and rejection record

Repository-wide collision search covered `time reversal`, `anti-causal`,
`likelihood ratio`, `entropy production`, `LMBT`, `CTT`, `OC-SLA` and TAORL.
It found reverse-time controls, but no candidate-wise paired
`forward-loss - reverse-loss` source score.  Backward-transport and
transport-consensus proposals were rejected because existing H03/CTT evidence
already falsified their claimed incremental mechanism.

