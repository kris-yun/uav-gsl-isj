# One execution only

## A. Full-support template bank first

1. Verify F0 and this package hashes.
2. Verify canonical 624-source geometry bank.
3. Verify full 54,912 PMFS seed manifest:
   - exact old 1,056 rows preserved;
   - 54,912 seeds unique;
   - disjoint from 96 GADEN seeds.
4. Generate all 54,912 PMFS forwards.
5. Export u/rawu from identical realizations.
6. Build/freeze nominal and state0 stress templates for all 624 candidates and
   both paths.
7. Regression-test OPEN implementation and Native occurrence invariance.
8. Freeze code/templates/evaluator as `pre_target_freeze`.

If the full bank cannot be afforded/completed:
STOP `AOD_F1_HOLD_FULL624_BUDGET`.
Do not create a 12-candidate scientific substitute after signing this contract.

## B. Timebase audit

9. Add logging-only physical-time/wind-index instrumentation.
10. Generate the FIRST scheduled GADEN run only.
11. Read only runtime/time/writer/release/wind metadata, no concentration.
12. Verify release t=0 and exact times 50..500.
13. Commit `timebase_freeze` or HOLD.

## C. Fresh sealed targets

14. Generate all 96 scheduled fresh GADEN realizations.
15. Verify 96/96 exact sources, seeds, duration and asset hashes.
16. Extract exactly one concentration snapshot at each frozen slot for each
    frozen path.
17. Freeze target arrays/hashes before scoring.

## D. One evaluation

18. Score 624 candidates using nominal u/rawu B2.
19. Score 624 candidates using state0 stress u/rawu B2.
20. Run secondary B0/ICRA comparators if available.
21. Apply `evaluate_f1_full624.py` semantics exactly.
22. Compute fixed diagnostics.
23. Repeat evaluation byte-identically.
24. Package evidence and STOP.

No source/path/seed/wind/score/support change after Step 1.
