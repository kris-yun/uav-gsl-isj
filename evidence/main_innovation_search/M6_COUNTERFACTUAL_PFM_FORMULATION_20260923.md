# M6 paper-level formulation update — Counterfactual Physics Foundation Model

Date: 2026-09-23

M6 should NOT be described as “fine-tune GeoPT on gas.”

The stronger PMFS-specific formulation is:

[
(O,W)ightarrow Z_{env}
]

once through a cross-physics pretrained foundation backbone, then each PMFS candidate source is queried as a controlled intervention

[
do(S=s_i)
]

through a small source-injection operator followed by shared source-conditioned transport blocks.

Working name:

**Counterfactual Physics Foundation Model (CF-PFM) for PMFS.**

This combines:
- M6 cross-physics foundation representation;
- a limited M4-style intervention factorization;

without yet claiming full causal discovery.

M4 remains a stronger independent causal-compositional claim only if the 2×2 unseen source×wind recombination gate passes.

Hard M6 evidence is still required:
- low-data pretrained > from-scratch;
- unseen-source generalization;
- truth-source rank;
- independent plume seed;
- destructive nulls.

No promotion to final main innovation yet.
