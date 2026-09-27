# F1 scientific contract draft — NOT YET AUTHORIZED

After F0 returns a valid frozen panel/path/wind package, the main thread should
sign the final numeric gate before generating fresh gas.

Provisional fresh budget:
- House03;
- 12 sources / 6 0.30 m neighbour pairs;
- 8 independent GADEN plume realizations/source;
- total 96 fresh plumes;
- each plume yields both frozen 10-step sparse paths.

Candidate PMFS template bank:
- 12 sources x 11 wind states x 8 deterministic transport replicas
  = 1056 PMFS forward realizations;
- `u` and `rawu` exported from the SAME realizations.

Primary causal comparison:
- exact same target observations;
- exact same candidate support;
- exact same B2 score;
- only amplitude observation operator changes:
  C0=`u`, C1=`rawu`.

Primary pair margin:
for truth source s and its predeclared neighbour k,

`margin_arm = SSE_arm(k) - SSE_arm(s)`

(higher is better)

`Delta_pair = margin_rawu - margin_u`.

Evaluation aggregation:
target/path -> source -> pair -> House03.
The 6 source pairs are the main spatial generalization units.

Secondary:
- 12-candidate true-source rank;
- unique Top1;
- MAP source-center error;
- binary B0;
- ICRA-2026 EDF-rank comparator.

Mismatch:
repeat C0/C1 scoring with state0-only candidate templates.
Do not create extra plume.

Recommended labels after numeric gate is signed:

`AOD_F1_RESOLUTION_CONFIRMED`
nominal fresh data confirms that decoupled/unblurred amplitude improves
neighbour-source discrimination.

`AOD_F1_RESOLUTION_ROBUSTNESS_TRADEOFF`
nominal effect confirms, but state0-only mismatch shows a predeclared loss of
robustness; this supports a resolution-vs-robustness scientific conclusion,
not universal rawu superiority.

`AOD_F1_NOT_CONFIRMED`
nominal fresh result fails the signed discrimination gate.

No closed loop is authorized by F0.
