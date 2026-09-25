# YMPO Novelty and Claim Boundary v0

Date: 2026-09-25

## Safe claim now

Under the completed House02/W2 D1R bank, local empirical concentration distributions form a more transferable source-observation representation than point-valued mean fields, ordered raw short-time fields, or mean+variance maps.

## Not safe yet

- Young-measure PDE theory is proven for GADEN;
- YMPO is cross-wind or cross-House invariant;
- a measure-valued neural network is better than the quantile baseline;
- Wasserstein/Hellinger is the correct inverse metric;
- real flight needs exactly 5/7/10 samples;
- YMPO improves PMFS closed-loop endpoint error.

## Prior-art boundary

Not novel:
- gas concentration maps;
- mean/variance maps;
- Kernel DM+V;
- Gaussian-process mixture maps;
- GMRF uncertainty maps;
- concentration intermittency / hit maps;
- generic probability-measure learning;
- Young measures;
- Wasserstein distance;
- quantile features.

Potential novelty exists only in the integrated GSL formulation:

1. replace the point-valued plume forward object by a **source-conditioned spatial Young-measure field**;
2. estimate that field from finite short-window samples with permutation invariance;
3. use it to generate a normalized PMFS source posterior;
4. require preservation of the empirically validated local source-distinguishability geometry;
5. validate unseen-source, cross-wind, cross-House and real-flight transfer.

Targeted prior-art searches have not surfaced a GSL method with this exact source-conditioned spatial empirical-measure forward object. This is not a proof of global novelty.

## Strongest ordinary attack

A reviewer can argue that YMPO is only engineered short-window statistics.

Therefore any final method must always report against:
- mean field;
- mean+variance map;
- mean+std+hit;
- hand quantile summary + strong ordinary discriminant model;
- full ordered raw observation;
- generic histogram/KME measure representations.

If a proposed learned YMPO cannot beat the hand quantile baseline on transfer/proper score, downgrade the learned module; do not rescue it with a more elaborate architecture.