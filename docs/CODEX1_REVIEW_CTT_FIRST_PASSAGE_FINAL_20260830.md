# CODEX1 REVIEW CONTRACT — CTT causal first-passage final H01 offline chain

Date: 2026-08-30
Review type: **independent source/provenance/science-contract audit**

## Review target

Repository: `kris-yun/uav-gsl-isj`
Branch: `research/ctt-causal-first-passage-event-inference-20260830`
Base: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Use the exact PR head SHA supplied in the PR body. Do not review a later moving branch head.

## Required checks

1. Verify all nine Python source files against `CTT_FINAL_LOCAL_SHA256_20260830.tsv` where listed. Report any mismatch.
2. `py_compile` every Python file in the first-passage source directories.
3. Confirm the code never trains on localization error, PMFS posterior/rank, planner outcome, future observation, or closed-loop reward.
4. Confirm sensor state is propagated persistently and the scientific chain is `S -> Z_t -> C_t -> R_t -> M_t -> Y_t` rather than occupancy-to-ppm.
5. Confirm the coarse 8-block event representation and the native 0.2-s first-passage representation are different experiments and that the coarse NO-GO is not overwritten.
6. Confirm `CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_PASS` is only a physical/pseudo-source premise result, not a closed-loop localization claim.
7. Audit the H01 predictive8 provenance correction: one fixed native `--wind` generated the packaged predictive bank; trajectory-specific `H01_wind35` is not a valid parent conditioning variable for that bank.
8. Confirm all neural gates that used the wrong local-wind conditioning remain negative/provenance diagnostics and are not presented as rejection of wind-conditioned CTT in general.
9. Confirm the final factorized neural implementation is exactly survival head + conditional phase head, with fixed proper loss `BCE(ever)+CE(F|ever)` and no test-derived weight.
10. Confirm the final source-evidence verdict remains `CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_NO_GO` and that no later file silently converts it to GO.
11. Audit `CODEX_CTT_H01_WIND_CONDITIONED_M1_BANK_AND_GATE_20260830.md`: it may authorize offline bank generation/training/falsification only, not a 300-s closed loop.
12. Check that the proposed new bank uses the exact generating wind field as M1 context, complete held-out wind contexts, held-out transport keys, native physical ppm, persistent measured ppm, and native 0.2-s timing.
13. Check that failure gates forbid post-hoc rescue by blend/temperature/loss weight/threshold/Top-K/router/posterior projection.
14. Compare base→head and report whether any pre-existing PMFS/GADEN/runtime/verdict file was modified. Expected: additions only.

## Evidence boundary

The branch contains source, preregistration contracts, hashes and terminal scientific documents. Local binary checkpoints and all per-case CSV evidence are not all checked into GitHub.

Therefore source/provenance review can be complete, but numerical reproduction must be reported as `EVIDENCE_COMPLETENESS=PARTIAL` unless the exact external evidence files/checkpoints are separately supplied and hash-verified.

Do not regenerate a new training run and call it reproduction of the frozen result.

## Required Codex1 output

Return one review report with:

- `SOURCE_INTEGRITY = PASS/FAIL`
- `PROVENANCE_AUDIT = PASS/FAIL`
- `CAUSAL_CHAIN_AUDIT = PASS/FAIL`
- `TEMPORAL_MECHANISM_AUDIT = PASS/FAIL`
- `NEURAL_ROLE_AUDIT = PASS/FAIL`
- `NO_GO_PRESERVATION = PASS/FAIL`
- `NEXT_BANK_CONTRACT_AUDIT = PASS/FAIL`
- `CLOSED_LOOP_AUTHORIZATION = NO`
- `EVIDENCE_COMPLETENESS = PARTIAL/COMPLETE`
- blocking findings ordered by severity
- exact reviewed head SHA

Do not merge the PR and do not launch closed loop as part of review.
