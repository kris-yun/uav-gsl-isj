# JTD-G0 frozen decision

Decision: `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`

Base R0 commit: `e527beea07c33cdbc362d156545409245f029968`; A0 input contract: PASS (18 x 16 full realizations).

Ordered 10 x 30 raw pooled ppm was verified by exact re-extraction of all 288 cubes.

FULL mean NLL: 1.45592972; median SHUFFLED mean NLL: 3.177093.
Relative gain: 0.541742; empirical p: 0.00497512.
Paired hierarchical-bootstrap 95% CI: [0.612207371, 2.99747968].
Four fold paired deltas: [1.9258837826319306, 0.8719216042815673, 2.5512503971985074, 0.9039843804124976].
Positive sources: 17/18; positive leave-one-source-out: 18/18.
Median truth rank FULL / null: 1 / 1.
Top-3 FULL / null: 0.982639 / 0.951389.

Allowed claim: only the frozen 18-source R0 discovery-gate outcome under this Gaussian working model.
Forbidden claim: dense-source, real-flight, or general path-likelihood validation.
No closed loop, dense expansion, new plume, or hyperparameter rescue was run.
Final commit and ZIP SHA256 are reported externally after immutable artifacts are committed and packaged.
