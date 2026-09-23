# M6 Update — Cached Environment Representation + Candidate Source Injection

Date: 2026-09-23

## Current architecture hypothesis

For one PMFS source-update step, geometry and wind are shared by all candidate sources.

Therefore compute the pretrained GeoPT environment representation once:

[
H_{env}=B_{1:6}(E_{GeoPT}(O,W)).
]

For each candidate source (s), inject only a small source-relative descriptor:

[
r_s(x)=[x-s,|x-s|,Q_s(x)]
]

through a zero-initialized FiLM adapter after block 6, then run the final two Physics-Attention blocks and a gas head.

This keeps the source candidate as a PMFS counterfactual intervention without modifying the pretrained raw input projection.

## Parameter/runtime evidence

Official-compatible 8-layer Transolver:
- total: 3.866M parameters;
- first six blocks + embedding: ~75.85%;
- last two blocks: ~24.15%;
- 5→64→512 source FiLM adapter: 33,664 parameters (<0.9%).

Real House02 PMFS scale:
- 631 free-space tokens;
- 142 source candidates.

CPU 4-thread random-weight runtime:
- cached first-six-block environment pass: ~0.108 s;
- 142 candidate injections + last-two-block passes: ~3.359 s total;
- ~0.02365 s/candidate;
- peak RSS ~452 MiB.

This is only a computational/interface result, not a performance claim.

## Recommended first learning protocol

P — official pretrained GeoPT frozen + source adapter/head only.

R — identical random frozen backbone + same adapter/head.

S — identical Transolver trained from scratch.

P-FT — partial fine-tune only if P already shows transfer.

The main foundation-model claim requires P to beat R/S in the low-data regime and ultimately improve truth-source candidate rank.

## Status

`M6 = ADVANCE, PENDING ACTUAL CHECKPOINT LOAD + SHARED-PILOT LOW-DATA TEST`.
