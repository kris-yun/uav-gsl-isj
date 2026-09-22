# Next fallback cycle queue

Date: 2026-09-22  
Scope: candidates to test only after the current HCMC independent-plume gate or when spare offline evidence is available.

## A. Higher-order Laplacian Renormalization (adjacent HCRC pivot)

2025 Nature Physics: *Higher-order Laplacian renormalization*  
DOI: 10.1038/s41567-025-02784-1  
Code: https://github.com/nplresearch/higher_order_LRG

Scientific transfer candidate:
construct a higher-order complex from jointly co-observed plume cells / scale triplets rather than a pairwise spatial graph, then ask whether source hypotheses reproduce order-specific diffusion/renormalization signatures.

This is **not an orthogonal replacement for HCRC**. It is a possible pivot if HCMC's particular structure-function representation fails but the broader renormalization idea remains supported.

Required before test:
- source-blind construction of 2-simplex / higher-order interactions;
- no truth-dependent simplex threshold;
- pairwise-Laplacian control;
- higher-order destruction null.

## B. Causal Koopman source identifiability

2025 Communications Physics: *Deep Koopman operators for causal discovery*  
Code: https://github.com/juannat7/kausal

Needed data:
stable candidate-conditioned counterfactual trajectory predictions at sensor-step resolution. The current five source-update snapshots are not enough for an honest dynamics/causality test.

## C. Function-space diffusion posterior

2026 Nature Communications: *FunDiff: Diffusion Models over Function Spaces for Physics-Informed Generative Modeling*  
Code: https://github.com/sifanexisted/fundiff

Needed data:
large pre-split GADEN bank spanning source positions, wind regimes and independent stochastic realizations. The concept is to infer source from compatibility with an entire conditional distribution over plume functions, not one plume realization.

## Priority rule

- If HCMC independent plume PASS: do not replace it; test these only as auxiliary/second-paper directions.
- If HCMC NO-GO but renormalization controls remain physically positive: test higher-order Laplacian RG first.
- If HCMC NO-GO due failure of the entire cross-scale premise: move to Causal Koopman (if temporal counterfactual bank can be exported) before paying the much larger FunDiff data/training cost.
