# CODEX handoff — P3T-D0 preparation

Date: 2026-10-01

Do not run this task until R1P5 has completed and its decision has been committed.

Read:
1. research/p3t_world_model_v0/MAINLINE_CANDIDATE_20261001.md
2. research/p3t_world_model_v0/P3T_D0_GAUSSIAN_SUPPORT_KILL_TEST.md
3. evidence/pmfs3d_r1_oracle_ranking_20261001/R1_FINAL_REPORT_20261001.md
4. research/pmfs3d_r1/R1_FORWARD_CONTRACT_FINAL.md

The first action is provenance recovery only:
- locate the exact R1 center trajectories or instrument the frozen R1 oracle binary to export them without changing dynamics;
- locate the exact GADEN/Gaden-RT diffusion parameters used by the historical simulator/dataset;
- prove that the Gaussian covariance schedule is physics-derived and fixed before truth evaluation.

If the covariance schedule is ambiguous and requires result-driven tuning, return P3T_D0_INVALID_STOP.

When provenance is clean, implement the Gaussian cell-prism support operator as specified in the frozen D0 charter. Keep candidate geometry, center dynamics, CFD, measured map and likelihood unchanged.

No new GADEN plume generation, H03, training or closed loop.

Commit code, provenance, tests and D0 evidence on a fresh branch created from the current research line. STOP after D0.
