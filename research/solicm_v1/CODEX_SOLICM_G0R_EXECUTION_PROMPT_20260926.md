# CODEX TASK — SOLICM-G0R Repaired Latent Causal Alignment Transfer Gate

Branch:
`research/solicm-latent-causal-g0r-20260926`

Authoritative charter:
`research/solicm_v1/SOLICM_G0R_REPAIR_CHARTER_20260926.md`

Original frozen branch remains immutable:
`research/solicm-latent-causal-g0-20260926`

Hard scope:
- 0 new plume;
- same H02 W0/W2 six-source bank and E2 probe/time contract;
- no H01 DEV;
- no House03;
- no G1A bank;
- no performance-driven hyperparameter search;
- do not reuse old 49 completed runs.

Phase S — implement the repaired reference semantics:
1. copy/vendor the original pinned LCA code into a new `solicm_v1` vendor path;
2. preserve original vendor copy unchanged;
3. implement only the chartered corrections:
   - raw logits classifier;
   - single-softmax pseudo-label/probability path;
   - true sampled-z return;
   - z_dim=9;
   - logvar clamp [-20,20];
   - log1p raw ppm + source-global scalar standardization;
   - target classifier BN running-stat isolation;
4. hash every changed file and write an exact patch manifest.

Phase C — software conformance:
1. run C1-C7 exactly;
2. export `SOLICM_G0R_SOFTWARE_CONFORMANCE.json` and logs;
3. if any check fails, stop with `SOLICM_G0R_SOFTWARE_CONFORMANCE_STOP`;
4. do NOT inspect target-label performance during this phase.

Phase L — fresh scientific lock:
1. freeze all model configs, folds, seeds, bootstrap seeds and file hashes AFTER conformance passes;
2. write `SOLICM_G0R_PRE_RUN_LOCK.json`;
3. record old G0 hashes only for provenance, not for result reuse.

Phase G0R — complete matrix:
1. rerun all 96 configs from scratch;
2. export raw heldout logits before any probability transformation;
3. compute metrics from a single softmax;
4. report pseudo-label coverage and BN counters;
5. independently recompute all metrics and inherited G0-1..G0-6;
6. issue exactly one G0R decision;
7. stop immediately.

Required deliverables:
- repaired-code patch manifest;
- `SOLICM_G0R_SOFTWARE_CONFORMANCE.json`;
- conformance logs;
- `SOLICM_G0R_PRE_RUN_LOCK.json`;
- repaired input-scaling audit;
- all 96 per-run configs/checkpoints/logits/metrics if training is authorized;
- pseudo-label coverage table;
- BN running-state audit;
- latent shape/path audit;
- direction×source summary;
- seed summary;
- 10,000 cluster-bootstrap output;
- latent-structure descriptive audit;
- `SOLICM_G0R_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `SOLICM_G0R_SOFTWARE_CONFORMANCE_STOP`
- `SOLICM_G0R_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL`
- `SOLICM_G0R_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL`
- `SOLICM_G0R_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL`