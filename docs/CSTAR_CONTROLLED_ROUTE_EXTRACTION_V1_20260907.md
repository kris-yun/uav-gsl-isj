# Bounded controlled-route extraction, seed 12

This follows environment PASS and the 12-realization / 6-source-group provenance
PASS. It does not authorize model training, production smoke or the 12-run gate.

Before reading any new route outcomes, commit geometry-only routes and their
generator. All 12 existing realizations are mandatory. Preserve the original
three leave-one-House-out folds, including every prefix and counterfactual
outcome from each parent. These are development data, not virgin confirmation.

Budget: one 60 s geometry-coverage history per realization, speed 0.5 m/s,
fixed height 0.3 m, cadence 0.2 s, seed 12. At 8,16,...,56 s, extract three
geometry-only 4 s futures from exactly the same prefix, pose and sensor memory.
The 20-step future and 0.1 ppm strict encounter threshold retain the existing
M2 premise definition. The three future endpoints maximize three predeclared
120-degree projections within a 2 m shortest-path budget; no gas or source
labels select them. History uses a deterministic farthest-from-visited graph
tour. Grid paths use four-connected edges and one cell extra clearance. Audit
every connecting segment. Keep all outcomes, even uninformative ones.

This is permitted offline GADEN do(route) extraction, not flight tracking.
Use the restored GADEN-core query executable and archived sensor/timebase code;
verify this query adapter against the already archived real ROS probe frames
before claiming parity. Report the exact commanded/query position deviation.
No concentration banks are built. Actual Nav2 tracking remains a later gate.

Inherit the VGR replay clock explicitly: one stored 0.5 s gas snapshot per
0.2 s sensor update (2.5x field playback), not a new physical-time equivalence
claim. Sensor parameters must equal the audited environment manifest. Copy
the complete causal sensor state at each branch, never reset branch memory.
The simulator's raw-gas delay queue is unavailable in deployment, so sensor
internal state is **absent** from model inputs; only measured history is allowed.
Raw gas and branch future gas/wind are evaluator-only files. Bootstrap is not
a measured wind observation. M1 uses the frozen 4,8,...,60 s causal prefixes,
with the complete geometry-only source candidate domain unchanged.

The existing asset validator must enforce provenance and the exact parent fold,
not merely require their path fields. An M2 outcome parent must agree with its
M1 history parent. Sharing a geometry-only route is not sharing outcome data;
the same physical realization or history/outcome payload across train/test is
forbidden. Pair checks must occur within each fold role. A qualified asset
report is not evidence that PICR/CPO improve scientific or closed-loop metrics.
