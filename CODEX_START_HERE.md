# Codex start here — HOLD before closed loop

The current candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)**.

## Important correction — 2026-09-20

Do **not** start the TNQC House closed-loop matrix yet.

The Orebro3DSEN 2/5/10-min source-identity experiments are only an **external auxiliary representation stress test**. They are not the project’s required offline gate because this project’s target benchmark is the VGR/GADEN House01/02/03 localization task with a 300 s budget and the final PMFS top-5% expected-location error.

The earlier status “OFFLINE POSITIVE / CLOSED-LOOP PENDING” was too strong. Correct status:

**EXTERNAL REPRESENTATION SIGNAL POSITIVE / VGR 300-S OFFLINE LOCALIZATION GATE NOT YET PASSED / CLOSED LOOP ON HOLD.**

Read:
1. `docs/TNQC_VGR_300S_CORRECTION_20260920.md`
2. `docs/TNQC_CODEX_HANDOFF_20260920.md`
3. `docs/TNQC_OFFLINE_GATE_20260920.md` (Orebro auxiliary evidence only)

Do not run `reference/run_tnqc_closed_loop_matrix_20260920.sh` until the VGR 300-s fixed-trajectory/offline localization replay has produced a positive final-error signal and a new explicit GO document has been committed.

No TNQC formula, weight, threshold, or House truth may be tuned while this hold is active.
