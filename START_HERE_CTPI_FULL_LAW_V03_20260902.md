# START HERE — CTPI-FL V0.3

Status: **ORACLE FALSIFICATION ONLY / HOLD**.

Run order:

1. Read `docs/CTPI_FULL_LAW_THEORY_FREEZE_V03_20260902.md`.
2. Read `docs/RESEARCHSTUDIO_IDEASPARK_TRACE_V03_20260902.md` and `docs/RESEARCHSTUDIO_IMPLEMENTABILITY_AUDIT_V03_20260902.md`.
3. Run mathematical self-tests in `experiments/cg_pc_ctt/ctpi_full_law_core.py` and glue self-test in `ctpi_full_law_gate.py`.
4. Execute truth-blind Stage1 on the frozen 4936-world route bank and verify exact F00 parity plus same-mean/full-law-distinct pairs.
5. Freeze Stage1 hashes. Only then run Stage2 truth evaluation.
6. Stage2 additionally checks whether Proposition 1 is directly load-bearing for localization: when truth has exact-F00-mean/full-law-distinct competitors, full-law persistence must break those ties in the truth direction on aggregate.
7. If Oracle Gate is GO, proceed only to a **bank-free M1 Gate**. Do not start network/SBI, new GADEN generation, or closed loop.

The old CPIR M2/M3 NO-GO conclusions remain frozen and are not reused.
