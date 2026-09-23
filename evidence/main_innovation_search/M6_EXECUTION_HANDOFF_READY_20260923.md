# M6 execution handoff update

Date: 2026-09-23

M6 now has:
- exact GeoPT interface correction: pos3 + fx11 -> 14-D preprocess input;
- corrected source-injection adapter implementation;
- source-blind House02 12-position train/val/test preregistration;
- low-data transfer charter;
- Codex G0.5→G1 execution task.

M6 branch entrypoint:

`CODEX_M6_G0_5_G1_EXECUTION_TASK.md`

Primary remaining empirical gates:
1. actual official checkpoint load coverage;
2. one-source GADEN generation cost;
3. GeoPT-vs-scratch low-data advantage;
4. held-out truth-source candidate rank.

No large data generation is permitted before the one-source cost benchmark.
