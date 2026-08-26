# CTT V13 House03 M1 checkpoint

This branch is a source-and-evidence checkpoint, not a frozen release and not a
closed-loop success claim.

## Confirmed at this checkpoint

- The native filament simulator can record deterministic time-resolved causal
  fronts on the PMFS Free support.
- Trace replay reconstructs the native cumulative hit-frequency map exactly.
- House03 G0 confirms a current-context versus frozen-bank Free-support maximum
  difference of 0.15.
- The wind-conditioned 201-class first-passage neural field beats the
  capacity-matched unconditioned field on two held-out wind contexts and two
  held-out transport members.
- Pre-Bayes matched-neighbour source-evidence ordering improves, while time
  shuffle, reverse causal time and delay permutation remove the gain.
- Verdict at this boundary: `M1_GO` for the House03 premise library.

## Not yet confirmed

- The first M2/M3 result used a dense 0.2 s pose path.  It is preserved as a
  diagnostic but does not match the approximately 2 s PMFS event ledger and is
  not eligible to advance.
- The corrected sparse-event M2/M3 contract is frozen in
  `CTT_H03_M2_M3_PREMISE_FREEZE_20260826.md`; its new result is pending.
- `J2+J3` has not yet been committed into the online posterior/planner path.
- OFF parity, live shadow activation, a frozen binary, and the House03 300 s
  OFF/ON closed-loop pair remain pending.

## Reproducibility boundary

The Python gates never accept real source truth or final localization error as
training inputs.  The C++ trace bank builder is truth-free and the CTT recorder
is isolated from planner behavior.  Large generated trace banks are identified
by hashes in the evidence contracts and are intentionally not committed.
