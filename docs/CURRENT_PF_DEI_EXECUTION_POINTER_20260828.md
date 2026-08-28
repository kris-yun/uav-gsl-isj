# CURRENT PF-DEI EXECUTION POINTER — 2026-08-28

## FINAL authorized task

`docs/CODEX_PF_DEI_FINAL_AUTONOMOUS_CLOSED_LOOP_20260828.md`

Normative method freeze:

`docs/PF_DEI_FINAL_METHOD_FREEZE_20260828.md`

This final plan supersedes all earlier PF-DEI execution tasks and the earlier broad closed-loop master plan.

Key corrections in the final plan:

- one final source-independent GADEN nuisance family is frozen **before** historical source-ranking results; there is no result-driven second transport-expansion round;
- source emission strength `Q` is explicitly audited/factorized instead of silently assuming fixed amplitude;
- the final runtime method uses native measured ppm and the exact persistent sensor model through simulation; historical deconvolution remains diagnostic only;
- candidate-conditioned NRE architecture/training protocol is fixed in advance; Codex may not perform architecture/model search;
- training trajectory skeletons are source-independent to prevent planner/trajectory shortcut leakage;
- PF-DEI posterior is recomputed from the complete run prefix and replaces only the PMFS source-posterior/evidence channel; it is not multiplied/blended with the native observation posterior, avoiding double counting;
- the native PMFS navigation-cost-aware planner remains unchanged;
- truth-blind historical predictive qualification is required before truth/performance is opened;
- after the final task starts, no scientific redesign is allowed. Only engineering fixes that preserve frozen contracts are permitted.

Do not execute as current authority:

- `CODEX_PF_DEI_CLOSED_LOOP_TO_FINAL_VERDICT_20260828.md`;
- `CODEX_PF_DEI_PHYSICAL_FORWARD_BANK_20260828.md`;
- `CODEX_PF_DEI_RUNLEVEL_SOURCE_EVIDENCE_20260828.md`;
- older deconvolution/sensor-memory/occupancy/Markov/V5 Active-Probe tasks.

Preserve all prior evidence/commits. Continue automatically under the final task until a defined terminal GO/NO-GO/engineering STOP state is reached.