# CODEX Handoff — LSC Cross-Wind D0

Branch:
`research/lsc-crosswind-d0-v0`

Read first:

1. `research/local_stochastic_confusability_v0/LSC_CROSSWIND_D0_PROTOCOL_20260925.md`
2. `research/local_stochastic_confusability_v0/analyze_lsc_crosswind_d0.py`

Task is **mechanism confirmation only**.

Do NOT:
- modify PASS thresholds;
- select different sources;
- select different winds;
- add seeds after reveal;
- train PMFS/closed-loop models;
- run IPTO/FSEI/RR-MVSI;
- use plume results to replace the source panel.

Execution:

1. verify House02 occupancy and canonical wind inventory hashes;
2. audit seed namespace `2026110001..2026110128` for collisions;
3. reuse the frozen D1R/Gate1A generator/extractor contract;
4. generate exactly 64 runs for `3,5-1_fast`;
5. generate exactly 64 runs for `4,5-3_slow`;
6. consolidate each wind into `[8,8,10,30]` raw-ppm NPY;
7. hash every artifact;
8. run the frozen analyzer once;
9. write the JSON result and short integrity/decision MD;
10. package all manifests, tensors, analyzer, hashes and decision into
   `/home/zyc/LSC_CROSSWIND_D0_REVIEW_20260925.tar.gz`;
11. commit/push evidence and STOP.

Report only:
- final branch/commit;
- exact wind paths/hashes;
- source count / reps / total runs;
- W0 anchor reproduction;
- W1/W2 per-direction rho and hard-easy gaps;
- pooled G1-G4 values;
- frozen decision;
- review package path/bytes/SHA256.

A scientific FAIL is final for this LSC mainline configuration.
