# Mandatory integration checks

These are software correctness checks, not scientific gates.

1. Re-run all supplied unit tests.
2. Dry-run the PMFS patch against the actual worktree.
3. Inspect the actual fork before suppressing `calculateMutualInformationGas()`;
   confirm it has no movement-relevant side effect in this fork.
4. With BRG disabled, native replay must be behaviorally identical:
   - sourceProbability;
   - varianceOfHitProb;
   - planner goal sequence;
   - declaration timing;
   - result output.
5. With BRG enabled, update BOTH:
   - sourceProbability;
   - simulations.varianceOfHitProb;
   before `chooseGoalAndMove()`.
6. One physical measurement event is consumed once.
7. Bank ID, candidate ordering and map geometry must match exactly.
8. Network/service errors invalidate that learned-arm case; never fall back.
9. Truth source is absent from TCP/runtime inputs.
10. Log q, source map, variance map, chosen goals and event IDs for audit.
