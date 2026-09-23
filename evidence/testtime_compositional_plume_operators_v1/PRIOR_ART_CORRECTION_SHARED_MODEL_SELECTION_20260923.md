# M7 Prior-Art Correction — Shared Model Selection Is Not Novel in Source Localization

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## Decision

The following idea is **NOT** a novelty claim:

> one environment/dispersion model is shared across source hypotheses and selected/marginalized using source-integrated evidence.

This already exists in source-localization literature.

## 1. 2015 direct boundary — multiple dispersion models

Ristić et al.,  
*Bayesian likelihood-free localisation of a biochemical source using multiple dispersion models*, Signal Processing 108 (2015), 13–24.  
DOI: 10.1016/j.sigpro.2014.08.023.

The paper:
- considers multiple complete atmospheric dispersion models;
- treats the dispersion-model index as an uncertain model variable;
- performs likelihood-free Bayesian source localization;
- simultaneously produces model probabilities/model selection.

Therefore M7 cannot claim:
- first source localization with a shared uncertain forward model;
- first joint source/model reasoning;
- first model selection in source inversion.

## 2. 2025 direct boundary — "many wrong models"

Piro, Heinonen, Cencini & Biferale,  
*Many wrong models approach to localise an odour source in turbulence with static sensors*, Journal of Turbulence 26(5), 2025, 153–173.  
DOI: 10.1080/14685248.2025.2492711.

Their weighted Bayesian update:
- runs multiple stochastic environment/plume models;
- computes a source belief for each model;
- evaluates model adequacy using an overlap/evidence quantity integrated over source location;
- ranks/blends model predictions into a master source belief.

Thus the concept:

\[
\text{source-marginal evidence}
\rightarrow
\text{shared model ranking}
\]

is already a direct OSL near-neighbor.

## 3. Consequence for the R1 world-shopping diagnostic

The corrected R1 diagnostic remains scientifically useful:

- correct/shared wind world suppresses false candidates;
- allowing each source to choose its preferred world rescues false candidates;
- truth score itself is nearly unchanged.

But this supports a **design constraint**, not a novelty claim.

M7 should retain:

\[
\text{one shared environment world for all source counterfactuals}
\]

because it is physically correct.

Do not sell it as new.

## 4. What remains genuinely different in M7

Old multi-model OSL:

\[
\{
M_1,M_2,\ldots,M_K
\}
\]

where every \(M_k\) is a **complete predefined plume/dispersion model**.

Model selection/blending chooses among those full models.

M7 instead proposes a mechanism library:

\[
\{
R_1,R_2,\ldots,R_K
\}
\]

of **reusable local/evolution physics operators**.

A previously unseen environment world is synthesized at test time:

\[
\mathcal T_E
=
\mathcal B_O
\circ
R_{k_m}
\circ\cdots\circ
R_{k_1}
\circ
\mathcal D_0
\circ
\mathcal A_W.
\]

This composition need not have existed as a complete plume model during training.

That is the key distinction.

## 5. M7 novelty must therefore contain ALL of these

1. **mechanism-level**, not full-model-level, components;
2. at least some components are **learned reusable evolution operators**;
3. the environment model is **composed/synthesized at test time**;
4. the composition can represent **unseen physics combinations/regimes**;
5. known wind/source/obstacle physics remain explicit;
6. the synthesized environment world is then reused for PMFS candidate-source counterfactuals;
7. downstream truth-source rank improves relative to:
   - Native PMFS;
   - fixed predefined model bank;
   - monolithic learned surrogate.

If M7 becomes only:
- choose among several full plume simulators; or
- blend several complete plume models;

then it directly collides with prior OSL and is NO-GO as the main idea.

## 6. Corrected paper-level thesis

Do NOT say:

> We introduce shared model selection for source localization.

Potential thesis if evidence supports it:

> We introduce a **mechanism-compositional plume world model** for PMFS-style localization: known gas-transport physics is retained explicitly, unresolved dynamics are represented by reusable learned evolution operators, and unseen transport worlds are synthesized at test time by composing frozen mechanisms rather than selecting among a fixed bank of complete plume models.

The shared-world constraint then provides physical consistency across source counterfactuals.

## 7. Status

\`SHARED-MODEL NOVELTY = KILLED\`

\`M7 MECHANISM-COMPOSITION NOVELTY = STILL OPEN\`

The R1 world-shopping result remains evidence for why the shared-world constraint is necessary, not evidence that it is new.
