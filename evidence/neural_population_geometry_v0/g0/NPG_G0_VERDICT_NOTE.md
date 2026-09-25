# NPG-G0 reference-only decision

Frozen decision: `NPG_G0_STOP_GEOMETRY_NOT_BETTER_THAN_ORDINARY_SELECTION`. This is a zero-plume House02 reference-bank test of a new mother-theory mapping. JTD-E2 STOP remains unchanged.

The 84 disjoint 0.3 m source pairs show benefit heterogeneity: 66 positive and 18 negative A/B-mean interaction utilities. G0-1 passes.

GEOMETRY versus AUDIT utility: Spearman +0.017151, pair-bootstrap 95% interval [-0.2096419518153564, 0.24419210207439881]. Split A -0.408849; Split B +0.316209. G0-2 fails.

GEOMETRY has a lower mean squared prediction error than INNER_CV by +0.004699, interval [0.00036605244635686354, 0.010298028484264542]; G0-3 passes. This does not establish prospective benefit-sign selection: balanced accuracy is 0.484848 for GEOMETRY versus 0.699495 for INNER_CV. G0-4 fails. G0-5 passes (4/4 bands).

The frozen decision is STOP because G0-2 and G0-4 fail. No predictor, transform, alpha grid, pair set, or threshold was revised after AUDIT utility was revealed. No G1 method-development stage, E2 target, H01 DEV, House03, neural network or closed loop was run.

Independent audit refit the 336 AUDIT pair models and 840 held-out geometry/scalar predictions, recomputed all 10,000 pair-bootstrap draws, and reproduced every gate.
