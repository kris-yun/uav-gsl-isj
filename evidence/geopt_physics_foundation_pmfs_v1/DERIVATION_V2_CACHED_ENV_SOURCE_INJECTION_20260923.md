# M6 Derivation v2 — Cached Environment Backbone + Counterfactual Source Injection Adapter

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## 1. Purpose

The key PMFS-specific difficulty is that GeoPT naturally represents:

- geometry;
- dynamics/wind;

but PMFS must sweep many **candidate sources** under the same environment.

Do not destroy the pretrained GeoPT input embedding by concatenating source channels to the raw input.

Instead separate:

[
	ext{environment representation}
]

from

[
	ext{candidate-source intervention}.
]

This also creates a natural bridge to the M4 compositional/counterfactual idea without requiring M4's causal claim to be accepted.

## 2. Environment backbone

For a fixed source-update context:

[
H_{m env}^{(6)}
=
B_{1:6}
left(
E_{m GeoPT}(x,g(x),w(x))
ight)
]

where:

- (x): coordinates;
- (g(x)): SDF / boundary-direction geometry;
- (w(x)): 4-D wind dynamics prompt;
- (E_{m GeoPT}): official input projection;
- (B_{1:6}): first six pretrained Physics-Attention blocks.

This part is **source-independent** and can be computed once per wind/environment update.

## 3. Candidate source representation

For each source candidate (s), create a local physical injection descriptor at every environment token.

Minimal pilot features:

[
r_s(x)
=
[
x-s,;
|x-s|,;
Q_s(x)
].
]

For PMFS quadtree source regions, a later version may also encode candidate region size/extent.

(Q_s(x)) is a fixed source-locality field, e.g. a compact or Gaussian injection kernel whose scale is declared independently of truth.

Do not use the truth source to tune it.

## 4. Zero-initialized source FiLM adapter

Use a tiny MLP:

[
A_s:r_s(x)ightarrow[gamma_s(x),eta_s(x)]
inmathbb R^{512}.
]

Then:

[
oxed{
H_s^{(6)}
=
(1+gamma_s)odot H_{m env}^{(6)}
+
eta_s
}
]

with the final adapter layer initialized to zero.

At initialization:

[
gamma_s=eta_s=0
]

and therefore

[
H_s^{(6)}=H_{m env}^{(6)}.
]

This avoids an arbitrary modulation coefficient and preserves the pretrained model exactly before gas-specific learning.

## 5. Source-conditioned global transport

Pass the modulated representation through the final two pretrained Physics-Attention blocks:

[
H_s^{(8)}
=
B_{7:8}(H_s^{(6)}).
]

This is important.

Injecting the source only after the complete backbone would leave no global attention layer to propagate the candidate-source intervention through the environment.

Injecting after block 6 gives two global source-conditioned physics-attention layers while keeping most of the environment encoder cacheable.

## 6. New gas head

Replace only the pretraining task head with a plume head:

[
hat C_s(x)
=
D_{m plume}(H_s^{(8)}(x)).
]

Possible first output:
- log-concentration;
- or PMFS-compatible hit probability.

Do not predict source coordinates end-to-end.

The PMFS candidate probability map remains the inverse layer.

## 7. Parameter accounting

Official-compatible 8-layer Transolver replica:

- total parameters: **3,865,673**;
- first six blocks + embedding constitute approximately **75.85%** of parameters;
- final two blocks: approximately **24.15%**.

A 5→64→512 FiLM adapter has approximately:

**33,664 parameters**, <0.9% of the backbone.

Recommended first low-data probe:

- load official pretrained backbone;
- freeze **all** pretrained parameters;
- train only:
  - source adapter;
  - new plume head.

Only if this fails for an identifiable representation reason should the last 1–2 pretrained blocks be unfrozen.

## 8. Clean pretraining controls

### P — pretrained frozen
Official GeoPT backbone frozen + source adapter/head.

### R — random frozen
Identical random-initialized backbone frozen + identical adapter/head.

This isolates representational value of pretraining.

### S — from scratch end-to-end
Identical Transolver architecture trained from scratch using the same gas data.

This tests whether enough gas data can simply relearn the physics representation.

### P-FT — pretrained partial fine-tune
Only after P shows positive transfer:
unfreeze last one/two blocks.

Do not start from P-FT.

## 9. Real House02 runtime probe

Using the real House02 PMFS grid:

- 631 free-space tokens;
- 142 exported PMFS source candidates.

CPU, four threads, official architecture replica:

### Environment cache

First six blocks:

**0.108 s**

for one House02 environment.

### Candidate scan

Inject 142 different source candidates, process each through the final two blocks, batch size 16:

**3.359 s total**

or

**0.02365 s/candidate**.

Peak process RSS:

~**452 MiB**.

This is an interface/runtime test with random model weights.

It does not establish prediction quality.

GPU runtime should be measured by Codex after actual checkpoint loading.

## 10. Why this is a PMFS-specific second innovation

GeoPT alone predicts physical quantities for one conditioned physical problem.

PMFS requires:

> evaluate many hypothetical source interventions inside the **same** environment at every source update.

The cached-environment / source-injection construction exploits exactly that structure:

[
(O,W)
quad	ext{fixed}
]

while

[
do(S=s_1),do(S=s_2),ldots
]

are swept cheaply.

This is more than putting source coordinates into a generic neural operator input.

## 11. Hard scientific test

On the shared GADEN pilot:

1. freeze environment/source split;
2. train P/R/S with identical plume data;
3. hold out at least one source position and seed;
4. generate candidate plume predictions;
5. run identical PMFS source replay.

Primary metric:

**truth-containing source-candidate rank.**

The source adapter only matters if it transfers source interventions into better source identity.

## 12. Kill conditions

Kill this adapter design if:

- source-conditioned predictions remain nearly source-independent;
- injecting after block 6 is too late to model transport;
- random frozen features perform the same as pretrained frozen features;
- source-rank does not improve;
- performance only appears after unfreezing most of the backbone.

Status:

`READY FOR ACTUAL-CHECKPOINT LOAD + SHARED-PILOT TRAINING`.
