# M6 Derivation v3 — Counterfactual Physics Foundation Model for PMFS

Date: 2026-09-23
Branch: `research/geopt-physics-foundation-pmfs-v1`
Status: **provisional paper-level formulation; still requires G1 source-rank evidence**

## 1. Why "GeoPT fine-tuning" is not enough

A paper whose main method is merely "fine-tune GeoPT on plume data" is too close to an application paper.

The PMFS-specific second derivation must change how candidate sources are represented and evaluated.

## 2. Core formulation

For one environment (e=(O,W)), learn/cache a physics-foundation representation:

[
Z_e=E_{PFM}(O,W).
]

A PMFS candidate source is a controlled counterfactual query:

[
do(S=s).
]

Define a source intervention operator (mathcal A_phi) and plume decoder:

[
oxed{hat H_s=D_psi(mathcal A_phi(Z_e,s))}.
]

Working name:

**Counterfactual Physics Foundation Model (CF-PFM) for PMFS.**

## 3. Scientific representation change

Native PMFS repeatedly evaluates separate forward simulations:

[
F(O,W,s_1),F(O,W,s_2),ldots
]

CF-PFM factorizes common environment physics once:

[
Z_e=E(O,W),
]

then evaluates source interventions inside the same environment representation.

This imposes the inductive structure that all candidates share one environment and differ only through the source mechanism.

## 4. Connection to M4 without overclaiming causality

The factorization borrows the intervention/compositional principle from M4:
- environment mechanism;
- source-injection mechanism.

The initial claim does not require saying that a full causal graph was discovered.

A safer statement is:

> source candidates are controlled counterfactual interventions into a shared pretrained physical environment representation.

Only if the M4 2×2 source×wind recombination test passes should stronger causal-compositional language be used.

## 5. Source intervention operator

Use source-relative features:

[
r_s(x)=[x-s,|x-s|,Q_s(x)].
]

This gives:
- localized source injection;
- relative-position generalization to unseen source locations.

## 6. Zero-initialized source FiLM

After a source-independent environment encoder:

[
Z_{e,s}=(1+gamma_phi(r_s))odot Z_e+eta_phi(r_s),
]

with final FiLM layer initialized to zero.

At initialization the gas-specific model exactly preserves the pretrained environment representation.

## 7. Global propagation

Do not inject source only at the last scalar head.

After source modulation, retain one or more global Physics-Attention blocks so a local source intervention can propagate through the wind/obstacle environment.

Current computational pilot:
- first 6 blocks: cached environment;
- last 2 blocks: source-conditioned global propagation.

This split must be ablated.

## 8. PMFS integration

For each source candidate (s_i), predict a candidate concentration/hit field (hat H_{s_i}), then keep the same PMFS candidate-belief update and initial movement rule for the first scientific test.

Thus the first hard experiment changes the forward representation only.

## 9. Required properties

### A — cross-physics pretraining value
GeoPT pretrained must beat the same Transolver from scratch under low plume-data budgets.

### B — counterfactual source generalization
Unseen source locations must remain queryable through the same source adapter.

### C — shared-environment consistency
All candidate predictions for fixed geometry/wind must use the same cached environment representation.

## 10. Strong controls

- monolithic source conditioning into a pretrained model;
- absolute source xyz instead of relative/local source representation;
- no environment factorization;
- random frozen backbone;
- same architecture from scratch.

## 11. Efficiency is secondary

House02 random-weight interface probe:
- 631 free-space tokens;
- 142 source candidates;
- cached first-six-block environment pass ~0.108 s CPU;
- 142 candidate final-two-block sweep ~3.36 s CPU total.

This only establishes closed-loop feasibility.

## 12. Main G1 falsification

Compare:
1. Native PMFS forward;
2. pretrained CF-PFM;
3. same CF-PFM from scratch;
4. monolithic pretrained conditioning;
5. small gas-specific surrogate.

Freeze source split and low-data fractions source-blind.

Hard metric:

[
oxed{	ext{truth-containing source-candidate rank}}
]

on unseen source + independent plume realization.

## 13. Promote/demote

Promote only if:
- pretrained > from-scratch in low data;
- unseen-source source rank improves;
- source-intervention factorization adds value beyond monolithic conditioning;
- independent seed and destructive nulls support the mechanism.

Demote if:
- foundation pretraining gives no low-data gain;
- source adapter fails on unseen sources;
- monolithic conditioning is equally good;
- gains are only field reconstruction, not source identity.

## 14. Provisional thesis

> PMFS repeatedly solves many hypothetical forward problems in one physical environment. CF-PFM recasts this as counterfactual querying of a cross-physics pretrained environment model: geometry and wind are encoded once, while each candidate source is injected as a controlled local intervention and propagated through shared physics-attention dynamics.

Status:

`ADVANCE TO G1 — NOT YET FINAL MAIN INNOVATION`.
