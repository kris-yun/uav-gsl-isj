# LSC Cross-Wind D0 — Independent Primary Audit

Date: 2026-09-25

Decision: **ACCEPT `LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`**

## 1. Review-package integrity

Uploaded review package:
`LSC_CROSSWIND_D0_REVIEW_20260925.tar.gz`

- bytes: 1,166,593;
- SHA256: `ac7a4c22bbaa2d91b42361b1b8163e746ddd3d78819ba89e270ec6ee814a875f`;
- internal SHA256SUMS: 406 files checked, 0 mismatch;
- 128 manifest files present;
- W1 manifests: 64;
- W2 manifests: 64;
- 128 unique seeds;
- 0 duplicate wind/source/replicate keys.

The uploaded standalone wind-hash TSV is byte-identical to the packaged TSV.

## 2. Frozen analyzer independently rerun

The packaged frozen analyzer was executed directly on the packaged W0/W1/W2 tensors, without using the packaged result JSON.

Reproduced W0 integrity anchor:
- split-energy rho = 0.696969697;
- direction-A energy-vs-fresh-error rho = -0.368705921;
- direction-B = -0.557272224.

Reproduced new-wind results:

### W1 = `3,5-1_fast`
- A rho = -0.747957592; hard-easy = 0.375000;
- B rho = -0.494156096; hard-easy = 0.291667;
- split-energy stability = 0.951515152.

### W2 = `4,5-3_slow`
- A rho = -0.166695252; hard-easy = 0.166667;
- B rho = -0.343917970; hard-easy = 0.083333;
- split-energy stability = 0.769696970.

Pooled:
- A rho = -0.463059074;
- B rho = -0.356945405;
- split-energy rho = 0.751879699.

Frozen gates:
- G1 = FAIL;
- G2 = PASS;
- G3 = PASS;
- G4 = PASS.

Therefore the independently reproduced decision is:

`LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`.

## 3. Infrastructure patch audit

The pre-data patch changes only:
- W0 16-replicate tensor selection to frozen reps 1-8 for the 4/4 anchor;
- SciPy Spearman result access from `.statistic` to tuple index 0;
- missing runner/package infrastructure.

The W0 anchor reproduced exactly after the repair and no W1/W2 outcome informed the patch.

Therefore this is an execution-layer repair, not a scientific-contract modification.

## 4. Scientific interpretation

LSC is not rejected as a House02/W0 descriptive phenomenon.

What fails is the stronger claim that one scalar local distribution-separation statistic gives a sufficiently stable cross-wind mapping to fresh source-pair confusion.

Important pattern:
- W1 exhibits a strong distinguishability/confusion relation;
- W2 preserves energy-distance split stability but weakens its relationship to fresh confusion;
- G2/G3/G4 passing means local ordering structure remains present;
- G1 failing in both pooled split directions means the preregistered cross-wind predictive-strength requirement is not met.

Thus the correct conclusion is:

> local stochastic source overlap is environment/operator dependent enough that the W0 mechanism cannot be promoted as a wind-general mainline mechanism.

## 5. No-rescue rule

Do not:
- add seeds;
- replace W2;
- lower the rho threshold;
- switch the primary metric to Bhattacharyya after reveal;
- cherry-pick W1;
- enter closed loop.

## 6. Reusable evidence

Retain:
- D1R/R0 reference assets;
- evidence that local source confusion exists within individual wind regimes;
- W1/W2 data as cross-operator failure evidence;
- the lesson that a source-confusability statistic itself is operator dependent.

Do not retain LSC as the paper main scientific mechanism.

## 7. Mainline implication

The next candidate must explain or explicitly condition on operator/environment dependence **before** claiming a universal source-confusion geometry.

Any future representation/inference mechanism should be tested for cross-operator invariance early, before algorithm development or closed-loop experiments.