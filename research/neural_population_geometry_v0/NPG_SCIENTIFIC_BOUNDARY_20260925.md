# Why NPG is scientifically different from JTD

JTD asked whether preserving cross-block dependence improves a source-conditioned Gaussian likelihood.

NPG asks a different question:

> Can task-relevant representation geometry, computed before held-out outcomes, predict whether a temporal interaction code is worth using for a particular source discrimination task under finite reference budget?

The object of interest is not `Sigma_s`.

It is prospective interaction utility as a function of task geometry and sample budget.

JTD can be locally correct and globally fail; NPG is only viable if it predicts that heterogeneity before target outcomes.

## Important 2026 biological support

Wakhloo et al. (Nature Neuroscience 2026) analytically connect neural population geometry and training-sample number to linear-readout generalization.

Hu et al. (Nature Neuroscience, 10 Sep 2026) directly show in an olfactory memory network that odor discrimination training changes task-relevant neural-manifold geometry and that manifold capacity tracks odor discrimination.

These papers motivate the hypothesis but do not prove it for GADEN or source localization.

## Novelty collision

2026 odor-source-localization work already uses generic UMAP manifold learning for diffusion-state clustering.

Therefore the proposed novelty is explicitly NOT dimensionality reduction or manifold learning.

The only potentially novel claim is prospective, task-conditioned, finite-budget prediction/selection of source-discriminative temporal interactions feeding the same source probability map.