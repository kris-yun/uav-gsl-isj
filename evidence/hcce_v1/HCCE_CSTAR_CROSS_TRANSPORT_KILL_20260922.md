# HCCE controlled cross-transport source-identity stress — kill test

Date: 2026-09-22  
Branch: `research/hcce-v1-development-screen-20260922`  
HCCE development base: `c5271515d565c343d2fd2a63c77bf0484f45772a`  
Controlled CStar asset source revision: `26e89a99532e4268c5022dca2e938bf1473377b1`

## Decision

`HCCE_V1_MAINLINE_NO_GO_CROSS_TRANSPORT_SOURCE_IDENTITY`

This supersedes the earlier HOLD verdict for HCCE as a paper-level main innovation.

The reason is not endpoint weakness on the old/new 12-case development pool. HCCE remained very strong there. The failure is that its proposed **causal-emergence source mechanism does not preserve source identity across a controlled transport intervention**.

## 1. Why this stress was run

HCMC previously produced a very large development gain but failed on truly independent plume realizations. Therefore a new main-line candidate must not be promoted merely because the old and new fixed-source endpoint pools are positive.

HCCE had already reached:

- old six: 45.88% reduction, 6/6;
- independent-plume six after unblinding: 62.99%, 6/6;
- all 12: 54.77%, 12/12;
- final-leaf null 0/1000 as good as real;
- temporal shift, sensor block shuffle and candidate mismatch each 0/30 as good as real.

However anti-metric auditing showed weak direct source-candidate identity, so a source-position/transport intervention became the required next gate.

## 2. Controlled asset

The existing CStar 240 s asset provides, for every House:

- two substantially different sources, SA and SB;
- two transport interventions, fast and slow;
- an exactly identical robot route between all four episodes in a House;
- 1200 samples per episode;
- measured gas and wind histories.

Source pairs:

- H01: SA = (-0.6, 1.95), SB = (-0.4, -2.9)
- H02: SA = (0, -1), SB = (1, -2.3)
- H03: SA = (-0.45, 1.9), SB = (8.2, 5.0)

The candidate-domain files in this asset contain coordinates only, so an exact continuous-grid HCCE localization run is impossible without fabricating missing source-conditioned candidate plume maps.

Instead, a **binary source-identity transfer diagnostic** was used. This does not claim to reproduce the HCCE endpoint. It tests the central proposed mechanism directly: whether causal-emergence coupling remains source-specific when transport changes.

## 3. Cross-transport identity protocol

For each House and target episode:

1. use the two opposite-transport episodes as source-conditioned templates;
2. template candidate SA = gas trajectory from SA under the opposite wind intervention;
3. template candidate SB = gas trajectory from SB under the opposite wind intervention;
4. keep the target episode entirely separate from its template;
5. rank-normalize each template gas trajectory to [0,1] to remove amplitude calibration;
6. target event state is measured gas > 0;
7. form the same 4-bin × binary-event eight-state microdynamics used by the HCCE CE 2.0 screen;
8. compute maximum nontrivial macro causal power minus the constant-event baseline;
9. choose the source template with the larger causal-emergence coupling.

Thus:

- fast targets are classified only from slow templates;
- slow targets are classified only from fast templates.

The route is exactly identical: maximum pose difference between any same-House episode pair is 0.

## 4. Result

HCCE-style causal-emergence source identity:

- correct = **2/12**
- accuracy = **16.7%**
- mean truth-score margin = **-0.01059**

Per House:

- H01: 1/4
- H02: 1/4
- H03: 0/4

The detailed score matrix is stored in the companion JSON/CSV evidence.

This is not a marginal miss. The causal-emergence coupling systematically prefers the wrong source under transport intervention.

## 5. Critical simple control

A deliberately trivial source-blind comparator was run on the exact same cross-transport pairing:

> choose the opposite-transport source template whose overall encounter/hit rate is closest to the target encounter rate.

This crude scalar control achieves:

- **10/12 correct = 83.3%**

The only failures are the two H02-SA cross-wind transfers, where the SA encounter rate itself changes strongly between fast and slow transport.

Therefore HCCE's macro causal coarse-graining is not merely failing because the controlled task is impossible. Much simpler source information survives the intervention, while the proposed HCCE causal-emergence coupling destroys or confounds it.

## 6. Interpretation

This explains why HCCE could look exceptionally strong on the old + independent stochastic-plume endpoint pool yet still fail the harder mechanism test.

The HCCE score is sensitive to source-conditioned plume/robot temporal organization, but the organization it captures is **not transport-invariant source identity**.

The likely failure mode is:

> causal macrostate optimization finds highly deterministic/specific joint dynamics, but those macrostates can be dominated by the current transport regime and encounter pattern rather than by the source intervention itself.

This is exactly the type of shortcut that the post-HCMC screening reset was designed to expose.

## 7. Consequence

Do not:

- freeze HCCE V1 for a new expensive localization holdout;
- add auxiliary modules to rescue it;
- tune its bins, lags, event threshold or macrostate search against the CStar labels;
- claim causal emergence as the paper's main innovation from the 54.77% endpoint result.

The HCCE route is now **NO-GO as the main line**.

Its positive old/new results remain useful evidence about temporal source-conditioned structure, but not enough for source localization under intervention.

## 8. External mother-theory anchors

The scientific mother idea itself remains legitimate and genuinely cross-domain:

- Zhang, Tao, Yang et al., *Dynamical reversibility and a new theory of causal emergence based on SVD*, npj Complexity, 2025, DOI `10.1038/s44260-025-00028-0`.
- Hoel, *Causal Emergence 2.0: Quantifying emergent complexity*, 2025, DOI `10.48550/arxiv.2503.13395`.
- Public CE 2.0 implementation used as a conceptual/code reference: `jessescool/Causal-Emergence-2.0`.

The failure is the transfer of that mother idea to this GSL mechanism, not a claim against causal-emergence theory itself.

## 9. Next cycle rule

The next candidate should be screened in this order:

1. old six;
2. unblinded independent-plume six;
3. direct source-identity under CStar source/transport intervention;
4. geometry/shortcut controls;
5. only if all pass, freeze and generate a new holdout.

This prevents another HCMC/HCCE-style large endpoint gain from being mistaken for a source-generalizing mechanism.
